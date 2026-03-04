import os
import json
from .config_loader import get_data_dir
from .crypto_utils import generate_key_pair

def get_projects_index() -> str:
    data_dir = get_data_dir()
    return os.path.join(data_dir, 'projects.json')

def load_projects() -> dict:
    index_path = get_projects_index()
    if not os.path.exists(index_path):
        return {}
    with open(index_path, 'r', encoding='utf-8') as file:
        return json.load(file)

def save_projects(data: dict):
    index_path = get_projects_index()
    with open(index_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4)

from datetime import datetime
import shutil

def create_project(project_name: str) -> bool:
    """Retorna True se criou com sucesso, False se ja existir."""
    projects = load_projects()
    if project_name in projects:
        return False
        
    data_dir = get_data_dir()
    project_dir = os.path.join(data_dir, project_name)
    os.makedirs(project_dir, exist_ok=True)
    
    private_pem, public_pem = generate_key_pair()
    
    priv_path = os.path.join(project_dir, 'private_key.pem')
    pub_path = os.path.join(project_dir, 'public_key.pem')
    
    with open(priv_path, 'wb') as f: f.write(private_pem)
    with open(pub_path, 'wb') as f: f.write(public_pem)
        
    projects[project_name] = {
        "private_key_path": priv_path,
        "public_key_path": pub_path,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    save_projects(projects)
    return True

def delete_project(project_name: str) -> bool:
    """Remove o projeto do registro json e deleta a pasta dele de forma irreversível. Retorna True se sucesso."""
    projects = load_projects()
    if project_name not in projects:
        return False
        
    # Remove pasta física
    data_dir = get_data_dir()
    project_dir = os.path.join(data_dir, project_name)
    if os.path.exists(project_dir):
        shutil.rmtree(project_dir)
        
    # Remove do índice JSON
    del projects[project_name]
    save_projects(projects)
    
    return True

def get_project_keys(project_name: str) -> tuple[bytes, bytes]:
    projects = load_projects()
    if project_name not in projects:
        raise ValueError(f"Projeto {project_name} não encontrado.")
    
    p = projects[project_name]
    with open(p['private_key_path'], 'rb') as f: priv = f.read()
    with open(p['public_key_path'], 'rb') as f: pub = f.read()
    
    return priv, pub
