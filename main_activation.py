#!/usr/bin/env python3
"""
MostaGare License Activation Server
Serveur d'activation de licences avec upload de fichier et code d'activation
"""

from fastapi import FastAPI, HTTPException, Form, File, UploadFile, Request
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timedelta
import json
import os
import uuid
import hashlib
import hmac
import base64
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration de l'application
app = FastAPI(
    title="MostaGare License Activation Server",
    description="Serveur d'activation de licences MostaGare",
    version="3.0.0"
)

# CORS pour permettre les requêtes depuis l'application locale
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production, limiter aux domaines autorisés
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Configuration des fichiers
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

# Fichiers de données
REQUIRED_EMAIL_FILE = os.path.join(DATA_DIR, "required_email.json")
ACTIVATIONS_FILE = os.path.join(DATA_DIR, "activations.json")
ACTIVATION_CODES_FILE = os.path.join(DATA_DIR, "activation_codes.json")
PUBLIC_KEY_FILE = os.path.join(DATA_DIR, "public.pem")
PRIVATE_KEY_FILE = os.path.join(DATA_DIR, "private.pem")

# Templates
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Modèles Pydantic
class ActivationRequest(BaseModel):
    activation_code: str
    license_data: dict
    machine_id: str = None

class ActivationResponse(BaseModel):
    success: bool
    message: str = None
    error: str = None
    license_info: dict = None
    remaining_days: int = None

# Utilitaires
def ensure_data_files():
    """S'assurer que tous les fichiers de données existent"""
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # Créer le fichier d'activations s'il n'existe pas
    if not os.path.exists(ACTIVATIONS_FILE):
        with open(ACTIVATIONS_FILE, 'w') as f:
            json.dump([], f, indent=2)
    
    # Créer le fichier des codes d'activation s'il n'existe pas
    if not os.path.exists(ACTIVATION_CODES_FILE):
        # Générer quelques codes d'exemple
        example_codes = {
            "DEMO-DEMO-DEMO-DEMO": {
                "email": "demo@company.com",
                "max_activations": 4,
                "created_at": datetime.now().isoformat(),
                "expires_at": (datetime.now() + timedelta(days=365)).isoformat(),
                "used": False,
                "project": "MostaGare"
            }
        }
        with open(ACTIVATION_CODES_FILE, 'w') as f:
            json.dump(example_codes, f, indent=2)

def load_required_email():
    """Charger les informations d'email requis (compatibilité)"""
    return load_software_config("MostaGare")  # Par défaut MostaGare

def load_software_config(project_name):
    """Charger la configuration pour un logiciel spécifique"""
    # Essayer d'abord le fichier spécifique au projet
    specific_file = os.path.join(DATA_DIR, f"required_email_{project_name.lower()}.json")
    
    if os.path.exists(specific_file):
        with open(specific_file, 'r') as f:
            return json.load(f)
    
    # Essayer le fichier de configurations multiples
    softwares_file = os.path.join(DATA_DIR, "software_configs.json")
    if os.path.exists(softwares_file):
        with open(softwares_file, 'r') as f:
            configs = json.load(f)
            if project_name in configs:
                return configs[project_name]
    
    # Fallback sur la configuration par défaut
    try:
        with open(REQUIRED_EMAIL_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Configuration par défaut
        default_config = {
            "required_email": "user@company.com",
            "company_name": "Default Company",
            "max_activations": 4,
            "license_duration_days": 365,
            "project": project_name,
            "description": f"Configuration par défaut pour {project_name}"
        }
        
        # Sauvegarder la configuration par défaut
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(specific_file, 'w') as f:
            json.dump(default_config, f, indent=2)
        
        return default_config

def get_all_software_configs():
    """Récupérer toutes les configurations de logiciels"""
    configs = {}
    
    # Charger depuis le fichier multi-logiciels
    softwares_file = os.path.join(DATA_DIR, "software_configs.json")
    if os.path.exists(softwares_file):
        with open(softwares_file, 'r') as f:
            configs.update(json.load(f))
    
    # Charger depuis les fichiers individuels
    if os.path.exists(DATA_DIR):
        for filename in os.listdir(DATA_DIR):
            if filename.startswith("required_email_") and filename.endswith(".json"):
                project_name = filename[15:-5]  # Enlever "required_email_" et ".json"
                file_path = os.path.join(DATA_DIR, filename)
                
                try:
                    with open(file_path, 'r') as f:
                        config = json.load(f)
                        # Utiliser le nom du projet depuis le fichier ou déduire du nom de fichier
                        project_key = config.get('project', project_name.title())
                        configs[project_key] = config
                except Exception as e:
                    logger.warning(f"Erreur lecture config {filename}: {e}")
    
    return configs

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

def load_activations():
    """Charger les activations existantes"""
    try:
        with open(ACTIVATIONS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_activation(activation_data):
    """Sauvegarder une nouvelle activation"""
    activations = load_activations()
    activation_data['activated_at'] = datetime.now().isoformat()
    activation_data['id'] = str(uuid.uuid4())
    activations.append(activation_data)
    
    with open(ACTIVATIONS_FILE, 'w') as f:
        json.dump(activations, f, indent=2)
    
    logger.info(f"Nouvelle activation sauvegardée: {activation_data['activation_code']}")

def verify_license_signature(license_data):
    """Vérifier la signature de la licence"""
    try:
        if not os.path.exists(PUBLIC_KEY_FILE):
            return False
            
        with open(PUBLIC_KEY_FILE, 'rb') as f:
            public_key = serialization.load_pem_public_key(f.read())
        
        # Extraire la signature et les données
        if 'signature' not in license_data or 'data' not in license_data:
            return False
            
        signature = base64.b64decode(license_data['signature'])
        data_to_verify = json.dumps(license_data['data'], sort_keys=True).encode()
        
        # Vérifier la signature
        public_key.verify(
            signature,
            data_to_verify,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return True
        
    except Exception as e:
        logger.error(f"Erreur vérification signature: {e}")
        return False

def get_machine_id_from_request(request: Request):
    """Extraire ou générer un ID machine"""
    # Essayer d'obtenir l'ID depuis les headers
    machine_id = request.headers.get('X-Machine-ID')
    
    if not machine_id:
        # Générer un ID basé sur l'IP et User-Agent
        client_ip = request.client.host
        user_agent = request.headers.get('User-Agent', '')
        machine_data = f"{client_ip}-{user_agent}"
        machine_id = hashlib.sha256(machine_data.encode()).hexdigest()[:16]
    
    return machine_id

# Initialisation
ensure_data_files()

# Routes

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Page d'accueil avec informations sur le serveur"""
    configs = get_all_software_configs()
    main_config = load_required_email()  # Configuration par défaut
    
    return templates.TemplateResponse("activation_home.html", {
        "request": request,
        "config": main_config,
        "all_configs": configs,
        "software_count": len(configs)
    })

@app.get("/api/softwares")
async def get_supported_softwares():
    """Obtenir la liste des logiciels supportés"""
    configs = get_all_software_configs()
    
    # Retourner une version simplifiée pour la sécurité
    simplified_configs = {}
    for project, config in configs.items():
        simplified_configs[project] = {
            "project": config.get("project", project),
            "description": config.get("description", f"Logiciel {project}"),
            "max_activations": config.get("max_activations", 4),
            "license_duration_days": config.get("license_duration_days", 365),
            "company_name": config.get("company_name", "Enterprise")
        }
    
    return {
        "softwares": simplified_configs,
        "count": len(simplified_configs)
    }

@app.get("/health")
async def health_check():
    """Vérification de l'état du serveur"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/api/activate", response_model=ActivationResponse)
async def activate_license(
    request: Request,
    activationCode: str = Form(...),
    licenseData: str = Form(...)
):
    """
    Activer une licence avec un code d'activation et les données de licence
    """
    try:
        # Valider le format du code d'activation
        if not activationCode or len(activationCode) != 19:  # XXXX-XXXX-XXXX-XXXX
            raise HTTPException(
                status_code=400,
                detail="Code d'activation invalide (format requis: XXXX-XXXX-XXXX-XXXX)"
            )
        
        # Parser les données de licence
        try:
            license_json = json.loads(licenseData)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=400,
                detail="Données de licence JSON invalides"
            )
        
        # Vérifier la signature de la licence
        if not verify_license_signature(license_json):
            raise HTTPException(
                status_code=400,
                detail="Signature de licence invalide"
            )
        
        # Charger et vérifier le code d'activation
        activation_codes = load_activation_codes()
        
        if activationCode not in activation_codes:
            raise HTTPException(
                status_code=400,
                detail="Code d'activation non reconnu"
            )
        
        code_info = activation_codes[activationCode]
        
        # Vérifier si le code a déjà été utilisé
        if code_info.get('used', False):
            raise HTTPException(
                status_code=400,
                detail="Ce code d'activation a déjà été utilisé"
            )
        
        # Vérifier l'expiration du code
        if 'expires_at' in code_info:
            expires_at = datetime.fromisoformat(code_info['expires_at'])
            if datetime.now() > expires_at:
                raise HTTPException(
                    status_code=400,
                    detail="Code d'activation expiré"
                )
        
        # Déterminer le projet depuis les données de licence
        license_email = license_json.get('data', {}).get('email', '')
        license_project = license_json.get('data', {}).get('project', 'MostaGare')
        
        # Charger la configuration pour ce projet spécifique
        required_config = load_software_config(license_project)
        
        # Vérifier l'email de la licence contre l'email requis pour ce projet
        if license_email != required_config.get('required_email', ''):
            raise HTTPException(
                status_code=403,
                detail=f"Email de licence non autorisé pour {license_project}. Email requis: {required_config.get('required_email')}"
            )
        
        # Générer l'ID machine
        machine_id = get_machine_id_from_request(request)
        
        # Vérifier le nombre d'activations existantes
        activations = load_activations()
        active_activations = [
            a for a in activations 
            if a.get('activation_code') == activationCode and a.get('status') == 'active'
        ]
        
        max_activations = code_info.get('max_activations', required_config.get('max_activations', 4))
        
        if len(active_activations) >= max_activations:
            raise HTTPException(
                status_code=403,
                detail=f"Nombre maximum d'activations atteint ({max_activations})"
            )
        
        # Créer l'activation
        activation_data = {
            'activation_code': activationCode,
            'machine_id': machine_id,
            'email': license_email,
            'license_data': license_json,
            'status': 'active',
            'client_ip': request.client.host,
            'user_agent': request.headers.get('User-Agent', ''),
        }
        
        # Sauvegarder l'activation
        save_activation(activation_data)
        
        # Marquer le code comme utilisé
        activation_codes[activationCode]['used'] = True
        activation_codes[activationCode]['first_used_at'] = datetime.now().isoformat()
        save_activation_codes(activation_codes)
        
        # Calculer les jours restants
        license_expires = license_json.get('data', {}).get('expires_at')
        remaining_days = None
        
        if license_expires:
            try:
                expires_date = datetime.fromisoformat(license_expires)
                remaining_days = (expires_date - datetime.now()).days
            except:
                pass
        
        # Préparer la réponse
        license_info = {
            'email': license_email,
            'project': license_json.get('data', {}).get('project', 'MostaGare'),
            'expires_at': license_expires,
            'activations': len(active_activations) + 1,
            'max_activations': max_activations,
            'key': license_json.get('data', {}).get('key', activationCode[:8])
        }
        
        return ActivationResponse(
            success=True,
            message="Licence activée avec succès",
            license_info=license_info,
            remaining_days=remaining_days
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur activation: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur interne du serveur: {str(e)}"
        )

@app.get("/api/activations")
async def get_activations():
    """Obtenir la liste des activations (pour admin)"""
    activations = load_activations()
    return {"activations": activations, "count": len(activations)}

@app.get("/admin/codes")
async def admin_codes(request: Request):
    """Interface d'administration pour gérer les codes d'activation"""
    codes = load_activation_codes()
    return templates.TemplateResponse("admin_codes.html", {
        "request": request,
        "codes": codes
    })

@app.post("/api/download-license")
async def download_license_by_code(
    activationCode: str = Form(...)
):
    """Télécharger une licence en utilisant seulement le code d'activation"""
    try:
        # Valider le format du code
        if not activationCode or len(activationCode) != 19:
            raise HTTPException(
                status_code=400,
                detail="Code d'activation invalide"
            )
        
        # Charger les codes d'activation
        activation_codes = load_activation_codes()
        
        if activationCode not in activation_codes:
            raise HTTPException(
                status_code=404,
                detail="Code d'activation non trouvé"
            )
        
        code_info = activation_codes[activationCode]
        
        # Vérifier l'expiration
        if 'expires_at' in code_info:
            expires_at = datetime.fromisoformat(code_info['expires_at'])
            if datetime.now() > expires_at:
                raise HTTPException(
                    status_code=403,
                    detail="Code d'activation expiré"
                )
        
        # Récupérer le projet depuis le code
        project_name = code_info.get('project', 'MostaGare')
        
        # Charger la configuration du projet
        config = load_software_config(project_name)
        
        # Générer les clés si elles n'existent pas
        if not os.path.exists(PRIVATE_KEY_FILE) or not os.path.exists(PUBLIC_KEY_FILE):
            from cryptography.hazmat.primitives.asymmetric import rsa
            from cryptography.hazmat.primitives import serialization
            
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048
            )
            
            # Sauvegarder la clé privée
            with open(PRIVATE_KEY_FILE, 'wb') as f:
                f.write(private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                ))
            
            # Sauvegarder la clé publique
            public_key = private_key.public_key()
            with open(PUBLIC_KEY_FILE, 'wb') as f:
                f.write(public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                ))
        
        # Créer les données de licence
        license_data = {
            "key": activationCode[:19],
            "email": code_info.get('email', config.get('required_email')),
            "project": project_name,
            "version": "1.0.0",
            "created_at": datetime.now().isoformat(),
            "expires_at": code_info.get('expires_at', (datetime.now() + timedelta(days=365)).isoformat()),
            "status": "ACTIVE",
            "activations": 0,
            "max_activations": code_info.get('max_activations', config.get('max_activations', 4))
        }
        
        # Signer la licence
        with open(PRIVATE_KEY_FILE, 'rb') as f:
            private_key = serialization.load_pem_private_key(f.read(), password=None)
        
        # Créer la signature
        import json
        data_to_sign = json.dumps(license_data, sort_keys=True).encode()
        signature = private_key.sign(
            data_to_sign,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
        # Créer le fichier de licence signé
        signed_license = {
            "license": license_data,
            "signature": base64.b64encode(signature).decode(),
            "alg": "RSA-PSS-SHA256"
        }
        
        return signed_license
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur téléchargement licence: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/register-activation")
async def register_activation(
    activationCode: str = Form(...),
    machineId: str = Form(...),
    machineName: str = Form(None)
):
    """Enregistrer une activation de machine"""
    try:
        # Charger les codes d'activation
        activation_codes = load_activation_codes()
        
        if activationCode not in activation_codes:
            raise HTTPException(
                status_code=404,
                detail="Code d'activation non trouvé"
            )
        
        # Incrémenter le compteur d'utilisation
        if 'used_count' not in activation_codes[activationCode]:
            activation_codes[activationCode]['used_count'] = 0
        
        activation_codes[activationCode]['used_count'] += 1
        
        # Ajouter l'information de la machine
        if 'machines' not in activation_codes[activationCode]:
            activation_codes[activationCode]['machines'] = []
        
        activation_codes[activationCode]['machines'].append({
            'machine_id': machineId,
            'machine_name': machineName or 'Unknown',
            'activated_at': datetime.now().isoformat()
        })
        
        save_activation_codes(activation_codes)
        
        return {
            "success": True,
            "message": "Activation enregistrée"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur enregistrement activation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/admin/generate-code")
async def generate_activation_code(
    email: str = Form(...),
    max_activations: int = Form(4),
    duration_days: int = Form(365)
):
    """Générer un nouveau code d'activation"""
    try:
        # Générer un code unique
        code = f"{uuid.uuid4().hex[:4].upper()}-{uuid.uuid4().hex[:4].upper()}-{uuid.uuid4().hex[:4].upper()}-{uuid.uuid4().hex[:4].upper()}"
        
        codes = load_activation_codes()
        
        # Vérifier l'unicité
        while code in codes:
            code = f"{uuid.uuid4().hex[:4].upper()}-{uuid.uuid4().hex[:4].upper()}-{uuid.uuid4().hex[:4].upper()}-{uuid.uuid4().hex[:4].upper()}"
        
        # Créer l'entrée du code
        codes[code] = {
            "email": email,
            "max_activations": max_activations,
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(days=duration_days)).isoformat(),
            "used": False,
            "project": "MostaGare"
        }
        
        save_activation_codes(codes)
        
        return {
            "success": True,
            "activation_code": code,
            "message": "Code d'activation généré avec succès"
        }
        
    except Exception as e:
        logger.error(f"Erreur génération code: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    
    # Configuration du serveur
    uvicorn.run(
        "main_activation:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )