# Serveur de Licences MostaGare

Ce répertoire contient le code du **serveur de licences** pour MostaGare et autres projets.

## Structure

```
licences_server/
├── main_activation.py          # Serveur FastAPI principal avec nouvelles APIs
├── main_enhanced.py           # Version améliorée du serveur
├── main.py                    # Version originale du serveur
├── add_software_config.py     # Script pour ajouter des configurations de logiciels
├── demo_setup.py             # Configuration de démonstration
├── deploy_enhanced.sh        # Script de déploiement
├── test_verify.py            # Tests de vérification
├── data/                     # Données du serveur
│   ├── required_all_email.json      # Configuration multi-projets
│   ├── activation_codes.json        # Codes d'activation
│   └── software_configs.json        # Configurations des logiciels
├── templates/                # Templates HTML
│   ├── activation_home.html         # Page d'accueil
│   └── admin_codes.html            # Interface admin
├── venv/                     # Environnement virtuel Python
└── __pycache__/             # Cache Python
```

## APIs disponibles

### Serveur principal (main_activation.py)
- `POST /api/download-license` - Télécharger licence par code
- `POST /api/register-activation` - Enregistrer une activation
- `POST /api/activate` - Activer une licence (méthode classique)
- `POST /api/admin/generate-code` - Générer un code d'activation
- `GET /api/softwares` - Liste des logiciels supportés
- `GET /health` - État du serveur

## Démarrage

```bash
cd licences_server
python main_activation.py
# Ou avec uvicorn:
uvicorn main_activation:app --host 0.0.0.0 --port 8000 --reload
```

## Configuration

Les configurations des projets se trouvent dans `data/required_all_email.json`:
- MostaGare
- CRMExpert  
- AccountingPlus
- InventoryPro

Chaque projet a ses propres paramètres d'email, mot de passe, nombre d'activations, etc.