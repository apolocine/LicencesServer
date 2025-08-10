#!/usr/bin/env python3
"""
Script pour tester la vérification de signature avec Python
"""
import json
import rsa
import os

def verify_license():
    # Charger la licence
    with open("MostaGare_licence.signed.json", "r") as f:
        signed_data = json.load(f)
    
    # Charger la clé publique
    with open("public.pem", "rb") as f:
        pub_key = rsa.PublicKey.load_pkcs1(f.read())
    
    license_data = signed_data["license"]
    signature = bytes.fromhex(signed_data["signature"])
    
    print("🔍 Structure de la licence:", list(license_data.keys()))
    
    # Sérialiser exactement comme le serveur l'a fait
    payload = json.dumps(license_data).encode()
    print("📝 Données sérialisées (Python):", payload.decode()[:100] + "...")
    print("📝 Taille des données:", len(payload))
    print("📝 Hash SHA256:", __import__('hashlib').sha256(payload).hexdigest()[:16])
    
    # Tester différents formats
    payload_compact = json.dumps(license_data, separators=(',', ':')).encode()
    payload_sorted = json.dumps(license_data, sort_keys=True).encode()
    
    print("📝 Compact (Python):", payload_compact.decode()[:100] + "...")
    print("📝 Taille compact:", len(payload_compact))
    print("📝 Hash compact:", __import__('hashlib').sha256(payload_compact).hexdigest()[:16])
    
    # Vérifier la signature
    try:
        rsa.verify(payload, signature, pub_key)
        print("✅ Signature VALIDE avec Python/RSA")
        return True
    except rsa.VerificationError:
        print("❌ Signature INVALIDE avec Python/RSA")
        return False

if __name__ == "__main__":
    print("🐍 Test de vérification avec Python...")
    verify_license()