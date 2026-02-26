import os
import yaml

def load_config() -> dict:
    """
    Tenta carregar primeiramente o config.local.yaml em ./config/.
    Em caso de falha, tenta carregar o config.example.yaml como fallback
    somente para leitura estrutural.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_dir = os.path.join(base_dir, 'config')
    
    local_conf_path = os.path.join(config_dir, 'config.local.yaml')
    example_conf_path = os.path.join(config_dir, 'config.example.yaml')
    
    target_path = local_conf_path if os.path.exists(local_conf_path) else example_conf_path
    
    if not os.path.exists(target_path):
        # Se nem o example existir, retorna uma config default hardcoded
        return {
            "data_path": "projects_data",
            "pyarmor": {
                "version": "8",
                "extra_obfuscation_flags": []
            }
        }
        
    with open(target_path, 'r', encoding='utf-8') as file:
        try:
            config = yaml.safe_load(file)
            return config if config else {}
        except yaml.YAMLError as exc:
            print(f"[ERRO DE CARREGAMENTO] erro ao carregar YAML: {exc}")
            return {}

def get_data_dir() -> str:
    """
    Retorna o caminho absoluto para o diretório de dados baseado na config.
    """
    config = load_config()
    relative_path = config.get("data_path", "projects_data")
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Se o caminho for absoluto, mantêm, senão compõe com o base_dir do repo
    if os.path.isabs(relative_path):
        return relative_path
    
    full_path = os.path.join(base_dir, relative_path)
    if not os.path.exists(full_path):
        os.makedirs(full_path, exist_ok=True)
        
    return full_path
