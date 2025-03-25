# Agente-Roadmap-Jornada

## Descrição
Este projeto implementa um agente inteligente para criação e gerenciamento de roadmaps de estudos.

## Instalação

### Pré-requisitos
- Python 3.8 ou superior
- [Poetry](https://python-poetry.org/docs/#installation) (gerenciador de dependências)

### Passos para instalação

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/Agente-Roadmap-Jornada.git
cd Agente-Roadmap-Jornada
```

2. Instale as dependências usando Poetry:
```bash
poetry install
```

## Configuração de Variáveis de Ambiente

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

## Executando o Projeto

Para executar o projeto após a instalação:

```bash
poetry run python .src/main.py
```

## Estrutura do Projeto

- `src/`: Contém o código-fonte do projeto.
  - `model_api.py`: Lógica para seleção e uso dos modelos de linguagem.
  - `main.py`: Ponto de entrada do projeto.
  - `prompt_maker.py`: Módulo responsável por criar prompts para os modelos de linguagem.
- `config.py`: Configurações centralizadas.
- `README.md`: Instruções de instalação e uso.
- `.env`: Arquivo de variáveis de ambiente (não deve ser commitado no repositório).