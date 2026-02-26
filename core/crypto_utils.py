import os
import json
import base64
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.exceptions import InvalidSignature

def generate_key_pair() -> tuple[bytes, bytes]:
    """Gera um par de chaves RSA de 2048 bits."""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    return private_pem, public_pem

def sign_license_data(private_key_pem: bytes, payload_dict: dict) -> str:
    """
    Converte o Dicionário de payload para JSON, cria um Hash e
    assina digitalmente o conteúdo com a chave privada.
    Retorna o JSON embalado juntamente com a assinatura convertida em Base64.
    """
    private_key = serialization.load_pem_private_key(
        private_key_pem,
        password=None,
    )
    
    payload_json = json.dumps(payload_dict, separators=(',', ':'), sort_keys=True)
    payload_bytes = payload_json.encode('utf-8')
    
    signature = private_key.sign(
        payload_bytes,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    
    signature_b64 = base64.b64encode(signature).decode('utf-8')
    
    final_license = {
        "payload": payload_dict,
        "signature": signature_b64
    }
    
    # A licença em si será exportada como um JSON string base64 codificado para ofuscamento visual
    license_out = base64.b64encode(json.dumps(final_license).encode('utf-8')).decode('utf-8')
    return license_out

def verify_license_signature(public_key_pem: bytes, license_b64: str) -> dict:
    """
    Recebe o arquivo de licença exportado e a chave pública.
    Desofusca a B64, extrai a assinatura e verifica se ela é válida para o dado payload.
    Retorna o payload se for válido, ou levanta erro.
    """
    try:
        license_json = base64.b64decode(license_b64).decode('utf-8')
        license_data = json.loads(license_json)
        
        payload_dict = license_data['payload']
        signature_b64 = license_data['signature']
        
        payload_json = json.dumps(payload_dict, separators=(',', ':'), sort_keys=True)
        payload_bytes = payload_json.encode('utf-8')
        
        signature_bytes = base64.b64decode(signature_b64)
        
        public_key = serialization.load_pem_public_key(public_key_pem)
        
        public_key.verify(
            signature_bytes,
            payload_bytes,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return payload_dict
        
    except (InvalidSignature, KeyError, ValueError, TypeError) as e:
        raise ValueError(f"Assinatura Inválida ou Corrompida: {e}")
