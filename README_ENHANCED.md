# 🚀 MostaGare License Server v2.0.0 Enhanced

## 📋 Nouvelles Fonctionnalités

### ✨ Améliorations Principales

1. **🖥️ Gestion Avancée des Postes**
   - Suivi détaillé des activations par poste
   - Interface d'administration pour gérer les postes actifs
   - Limitation configurable du nombre de postes (1-20)

2. **📊 Monitoring en Temps Réel**
   - Dashboard avec statistiques d'utilisation
   - Historique des activations et désactivations
   - Alertes en cas de limite atteinte

3. **🔧 Configuration Dynamique**
   - Modification du nombre de postes sans redémarrage
   - APIs REST pour intégration avec applications clientes
   - Interface web moderne et responsive

4. **🛡️ Sécurité Renforcée**
   - Traçabilité complète des actions administratives
   - Validation des permissions avant modifications
   - Sauvegarde automatique avant changements

## 🛠️ Installation et Configuration

### Prérequis
```bash
pip install fastapi uvicorn jinja2 python-multipart cryptography
```

### Structure des Fichiers
```
licences_server/
├── main_enhanced.py          # Serveur principal enhanced
├── templates/                # Templates HTML
│   ├── home.html            # Page d'accueil
│   ├── form.html            # Formulaire de demande
│   ├── success.html         # Page de succès
│   └── activations_admin.html # Admin des postes
├── data/                    # Données du serveur
│   ├── rules.json          # Configuration par défaut
│   ├── licenses.json       # Base des licences
│   └── activations.json    # Détail des activations
└── static/                 # Ressources statiques
```

### Démarrage du Serveur

1. **Copier les fichiers nécessaires** :
```bash
# Copier le serveur enhanced
cp licences/main_enhanced.py /home/hmd/www/ws/licences_server/main.py

# Copier les templates
cp -r licences/templates/* /home/hmd/www/ws/licences_server/templates/

# Copier la configuration
cp licences/data/rules.json /home/hmd/www/ws/licences_server/data/
```

2. **Redémarrer le serveur** :
```bash
# Si vous utilisez PM2
pm2 restart licences

# Ou directement
cd /home/hmd/www/ws/licences_server
python main.py
```

## 🌐 Nouvelles API Endpoints

### Activation de Postes
```bash
POST /api/activate
{
  "license_key": "MOSTAGARE-xxxx-yyyy",
  "device_id": "unique-device-identifier",
  "device_name": "Poste Vente 1",
  "os_info": "Windows 11",
  "hostname": "PC-VENTE-01"
}
```

### Désactivation de Postes
```bash
DELETE /api/deactivate/{license_key}/{device_id}
```

### Configuration Administrative
```bash
POST /api/admin/update-max-activations
{
  "email": "client@entreprise.com",
  "project": "MostaGare",
  "max_activations": 6
}
```

## 📱 Interface d'Administration

### Pages Disponibles

1. **🏠 Accueil** (`/`)
   - Vue d'ensemble du serveur
   - Statistiques globales
   - Navigation rapide

2. **👥 Gestion des Postes** (`/admin/activations`)
   - Liste des licences et postes actifs
   - Configuration du nombre de postes
   - Désactivation de postes
   - Statistiques d'utilisation

3. **📋 Gestion des Licences** (`/admin/licenses`)
   - Vue de toutes les licences générées
   - Recherche et filtrage
   - Export des données

## 🔄 Migration depuis l'Ancien Serveur

### Étapes de Migration

1. **Sauvegarde des données** :
```bash
cp /home/hmd/www/ws/licences_server/data/licenses.json ~/backup/
cp /home/hmd/www/ws/licences_server/data/keys/ ~/backup/ -r
```

2. **Mise à jour du code** :
```bash
# Remplacer le serveur principal
cp licences/main_enhanced.py /home/hmd/www/ws/licences_server/main.py
```

3. **Ajout des templates** :
```bash
# Copier les nouveaux templates
cp -r licences/templates/* /home/hmd/www/ws/licences_server/templates/
```

4. **Configuration** :
```bash
# Mise à jour des règles
cp licences/data/rules.json /home/hmd/www/ws/licences_server/data/
```

5. **Redémarrage** :
```bash
pm2 restart licences
```

## 📊 Fonctionnalités Avancées

### Auto-refresh des Données
- Les pages d'administration se rafraîchissent automatiquement toutes les 30 secondes
- Suivi en temps réel de l'utilisation des postes

### Validation Intelligente
- Empêche de définir une limite inférieure au nombre de postes actifs
- Vérification automatique de la cohérence des données

### Historique Complet
- Traçage de toutes les modifications administratives
- Conservation de l'historique des activations/désactivations

## 🔧 Dépannage

### Problème : Template Not Found
```bash
# Vérifier la présence des templates
ls -la /home/hmd/www/ws/licences_server/templates/

# Si manquants, les copier depuis le projet
cp -r licences/templates/* /home/hmd/www/ws/licences_server/templates/
```

### Problème : Permissions Insuffisantes
```bash
# Donner les bonnes permissions
chmod 755 /home/hmd/www/ws/licences_server/data/
chmod 644 /home/hmd/www/ws/licences_server/data/*.json
```

### Problème : Port déjà utilisé
```bash
# Changer le port dans main_enhanced.py (ligne finale)
uvicorn.run(app, host="0.0.0.0", port=8001)  # Au lieu de 8000
```

## 🎯 Cas d'Usage

### Configuration 4 Postes pour un Client
1. Aller sur `/admin/activations`
2. Saisir l'email du client et "MostaGare"
3. Définir "4" dans limite postes
4. Cliquer "Mettre à jour"

### Désactivation d'un Poste Défaillant
1. Trouver la licence sur `/admin/activations`
2. Localiser le poste problématique
3. Cliquer "❌ Désactiver"
4. Confirmer l'action

### Monitoring de l'Utilisation
1. Page d'accueil pour vue globale
2. `/admin/activations` pour détails par licence
3. Auto-refresh pour suivi temps réel

## 📈 Statistiques Disponibles

- **Total Licences** : Nombre de licences générées
- **Postes Actifs** : Nombre total de postes connectés
- **Postes Maximum** : Capacité totale autorisée
- **Postes Disponibles** : Places restantes
- **Taux d'Occupation** : Pourcentage d'utilisation par licence

## 🚀 Prochaines Évolutions

- [ ] Notifications email automatiques
- [ ] Intégration webhook pour événements
- [ ] API GraphQL pour requêtes complexes
- [ ] Dashboard analytics avancé
- [ ] Gestion multi-tenant

---

**Version** : 2.0.0 Enhanced Edition  
**Compatibilité** : MostaGare 1.0.0+  
**Support** : Documentation complète incluse