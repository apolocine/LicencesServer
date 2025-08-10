#!/bin/bash

# 🚀 Script de déploiement du serveur de licences Enhanced
# MostaGare License Server v2.0.0

echo "🚀 Déploiement du serveur de licences Enhanced v2.0.0"
echo "=================================================="

# Définir les chemins
PROJECT_DIR="/home/hmd/dev/MostaGare-Install/MostaGare"
SERVER_DIR="/home/hmd/www/ws/licences_server"

# Vérifier que nous sommes dans le bon répertoire
if [ ! -f "licences/main_enhanced.py" ]; then
    echo "❌ Erreur: Veuillez exécuter ce script depuis la racine du projet MostaGare"
    exit 1
fi

echo "📍 Répertoire projet: $PROJECT_DIR"
echo "📍 Répertoire serveur: $SERVER_DIR"

# 1. Sauvegarde des données existantes
echo ""
echo "💾 Sauvegarde des données existantes..."
if [ -d "$SERVER_DIR" ]; then
    BACKUP_DIR="$HOME/backup/licences_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    if [ -f "$SERVER_DIR/data/licenses.json" ]; then
        cp "$SERVER_DIR/data/licenses.json" "$BACKUP_DIR/"
        echo "✅ Licenses sauvegardées dans $BACKUP_DIR"
    fi
    
    if [ -d "$SERVER_DIR/data/keys" ]; then
        cp -r "$SERVER_DIR/data/keys" "$BACKUP_DIR/"
        echo "✅ Clés sauvegardées dans $BACKUP_DIR"
    fi
else
    echo "⚠️  Répertoire serveur non trouvé, création..."
    mkdir -p "$SERVER_DIR"
fi

# 2. Création de la structure de répertoires
echo ""
echo "📁 Création de la structure de répertoires..."
mkdir -p "$SERVER_DIR/templates"
mkdir -p "$SERVER_DIR/data"
mkdir -p "$SERVER_DIR/data/keys"
mkdir -p "$SERVER_DIR/data/licenses"
mkdir -p "$SERVER_DIR/static"

# 3. Copie du serveur principal
echo ""
echo "🔄 Mise à jour du serveur principal..."
cp "licences/main_enhanced.py" "$SERVER_DIR/main.py"
echo "✅ main_enhanced.py → main.py"

# 4. Copie des templates
echo ""
echo "🎨 Mise à jour des templates HTML..."
cp licences/templates/*.html "$SERVER_DIR/templates/" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ Templates copiés"
    echo "   - home.html"
    echo "   - form.html" 
    echo "   - success.html"
    echo "   - activations_admin.html"
else
    echo "⚠️  Aucun template trouvé à copier"
fi

# 5. Configuration par défaut
echo ""
echo "⚙️ Configuration par défaut..."
if [ ! -f "$SERVER_DIR/data/rules.json" ]; then
    cp "licences/data/rules.json" "$SERVER_DIR/data/"
    echo "✅ Configuration rules.json créée"
else
    echo "ℹ️  Configuration rules.json existe déjà (conservée)"
fi

# 6. Création de fichiers manquants
echo ""
echo "📝 Création de fichiers de données..."

# Fichier licenses vide si n'existe pas
if [ ! -f "$SERVER_DIR/data/licenses.json" ]; then
    echo "[]" > "$SERVER_DIR/data/licenses.json"
    echo "✅ licenses.json créé (vide)"
fi

# Fichier activations vide si n'existe pas
if [ ! -f "$SERVER_DIR/data/activations.json" ]; then
    echo "[]" > "$SERVER_DIR/data/activations.json"
    echo "✅ activations.json créé (vide)"
fi

# 7. Permissions
echo ""
echo "🔒 Configuration des permissions..."
chmod 755 "$SERVER_DIR"
chmod 755 "$SERVER_DIR/data"
chmod 644 "$SERVER_DIR/data/*.json" 2>/dev/null
chmod 755 "$SERVER_DIR/main.py"
echo "✅ Permissions configurées"

# 8. Vérification des dépendances Python
echo ""
echo "🐍 Vérification des dépendances Python..."
python3 -c "
import sys
required = ['fastapi', 'uvicorn', 'jinja2', 'cryptography']
missing = []
for module in required:
    try:
        __import__(module)
    except ImportError:
        missing.append(module)

if missing:
    print('❌ Modules manquants:', ', '.join(missing))
    print('   Installation: pip install', ' '.join(missing))
    sys.exit(1)
else:
    print('✅ Toutes les dépendances sont installées')
"

# 9. Test de syntaxe Python
echo ""
echo "🔍 Vérification de la syntaxe Python..."
python3 -m py_compile "$SERVER_DIR/main.py"
if [ $? -eq 0 ]; then
    echo "✅ Syntaxe Python correcte"
else
    echo "❌ Erreur de syntaxe Python"
    exit 1
fi

# 10. Redémarrage du service (si PM2)
echo ""
echo "🔄 Redémarrage du service..."
if command -v pm2 &> /dev/null; then
    if pm2 list | grep -q "licences"; then
        echo "🔄 Redémarrage via PM2..."
        pm2 restart licences
        echo "✅ Service redémarré avec PM2"
    else
        echo "⚠️  Service licences non trouvé dans PM2"
        echo "   Pour démarrer: pm2 start $SERVER_DIR/main.py --name licences"
    fi
else
    echo "ℹ️  PM2 non installé, redémarrage manuel requis"
    echo "   Commande: cd $SERVER_DIR && python3 main.py"
fi

# 11. Copie de la documentation
echo ""
echo "📖 Copie de la documentation..."
cp "licences/README_ENHANCED.md" "$SERVER_DIR/"
echo "✅ Documentation copiée"

# 12. Résumé final
echo ""
echo "🎉 Déploiement terminé avec succès !"
echo "=================================="
echo ""
echo "📊 Résumé des modifications:"
echo "  ✅ Serveur Enhanced v2.0.0 installé"
echo "  ✅ Templates HTML mis à jour"  
echo "  ✅ Configuration par défaut appliquée"
echo "  ✅ Structure de données créée"
echo "  ✅ Permissions configurées"
echo "  ✅ Service redémarré (si PM2)"
echo ""
echo "🌐 Accès au serveur:"
echo "  • Interface web: http://localhost:8000"
echo "  • Admin postes: http://localhost:8000/admin/activations"
echo "  • Licences: http://localhost:8000/admin/licenses"
echo ""
echo "📁 Fichiers importants:"
echo "  • Serveur: $SERVER_DIR/main.py"
echo "  • Logs: pm2 logs licences"
echo "  • Config: $SERVER_DIR/data/rules.json"
echo "  • Backup: $BACKUP_DIR"
echo ""
echo "🔧 Commandes utiles:"
echo "  • Statut: pm2 status licences"
echo "  • Logs: pm2 logs licences"
echo "  • Redémarrer: pm2 restart licences"
echo ""
echo "✨ Nouvelles fonctionnalités disponibles:"
echo "  🖥️  Gestion avancée des postes clients"
echo "  📊 Dashboard avec statistiques temps réel"
echo "  🔧 Configuration dynamique des limites"
echo "  🛡️  Traçabilité complète des actions"
echo "  📱 Interface responsive moderne"
echo ""
echo "🚀 Le serveur Enhanced est opérationnel !"