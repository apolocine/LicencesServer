#!/usr/bin/env python3
"""
Script pour ajouter de nouveaux logiciels/emails dans la configuration des licences
"""

import json
import os
import sys
from datetime import datetime

CONFIG_DIR = os.path.join(os.path.dirname(__file__), "data")
SOFTWARES_CONFIG_FILE = os.path.join(CONFIG_DIR, "software_configs.json")

def load_software_configs():
    """Charger la configuration des logiciels"""
    if not os.path.exists(SOFTWARES_CONFIG_FILE):
        # Configuration par défaut
        default_configs = {
            "MostaGare": {
                "required_email": "user@company.com",
                "company_name": "Default Company",
                "max_activations": 4,
                "license_duration_days": 365,
                "project": "MostaGare",
                "description": "Système de gestion de transport MostaGare",
                "created_at": datetime.now().isoformat()
            }
        }
        save_software_configs(default_configs)
        return default_configs
    
    with open(SOFTWARES_CONFIG_FILE, 'r') as f:
        return json.load(f)

def save_software_configs(configs):
    """Sauvegarder la configuration des logiciels"""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(SOFTWARES_CONFIG_FILE, 'w') as f:
        json.dump(configs, f, indent=2, ensure_ascii=False)

def add_software():
    """Ajouter un nouveau logiciel interactivement"""
    print("=== Ajout d'un nouveau logiciel ===\n")
    
    configs = load_software_configs()
    
    # Demander les informations
    project_name = input("Nom du logiciel/projet : ").strip()
    if not project_name:
        print("❌ Le nom du projet est requis")
        return False
    
    if project_name in configs:
        overwrite = input(f"⚠️ Le projet '{project_name}' existe déjà. Écraser ? (y/N) : ").strip().lower()
        if overwrite != 'y':
            print("❌ Opération annulée")
            return False
    
    required_email = input("Email autorisé (ex: user@company.com) : ").strip()
    if not required_email or "@" not in required_email:
        print("❌ Email valide requis")
        return False
    
    company_name = input("Nom de l'entreprise : ").strip() or "Entreprise"
    
    try:
        max_activations = int(input("Nombre maximum d'activations [4] : ").strip() or "4")
        if max_activations < 1 or max_activations > 50:
            print("❌ Nombre d'activations doit être entre 1 et 50")
            return False
    except ValueError:
        print("❌ Nombre d'activations invalide")
        return False
    
    try:
        license_duration = int(input("Durée de licence en jours [365] : ").strip() or "365")
        if license_duration < 1 or license_duration > 3650:
            print("❌ Durée doit être entre 1 et 3650 jours")
            return False
    except ValueError:
        print("❌ Durée invalide")
        return False
    
    description = input("Description du logiciel : ").strip() or f"Logiciel {project_name}"
    
    # Créer la configuration
    new_config = {
        "required_email": required_email,
        "company_name": company_name,
        "max_activations": max_activations,
        "license_duration_days": license_duration,
        "project": project_name,
        "description": description,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    # Confirmer
    print("\n=== Récapitulatif ===")
    print(f"Projet         : {project_name}")
    print(f"Email autorisé : {required_email}")
    print(f"Entreprise     : {company_name}")
    print(f"Max activations: {max_activations}")
    print(f"Durée licence  : {license_duration} jours")
    print(f"Description    : {description}")
    
    confirm = input("\nConfirmer l'ajout ? (Y/n) : ").strip().lower()
    if confirm == 'n':
        print("❌ Opération annulée")
        return False
    
    # Sauvegarder
    configs[project_name] = new_config
    save_software_configs(configs)
    
    # Créer un fichier de configuration spécifique pour ce logiciel
    specific_config_file = os.path.join(CONFIG_DIR, f"required_email_{project_name.lower()}.json")
    with open(specific_config_file, 'w') as f:
        json.dump(new_config, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Logiciel '{project_name}' ajouté avec succès !")
    print(f"📁 Configuration sauvegardée dans : {specific_config_file}")
    
    return True

def list_softwares():
    """Lister tous les logiciels configurés"""
    configs = load_software_configs()
    
    print("=== Logiciels configurés ===\n")
    
    if not configs:
        print("Aucun logiciel configuré")
        return
    
    for i, (project, config) in enumerate(configs.items(), 1):
        print(f"{i}. {project}")
        print(f"   📧 Email      : {config.get('required_email', 'N/A')}")
        print(f"   🏢 Entreprise : {config.get('company_name', 'N/A')}")
        print(f"   📊 Max activ. : {config.get('max_activations', 'N/A')}")
        print(f"   ⏰ Durée      : {config.get('license_duration_days', 'N/A')} jours")
        print(f"   📝 Description: {config.get('description', 'N/A')}")
        print(f"   📅 Créé le    : {config.get('created_at', 'N/A')[:10] if config.get('created_at') else 'N/A'}")
        print()

def remove_software():
    """Supprimer un logiciel"""
    configs = load_software_configs()
    
    if not configs:
        print("Aucun logiciel configuré")
        return
    
    print("=== Suppression d'un logiciel ===\n")
    list_softwares()
    
    project_name = input("Nom du logiciel à supprimer : ").strip()
    
    if project_name not in configs:
        print(f"❌ Logiciel '{project_name}' non trouvé")
        return
    
    confirm = input(f"⚠️ Confirmer la suppression de '{project_name}' ? (y/N) : ").strip().lower()
    if confirm != 'y':
        print("❌ Suppression annulée")
        return
    
    # Supprimer de la configuration
    del configs[project_name]
    save_software_configs(configs)
    
    # Supprimer le fichier spécifique s'il existe
    specific_config_file = os.path.join(CONFIG_DIR, f"required_email_{project_name.lower()}.json")
    if os.path.exists(specific_config_file):
        os.remove(specific_config_file)
        print(f"📁 Fichier {specific_config_file} supprimé")
    
    print(f"✅ Logiciel '{project_name}' supprimé avec succès !")

def update_software():
    """Mettre à jour un logiciel existant"""
    configs = load_software_configs()
    
    if not configs:
        print("Aucun logiciel configuré")
        return
    
    print("=== Mise à jour d'un logiciel ===\n")
    list_softwares()
    
    project_name = input("Nom du logiciel à modifier : ").strip()
    
    if project_name not in configs:
        print(f"❌ Logiciel '{project_name}' non trouvé")
        return
    
    current_config = configs[project_name]
    print(f"\n📝 Configuration actuelle de '{project_name}':")
    print(f"   📧 Email      : {current_config.get('required_email')}")
    print(f"   🏢 Entreprise : {current_config.get('company_name')}")
    print(f"   📊 Max activ. : {current_config.get('max_activations')}")
    print(f"   ⏰ Durée      : {current_config.get('license_duration_days')} jours")
    print(f"   📝 Description: {current_config.get('description')}")
    
    print("\n💡 Laissez vide pour conserver la valeur actuelle")
    
    # Mise à jour des champs
    new_email = input(f"Nouvel email [{current_config.get('required_email')}] : ").strip()
    if new_email:
        current_config['required_email'] = new_email
    
    new_company = input(f"Nouvelle entreprise [{current_config.get('company_name')}] : ").strip()
    if new_company:
        current_config['company_name'] = new_company
    
    new_max_act = input(f"Nouveau max activations [{current_config.get('max_activations')}] : ").strip()
    if new_max_act:
        try:
            current_config['max_activations'] = int(new_max_act)
        except ValueError:
            print("⚠️ Valeur invalide pour max activations, ignorée")
    
    new_duration = input(f"Nouvelle durée [{current_config.get('license_duration_days')}] : ").strip()
    if new_duration:
        try:
            current_config['license_duration_days'] = int(new_duration)
        except ValueError:
            print("⚠️ Valeur invalide pour la durée, ignorée")
    
    new_description = input(f"Nouvelle description [{current_config.get('description')}] : ").strip()
    if new_description:
        current_config['description'] = new_description
    
    current_config['updated_at'] = datetime.now().isoformat()
    
    # Sauvegarder
    configs[project_name] = current_config
    save_software_configs(configs)
    
    # Mettre à jour le fichier spécifique
    specific_config_file = os.path.join(CONFIG_DIR, f"required_email_{project_name.lower()}.json")
    with open(specific_config_file, 'w') as f:
        json.dump(current_config, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Logiciel '{project_name}' mis à jour avec succès !")

def main():
    """Menu principal"""
    while True:
        print("\n" + "="*50)
        print("🔧 GESTIONNAIRE DE CONFIGURATION LOGICIELS")
        print("="*50)
        print("1. 📝 Ajouter un nouveau logiciel")
        print("2. 📋 Lister les logiciels")
        print("3. ✏️  Modifier un logiciel")
        print("4. 🗑️  Supprimer un logiciel")
        print("5. ❌ Quitter")
        print()
        
        choice = input("Votre choix (1-5) : ").strip()
        
        if choice == '1':
            add_software()
        elif choice == '2':
            list_softwares()
        elif choice == '3':
            update_software()
        elif choice == '4':
            remove_software()
        elif choice == '5':
            print("👋 Au revoir !")
            break
        else:
            print("❌ Choix invalide")
        
        input("\n⏸️ Appuyez sur Entrée pour continuer...")

if __name__ == "__main__":
    try:
        if len(sys.argv) > 1:
            if sys.argv[1] == "list":
                list_softwares()
            elif sys.argv[1] == "add":
                add_software()
            else:
                print("Usage: python add_software_config.py [list|add]")
        else:
            main()
    except KeyboardInterrupt:
        print("\n\n👋 Opération interrompue par l'utilisateur")
    except Exception as e:
        print(f"❌ Erreur: {e}")