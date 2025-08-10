# 🔐 MostaGare License Server - Documentation Complète

  📋 Contenu de la documentation :

  🎯 Vue d'ensemble complète

  - Objectifs et architecture du système
  - Stack technique détaillé
  - Structure des fichiers et dossiers

  🚀 Installation et déploiement

  - Guide étape par étape
  - Configuration des environnements
  - Déploiement en production

  🌐 Interface web détaillée

  - Toutes les pages avec captures fonctionnelles
  - Fonctionnalités de chaque interface
  - Workflows utilisateur

  🔌 APIs RESTful complètes

  - Documentation de toutes les routes
  - Exemples de requêtes/réponses
  - Codes d'erreur et gestion

  🔐 Sécurité approfondie

  - Cryptographie RSA détaillée
  - Authentification JWT
  - Système de permissions RBAC

  📊 Monitoring et données

  - Métriques et statistiques
  - Structure des fichiers JSON
  - Logs et debugging

  🔧 Configuration avancée

  - Variables d'environnement
  - Recommandations de sécurité
  - Déploiement professionnel

  🧪 Tests et maintenance

  - Tests de santé du système
  - Dépannage courant
  - Maintenance préventive

  📚 Intégration cliente

  - Guide d'intégration
  - Exemples de code
  - Bonnes pratiques

  🚀 Roadmap et évolutions

  - Fonctionnalités futures
  - Améliorations prévues
  - Contribution au projet

  Cette documentation est vraiment exhaustive avec plus de 500 lignes couvrant tous les aspects
  du serveur, des détails techniques les plus fins aux guides pratiques d'utilisation ! 📖✨



## 📋 Vue d'ensemble

Le **MostaGare License Server** est une solution complète de gestion et d'activation de licences logicielles. Il fournit une interface web moderne, des APIs RESTful sécurisées et un système de cryptographie RSA pour la génération, la distribution et l'activation de licences pour plusieurs projets logiciels.

### 🎯 Objectifs principaux
- **Centralisation** : Gestion unifiée des licences pour plusieurs projets
- **Sécurité** : Signatures cryptographiques RSA et authentification robuste
- **Automatisation** : Génération et activation automatisées
- **Monitoring** : Suivi en temps réel des activations et statistiques
- **Interface moderne** : Interface web responsive avec design professionnel

---

## 🏗️ Architecture du système

### 📁 Structure du projet
```
licences_server/
├── main_web_ui.py              # Serveur principal FastAPI
├── generate_keys.py            # Générateur de clés RSA
├── setup_users.py              # Configuration utilisateurs
├── requirements.txt            # Dépendances Python
├── data/                       # Données du serveur
│   ├── users_conf.json         # Configuration utilisateurs
│   ├── activation_codes.json   # Codes d'activation
│   ├── required_all_email.json # Configuration projets
│   ├── private.pem             # Clé privée RSA
│   └── public.pem              # Clé publique RSA
└── templates/                  # Templates HTML
    ├── login.html              # Page d'accueil/login
    ├── dashboard.html          # Tableau de bord
    ├── projects.html           # Gestion des projets
    ├── admin_codes_enhanced.html # Gestion des codes
    ├── users.html              # Gestion des utilisateurs
    └── activations.html        # Historique des activations
```

### 🔧 Stack technique
- **Backend** : FastAPI (Python 3.11+)
- **Authentification** : JWT + bcrypt
- **Cryptographie** : RSA-PKCS1v15-SHA256
- **Frontend** : HTML5 + Tailwind CSS + JavaScript
- **Serveur** : Uvicorn ASGI
- **Base de données** : Fichiers JSON (léger et portable)

---

## 🚀 Installation et déploiement

### Prérequis
```bash
# Python 3.11 ou supérieur
python3 --version

# Pip pour l'installation des dépendances
pip --version
```

### 📦 Installation des dépendances
```bash
# Créer un environnement virtuel
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# Installer les dépendances
pip install -r requirements.txt
```

### 🔑 Génération des clés RSA
```bash
# Générer les clés de signature
python3 generate_keys.py
```

### 👥 Configuration des utilisateurs
```bash
# Créer les comptes administrateurs
python3 setup_users.py
```

### ▶️ Lancement du serveur
```bash
# Mode développement
python3 main_web_ui.py

# Mode production
uvicorn main_web_ui:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## 🌐 Interface web

### 🏠 Page d'accueil (`/`)
**Fonctionnalités :**
- **Présentation moderne** du système de licences
- **Formulaire de demande** de codes d'activation
- **Sélection de projet** (MostaGare, CRMExpert, etc.)
- **Génération automatique** de codes
- **Accès administration** via modal sécurisé

**Champs du formulaire :**
- Email du demandeur
- Projet/Logiciel cible
- Nom de l'entreprise
- Message optionnel

### 🔐 Authentification (`/login`)
**Système de sécurité :**
- Authentification JWT avec cookies HTTPOnly
- Mots de passe hashés avec bcrypt
- Sessions sécurisées (24h par défaut)
- Gestion des erreurs et redirections

**Comptes par défaut :**
- `admin / admin123` - Accès complet
- `manager / manager123` - Gestion codes/licences

### 📊 Dashboard (`/dashboard`)
**Métriques affichées :**
- Total des licences gérées
- Codes d'activation actifs
- Activations du jour
- Nombre de projets

**Actions rapides :**
- Génération de codes
- Gestion des projets
- Consultation des activations
- Administration utilisateurs

### 🏢 Gestion des projets (`/admin/projects`)
**Fonctionnalités :**
- **CRUD complet** des projets logiciels
- Configuration des emails autorisés
- Paramétrage des durées de licence
- Gestion du nombre d'activations
- Descriptions et métadonnées

**Paramètres configurables :**
- Nom du projet
- Email requis pour activation
- Mot de passe optionnel
- Nom de l'entreprise
- Nombre maximum d'activations
- Durée de la licence (jours)
- Description

### 🔑 Gestion des codes (`/admin/codes`)
**Interface complète :**
- **Génération manuelle** de codes
- **Statistiques en temps réel** (total, utilisés, actifs, expirés)
- **Filtres avancés** (projet, statut, recherche)
- **Actions en masse** (copie, suppression)
- **Tracking détaillé** des utilisations

**Informations par code :**
- Code d'activation unique
- Projet associé
- Email du bénéficiaire
- Ratio d'activations (utilisé/maximum)
- Statut (disponible, utilisé, expiré)
- Date d'expiration
- Actions disponibles

### 👥 Gestion des utilisateurs (`/admin/users`)
**Administration des comptes :**
- **CRUD utilisateurs** complet
- **Gestion des rôles** (admin, manager, viewer)
- **Permissions granulaires** par fonctionnalité
- **Mots de passe sécurisés** (bcrypt)
- **Suivi des connexions**

**Rôles et permissions :**
- **Admin** : Toutes permissions
- **Manager** : Gestion codes/licences + statistiques
- **Viewer** : Consultation statistiques uniquement

### 📈 Historique des activations (`/admin/activations`)
**Monitoring complet :**
- **Historique détaillé** de toutes les activations
- **Filtres temporels** et par projet
- **Statistiques agrégées** (machines uniques, projets actifs)
- **Auto-refresh** toutes les 30 secondes
- **Recherche avancée** (email, machine ID, code)

---

## 🔌 APIs RESTful

### 📡 APIs publiques

#### `POST /api/request-activation-code`
**Demande de code d'activation (formulaire web)**

**Paramètres (Form-data) :**
```json
{
  "email": "client@example.com",
  "project": "MostaGare",
  "company": "Mon Entreprise",
  "message": "Informations complémentaires"
}
```

**Réponse :**
```json
{
  "success": true,
  "message": "Code d'activation généré: ABCD-1234-EFGH-5678",
  "activation_code": "ABCD-1234-EFGH-5678",
  "project": "MostaGare",
  "expires_in_days": 365
}
```

#### `POST /api/download-license`
**Téléchargement de licence par code d'activation**

**Paramètres (JSON ou Form-data) :**
```json
{
  "activationCode": "ABCD-1234-EFGH-5678"
}
```

**Réponse (Licence signée) :**
```json
{
  "license": {
    "activations": [],
    "company": "Mon Entreprise",
    "created_at": "2025-08-11T00:00:00.000000",
    "email": "client@example.com",
    "expires_at": "2026-08-11T00:00:00.000000",
    "key": "ABCD-1234-EFGH-5678",
    "max_activations": 4,
    "project": "MostaGare",
    "status": "ACTIVE",
    "version": "1.0.0"
  },
  "signature": "3e1480ac62e14f7de4b462fa31e69193e83b405d4f7c4b71...",
  "alg": "RSA-PKCS1v15-SHA256"
}
```

#### `POST /api/notify-activation`
**Notification d'activation de machine**

**Paramètres (Form-data) :**
```json
{
  "activationCode": "ABCD-1234-EFGH-5678",
  "machineId": "unique-machine-identifier",
  "machineName": "Desktop-PC-01"
}
```

**Réponse :**
```json
{
  "success": true,
  "message": "Activation enregistrée",
  "used_count": 1,
  "activations": 1
}
```

### 🔒 APIs administratives

#### `POST /api/admin/generate-code`
**Génération manuelle de codes (Authentification requise)**

**Paramètres (Form-data) :**
```json
{
  "project": "MostaGare",
  "email": "client@example.com",
  "max_activations": 4,
  "duration_days": 365
}
```

#### `POST /admin/projects/save`
**Sauvegarde de projet (Permission manage_licenses requise)**

#### `POST /admin/users/save`
**Gestion utilisateurs (Permission manage_users requise)**

### 🏥 API de santé

#### `GET /health`
**Vérification de l'état du serveur**
```json
{
  "status": "healthy",
  "timestamp": "2025-08-11T00:00:00.000000"
}
```

---

## 🔐 Système de sécurité

### 🔑 Cryptographie RSA
**Génération de signatures :**
- **Algorithme** : RSA-PKCS1v15-SHA256
- **Taille de clé** : 2048 bits
- **Format** : PEM (Privacy-Enhanced Mail)

**Processus de signature :**
1. Création du payload JSON canonique
2. Tri alphabétique des clés
3. Sérialisation JSON sans espaces
4. Signature RSA avec clé privée
5. Encodage hexadécimal de la signature

**Vérification côté client :**
- Reconstruction du payload canonique
- Vérification avec la clé publique
- Support des licences avec activations ajoutées

### 🛡️ Authentification JWT
**Configuration sécurisée :**
- **Algorithme** : HS256
- **Durée** : 24 heures (configurable)
- **Stockage** : Cookie HTTPOnly
- **Secret** : Configurable via variable d'environnement

**Gestion des sessions :**
- Renouvellement automatique
- Déconnexion sécurisée
- Validation à chaque requête

### 🔒 Permissions granulaires
**Système RBAC (Role-Based Access Control) :**

| Permission | Description | Admin | Manager | Viewer |
|------------|-------------|-------|---------|--------|
| `manage_users` | Gestion utilisateurs | ✅ | ❌ | ❌ |
| `manage_codes` | Génération codes | ✅ | ✅ | ❌ |
| `manage_licenses` | Gestion projets | ✅ | ✅ | ❌ |
| `view_stats` | Consultation stats | ✅ | ✅ | ✅ |

---

## 📊 Système de monitoring

### 📈 Métriques disponibles
- **Codes générés** (total, par période)
- **Activations** (par jour, par projet, par machine)
- **Projets actifs** et statistiques d'usage
- **Performances** (temps de réponse, erreurs)

### 🔍 Logs structurés
```python
# Configuration logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Types de logs
logger.info("Code généré: ABCD-1234-EFGH-5678")
logger.warning("Clé privée non trouvée, signature temporaire")
logger.error("Erreur activation: Code non trouvé")
```

### 📋 Fichiers de données
**Structure des données JSON :**

**activation_codes.json :**
```json
{
  "ABCD-1234-EFGH-5678": {
    "email": "client@example.com",
    "project": "MostaGare",
    "company": "Mon Entreprise",
    "max_activations": 4,
    "created_at": "2025-08-11T00:00:00.000000",
    "expires_at": "2026-08-11T00:00:00.000000",
    "used": true,
    "used_count": 2,
    "auto_generated": true,
    "first_activation_at": "2025-08-11T01:00:00.000000",
    "activations": [
      {
        "machine_id": "unique-id-1",
        "machine_name": "Desktop-PC-01",
        "activated_at": "2025-08-11T01:00:00.000000"
      }
    ]
  }
}
```

**users_conf.json :**
```json
{
  "admin": {
    "username": "admin",
    "email": "admin@example.com",
    "role": "admin",
    "permissions": ["manage_users", "manage_codes", "manage_licenses", "view_stats"],
    "password_hash": "$2b$12$...",
    "created_at": "2025-08-11T00:00:00.000000",
    "last_login": "2025-08-11T01:00:00.000000",
    "active": true
  }
}
```

**required_all_email.json :**
```json
{
  "MostaGare": {
    "required_email": "admin@mostagare.com",
    "company_name": "MostaGare Solutions",
    "max_activations": 4,
    "license_duration_days": 365,
    "project": "MostaGare",
    "description": "Système de gestion de transport routier",
    "created_at": "2025-08-11T00:00:00.000000",
    "updated_at": "2025-08-11T01:00:00.000000"
  }
}
```

---

## 🔧 Configuration avancée

### ⚙️ Variables d'environnement
```bash
# Sécurité JWT
JWT_SECRET="your-super-secret-key-change-in-production"
JWT_EXPIRATION_HOURS=24

# Configuration serveur
HOST="0.0.0.0"
PORT=8000
WORKERS=4

# Chemins des fichiers
DATA_DIR="/path/to/data"
TEMPLATES_DIR="/path/to/templates"

# Cryptographie
PRIVATE_KEY_FILE="/path/to/private.pem"
PUBLIC_KEY_FILE="/path/to/public.pem"
```

### 🔒 Sécurité en production
**Recommandations obligatoires :**
1. **Changer** tous les mots de passe par défaut
2. **Générer** un nouveau secret JWT
3. **Sécuriser** les clés RSA (permissions 600)
4. **Activer** HTTPS avec certificats valides
5. **Configurer** un reverse proxy (Nginx/Apache)
6. **Sauvegarder** régulièrement les données
7. **Monitorer** les logs d'erreur
8. **Mettre à jour** les dépendances

### 🚀 Déploiement en production
```bash
# Avec systemd
sudo cp licences_server.service /etc/systemd/system/
sudo systemctl enable licences_server
sudo systemctl start licences_server

# Avec Docker
docker build -t licences-server .
docker run -d -p 8000:8000 --name licences-server \
  -v /data:/app/data licences-server

# Avec Nginx (reverse proxy)
server {
    listen 443 ssl;
    server_name licences.example.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 🧪 Tests et maintenance

### 🔍 Tests de santé
```bash
# Vérifier l'état du serveur
curl https://licences.example.com/health

# Tester une génération de code
curl -X POST https://licences.example.com/api/request-activation-code \
  -d "email=test@example.com&project=MostaGare&company=Test"

# Vérifier l'authentification
curl -X POST https://licences.example.com/login \
  -d "username=admin&password=admin123"
```

### 🛠️ Maintenance préventive
**Actions régulières :**
- **Sauvegarde** des fichiers de données
- **Rotation** des logs
- **Surveillance** de l'espace disque
- **Vérification** des certificats SSL
- **Mise à jour** des dépendances de sécurité

### 📋 Dépannage courant
**Problèmes fréquents :**

1. **"Signature invalide"**
   - Vérifier les clés RSA (private.pem/public.pem)
   - S'assurer de la cohérence des algorithmes

2. **"Code d'activation non trouvé"**
   - Vérifier activation_codes.json
   - Contrôler la synchronisation des données

3. **"Erreur d'authentification"**
   - Vérifier users_conf.json
   - Contrôler les mots de passe hashés

4. **"Permission refusée"**
   - Vérifier les rôles utilisateur
   - Contrôler les permissions assignées

---

## 📚 Intégration client

### 🔌 Côté application cliente
**Étapes d'intégration :**

1. **Copier la clé publique** dans l'application
2. **Implémenter l'API** de téléchargement
3. **Ajouter la notification** d'activation
4. **Vérifier les signatures** RSA

**Exemple d'intégration Node.js :**
```javascript
// Téléchargement de licence
const response = await fetch('https://licences.example.com/api/download-license', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ activationCode: code })
});

const license = await response.json();

// Notification d'activation
await fetch('https://licences.example.com/api/notify-activation', {
  method: 'POST',
  headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  body: `activationCode=${code}&machineId=${machineId}&machineName=${machineName}`
});
```

---

## 🚀 Roadmap et évolutions

### 🔮 Fonctionnalités prévues
- **API GraphQL** pour requêtes complexes
- **Webhooks** pour notifications externes
- **Multi-tenant** pour plusieurs organisations
- **Analytics avancées** avec tableaux de bord
- **Import/Export** des configurations
- **Intégration LDAP/OAuth** pour l'authentification

### 🔧 Améliorations techniques
- **Cache Redis** pour les performances
- **Base de données** relationnelle (PostgreSQL)
- **Tests automatisés** (unittest/pytest)
- **CI/CD** avec GitHub Actions
- **Monitoring** avec Prometheus/Grafana
- **Documentation** API avec OpenAPI/Swagger

---

## 👥 Support et contribution

### 📞 Support technique
- **Documentation** : Ce README et commentaires de code
- **Logs** : Consultez `/var/log/licences-server/`
- **Monitoring** : Interface web `/admin/activations`

### 🤝 Contribution
Pour contribuer au projet :
1. Fork le repository
2. Créer une branche feature
3. Implémenter les modifications
4. Ajouter des tests si nécessaire
5. Soumettre une Pull Request

### 📄 Licence
Ce projet est sous licence propriétaire. Tous droits réservés.

---

## 📊 Résumé des capacités

| Fonctionnalité | Description | Statut |
|----------------|-------------|---------|
| 🌐 Interface web moderne | Page d'accueil + administration complète | ✅ Implémenté |
| 🔐 Authentification JWT | Sécurité robuste avec bcrypt | ✅ Implémenté |
| 🔑 Génération de codes | Format universel + validation | ✅ Implémenté |
| 📜 Signatures RSA | Cryptographie industrielle | ✅ Implémenté |
| 📊 Monitoring complet | Statistiques temps réel | ✅ Implémenté |
| 🚀 APIs RESTful | Intégration facile | ✅ Implémenté |
| 👥 Multi-utilisateurs | Rôles et permissions | ✅ Implémenté |
| 🏢 Multi-projets | Gestion centralisée | ✅ Implémenté |
| 📈 Historique détaillé | Traçabilité complète | ✅ Implémenté |
| 🔧 Configuration flexible | Paramétrage avancé | ✅ Implémenté |

**Version :** 4.0.0  
**Dernière mise à jour :** Août 2025  
**Auteur :** Équipe MostaGare  
**Contact :** Dr Hamid MADANI <drmdh@msn.com>