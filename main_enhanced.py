from fastapi import FastAPI, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from datetime import datetime, timedelta
import uuid, json, os
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding

app = FastAPI(title="MostaGare License Server", version="2.0.0")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

LICENSE_FILE = "data/licenses.json"
RULES_FILE = "data/rules.json"
RULES_HISTORY = "data/rules_history.json"
LOG_FILE = "data/activations.log"
KEYS_DIR = "data/keys"
ACTIVATIONS_FILE = "data/activations.json"  # Nouveau : stockage détaillé des activations

# Utils

def load_rules():
    with open(RULES_FILE, "r") as f:
        return json.load(f)

def save_rules(data):
    if os.path.exists(RULES_HISTORY):
        with open(RULES_HISTORY, "r") as f:
            history = json.load(f)
    else:
        history = []
    history.append({"timestamp": datetime.now().isoformat(), "rules": data})
    with open(RULES_HISTORY, "w") as f:
        json.dump(history, f, indent=2)
    with open(RULES_FILE, "w") as f:
        json.dump(data, f, indent=2)

def save_license(license_data):
    if os.path.exists(LICENSE_FILE):
        with open(LICENSE_FILE, "r") as f:
            data = json.load(f)
    else:
        data = []
    data.append(license_data)
    with open(LICENSE_FILE, "w") as f:
        json.dump(data, f, indent=2)

def find_license_by_key(key):
    if not os.path.exists(LICENSE_FILE):
        return None
    with open(LICENSE_FILE, "r") as f:
        licenses = json.load(f)
    for lic in licenses:
        if lic["key"] == key:
            return lic
    return None

def find_license_by_email_project(email, project):
    """Trouver une licence existante pour ce client et ce projet"""
    if not os.path.exists(LICENSE_FILE):
        return None
    with open(LICENSE_FILE, "r") as f:
        licenses = json.load(f)
    for lic in licenses:
        if lic["email"] == email and lic["project"] == project:
            return lic
    return None

def update_license(key, update):
    with open(LICENSE_FILE, "r") as f:
        data = json.load(f)
    for lic in data:
        if lic["key"] == key:
            lic.update(update)
    with open(LICENSE_FILE, "w") as f:
        json.dump(data, f, indent=2)

def log_activation(entry):
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")

def save_activation_details(activation_data):
    """Sauvegarder les détails d'activation pour suivi précis"""
    if os.path.exists(ACTIVATIONS_FILE):
        with open(ACTIVATIONS_FILE, "r") as f:
            activations = json.load(f)
    else:
        activations = []
    
    activations.append(activation_data)
    with open(ACTIVATIONS_FILE, "w") as f:
        json.dump(activations, f, indent=2)

def get_active_machines_for_license(license_key):
    """Récupérer les machines actives pour une licence donnée"""
    if not os.path.exists(ACTIVATIONS_FILE):
        return []
    
    with open(ACTIVATIONS_FILE, "r") as f:
        activations = json.load(f)
    
    # Filtrer par licence et récupérer les activations uniques par machine
    license_activations = {}
    for activation in activations:
        if activation["license_key"] == license_key:
            device_id = activation["device_id"]
            # Garder la dernière activation pour chaque machine
            if device_id not in license_activations or activation["timestamp"] > license_activations[device_id]["timestamp"]:
                license_activations[device_id] = activation
    
    return list(license_activations.values())

def update_license_max_activations(email, project, new_max_activations):
    """Mettre à jour le nombre maximum d'activations pour une licence spécifique"""
    if not os.path.exists(LICENSE_FILE):
        return False
    
    with open(LICENSE_FILE, "r") as f:
        licenses = json.load(f)
    
    updated = False
    for lic in licenses:
        if lic["email"] == email and lic["project"] == project:
            old_max = lic.get("max_activations", 3)
            lic["max_activations"] = new_max_activations
            
            # Ajouter un historique de modification
            if "config_history" not in lic:
                lic["config_history"] = []
            
            lic["config_history"].append({
                "timestamp": datetime.now().isoformat(),
                "action": "update_max_activations",
                "old_value": old_max,
                "new_value": new_max_activations,
                "admin_action": True
            })
            updated = True
    
    if updated:
        with open(LICENSE_FILE, "w") as f:
            json.dump(licenses, f, indent=2)
        
        # Re-signer la licence mise à jour
        for lic in licenses:
            if lic["email"] == email and lic["project"] == project:
                sign_license(lic)
                break
    
    return updated

def sign_license(data):
    pubkey_path = os.path.join(KEYS_DIR, "public.pem")
    privkey_path = os.path.join(KEYS_DIR, "private.pem")
    os.makedirs(KEYS_DIR, exist_ok=True)

    # Génération de la paire si absente (PyCA cryptography)
    if not os.path.exists(privkey_path) or not os.path.exists(pubkey_path):
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public_key = private_key.public_key()

        with open(privkey_path, "wb") as f:
            f.write(
                private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption(),
                )
            )
        with open(pubkey_path, "wb") as f:
            f.write(
                public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo,
                )
            )
    else:
        with open(privkey_path, "rb") as f:
            private_key = serialization.load_pem_private_key(f.read(), password=None)

    # Signature RSA-PKCS1v1.5 + SHA256 sur un JSON CANONIQUE (stable)
    payload = json.dumps(data, sort_keys=True, separators=(",", ":")).encode()
    signature = private_key.sign(
        payload,
        padding.PKCS1v15(),
        hashes.SHA256()
    )

    signed_data = {
        "license": data,
        "signature": signature.hex(),   # on garde hex pour compat client (Node/Python)
        "alg": "RSA-PKCS1v1.5-SHA256"
    }
    path = f"data/licenses/{data['key']}.signed.json"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(signed_data, f, indent=2)
    return path


# Page d'accueil
@app.get("/", response_class=HTMLResponse)
def home_page(request: Request):
    return templates.TemplateResponse("home.html", {
        "request": request,
        "menu": [
            {"label": "🎟️ Demander une licence", "url": "/license"},
            {"label": "📋 Licences générées", "url": "/admin/licenses"},
            {"label": "⚙️ Règles de délivrance", "url": "/admin/rules"},
            {"label": "🔐 Gestion des clés", "url": "/admin/keys"},
            {"label": "👥 Gestion des postes", "url": "/admin/activations"},  # Nouveau
            {"label": "📈 Journal des activations", "url": "/admin/rules/history"}
        ]
    })

# Formulaire public
@app.get("/license", response_class=HTMLResponse)
def show_form(request: Request):
    rules = load_rules()
    return templates.TemplateResponse("form.html", {"request": request, "projects": rules["projects"]})

@app.post("/request-license")
def request_license(email: str = Form(...), project: str = Form(...)):
    rules = load_rules()
    project_info = next((p for p in rules["projects"] if p["id"] == project), None)
    if not project_info:
        raise HTTPException(400, "Projet invalide")
    
    # Vérifier s'il existe déjà une licence pour ce client/projet
    existing_license = find_license_by_email_project(email, project)
    if existing_license:
        # Retourner la licence existante
        return RedirectResponse(f"/license-success?key={existing_license['key']}&existing=true", status_code=303)
    
    key = f"{project.upper()}-{uuid.uuid4().hex[:4]}-{uuid.uuid4().hex[:4]}"
    now = datetime.now()
    license_data = {
        "key": key,
        "email": email,
        "project": project,
        "version": project_info["version"],
        "created_at": now.isoformat(),
        "expires_at": (now + timedelta(days=rules["default_rules"]["license_duration_days"])).isoformat(),
        "status": "ACTIVE",
        "activations": [],  # Changé : liste détaillée au lieu d'un compteur
        "max_activations": rules["default_rules"]["max_activations"]
    }
    save_license(license_data)
    signed_path = sign_license(license_data)
    return RedirectResponse(f"/license-success?key={key}", status_code=303)

@app.get("/license-success", response_class=HTMLResponse)
def show_success(request: Request, key: str, existing: bool = False):
    return templates.TemplateResponse("success.html", {
        "request": request, 
        "key": key, 
        "existing": existing
    })


# --- API pour gestion des activations ---

class ActivationRequest(BaseModel):
    license_key: str
    device_id: str
    device_name: str = "Unknown Device"
    os_info: str = ""
    hostname: str = ""

@app.post("/api/activate")
def activate_device(payload: ActivationRequest, request: Request):
    """Activer un nouveau poste pour une licence"""
    lic = find_license_by_key(payload.license_key)
    if not lic:
        raise HTTPException(404, "Licence inconnue")
    
    if lic["status"] != "ACTIVE":
        raise HTTPException(403, "Licence inactive")
    
    # Vérifier expiration
    if datetime.now() > datetime.fromisoformat(lic["expires_at"]):
        raise HTTPException(403, "Licence expirée")
    
    # Récupérer les activations actuelles
    active_machines = get_active_machines_for_license(payload.license_key)
    
    # Vérifier si cet appareil est déjà activé
    existing_activation = next((m for m in active_machines if m["device_id"] == payload.device_id), None)
    if existing_activation:
        return {
            "status": "already_active",
            "message": "Appareil déjà activé",
            "activation_date": existing_activation["timestamp"],
            "remaining_activations": lic["max_activations"] - len(active_machines)
        }
    
    # Vérifier la limite d'activations
    if len(active_machines) >= lic["max_activations"]:
        raise HTTPException(403, f"Limite d'activations atteinte ({lic['max_activations']} postes maximum)")
    
    # Créer la nouvelle activation
    activation_data = {
        "license_key": payload.license_key,
        "device_id": payload.device_id,
        "device_name": payload.device_name,
        "os_info": payload.os_info,
        "hostname": payload.hostname,
        "ip_address": request.client.host,
        "timestamp": datetime.now().isoformat(),
        "status": "active"
    }
    
    save_activation_details(activation_data)
    
    # Mettre à jour la licence
    new_activations = active_machines + [activation_data]
    update_license(payload.license_key, {
        "activations": [{"device_id": a["device_id"], "timestamp": a["timestamp"]} for a in new_activations]
    })
    
    return {
        "status": "activated",
        "message": "Poste activé avec succès",
        "activation_date": activation_data["timestamp"],
        "remaining_activations": lic["max_activations"] - len(new_activations)
    }

@app.delete("/api/deactivate/{license_key}/{device_id}")
def deactivate_device(license_key: str, device_id: str):
    """Désactiver un poste"""
    lic = find_license_by_key(license_key)
    if not lic:
        raise HTTPException(404, "Licence inconnue")
    
    # Marquer l'activation comme inactive
    if os.path.exists(ACTIVATIONS_FILE):
        with open(ACTIVATIONS_FILE, "r") as f:
            activations = json.load(f)
        
        for activation in activations:
            if (activation["license_key"] == license_key and 
                activation["device_id"] == device_id and 
                activation.get("status") == "active"):
                activation["status"] = "deactivated"
                activation["deactivated_at"] = datetime.now().isoformat()
        
        with open(ACTIVATIONS_FILE, "w") as f:
            json.dump(activations, f, indent=2)
    
    # Mettre à jour la licence
    active_machines = get_active_machines_for_license(license_key)
    active_machines = [m for m in active_machines if m["device_id"] != device_id]
    
    update_license(license_key, {
        "activations": [{"device_id": a["device_id"], "timestamp": a["timestamp"]} for a in active_machines]
    })
    
    return {"status": "deactivated", "message": "Poste désactivé"}

# --- API pour configuration administrative ---

class ConfigUpdateRequest(BaseModel):
    email: str
    project: str
    max_activations: int

@app.post("/api/admin/update-max-activations")
def admin_update_max_activations(payload: ConfigUpdateRequest):
    """Mettre à jour le nombre maximum de postes pour une licence spécifique"""
    if payload.max_activations < 1 or payload.max_activations > 20:
        raise HTTPException(400, "Le nombre de postes doit être entre 1 et 20")
    
    success = update_license_max_activations(
        payload.email, 
        payload.project, 
        payload.max_activations
    )
    
    if not success:
        raise HTTPException(404, "Licence non trouvée")
    
    return {
        "success": True,
        "message": f"Limite mise à jour : {payload.max_activations} postes maximum",
        "email": payload.email,
        "project": payload.project,
        "new_limit": payload.max_activations
    }

# --- Interface d'administration des activations ---

@app.get("/admin/activations", response_class=HTMLResponse)
def admin_activations(request: Request):
    """Page d'administration des activations/postes"""
    if not os.path.exists(LICENSE_FILE):
        licenses = []
    else:
        with open(LICENSE_FILE, "r") as f:
            licenses = json.load(f)
    
    # Enrichir avec les données d'activation
    for lic in licenses:
        active_machines = get_active_machines_for_license(lic["key"])
        lic["active_machines"] = active_machines
        lic["active_count"] = len(active_machines)
    
    return templates.TemplateResponse("activations_admin.html", {
        "request": request, 
        "licenses": licenses
    })

@app.post("/admin/activations/update-limit")
def admin_update_activation_limit(
    email: str = Form(...),
    project: str = Form(...),
    max_activations: int = Form(...)
):
    """Formulaire pour mettre à jour la limite d'activations"""
    if max_activations < 1 or max_activations > 20:
        raise HTTPException(400, "Le nombre de postes doit être entre 1 et 20")
    
    # Vérifier que la nouvelle limite n'est pas inférieure au nombre actuel d'activations
    lic = find_license_by_email_project(email, project)
    if lic:
        active_machines = get_active_machines_for_license(lic["key"])
        if max_activations < len(active_machines):
            raise HTTPException(400, f"Impossible de définir une limite inférieure au nombre de postes actuellement actifs ({len(active_machines)})")
    
    success = update_license_max_activations(email, project, max_activations)
    
    if not success:
        raise HTTPException(404, "Licence non trouvée")
    
    return RedirectResponse("/admin/activations", status_code=303)

# Le reste du code reste identique...
# (Copier tout le reste du fichier original à partir de la ligne suivante)

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

@app.post("/api/licenses/generate-from-client")
def generate_license_from_client(request: Request, data: dict):
    """
    Reçoit : {
      email, project, version, device_id, os_info, hostname, ...
    }
    Retourne : fichier de licence signée
    """
    rules = load_rules()
    project_info = next((p for p in rules["projects"] if p["id"] == data["project"]), None)
    if not project_info:
        raise HTTPException(400, "Projet non reconnu")

    key = f"{data['project'].upper()}-{uuid.uuid4().hex[:4]}-{uuid.uuid4().hex[:4]}"
    now = datetime.now()
    license_data = {
        "key": key,
        "email": data["email"],
        "project": data["project"],
        "version": data.get("version", project_info["version"]),
        "device_id": data["device_id"],
        "created_at": now.isoformat(),
        "expires_at": (now + timedelta(days=rules["default_rules"]["license_duration_days"])).isoformat(),
        "status": "ACTIVE",
        "activations": [],
        "max_activations": rules["default_rules"]["max_activations"],
        "os_info": data.get("os_info"),
        "hostname": data.get("hostname")
    }

    save_license(license_data)

    # Génération ou chargement des clés RSA avec cryptography
    pubkey_path = os.path.join(KEYS_DIR, "public.pem")
    privkey_path = os.path.join(KEYS_DIR, "private.pem")
    os.makedirs(KEYS_DIR, exist_ok=True)
    if not os.path.exists(privkey_path) or not os.path.exists(pubkey_path):
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public_key = private_key.public_key()
        with open(privkey_path, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        with open(pubkey_path, "wb") as f:
            f.write(public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ))
    else:
        with open(privkey_path, "rb") as f:
            private_key = serialization.load_pem_private_key(f.read(), password=None)

    # Signature du JSON canonique avec RSA SHA256
    payload = json.dumps(license_data, sort_keys=True, separators=(",", ":")).encode()
    signature = private_key.sign(
        payload,
        padding.PKCS1v15(),
        hashes.SHA256()
    )

    signed_data = {
        "license": license_data,
        "signature": signature.hex(),
        "alg": "RSA-PKCS1v1.5-SHA256"
    }

    path = f"data/licenses/{key}.signed.json"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(signed_data, f, indent=2)

    return FileResponse(path, filename=f"{key}.signed.json", media_type="application/json")


# --- Signature verification helper & endpoint (cryptography/PyCA) ---
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding


def _verify_signed_license_file(filepath: str) -> bool:
    """Return True if the signed license JSON verifies with public.pem (RSA PKCS1v1.5 SHA256)."""
    pubkey_path = os.path.join(KEYS_DIR, "public.pem")
    if not os.path.exists(pubkey_path):
        raise HTTPException(404, "Clé publique introuvable. Générez-la depuis /admin/keys.")
    if not os.path.exists(filepath):
        raise HTTPException(404, "Fichier de licence signé introuvable.")

    # Load public key
    with open(pubkey_path, "rb") as f:
        public_key = serialization.load_pem_public_key(f.read())

    # Load signed JSON
    with open(filepath, "r") as f:
        signed = json.load(f)

    if not isinstance(signed, dict) or "license" not in signed or "signature" not in signed:
        raise HTTPException(400, "Format de licence invalide.")

    # Rebuild the exact payload the server signed (same json.dumps default settings)
    payload = json.dumps(signed["license"]).encode()
    signature = bytes.fromhex(signed["signature"])

    try:
        public_key.verify(
            signature,
            payload,
            padding.PKCS1v15(),
            hashes.SHA256(),
        )
        return True
    except Exception:
        return False


@app.get("/verify-signature")
def verify_signature(key: str):
    """
    Vérifie localement la signature d'une licence signée :
    GET /verify-signature?key=GESTIGARE-ABCD-1234
    """
    filepath = f"data/licenses/{key}.signed.json"
    ok = _verify_signed_license_file(filepath)
    return {"key": key, "valid_signature": ok}

@app.get("/download-license")
def download_license(key: str):
    path = f"data/licenses/{key}.signed.json"
    if not os.path.exists(path):
        raise HTTPException(404, "Fichier introuvable")
    return FileResponse(path, filename=f"{key}.signed.json", media_type="application/json")

# Formulaire de génération des règles
@app.get("/admin/rules", response_class=HTMLResponse)
def show_rules_form(request: Request):
    rules = load_rules()
    return templates.TemplateResponse("rules_form.html", {"request": request, "rules": rules})

@app.post("/admin/rules")
def update_rules(
    license_duration_days: int = Form(...),
    max_activations: int = Form(...),
    restrict_same_email: bool = Form(False),
    allow_multiple_versions: bool = Form(False),
    require_device_id: bool = Form(False),
    check_expiration: bool = Form(False),
    track_ip_address: bool = Form(False),
    limit_by_version: bool = Form(False),
    require_api_token: bool = Form(False),
    rate_limit_per_ip_per_hour: int = Form(...),
    log_requests: bool = Form(False)
):
    if license_duration_days < 30 or license_duration_days > 1825:
        raise HTTPException(400, "Durée invalide (30-1825 jours)")
    if max_activations < 1 or max_activations > 100:
        raise HTTPException(400, "Activations entre 1 et 100")

    rules = load_rules()
    rules["default_rules"].update({
        "license_duration_days": license_duration_days,
        "max_activations": max_activations,
        "restrict_same_email": restrict_same_email,
        "allow_multiple_versions": allow_multiple_versions
    })
    rules["activation_rules"].update({
        "require_device_id": require_device_id,
        "check_expiration": check_expiration,
        "track_ip_address": track_ip_address,
        "limit_by_version": limit_by_version
    })
    rules["security"].update({
        "require_api_token": require_api_token,
        "rate_limit_per_ip_per_hour": rate_limit_per_ip_per_hour,
        "log_requests": log_requests
    })
    save_rules(rules)
    return RedirectResponse("/admin/rules", status_code=303)

@app.post("/admin/rules/reset")
def reset_rules():
    with open("data/rules_default.json", "r") as f:
        defaults = json.load(f)
    save_rules(defaults)
    return RedirectResponse("/admin/rules", status_code=303)

@app.get("/admin/rules/history", response_class=HTMLResponse)
def show_rules_history(request: Request):
    if not os.path.exists(RULES_HISTORY):
        return templates.TemplateResponse("rules_history.html", {"request": request, "history": []})
    with open(RULES_HISTORY, "r") as f:
        history = json.load(f)
    return templates.TemplateResponse("rules_history.html", {"request": request, "history": history})
 
 
# Page d'administration des licences avec recherche et suppression
@app.get("/admin/licenses", response_class=HTMLResponse)
def admin_licenses(request: Request, q: str = ""):
    if not os.path.exists(LICENSE_FILE):
        licenses = []
    else:
        with open(LICENSE_FILE, "r") as f:
            licenses = json.load(f)
    if q:
        q = q.lower()
        licenses = [lic for lic in licenses if q in lic["email"].lower() or q in lic["project"].lower() or q in lic["key"].lower()]
    return templates.TemplateResponse("licenses_admin.html", {"request": request, "licenses": licenses, "query": q})

@app.post("/admin/licenses/delete")
def delete_license(key: str = Form(...)):
    if not os.path.exists(LICENSE_FILE):
        raise HTTPException(404, "Aucune licence")
    with open(LICENSE_FILE, "r") as f:
        licenses = json.load(f)
    updated = [lic for lic in licenses if lic["key"] != key]
    with open(LICENSE_FILE, "w") as f:
        json.dump(updated, f, indent=2)
    # Supprimer le fichier signé si existant
    signed_path = f"data/licenses/{key}.signed.json"
    if os.path.exists(signed_path):
        os.remove(signed_path)
    return RedirectResponse("/admin/licenses", status_code=303)

@app.get("/admin/licenses/export")
def export_licenses_csv():
    import csv
    from io import StringIO

    if not os.path.exists(LICENSE_FILE):
        raise HTTPException(404, "Aucune licence")

    with open(LICENSE_FILE, "r") as f:
        licenses = json.load(f)

    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=["key", "email", "project", "version", "status", "activations", "max_activations", "expires_at"])
    writer.writeheader()
    for lic in licenses:
        writer.writerow({
            "key": lic["key"],
            "email": lic["email"],
            "project": lic["project"],
            "version": lic.get("version", ""),
            "status": lic["status"],
            "activations": len(lic.get("activations", [])),
            "max_activations": lic["max_activations"],
            "expires_at": lic["expires_at"]
        })

    response = HTMLResponse(content=output.getvalue(), media_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=licenses.csv"
    return response

from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, PlainTextResponse

# Formulaire pour générer la paire de clés
@app.get("/admin/keys", response_class=HTMLResponse)
def show_keygen_form(request: Request):
    return templates.TemplateResponse("keys_form.html", {"request": request})

@app.post("/admin/keys")
def generate_keypair_safe():
    pubkey_path = os.path.join(KEYS_DIR, "public.pem")
    privkey_path = os.path.join(KEYS_DIR, "private.pem")
    if os.path.exists(pubkey_path) or os.path.exists(privkey_path):
        raise HTTPException(400, "❗ Clé déjà générée. Utilisez /admin/keys/force pour forcer.")
    os.makedirs(KEYS_DIR, exist_ok=True)

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()

    with open(privkey_path, "wb") as f:
        f.write(
            private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )
    with open(pubkey_path, "wb") as f:
        f.write(
            public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
        )
    return RedirectResponse("/admin/keys", status_code=303)


@app.get("/admin/keys/download")
def download_public_key():
    pubkey_path = os.path.join(KEYS_DIR, "public.pem")
    if not os.path.exists(pubkey_path):
        raise HTTPException(404, "Clé publique introuvable")
    return FileResponse(pubkey_path, filename="public.pem", media_type="application/x-pem-file")

@app.get("/admin/keys/preview", response_class=PlainTextResponse)
def preview_public_key():
    pubkey_path = os.path.join(KEYS_DIR, "public.pem")
    if not os.path.exists(pubkey_path):
        return "❌ Clé publique non générée."
    with open(pubkey_path, "r") as f:
        return f.read()

@app.post("/admin/keys/force")
def generate_keypair_force():
    pubkey_path = os.path.join(KEYS_DIR, "public.pem")
    privkey_path = os.path.join(KEYS_DIR, "private.pem")
    os.makedirs(KEYS_DIR, exist_ok=True)

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()

    with open(privkey_path, "wb") as f:
        f.write(
            private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )
    with open(pubkey_path, "wb") as f:
        f.write(
            public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
        )
    return RedirectResponse("/admin/keys", status_code=303)

    
from fastapi import BackgroundTasks
import smtplib
from email.message import EmailMessage

@app.get("/admin/keys/send")
def send_public_key(background_tasks: BackgroundTasks):
    pubkey_path = os.path.join(KEYS_DIR, "public.pem")
    if not os.path.exists(pubkey_path):
        raise HTTPException(404, "Clé publique introuvable")

    def send_email():
        msg = EmailMessage()
        msg["Subject"] = "Clé publique AMIA"
        msg["From"] = "licence@amia.fr"
        msg["To"] = "admin@amia.fr"
        msg.set_content("Veuillez trouver ci-joint la clé publique.")

        with open(pubkey_path, "rb") as f:
            msg.add_attachment(f.read(), filename="public.pem", maintype="application", subtype="x-pem-file")

        with smtplib.SMTP("localhost") as smtp:
            smtp.send_message(msg)

        background_tasks.add_task(send_email)
    return {"message": "✉️ Clé envoyée par email (en arrière-plan)"}


# API de vérification
class VerifyRequest(BaseModel):
    key: str
    device_id: str
    version: str

@app.post("/verify")
def verify_license(payload: VerifyRequest, request: Request):
    rules = load_rules()
    lic = find_license_by_key(payload.key)
    if not lic:
        raise HTTPException(404, "Licence inconnue")
    if lic["status"] != "ACTIVE":
        raise HTTPException(403, "Licence inactive")
    if rules["activation_rules"]["limit_by_version"] and lic["version"] != payload.version:
        raise HTTPException(403, "Version non autorisée")
    if rules["activation_rules"]["check_expiration"] and datetime.now() > datetime.fromisoformat(lic["expires_at"]):
        raise HTTPException(403, "Licence expirée")
    
    # Nouvelle logique pour gérer les activations détaillées
    active_machines = get_active_machines_for_license(payload.key)
    
    if len(active_machines) >= lic["max_activations"]:
        # Vérifier si cet appareil est déjà dans la liste
        existing = next((m for m in active_machines if m["device_id"] == payload.device_id), None)
        if not existing:
            raise HTTPException(403, "Limite d'activation atteinte")

    if rules["activation_rules"]["track_ip_address"]:
        log_activation({
            "key": payload.key,
            "device_id": payload.device_id,
            "ip": request.client.host,
            "timestamp": datetime.now().isoformat()
        })

    return {"status": "valid", "project": lic["project"], "expires_at": lic["expires_at"]}

if __name__ == "__main__":
    import uvicorn
    print("🚀 Serveur de licences MostaGare v2.0.0")
    print("📋 Fonctionnalités :")
    print("   • Gestion avancée des postes/activations")
    print("   • Configuration dynamique du nombre de postes")
    print("   • Interface d'administration complète")
    print("   • API REST pour intégration")
    uvicorn.run(app, host="0.0.0.0", port=8000)