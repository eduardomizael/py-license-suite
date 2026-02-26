import os
import ctypes
import struct
from datetime import datetime

TIME_FILE_NAME = ".sys_time_cache.bin"

def get_hidden_file_path() -> str:
    """Retorna o caminho onde o arquivo de checagem do relógio ficará"""
    appdata = os.getenv('APPDATA')
    if not appdata:
        appdata = os.path.expanduser("~")
    # Esconde no diretório do usuário para evitar deleção acidental
    return os.path.join(appdata, TIME_FILE_NAME)

def hide_file(filepath: str):
    """Torna o arquivo oculto usando API do Windows"""
    if os.name == 'nt':
        # FILE_ATTRIBUTE_HIDDEN = 0x02
        try:
            ctypes.windll.kernel32.SetFileAttributesW(filepath, 0x02)
        except Exception:
            pass

def check_system_clock() -> bool:
    """
    Verifica se a data/hora atual é maior ou igual à ultima marcação salva.
    Isso impede que o usuário volte a data e hora local do computador.
    Retorna True se estiver Ok ou se for a primeira vez. False se fraudado.
    """
    filepath = get_hidden_file_path()
    if not os.path.exists(filepath):
        return True # Primeira execução
        
    try:
        with open(filepath, 'rb') as f:
            data = f.read(8)
            if len(data) == 8:
                last_timestamp = struct.unpack('d', data)[0]
                current_timestamp = datetime.now().timestamp()
                
                # Permite margem de 1 HR de atraso pra daylight saving times, etc
                if current_timestamp < (last_timestamp - 3600):
                    return False
    except Exception:
        pass
    
    return True

def update_system_clock():
    """
    Salva a hora atual no arquivo binário oculto.
    Deve ser ligado no `atexit.register` para rodar no fechamento saudável
    da aplicação ou num loop principal de tempos em tempos.
    """
    filepath = get_hidden_file_path()
    try:
        with open(filepath, 'wb') as f:
            current_timestamp = datetime.now().timestamp()
            f.write(struct.pack('d', current_timestamp))
        hide_file(filepath)
    except Exception:
        pass
