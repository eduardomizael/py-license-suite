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

Basta invocar o builder mandando entregar as chaves públicas injetadas apontando o caminho da **raiz** do projeto cliente. Ele irá usar o PyArmor para ofuscar o validador. Além de proteger o código, **o próprio comando da Suíte vai injetar a trava no seu script inicial e instalar a biblioteca necessária (`cryptography`) nativamente lá**.

Se você quiser segurança extrema (para que ninguém delete as injeções alterando seu código-fonte `app.py` original em bloco de notas), você pode solicitar que a ferramenta gere um `Executável Autônomo (.exe)` que blinda o arquivo de entrada da sua aplicação inteiramente usando o PyInstaller.

```bash
uv run cli.py build --project SeuSoftware --target "C:\\dev\\meu-sistema-app" --entrypoint "app.py" --build-exe
```

*Observação: A flag `--entrypoint` é opcional. Se não informada, o robô irá tentar modificar automaticamente um arquivo chamado `main.py`.*

### 3. Gerando uma Licença válida (`.lic`)

Quando seu cliente disser o Hardware-ID que acusar na inicialização da máquina dele, você executará o keygen informando esse código.

```bash
uv run cli.py keygen --project SeuSoftware --hwid "<SHA_HASH_MAQUINA>" --expires 2026-12-31
```

Entregue o gerado `.lic` ao lado do executável final do cliente para prosseguir o uso.
