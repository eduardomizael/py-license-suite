import subprocess
import hashlib

def get_wmi_value(command: str) -> str:
    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            shell=True,
            startupinfo=startupinfo,
            check=True
        )
        lines = result.stdout.strip().split('\\n')
        if len(lines) > 1:
            return lines[1].strip()
        return "Unknown"
    except Exception as e:
        return "Error"

def generate_hardware_id() -> str:
    """
    Coleta o Serial da Placa-Mãe e o UUID do BIOS no Windows usando WMI (WMIC).
    Combina-os e retorna um hash SHA-256 único e idempotente.
    """
    baseboard_serial = get_wmi_value("wmic baseboard get serialnumber")
    bios_uuid = get_wmi_value("wmic csproduct get uuid")
    
    # Previne que falhas wmi não quebrem e gerem HWID sempre iguais genericamente
    if baseboard_serial == "Error" or bios_uuid == "Error":
        raise RuntimeError("Não foi possivel coletar o ID do Hardware da Máquina. Certifique-se de estar no Windows e ter permissões.")
        
    combo = f"{baseboard_serial}:{bios_uuid}"
    return hashlib.sha256(combo.encode('utf-8')).hexdigest()
