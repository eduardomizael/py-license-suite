import os
import sys
import json
import base64
from datetime import datetime
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.exceptions import InvalidSignature

from .hardware import generate_hardware_id
from .anti_tampering import check_system_clock, update_system_clock

# ESTE VALOR SERÁ INJETADO PELO BUILDER DA SUÍTE!
# NÃO MODIFICAR MANUALMENTE ESTA STRING LITERALLY
__INJECTED_PUBLIC_KEY__ = """{{PUBLIC_KEY_PLACEHOLDER}}"""

def _get_public_key():
    if "{{PUBLIC_KEY_PLACEHOLDER}}" in __INJECTED_PUBLIC_KEY__:
        raise RuntimeError("Erro Grave: A Suíte de Licenciamento não injetou a chave pública no processo de Build.")
    return __INJECTED_PUBLIC_KEY__.encode('utf-8')

def _verify_signature(license_b64: str) -> dict:
    public_key_pem = _get_public_key()
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
    except Exception as e:
        print("\\n[!] A LICENÇA ESTÁ CORROMPIDA OU É INVÁLIDA.")
        sys.exit(1)

def check_startup_licensing(license_path: str = "license.lic"):
    """
    O ponto de entrada principal que o cliente deverá invocar
    logo na primeira linha do seu sistema `main.py`.
    """
    
    # 1. Verifica se a máquina foi adulterada cronologicamente
    if not check_system_clock():
        print("\\n[!] MÁQUINA BLOQUEADA POR FRAUDE DE RELÓGIO (TIMESTAMP TAMPERING).")
        sys.exit(1)
        
    # 2. Verifica a existência e parseia metadados
    if not os.path.exists(license_path):
        hw_hash = generate_hardware_id()
        print("\\n" + "="*40)
        print(" NENHUM ARQUIVO DE LICENÇA (license.lic) ENCONTRADO ")
        print(" O HWID (Identificador desta Máquina) é:")
        print(f" {hw_hash}")
        print(" Envie-o para o provedor do software.")
        print("="*40 + "\\n")
        sys.exit(1)
        
    with open(license_path, 'r', encoding='utf-8') as f:
        licence_content = f.read().strip()
        
    payload = _verify_signature(licence_content)
    
    # 3. Valida O HWID na licença contra a máquina
    current_hwid = generate_hardware_id()
    if payload.get('hwid') != current_hwid:
        print("\\n[!] LICENÇA REJEITADA: Esta licença pertence a outra máquina ou o Hardware foi alterado.")
        sys.exit(1)
        
    # 4. Validação Teto de Expiração
    expiration_str = payload.get('expires_at')
    try:
        expiration_date = datetime.strptime(expiration_str, '%Y-%m-%d')
        if datetime.now() > expiration_date:
            print("\\n[!] SUA LICENÇA EXPIROU EM:", expiration_str)
            sys.exit(1)
    except Exception:
        print("\\n[!] LICENÇA REJEITADA: Data de expiração corrompida.")
        sys.exit(1)

def hook_close_event():
    """
    Esta função deve ser acoplada no `atexit.register` pelo cliente
    no script raiz para garantir que a passagem limpa do relógio será anotada
    como registro antifraudes.
    """
    update_system_clock()
