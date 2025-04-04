# Agente-Roadmap-Jornada

## Descrição
Este projeto implementa um agente inteligente para criação e gerenciamento de roadmaps de estudos.

## Instalação

### Pré-requisitos
- Docker
- Docker Compose

## Executando com Docker

O projeto está configurado para ser executado facilmente com Docker Compose, que gerencia tanto o backend (FastAPI) quanto o frontend (Streamlit). Comece clonando o repositório:

```bash
git clone https://github.com/seu-usuario/Agente-Roadmap-Jornada.git
cd Agente-Roadmap-Jornada
```

### Configuração de Variáveis de Ambiente

O projeto utiliza variáveis de ambiente para gerenciar tokens e configurações sensíveis. Siga os passos abaixo para configurá-las:

1. Crie um arquivo `.env` na raiz do projeto:
```bash
touch .env
```

2. Adicione suas variáveis de ambiente no arquivo `.env`:
```
HF_TOKEN=seu_token_huggingface
OPENAI_TOKEN=seu_token_openai
DEEPSEEK_TOKEN=seu_token_deepseek
```

### Construa e inicie os containers

```bash
docker compose build
docker compose up
```

### Acesse as aplicações

- Acesse o backend em: `http://localhost:8000`
- Acesse o frontend em: `http://localhost:8501`
- Acesse a documentação da API em: `http://localhost:8000/docs`

Para parar os containers:

```bash
docker compose down
```

## Estrutura do Projeto
- `backend/`: Contém o código-fonte do backend.
  - `main.py`: Aplicação FastAPI principal.
  - `database/`: Módulos para gerenciamento do banco de dados SQLite.
  - `ai_agent/`: Lógica para interação com modelos de linguagem.
    - `llm_service.py`: Serviço para seleção e uso dos modelos de linguagem.
    - `prompt_maker.py`: Módulo responsável por criar prompts para os modelos.
  - `prompt_files/`: Arquivos de template para geração de prompts.
`frontend/`: Contém o código-fonte do frontend Streamlit.
  - `streamlit_app.py`: Interface de usuário baseada em Streamlit para interação com o sistema.
- `data/`: Diretório onde o banco de dados SQLite é armazenado.
- `docker-compose.yml`: Configuração dos serviços Docker.
- `.env`: Arquivo de variáveis de ambiente (não deve ser commitado no repositório).