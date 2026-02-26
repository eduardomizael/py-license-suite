import argparse
import sys
from datetime import datetime
from core.project_manager import create_project, load_projects
from core.crypto_utils import sign_license_data, verify_license_signature

def main():
    parser = argparse.ArgumentParser(description="PyLicense Suite - Ferramenta de Licenciamento Offline")
    subparsers = parser.add_subparsers(dest='command', help='Comandos disponíveis')
    
    # pylicense init
    parser_init = subparsers.add_parser('init', help='Cria um novo projeto de licenciamento')
    parser_init.add_argument('--name', required=True, help='Nome do projeto (ex: MeuApp)')
    
    # pylicense list
    parser_list = subparsers.add_parser('list', help='Lista todos os projetos')

    # pylicense keygen
    parser_keygen = subparsers.add_parser('keygen', help='Gera uma nova licença (.lic)')
    parser_keygen.add_argument('--project', required=True, help='Nome do projeto pai')
    parser_keygen.add_argument('--hwid', required=True, help='Hash de Hardware do Cliente')
    parser_keygen.add_argument('--expires', required=True, help='Data de expiração YYYY-MM-DD')
    
    # pylicense build
    parser_build = subparsers.add_parser('build', help='Injeta e ofusca o módulo do cliente para um diretório alvo')
    parser_build.add_argument('--project', required=True, help='Nome do Projeto da Suíte')
    parser_build.add_argument('--target', required=True, help='Caminho/Output diretorio do projeto do Cliente onde o modulo deve entrar')
    parser_build.add_argument('--entrypoint', default='main.py', help='Arquivo principal do projeto do cliente para injetar a validação')

    args = parser.parse_args()
    
    if args.command == 'init':
        if create_project(args.name):
            print(f"[SUCESSO] Projeto '{args.name}' criado. Chave RSA de 2048-bits emitidas em /projects_data/{args.name}.")
        else:
            print(f"[ERRO] Projeto '{args.name}' ja existe.")
            
    elif args.command == 'list':
        projs = load_projects()
        if not projs:
            print("Nenhum projeto cadastrado.")
        for name, data in projs.items():
            print(f"- {name} (criado em: {data.get('created_at', 'N/A')})")
            
    elif args.command == 'keygen':
        from core.project_manager import get_project_keys
        try:
            from datetime import datetime
            datetime.strptime(args.expires, '%Y-%m-%d')
        except ValueError:
            print("[ERRO] Formato de data de validade incorreto. Use YYYY-MM-DD.")
            sys.exit(1)
            
        print(f"Buscando chave privada do projeto '{args.project}'...")
        try:
            priv_pem, _ = get_project_keys(args.project)
        except ValueError as e:
            print(e)
            sys.exit(1)
            
        payload = {
            "hwid": args.hwid,
            "expires_at": args.expires,
            "issued_at": datetime.now().strftime('%Y-%m-%d')
        }
        
        try:
            licence_string = sign_license_data(priv_pem, payload)
            out_name = f"license_{args.hwid[:8]}.lic"
            with open(out_name, 'w') as f:
                f.write(licence_string)
            print(f"[SUCESSO] Licença gerada e salva no arquivo '{out_name}'.")
        except Exception as e:
            print(f"[ERRO] Falha ao assinar: {e}")
            
    elif args.command == 'build':
        from core.builder import build_project
        print(f"Iniciando Build do Py-License para o projeto '{args.project}'...")
        build_project(args.project, args.target, args.entrypoint)
        
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
