#!/usr/bin/env python3
"""
Script de démonstration pour configurer plusieurs logiciels
"""

import json
import os
import sys
from datetime import datetime, timedelta
import uuid

# Ajouter le répertoire parent au path pour importer add_software_config
sys.path.append(os.path.dirname(__file__))
from add_software_config import save_software_configs

def setup_demo_softwares():
    """Configurer des logiciels de démonstration"""
    
    demo_configs = {
        "MostaGare": {
            "required_email": "admin@mostagare.com",
            "company_name": "MostaGare Solutions",
            "max_activations": 4,
            "license_duration_days": 365,
            "project": "MostaGare",
            "description": "Système de gestion de transport routier",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        },
        
        "InventoryPro": {
            "required_email": "user@inventorypro.com",
            "company_name": "Inventory Solutions Ltd",
            "max_activations": 2,
            "license_duration_days": 180,
            "project": "InventoryPro",
            "description": "Gestion avancée des stocks et inventaire",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        },
        
        "CRMExpert": {
            "required_email": "contact@crmexpert.fr",
            "company_name": "CRM Expert France",
            "max_activations": 10,
            "license_duration_days": 730,
            "project": "CRMExpert",
            "description": "Solution CRM complète pour entreprises",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        },
        
        "AccountingPlus": {
            "required_email": "admin@accountingplus.com",
            "company_name": "Accounting Plus Inc",
            "max_activations": 5,
            "license_duration_days": 365,
            "project": "AccountingPlus",
            "description": "Logiciel de comptabilité professionnelle",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
    }
    
    print("🚀 Configuration des logiciels de démonstration...")
    print(f"📦 {len(demo_configs)} logiciels à configurer\n")
    
    # Sauvegarder la configuration globale
    save_software_configs(demo_configs)
    print("✅ Configuration globale sauvegardée")
    
    # Créer les fichiers individuels
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(data_dir, exist_ok=True)
    
    for project_name, config in demo_configs.items():
        specific_file = os.path.join(data_dir, f"required_email_{project_name.lower()}.json")
        
        with open(specific_file, 'w') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print(f"✅ {project_name}: {specific_file}")
    
    print("\n🎯 Génération de codes d'activation d'exemple...")
    
    # Générer des codes d'activation d'exemple
    activation_codes = {}
    
    for project_name, config in demo_configs.items():
        # Générer 2 codes par logiciel
        for i in range(2):
            code = f"{uuid.uuid4().hex[:4].upper()}-{uuid.uuid4().hex[:4].upper()}-{uuid.uuid4().hex[:4].upper()}-{uuid.uuid4().hex[:4].upper()}"
            
            activation_codes[code] = {
                "email": config["required_email"],
                "max_activations": config["max_activations"],
                "created_at": datetime.now().isoformat(),
                "expires_at": (datetime.now() + timedelta(days=config["license_duration_days"])).isoformat(),
                "used": False,
                "project": project_name,
                "description": f"Code de démonstration pour {project_name}"
            }
            
            print(f"🔑 {project_name}: {code}")
    
    # Sauvegarder les codes d'activation
    codes_file = os.path.join(data_dir, "activation_codes.json")
    
    # Charger les codes existants s'ils existent
    existing_codes = {}
    if os.path.exists(codes_file):
        try:
            with open(codes_file, 'r') as f:
                existing_codes = json.load(f)
        except:
            pass
    
    # Fusionner avec les nouveaux codes
    existing_codes.update(activation_codes)
    
    with open(codes_file, 'w') as f:
        json.dump(existing_codes, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ {len(activation_codes)} codes d'activation générés et sauvegardés")
    print(f"📁 Fichier: {codes_file}")
    
    print("\n🎉 Configuration de démonstration terminée !")
    print("\n📋 Résumé:")
    print("="*50)
    
    for project_name, config in demo_configs.items():
        print(f"🏷️  {project_name}")
        print(f"   📧 Email: {config['required_email']}")
        print(f"   🏢 Société: {config['company_name']}")
        print(f"   📊 Max activations: {config['max_activations']}")
        print(f"   ⏰ Durée: {config['license_duration_days']} jours")
        print()
    
    print("🔗 URLs importantes:")
    print("   🏠 Page d'accueil: http://localhost:8000/")
    print("   🔧 Admin codes: http://localhost:8000/admin/codes")
    print("   📊 API logiciels: http://localhost:8000/api/softwares")
    print("   ❤️ Health check: http://localhost:8000/health")

if __name__ == "__main__":
    try:
        setup_demo_softwares()
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()