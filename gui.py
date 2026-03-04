import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime

# Importações do Core
from core.project_manager import create_project, load_projects, get_project_keys, delete_project
from core.crypto_utils import sign_license_data
from core.builder import build_project

class RedirectText:
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, string):
        self.text_widget.configure(state=tk.NORMAL)
        self.text_widget.insert(tk.END, string)
        self.text_widget.see(tk.END)
        self.text_widget.configure(state=tk.DISABLED)
        # Força atualização caso estejamos em thread separada
        self.text_widget.update_idletasks()

    def flush(self):
        pass

class PyLicenseGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PyLicense Suite - Interface Gráfica")
        self.geometry("700x550")
        self.minsize(600, 450)
        
        # Variáveis globais de interface
        self.projects_dict = {}
        
        self.create_widgets()
        self.refresh_projects()
        
    def create_widgets(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Abas
        self.tab_projects = ttk.Frame(self.notebook)
        self.tab_keygen = ttk.Frame(self.notebook)
        self.tab_build = ttk.Frame(self.notebook)
        
        self.notebook.add(self.tab_projects, text="Projetos")
        self.notebook.add(self.tab_keygen, text="Gerar Licença")
        self.notebook.add(self.tab_build, text="Build Cliente")
        
        self.setup_projects_tab()
        self.setup_keygen_tab()
        self.setup_build_tab()

    # --- ABA: PROJETOS ---
    def setup_projects_tab(self):
        frame_top = ttk.LabelFrame(self.tab_projects, text="Novo Projeto", padding=10)
        frame_top.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(frame_top, text="Nome do Projeto:").pack(side=tk.LEFT, padx=5)
        self.entry_proj_name = ttk.Entry(frame_top, width=30)
        self.entry_proj_name.pack(side=tk.LEFT, padx=5)
        
        btn_create = ttk.Button(frame_top, text="Criar Projeto", command=self.on_create_project)
        btn_create.pack(side=tk.LEFT, padx=5)
        
        btn_delete = ttk.Button(frame_top, text="Excluir Selecionado", command=self.on_delete_project)
        btn_delete.pack(side=tk.RIGHT, padx=5)
        
        frame_list = ttk.LabelFrame(self.tab_projects, text="Projetos Existentes", padding=10)
        frame_list.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        columns = ("nome", "criado_em")
        self.tree_projects = ttk.Treeview(frame_list, columns=columns, show="headings")
        self.tree_projects.heading("nome", text="Nome do Projeto")
        self.tree_projects.heading("criado_em", text="Criado Em")
        self.tree_projects.column("nome", width=300)
        self.tree_projects.column("criado_em", width=200)
        
        scrollbar = ttk.Scrollbar(frame_list, orient=tk.VERTICAL, command=self.tree_projects.yview)
        self.tree_projects.configure(yscrollcommand=scrollbar.set)
        
        self.tree_projects.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # --- ABA: GERAR LICENÇA ---
    def setup_keygen_tab(self):
        frame_form = ttk.Frame(self.tab_keygen, padding=20)
        frame_form.pack(fill=tk.BOTH, expand=True)
        
        # Projeto
        ttk.Label(frame_form, text="Selecione o Projeto:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.combo_project_keygen = ttk.Combobox(frame_form, state="readonly", width=40)
        self.combo_project_keygen.grid(row=0, column=1, sticky=tk.W, pady=5)
        
        # HWID
        ttk.Label(frame_form, text="Hardware ID (HWID):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.entry_hwid = ttk.Entry(frame_form, width=43)
        self.entry_hwid.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        # Data de Expiração
        ttk.Label(frame_form, text="Expira em (YYYY-MM-DD):").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.entry_expires = ttk.Entry(frame_form, width=20)
        self.entry_expires.grid(row=2, column=1, sticky=tk.W, pady=5)
        
        btn_generate = ttk.Button(frame_form, text="Gerar Licença", command=self.on_generate_license)
        btn_generate.grid(row=3, column=1, sticky=tk.E, pady=15)

    # --- ABA: BUILD CLIENTE ---
    def setup_build_tab(self):
        frame_form = ttk.Frame(self.tab_build, padding=10)
        frame_form.pack(fill=tk.X)
        
        # Selecionar Projeto
        ttk.Label(frame_form, text="Projeto Base:").grid(row=0, column=0, sticky=tk.W, pady=5, padx=5)
        self.combo_project_build = ttk.Combobox(frame_form, state="readonly", width=30)
        self.combo_project_build.grid(row=0, column=1, sticky=tk.W, pady=5, padx=5)
        
        # Selecionar Entrypoint
        ttk.Label(frame_form, text="Entrypoint:").grid(row=1, column=0, sticky=tk.W, pady=5, padx=5)
        
        frame_entry = ttk.Frame(frame_form)
        frame_entry.grid(row=1, column=1, sticky=tk.W, pady=5, padx=5)
        
        self.lbl_entrypoint_path = ttk.Label(frame_entry, text="Nenhum arquivo selecionado...", width=45, relief="sunken", anchor="w")
        self.lbl_entrypoint_path.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.selected_entrypoint_full_path = ""
        
        btn_select = ttk.Button(frame_entry, text="Procurar...", command=self.on_select_entrypoint)
        btn_select.pack(side=tk.LEFT, padx=5)
        
        # Checkbox Build Exec
        self.var_build_exe = tk.BooleanVar(value=False)
        chk_build = ttk.Checkbutton(frame_form, text="Compilar executável (.exe) usando PyInstaller", variable=self.var_build_exe)
        chk_build.grid(row=2, column=1, sticky=tk.W, pady=5, padx=5)
        
        self.btn_build = ttk.Button(frame_form, text="Injetar e Compilar", command=self.on_build_project)
        self.btn_build.grid(row=3, column=1, sticky=tk.W, pady=10, padx=5)
        
        # Log Box
        frame_log = ttk.LabelFrame(self.tab_build, text="Console Output", padding=5)
        frame_log.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.text_log = tk.Text(frame_log, state=tk.DISABLED, bg="black", fg="white", font=("Consolas", 9))
        self.text_log.pack(fill=tk.BOTH, expand=True)

    # --- MÉTODOS DE AÇÃO ---
    def refresh_projects(self):
        self.projects_dict = load_projects()
        
        # Atualiza Treeview
        for item in self.tree_projects.get_children():
            self.tree_projects.delete(item)
            
        proj_names = []
        for name, data in self.projects_dict.items():
            proj_names.append(name)
            created_at = data.get("created_at", "N/A")
            self.tree_projects.insert("", tk.END, values=(name, created_at))
            
        # Atualiza Comboboxes
        self.combo_project_keygen['values'] = proj_names
        self.combo_project_build['values'] = proj_names
        
        if proj_names:
            if not self.combo_project_keygen.get(): self.combo_project_keygen.set(proj_names[0])
            if not self.combo_project_build.get(): self.combo_project_build.set(proj_names[0])

    def on_create_project(self):
        name = self.entry_proj_name.get().strip()
        if not name:
            messagebox.showwarning("Aviso", "Por favor, insira o nome do projeto.")
            return
            
        if create_project(name):
            messagebox.showinfo("Sucesso", f"Projeto '{name}' criado com sucesso.\nChaves geradas.")
            self.entry_proj_name.delete(0, tk.END)
            self.refresh_projects()
        else:
            messagebox.showerror("Erro", f"O projeto '{name}' já existe.")

    def on_delete_project(self):
        selected_item = self.tree_projects.focus()
        if not selected_item:
            messagebox.showwarning("Aviso", "Selecione um projeto na lista para excluir.")
            return
            
        project_name = self.tree_projects.item(selected_item, "values")[0]
        
        confirm = messagebox.askyesno(
            "Confirmar Exclusão", 
            f"Você tem certeza que deseja deletar o projeto '{project_name}'?\nIsso apagará PERMANENTEMENTE a chave RSA e metadados dele!"
        )
        
        if confirm:
            if delete_project(project_name):
                messagebox.showinfo("Sucesso", f"O projeto '{project_name}' foi excluído com sucesso.")
                self.refresh_projects()
            else:
                messagebox.showerror("Erro", f"Houve uma falha ao tentar excluir o projeto '{project_name}'.")

    def on_generate_license(self):
        proj = self.combo_project_keygen.get()
        hwid = self.entry_hwid.get().strip()
        expires = self.entry_expires.get().strip()
        
        if not proj or not hwid or not expires:
            messagebox.showwarning("Aviso", "Preencha todos os campos (Projeto, HWID e Validade).")
            return
            
        try:
            datetime.strptime(expires, '%Y-%m-%d')
        except ValueError:
            messagebox.showerror("Erro", "Formato de data incorreto. Use YYYY-MM-DD.")
            return
            
        try:
            priv_pem, _ = get_project_keys(proj)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao acessar chaves do projeto:\n{e}")
            return
            
        payload = {
            "hwid": hwid,
            "expires_at": expires,
            "issued_at": datetime.now().strftime('%Y-%m-%d')
        }
        
        try:
            licence_string = sign_license_data(priv_pem, payload)
            out_name = f"license_{hwid[:8]}.lic"
            with open(out_name, 'w') as f:
                f.write(licence_string)
            messagebox.showinfo("Sucesso", f"Licença gerada com sucesso e salva em:\n{out_name}")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao gerar licença:\n{e}")

    def on_select_entrypoint(self):
        filepath = filedialog.askopenfilename(
            title="Selecione o entrypoint (ex: main.py)",
            filetypes=[("Arquivos Python", "*.py"), ("Todos os Arquivos", "*.*")]
        )
        if filepath:
            self.selected_entrypoint_full_path = filepath
            # Mostrar o caminho usando ... no inicio se for muito longo
            display_path = filepath if len(filepath) < 55 else "..." + filepath[-50:]
            self.lbl_entrypoint_path.config(text=display_path)

    def on_build_project(self):
        proj_name = self.combo_project_build.get()
        full_entrypoint = self.selected_entrypoint_full_path
        build_exe = self.var_build_exe.get()
        
        if not proj_name:
            messagebox.showwarning("Aviso", "Selecione o projeto PyLicense base.")
            return
            
        if not full_entrypoint or not os.path.exists(full_entrypoint):
            messagebox.showwarning("Aviso", "Selecione um arquivo de entrypoint válido.")
            return
            
        # Extrai o diretório pai e o nome do arquivo
        target_dir = os.path.dirname(full_entrypoint)
        entrypoint_file = os.path.basename(full_entrypoint)
        
        # Prepara a UI para o processo
        self.btn_build.config(state=tk.DISABLED)
        self.text_log.configure(state=tk.NORMAL)
        self.text_log.delete(1.0, tk.END)
        self.text_log.configure(state=tk.DISABLED)
        
        # Em threads para não travar a UI
        t = threading.Thread(target=self._build_task, args=(proj_name, target_dir, entrypoint_file, build_exe))
        t.daemon = True
        t.start()

    def _build_task(self, proj_name, target_dir, entrypoint_file, build_exe):
        original_stdout = sys.stdout
        sys.stdout = RedirectText(self.text_log)
        
        try:
            print(f"=== Iniciando processo de Build para o cliente ===")
            print(f"Projeto Proteção: {proj_name}")
            print(f"Diretório Alvo: {target_dir}")
            print(f"Entrypoint: {entrypoint_file}")
            print("==================================================\n")
            
            success = build_project(proj_name, target_dir, entrypoint_file, build_exe)
            
            if success:
                print("\n=== PROCESSO CONCLUÍDO COM SUCESSO ===")
            else:
                print("\n=== PROCESSO FINALIZADO COM ERROS ===")
        except Exception as e:
            print(f"\n[ERRO FATAL DURANTE O BUILD]: {e}")
        finally:
            sys.stdout = original_stdout
            self.after(0, lambda: self.btn_build.config(state=tk.NORMAL))

if __name__ == "__main__":
    app = PyLicenseGUI()
    app.mainloop()
