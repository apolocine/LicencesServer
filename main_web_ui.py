#!/usr/bin/env python3
"""
MostaGare License Server avec Interface Web Complète
Serveur d'activation de licences avec authentification et interface d'administration
"""

from fastapi import FastAPI, HTTPException, Form, File, UploadFile, Request, Depends, status, Cookie
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from datetime import datetime, timedelta
import json
import os
import uuid
import hashlib
import hmac
import base64
import bcrypt
from jose import jwt
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration de l'application
app = FastAPI(
    title="MostaGare License Server with Web UI",
    description="Serveur d'activation de licences avec interface web",
    version="4.0.0"
)

# CORS pour permettre les requêtes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Configuration des fichiers
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

# Fichiers de données
USERS_CONF_FILE = os.path.join(DATA_DIR, "users_conf.json")
REQUIRED_EMAIL_FILE = os.path.join(DATA_DIR, "required_email.json")
REQUIRED_ALL_EMAIL_FILE = os.path.join(DATA_DIR, "required_all_email.json")
ACTIVATIONS_FILE = os.path.join(DATA_DIR, "activations.json")
ACTIVATION_CODES_FILE = os.path.join(DATA_DIR, "activation_codes.json")
PUBLIC_KEY_FILE = os.path.join(DATA_DIR, "public.pem")
PRIVATE_KEY_FILE = os.path.join(DATA_DIR, "private.pem")

# Configuration JWT
JWT_SECRET = "your-secret-key-here-change-in-production"
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Templates
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Modèles Pydantic
class ActivationRequest(BaseModel):
    activation_code: str
    license_data: dict
    machine_id: str = None

class User(BaseModel):
    username: str
    role: str
    email: str
    permissions: list
    active: bool

# Utilitaires d'authentification
def load_users():
    """Charger les utilisateurs depuis le fichier de configuration"""
    try:
        with open(USERS_CONF_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifier le mot de passe avec bcrypt"""
    try:
        return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())
    except:
        return False

def create_access_token(data: dict):
    """Créer un token JWT"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

def get_current_user(request: Request):
    """Récupérer l'utilisateur actuel depuis le cookie ou token"""
    token = request.cookies.get("access_token")
    if not token:
        return None
    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        username = payload.get("sub")
        if username is None:
            return None
    except jwt.PyJWTError:
        return None
    
    users = load_users()
    user_data = users.get(username)
    if user_data is None or not user_data.get('active', False):
        return None
        
    return User(**user_data)

def require_auth(request: Request):
    """Décorateur pour exiger l'authentification"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Non authentifié"
        )
    return user

def require_permission(permission: str):
    """Décorateur pour exiger une permission spécifique"""
    def check_permission(request: Request):
        user = require_auth(request)
        if permission not in user.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission requise: {permission}"
            )
        return user
    return check_permission

# Utilitaires des licences (reprises de main_activation.py)
def ensure_data_files():
    """S'assurer que tous les fichiers de données existent"""
    os.makedirs(DATA_DIR, exist_ok=True)
    
    if not os.path.exists(ACTIVATIONS_FILE):
        with open(ACTIVATIONS_FILE, 'w') as f:
            json.dump([], f, indent=2)
    
    if not os.path.exists(ACTIVATION_CODES_FILE):
        with open(ACTIVATION_CODES_FILE, 'w') as f:
            json.dump({}, f, indent=2)

def load_software_config(project_name):
    """Charger la configuration pour un logiciel spécifique"""
    try:
        with open(REQUIRED_ALL_EMAIL_FILE, 'r') as f:
            configs = json.load(f)
            return configs.get(project_name, {})
    except FileNotFoundError:
        return {}

def get_all_software_configs():
    """Récupérer toutes les configurations de logiciels"""
    try:
        with open(REQUIRED_ALL_EMAIL_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_all_software_configs(configs):
    """Sauvegarder toutes les configurations"""
    with open(REQUIRED_ALL_EMAIL_FILE, 'w') as f:
        json.dump(configs, f, indent=2)

def load_activation_codes():
    """Charger les codes d'activation"""
    try:
        with open(ACTIVATION_CODES_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_activation_codes(codes):
    """Sauvegarder les codes d'activation"""
    with open(ACTIVATION_CODES_FILE, 'w') as f:
        json.dump(codes, f, indent=2)

def get_stats():
    """Récupérer les statistiques du serveur"""
    codes = load_activation_codes()
    projects = get_all_software_configs()
    
    return {
        "total_licenses": len(projects),
        "active_codes": len([c for c in codes.values() if not c.get('used', False)]),
        "today_activations": 0,  # TODO: calculer depuis les activations
        "total_projects": len(projects)
    }

# Initialisation
ensure_data_files()

# Routes d'authentification
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Redirection vers le login ou dashboard"""
    user = get_current_user(request)
    if user:
        return RedirectResponse(url="/dashboard")
    return RedirectResponse(url="/login")

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Page de connexion"""
    user = get_current_user(request)
    if user:
        return RedirectResponse(url="/dashboard")
    
    # Charger dynamiquement la liste des projets
    projects = get_all_software_configs()
    
    return templates.TemplateResponse("login.html", {
        "request": request,
        "projects": projects
    })

@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    """Traitement de la connexion"""
    users = load_users()
    user_data = users.get(username)
    
    if not user_data or not user_data.get('active', False):
        projects = get_all_software_configs()
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Utilisateur non trouvé ou inactif",
            "username": username,
            "projects": projects
        })
    
    if not verify_password(password, user_data.get('password_hash', '')):
        projects = get_all_software_configs()
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Mot de passe incorrect",
            "username": username,
            "projects": projects
        })
    
    # Mettre à jour la dernière connexion
    user_data['last_login'] = datetime.now().isoformat()
    users[username] = user_data
    with open(USERS_CONF_FILE, 'w') as f:
        json.dump(users, f, indent=2)
    
    # Créer le token
    token = create_access_token({"sub": username})
    
    # Redirection avec cookie
    response = RedirectResponse(url="/dashboard", status_code=302)
    response.set_cookie(
        key="access_token",
        value=token,
        max_age=JWT_EXPIRATION_HOURS * 3600,
        httponly=True,
        secure=False  # True en production avec HTTPS
    )
    return response

@app.get("/logout")
async def logout():
    """Déconnexion"""
    response = RedirectResponse(url="/login")
    response.delete_cookie("access_token")
    return response

# Routes de l'interface d'administration
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, user: User = Depends(require_auth)):
    """Dashboard principal"""
    stats = get_stats()
    recent_activities = []  # TODO: implémenter les activités récentes
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": user,
        "stats": stats,
        "recent_activities": recent_activities
    })

@app.get("/admin/projects", response_class=HTMLResponse)
async def projects_page(request: Request, user: User = Depends(require_permission("manage_licenses"))):
    """Page de gestion des projets"""
    projects = get_all_software_configs()
    return templates.TemplateResponse("projects.html", {
        "request": request,
        "user": user,
        "projects": projects
    })

@app.post("/admin/projects/save")
async def save_project(request: Request, 
                      project_id: str = Form(""),
                      project_name: str = Form(...),
                      required_email: str = Form(...),
                      password: str = Form(""),
                      company_name: str = Form(...),
                      max_activations: int = Form(...),
                      license_duration_days: int = Form(...),
                      description: str = Form(""),
                      user: User = Depends(require_permission("manage_licenses"))):
    """Sauvegarder un projet"""
    
    projects = get_all_software_configs()
    
    project_data = {
        "required_email": required_email,
        "company_name": company_name,
        "max_activations": max_activations,
        "license_duration_days": license_duration_days,
        "project": project_name,
        "description": description,
        "updated_at": datetime.now().isoformat()
    }
    
    if password:
        project_data["password"] = password
    
    if not project_id:  # Nouveau projet
        project_data["created_at"] = datetime.now().isoformat()
    else:
        # Conserver la date de création existante
        if project_id in projects:
            project_data["created_at"] = projects[project_id].get("created_at", datetime.now().isoformat())
        project_name = project_id  # Utiliser l'ID existant
    
    projects[project_name] = project_data
    save_all_software_configs(projects)
    
    return RedirectResponse(url="/admin/projects?message=Projet sauvegardé avec succès", status_code=302)

@app.get("/admin/projects/delete/{project_name}")
async def delete_project(project_name: str, user: User = Depends(require_permission("manage_licenses"))):
    """Supprimer un projet"""
    if project_name == "MostaGare":
        return RedirectResponse(url="/admin/projects?error=Impossible de supprimer le projet principal", status_code=302)
    
    projects = get_all_software_configs()
    if project_name in projects:
        del projects[project_name]
        save_all_software_configs(projects)
    
    return RedirectResponse(url="/admin/projects?message=Projet supprimé avec succès", status_code=302)

@app.get("/admin/codes", response_class=HTMLResponse)
async def codes_page(request: Request, user: User = Depends(require_permission("manage_codes"))):
    """Page de gestion des codes"""
    codes = load_activation_codes()
    projects = get_all_software_configs()
    
    return templates.TemplateResponse("admin_codes_enhanced.html", {
        "request": request,
        "user": user,
        "codes": codes,
        "projects": projects,
        "expired_count": 0  # TODO: calculer les codes expirés
    })

@app.post("/api/admin/generate-code")
async def generate_activation_code(
    project: str = Form(...),
    email: str = Form(...),
    max_activations: int = Form(4),
    duration_days: int = Form(365),
    user: User = Depends(require_permission("manage_codes"))
):
    """Générer un nouveau code d'activation"""
    try:
        # Générer un code unique au format générique
        code = f"{uuid.uuid4().hex[:4].upper()}-{uuid.uuid4().hex[:4].upper()}-{uuid.uuid4().hex[:4].upper()}-{uuid.uuid4().hex[:4].upper()}"
        
        codes = load_activation_codes()
        
        # Vérifier l'unicité
        while code in codes:
            code = f"{uuid.uuid4().hex[:4].upper()}-{uuid.uuid4().hex[:4].upper()}-{uuid.uuid4().hex[:4].upper()}-{uuid.uuid4().hex[:4].upper()}"
        
        # Créer l'entrée du code
        codes[code] = {
            "email": email,
            "project": project,
            "max_activations": max_activations,
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(days=duration_days)).isoformat(),
            "used": False,
            "used_count": 0
        }
        
        save_activation_codes(codes)
        
        return RedirectResponse(url="/admin/codes?message=Code généré avec succès", status_code=302)
        
    except Exception as e:
        logger.error(f"Erreur génération code: {e}")
        return RedirectResponse(url="/admin/codes?error=Erreur lors de la génération", status_code=302)

@app.get("/admin/codes/delete/{code}")
async def delete_code(code: str, user: User = Depends(require_permission("manage_codes"))):
    """Supprimer un code d'activation"""
    codes = load_activation_codes()
    if code in codes and not codes[code].get('used', False):
        del codes[code]
        save_activation_codes(codes)
        return RedirectResponse(url="/admin/codes?message=Code supprimé avec succès", status_code=302)
    
    return RedirectResponse(url="/admin/codes?error=Impossible de supprimer ce code", status_code=302)

@app.get("/admin/users", response_class=HTMLResponse)
async def users_page(request: Request, user: User = Depends(require_permission("manage_users"))):
    """Page de gestion des utilisateurs"""
    users = load_users()
    return templates.TemplateResponse("users.html", {
        "request": request,
        "user": user,
        "users": users
    })

@app.post("/admin/users/save")
async def save_user(request: Request,
                    username: str = Form(...),
                    email: str = Form(...),
                    role: str = Form(...),
                    password: str = Form(""),
                    active: bool = Form(True),
                    user: User = Depends(require_permission("manage_users"))):
    """Sauvegarder un utilisateur"""
    users = load_users()
    
    # Définir les permissions par rôle
    role_permissions = {
        "admin": ["manage_users", "manage_codes", "manage_licenses", "view_stats"],
        "manager": ["manage_codes", "manage_licenses", "view_stats"],
        "viewer": ["view_stats"]
    }
    
    user_data = {
        "username": username,
        "email": email,
        "role": role,
        "permissions": role_permissions.get(role, []),
        "active": active,
        "last_login": users.get(username, {}).get('last_login')
    }
    
    # Si nouveau mot de passe fourni, le hasher
    if password:
        user_data["password_hash"] = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    else:
        # Conserver l'ancien hash si pas de nouveau mot de passe
        if username in users:
            user_data["password_hash"] = users[username].get("password_hash")
    
    if username not in users:
        user_data["created_at"] = datetime.now().isoformat()
    else:
        user_data["created_at"] = users[username].get("created_at", datetime.now().isoformat())
    
    users[username] = user_data
    
    with open(USERS_CONF_FILE, 'w') as f:
        json.dump(users, f, indent=2)
    
    return RedirectResponse(url="/admin/users?message=Utilisateur sauvegardé avec succès", status_code=302)

@app.get("/admin/users/delete/{username}")
async def delete_user(username: str, request: Request, user: User = Depends(require_permission("manage_users"))):
    """Supprimer un utilisateur"""
    if username == user.username:
        return RedirectResponse(url="/admin/users?error=Impossible de supprimer votre propre compte", status_code=302)
    
    users = load_users()
    if username in users:
        del users[username]
        with open(USERS_CONF_FILE, 'w') as f:
            json.dump(users, f, indent=2)
    
    return RedirectResponse(url="/admin/users?message=Utilisateur supprimé avec succès", status_code=302)

@app.get("/admin/activations", response_class=HTMLResponse)
async def activations_page(request: Request, user: User = Depends(require_permission("view_stats"))):
    """Page des activations"""
    try:
        with open(ACTIVATIONS_FILE, 'r') as f:
            activations = json.load(f)
    except FileNotFoundError:
        activations = []
    
    codes = load_activation_codes()
    projects = get_all_software_configs()
    
    return templates.TemplateResponse("activations.html", {
        "request": request,
        "user": user,
        "activations": activations,
        "codes": codes,
        "projects": projects
    })

# Route pour demande de code d'activation (public)
@app.post("/api/request-activation-code")
async def request_activation_code(
    email: str = Form(...),
    project: str = Form(...),
    company: str = Form(...),
    message: str = Form("")
):
    """API publique pour demander un code d'activation"""
    try:
        # Vérifier que le projet existe
        projects = get_all_software_configs()
        if project not in projects:
            raise HTTPException(status_code=400, detail="Projet non reconnu")
        
        project_config = projects[project]
        
        # Vérifier l'email autorisé pour ce projet
        required_email = project_config.get('required_email', '')
        if required_email and email.lower() != required_email.lower():
            raise HTTPException(
                status_code=403, 
                detail="Email non autorisé pour ce projet. Veuillez utiliser l'email autorisé pour ce logiciel."
            )
        
        # Créer la demande (pour l'instant, on génère directement le code)
        # Dans une vraie application, on stockerait la demande pour validation manuelle
        
        # Générer automatiquement le code d'activation au format générique
        code = f"{uuid.uuid4().hex[:4].upper()}-{uuid.uuid4().hex[:4].upper()}-{uuid.uuid4().hex[:4].upper()}-{uuid.uuid4().hex[:4].upper()}"
        
        codes = load_activation_codes()
        
        # Vérifier l'unicité du code
        while code in codes:
            code = f"{uuid.uuid4().hex[:4].upper()}-{uuid.uuid4().hex[:4].upper()}-{uuid.uuid4().hex[:4].upper()}-{uuid.uuid4().hex[:4].upper()}"
        
        # Créer l'entrée du code avec les paramètres du projet
        codes[code] = {
            "email": email,
            "project": project,
            "company": company,
            "message": message,
            "max_activations": project_config.get('max_activations', 4),
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(days=project_config.get('license_duration_days', 365))).isoformat(),
            "used": False,
            "used_count": 0,
            "auto_generated": True  # Marquer comme généré automatiquement
        }
        
        save_activation_codes(codes)
        
        return {
            "success": True,
            "message": f"Code d'activation généré: {code}",
            "activation_code": code,
            "project": project,
            "expires_in_days": project_config.get('license_duration_days', 365)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur demande code activation: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors du traitement de la demande")

# Routes API pour les clients (reprises de main_activation.py)
@app.post("/api/download-license")
async def download_license_by_code(request: Request, activationCode: str = Form(None)):
    """API pour télécharger une licence par code d'activation"""
    try:
        # Supporter JSON et form-data
        if not activationCode:
            try:
                body = await request.json()
                activationCode = body.get('activationCode')
            except:
                pass
        
        if not activationCode:
            raise HTTPException(status_code=400, detail="Code d'activation requis")
        
        codes = load_activation_codes()
        
        if activationCode not in codes:
            raise HTTPException(status_code=404, detail="Code d'activation non trouvé")
        
        code_info = codes[activationCode]
        project_name = code_info.get('project', 'MostaGare')
        config = load_software_config(project_name)
        
        # Créer les données de licence au format exact attendu par l'application
        license_data = {
            "activations": [],  # Array vide, pas un nombre
            "company": code_info.get('company', config.get('company_name', 'Unknown')),
            "created_at": datetime.now().isoformat(),
            "email": code_info.get('email', config.get('required_email')),
            "expires_at": code_info.get('expires_at', (datetime.now() + timedelta(days=365)).isoformat()),
            "key": activationCode,  # Code complet, pas tronqué
            "max_activations": code_info.get('max_activations', config.get('max_activations', 4)),
            "project": project_name,
            "status": "ACTIVE",
            "version": "1.0.0"
        }
        
        # Générer une signature RSA compatible avec cryptography
        # Utiliser les vraies clés RSA pour assurer la compatibilité
        try:
            # Charger la clé privée si elle existe
            if os.path.exists(PRIVATE_KEY_FILE):
                with open(PRIVATE_KEY_FILE, 'rb') as f:
                    private_key = serialization.load_pem_private_key(
                        f.read(),
                        password=None
                    )
                
                # Créer le JSON canonique pour signature
                sorted_keys = sorted(license_data.keys())
                sorted_license = {key: license_data[key] for key in sorted_keys}
                canonical_payload = json.dumps(sorted_license, separators=(',', ':'))
                
                # Signer avec RSA-PKCS1v15-SHA256 (compatible avec Node.js crypto)
                signature_bytes = private_key.sign(
                    canonical_payload.encode('utf-8'),
                    padding.PKCS1v15(),
                    hashes.SHA256()
                )
                signature = signature_bytes.hex()
            else:
                # Fallback : signature temporaire compatible
                import base64
                signature_data = f"{project_name}:{activationCode}:{license_data['email']}"
                signature = base64.b64encode(signature_data.encode()).decode()
                logger.warning("Clé privée non trouvée, utilisation signature temporaire")
        except Exception as e:
            # Fallback en cas d'erreur
            import base64
            signature_data = f"{project_name}:{activationCode}:{license_data['email']}"
            signature = base64.b64encode(signature_data.encode()).decode()
            logger.error(f"Erreur signature RSA: {e}, utilisation signature temporaire")
        
        signed_license = {
            "license": license_data,
            "signature": signature,
            "alg": "RSA-PKCS1v15-SHA256"
        }
        
        return signed_license
        
    except Exception as e:
        logger.error(f"Erreur téléchargement licence: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/notify-activation")
async def notify_activation(
    activationCode: str = Form(...),
    machineId: str = Form(...),
    machineName: str = Form(None)
):
    """Notifier le serveur qu'une activation a eu lieu"""
    try:
        codes = load_activation_codes()
        
        if activationCode not in codes:
            raise HTTPException(status_code=404, detail="Code d'activation non trouvé")
        
        code_info = codes[activationCode]
        
        # Incrémenter le compteur d'utilisation
        current_count = code_info.get('used_count', 0)
        code_info['used_count'] = current_count + 1
        
        # Marquer comme utilisé si c'est la première activation
        if not code_info.get('used', False):
            code_info['used'] = True
            code_info['first_activation_at'] = datetime.now().isoformat()
        
        # Enregistrer les détails de la machine si pas déjà fait
        if 'activations' not in code_info:
            code_info['activations'] = []
        
        # Vérifier si cette machine est déjà dans la liste
        machine_exists = any(
            activation.get('machine_id') == machineId 
            for activation in code_info['activations']
        )
        
        if not machine_exists:
            code_info['activations'].append({
                'machine_id': machineId,
                'machine_name': machineName or 'Inconnue',
                'activated_at': datetime.now().isoformat()
            })
        
        # Sauvegarder les modifications
        codes[activationCode] = code_info
        save_activation_codes(codes)
        
        return {
            "success": True,
            "message": "Activation enregistrée",
            "used_count": code_info['used_count'],
            "activations": len(code_info['activations'])
        }
        
    except Exception as e:
        logger.error(f"Erreur notification activation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Vérification de l'état du serveur"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main_web_ui:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )