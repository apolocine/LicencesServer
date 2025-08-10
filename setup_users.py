#!/usr/bin/env python3
"""
Script pour créer/mettre à jour les utilisateurs avec mots de passe hashés
"""
import json
import bcrypt
import os
from datetime import datetime

def hash_password(password):
    """Hasher un mot de passe avec bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def setup_default_users():
    """Créer les utilisateurs par défaut"""
    
    # Configuration des utilisateurs par défaut
    default_users = {
        "admin": {
            "username": "admin",
            "password": "admin123",  # Mot de passe par défaut
            "role": "admin",
            "email": "admin@amia.fr",
            "permissions": ["manage_users", "manage_codes", "manage_licenses", "view_stats"]
        },
        "manager": {
            "username": "manager", 
            "password": "manager123",  # Mot de passe par défaut
            "role": "manager",
            "email": "manager@amia.fr",
            "permissions": ["manage_codes", "manage_licenses", "view_stats"]
        }
    }
    
    users_data = {}
    
    print("Configuration des utilisateurs...")
    
    for username, user_info in default_users.items():
        password = user_info.pop("password")
        hashed_password = hash_password(password)
        
        users_data[username] = {
            **user_info,
            "password_hash": hashed_password,
            "created_at": datetime.now().isoformat(),
            "last_login": None,
            "active": True
        }
        
        print(f"✓ Utilisateur '{username}' créé (mot de passe: {password})")
    
    # Sauvegarder dans le fichier
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(data_dir, exist_ok=True)
    
    users_file = os.path.join(data_dir, "users_conf.json")
    with open(users_file, 'w') as f:
        json.dump(users_data, f, indent=2)
    
    print(f"\nUtilisateurs sauvegardés dans: {users_file}")
    print("\nComptes créés:")
    print("- admin / admin123 (administrateur complet)")
    print("- manager / manager123 (gestion codes et licences)")
    print("\nIMPORTANT: Changez ces mots de passe par défaut en production!")

if __name__ == "__main__":
    setup_default_users()