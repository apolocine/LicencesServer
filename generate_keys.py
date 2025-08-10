#!/usr/bin/env python3
"""
Script pour générer les clés RSA pour le serveur de licences
"""
import os
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

def generate_rsa_keys():
    """Générer une paire de clés RSA pour la signature des licences"""
    
    # Générer la clé privée
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    
    # Sérialiser la clé privée
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    # Obtenir la clé publique
    public_key = private_key.public_key()
    
    # Sérialiser la clé publique
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    return private_pem, public_pem

def save_keys():
    """Sauvegarder les clés dans le dossier data"""
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(data_dir, exist_ok=True)
    
    private_key_file = os.path.join(data_dir, "private.pem")
    public_key_file = os.path.join(data_dir, "public.pem")
    
    # Vérifier si les clés existent déjà
    if os.path.exists(private_key_file) or os.path.exists(public_key_file):
        response = input("Les clés RSA existent déjà. Voulez-vous les remplacer ? (y/N): ")
        if response.lower() != 'y':
            print("Génération annulée.")
            return
    
    print("Génération des clés RSA...")
    private_pem, public_pem = generate_rsa_keys()
    
    # Sauvegarder la clé privée
    with open(private_key_file, 'wb') as f:
        f.write(private_pem)
    
    # Sauvegarder la clé publique
    with open(public_key_file, 'wb') as f:
        f.write(public_pem)
    
    print(f"✓ Clé privée sauvegardée: {private_key_file}")
    print(f"✓ Clé publique sauvegardée: {public_key_file}")
    print("\nIMPORTANT:")
    print("- Gardez la clé privée secrète et sécurisée")
    print("- La clé publique doit être copiée dans l'application cliente")
    print("- Sauvegardez ces clés de manière sécurisée")

if __name__ == "__main__":
    save_keys()