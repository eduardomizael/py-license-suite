# 🛡️ Py-License-Suite

Um pacote Open Source para geração, gerenciamento e validação de licenças Offline para software em Python, construído para ser blindado pelo [PyArmor](https://pyarmor.readthedocs.io/).

O Sistema foi desenhado em duas vias:

1. **O Servidor (CLI Central)**: Que vai na sua máquina desenvolvedora e expede as chaves RSA blindadas e os arquivos `.lic`.
2. **O Cliente (Validador)**: Pastas e módulos agnósticos ofuscados por você para rodar estritamente dentro da máquina do comprador contendo mecanismos Anti-Fraude e de Check do Hardware ID.

---

## 💻 Requisitos

- Windows (Atualmente com scripts WMI desenhados para capturar BIOS + Placa-Mãe Windows)
- Python 3.12+
- `uv` Package Manager recomendado.

## 📦 Instalação

Clone este repositório, ou utilize via gerenciador de dependências, de forma separada dos seus scripts finais clientes.

Via **UV**:

```bash
uv sync   # Vai instalar cryptography, pyarmor, pyyaml...
```

---

## 🛠 Como Funciona (Workflow Básico)

O pacote dispões do entrypoint central: `cli.py`.

### 1. Inicializando seu Novo Projeto

Você cria um ambiente isolado dentro do py-license-suite (ele adicionará seu sistema num banco de dados json não-versionado). O sistema gera pares de chave Privada e Pública e deixa no seu computador.

```bash
uv run cli.py init --name SeuSoftware
```

### 2. Injetando a Licença no "SeuSoftware"

Basta invocar o builder mandando entregar as chaves públicas injetadas em cópias dos templates na pasta do seu código base (por ex. `C:\dev\meu-sistema-app\license_check`). Ele irá usar o PyArmor para ofuscar (criptografar) essas rotinas client-side num bloco preto, entregando pro seu projeto final.

```bash
uv run cli.py build --project SeuSoftware --target "C:\\dev\\meu-sistema-app\\license_check"
```

Dentro do arquivo inicial do projeto final (`main.py` de preferência), você vai apenas referenciar o pacote `license_check` que acabamos de mandar e instanciar:

```python
from license_check.security import check_startup_licensing
from license_check.anti_tampering import update_system_clock
import atexit

# Mata a exe no processo sys.exit(1) caso hardware ID, expiração ou fraudes baterem.
check_startup_licensing()
# Mantem a vida da proteção anti-fraude checada a cada uso
atexit.register(update_system_clock)
```

### 3. Gerando uma Licença válida (`.lic`)

Quando seu cliente disser o Hardware-ID que acusar na inicialização da máquina dele, você executará o keygen informando esse código.

```bash
uv run cli.py keygen --project SeuSoftware --hwid "<SHA_HASH_MAQUINA>" --expires 2026-12-31
```

Entregue o gerado `.lic` ao lado do executável final do cliente para prosseguir o uso.
