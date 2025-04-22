import streamlit as st
import os
import sys
import time
import datetime
from pathlib import Path
from loguru import logger
from dotenv import load_dotenv
import requests
import streamlit.components.v1 as components
import re

# --- Configuração do Loguru ---
logger.remove()
logger.add(
    sys.stderr,
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
    level="DEBUG" # Alterado para INFO para produção, DEBUG para desenvolvimento
)
logger.info("--- Iniciando Aplicativo Streamlit ---")

# --- Variáveis de Ambiente ---
load_dotenv()
# Get Backend URL from environment variable (set in docker-compose)
BACKEND_URL=os.getenv("BACKEND_URL", "http://backend:8000")
logger.info(f"Backend API URL: {BACKEND_URL}")
logger.info("Variáveis de ambiente carregadas (se o arquivo .env existir).")

# --- Configuração da Página (precisa ser o primeiro comando st) ---
st.set_page_config(
        page_title="Gerador de Plano de Estudos IA",
        page_icon="🤖",
        layout="wide"
    )

# --- Inicializar Estado da Sessão ---
if 'page' not in st.session_state:
    st.session_state.page = 'form' # 'form' ou 'result'
    logger.debug("Estado da sessão 'page' inicializado para 'form'.")
if 'form_data' not in st.session_state:
    st.session_state.form_data = {} # Stores form inputs for pre-filling
    logger.debug("Estado da sessão 'form_data' inicializado como dicionário vazio.")
if 'is_processing' not in st.session_state:
    st.session_state.is_processing = False # Flag to prevent multiple submissions/navigation
if 'error_message' not in st.session_state:
    st.session_state.error_message = None # Stores errors from backend or validation
if 'plan_id' not in st.session_state:
    st.session_state.plan_id = None # Stores the ID of the current study plan conversation
    logger.debug("Estado da sessão 'plan_id' inicializado para None.")
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = [] # Stores the list of chat messages [{"role": ..., "content": ...}]
    logger.debug("Estado da sessão 'chat_history' inicializado como lista vazia.")
if 'study_plan' not in st.session_state:
    st.session_state.study_plan = None # Armazena apenas o conteúdo do plano de estudos
    logger.debug("Estado da sessão 'study_plan' inicializado como None.")

def render_mermaid(code: str) -> None:
    """Renderiza um diagrama Mermaid usando componentes HTML do Streamlit."""
    components.html(
        f"""
        <pre class="mermaid">
            {code}
        </pre>

        <script type="module">
            import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
            mermaid.initialize({{ startOnLoad: true }});
        </script>
        """,
        height=800  # Ajuste a altura conforme necessário
    )

def extract_mermaid_blocks(content: str) -> list:
    """Extrai blocos de código Mermaid de texto markdown."""
    pattern = r"```mermaid\s+(.*?)\s+```"
    return re.findall(pattern, content, re.DOTALL)

# --- Implementações das Páginas ---


def form_page():
    """Renderiza a página do formulário de entrada."""
    logger.info("Renderizando página 'form'.")
    st.title("Crie seu Plano de Estudos Personalizado 📚")
    st.markdown("""
    ### Preencha o formulário abaixo para gerar seu plano de estudos personalizado!
    Quanto mais específico você for, melhor será o plano adaptado às suas necessidades e disponibilidade.
    """)
    # Exibe mensagem de erro anterior, se houver
    if st.session_state.error_message:
        st.error(f"⚠️ Erro anterior: {st.session_state.error_message}")
        st.session_state.error_message = None # Limpa após exibir

    defaults = st.session_state.get('form_data', {})
    logger.debug(f"Usando dados padrão do formulário: {defaults}")

    with st.form(key='study_plan_input_form'):
        st.subheader("Seus Dados")

        # Nome e E-mail
        name = st.text_input("Nome*", value=defaults.get('name', ''), key="form_name")
        email = st.text_input("Email*", value=defaults.get('email', ''), key="form_email")

        # Horas por dia da semana
        st.subheader("Disponibilidade Semanal*")
        days_of_week = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
        hours_per_day = {}
        
        # Default values from session or 0
        default_hours = defaults.get('hours_per_day', {})
        
        cols = st.columns(len(days_of_week))
        for i, day in enumerate(days_of_week):  
            with cols[i]:  
                default_val = default_hours.get(day, 2 if day in ["Segunda", "Terça", "Quarta", "Quinta", "Sexta"] else 0)  
                hours = st.slider(  
                    day[:3], 
                    min_value=0,  
                    max_value=8,  
                    value=default_val,  
                    key=f"form_hours_{day}"  
                )  
                hours_per_day[day] = hours

        # Dia de início do plano
        start_date_default = defaults.get('start_date', datetime.date.today())
        if isinstance(start_date_default, str):
            try:
                start_date_default = datetime.datetime.strptime(start_date_default, "%Y-%m-%d").date()
            except ValueError:
                logger.warning(f"Não foi possível analisar a string de data '{start_date_default}' do estado da sessão. Usando hoje.")
                start_date_default = datetime.date.today()
        elif not isinstance(start_date_default, datetime.date):
            logger.warning(f"Tipo de data inválido '{type(start_date_default)}' encontrado no estado da sessão. Usando hoje.")
            start_date_default = datetime.date.today()
        start_date = st.date_input(
            "Data de Início Preferida*",
            value=start_date_default,
            min_value=datetime.date.today(),
            key="form_start_date"
        )

        # Nível de conhecimento
        st.subheader("Nível de Conhecimento*")
        skill_options = ["Nunca utilizei", "Iniciante", "Intermediário", "Avançado"]
        
        python_level = st.radio(
            "Qual seu nível em Python?",
            options=skill_options,
            index=skill_options.index(defaults.get('python_level', 'Iniciante')),
            key="form_python_level"
        )
        
        sql_level = st.radio(
            "Qual seu nível em SQL?",
            options=skill_options,
            index=skill_options.index(defaults.get('sql_level', 'Iniciante')),
            key="form_sql_level"
        )
        
        cloud_level = st.radio(
            "Qual seu nível em Cloud?",
            options=skill_options,
            index=skill_options.index(defaults.get('cloud_level', 'Iniciante')),
            key="form_cloud_level"
        )

        # Experiência com ferramentas
        st.subheader("Experiência com Ferramentas*")
        used_git = st.radio(
            "Você já utilizou Git/GitHub?",
            options=["Sim", "Não"],
            index=0 if defaults.get('used_git', False) else 1,
            key="form_used_git"
        )
        
        used_docker = st.radio(
            "Você já utilizou Docker?",
            options=["Sim", "Não"],
            index=0 if defaults.get('used_docker', False) else 1,
            key="form_used_docker"
        )

        # Interesses adicionais
        st.subheader("Interesses Adicionais (Opcional)")
        interest_options = ["Webscraping", "n8n", "Airflow", "DBT", "PowerBI", "Kafka", "Terraform", "FastAPI"]
        interests = st.pills(
            "Em quais desses temas você também se interessa?",
            options=interest_options,
            selection_mode="multi",
            default=defaults.get('interests', []),
            key="form_interests"
        )

        # Desafio atual
        st.subheader("Desafio Atual (Opcional)")
        main_challenge = st.text_area(
            "Qual o maior desafio que você precisa resolver hoje, seja no seu trabalho ou em algum projeto pessoal?",
            value=defaults.get('main_challenge', ''),
            height=80,
            placeholder="Ex: 'Preciso automatizar relatórios mensais', 'Quero migrar minha aplicação para a nuvem'",
            key="form_main_challenge"
        )

        st.markdown("---")
        st.markdown("*\* Campos obrigatórios*")

        # Desabilita o botão durante o processamento
        submitted = st.form_submit_button("✨ Gerar Plano de Estudos", disabled=st.session_state.is_processing)

        if submitted:
            logger.info("Formulário enviado.")
            # --- Validação de Entrada ---
            validation_passed = True
            error_messages = []
            if not name: error_messages.append("Por favor, insira seu Nome."); validation_passed = False
            if not email: error_messages.append("Por favor, insira seu Email."); validation_passed = False
            if sum(hours_per_day.values()) == 0: error_messages.append("Por favor, informe suas horas disponíveis em pelo menos um dia."); validation_passed = False
            if not python_level: error_messages.append("Por favor, selecione seu nível em Python."); validation_passed = False
            if not sql_level: error_messages.append("Por favor, selecione seu nível em SQL."); validation_passed = False
            if not cloud_level: error_messages.append("Por favor, selecione seu nível em Cloud."); validation_passed = False
            if not used_git: error_messages.append("Por favor, informe se já usou Git/GitHub."); validation_passed = False
            if not used_docker: error_messages.append("Por favor, informe se já usou Docker."); validation_passed = False

            if not validation_passed:
                for msg in error_messages:
                    st.error(f"⚠️ {msg}")
            else:
                logger.info("Validação do formulário bem-sucedida.")
                # --- Armazenar entradas atuais para possível pré-preenchimento ---
                current_form_data = {
                    "name": name,
                    "email": email,
                    "hours_per_day": hours_per_day,
                    "start_date": start_date,
                    "python_level": python_level,
                    "sql_level": sql_level,
                    "cloud_level": cloud_level,
                    "used_git": used_git == "Sim",
                    "used_docker": used_docker == "Sim",
                    "interests": interests,
                    "main_challenge": main_challenge
                }
                st.session_state.form_data = current_form_data
                logger.debug(f"Dados do formulário atual armazenados no estado da sessão: {current_form_data}")
                
                # Define flag de processamento e executa novamente para desabilitar botão/navegação
                st.session_state.is_processing = True
                st.session_state.error_message = None # Limpa erros anteriores
                st.rerun() # Executa novamente para mostrar spinner e desabilitar controles

    # --- Lógica de Chamada da API (Fora do bloco do formulário, acionada pela flag is_processing) ---
    if st.session_state.is_processing:
        logger.info("Flag de processamento é True, tentando chamada de API.")
        with st.spinner("⏳ Gerando seu plano de estudos personalizado... Por favor, aguarde."):
            try:
                # Prepara payload de dados para a API backend
                payload = st.session_state.form_data.copy()
                # Converte data para string para serialização JSON
                payload['start_date'] = payload['start_date'].isoformat()

                logger.info(f"Enviando requisição POST para {BACKEND_URL}/generate_plan")
                logger.debug(f"Payload Snippet: {str(payload)[:200]}...") # Truncated log

                # Faz a chamada de API para o backend
                response = requests.post(f"{BACKEND_URL}/generate_plan", json=payload, timeout=180) # Timeout aumentado para LLM
                response.raise_for_status() # Levanta HTTPError para respostas ruins (4xx ou 5xx)

                # Processa resposta bem-sucedida
                api_response = response.json()
                logger.info("Chamada de API bem-sucedida.")
                logger.debug(f"API Response Snippet: {str(api_response)[:200]}...") # Truncated log

                # Store the plan_id and the initial chat history
                st.session_state.plan_id = api_response.get("plan_id")
                st.session_state.chat_history = api_response.get("chat", [])

                # Extrair o plano de estudos, antes de mudar de página
                for message in st.session_state.chat_history:
                    if message["role"] == "assistant":
                        st.session_state.study_plan = message["content"]
                        logger.info("Plano de estudos extraído e armazenado no estado da sessão.")
                        break


                st.session_state.page = 'result'
                logger.info(f"Navegando para a página de resultados com plan_id: {st.session_state.plan_id}")
                logger.debug(f"Initial Chat History Snippet: {str(st.session_state.chat_history)[:200]}...") # Truncated log
                st.session_state.is_processing = False # Reseta flag
                st.success("✅ Plano de estudos gerado com sucesso!")
                time.sleep(1.5)
                st.rerun() # Executa novamente para navegar para a página de resultado

            except requests.exceptions.RequestException as e:
                logger.error(f"Falha na requisição da API: {e}", exc_info=True)
                error_detail = f"Erro de comunicação com o servidor: {e}"
                try:
                    # Tenta obter erro mais específico do corpo da resposta, se disponível
                    error_data = e.response.json()
                    error_detail = error_data.get("detail", error_detail)
                except Exception:
                    pass # Mantém o detalhe do erro original
                st.session_state.error_message = error_detail
                st.session_state.is_processing = False # Reseta flag
                st.rerun() # Executa novamente para mostrar erro na página do formulário

            except Exception as e: # Captura outros erros potenciais
                logger.error(f"Ocorreu um erro inesperado durante o processamento: {e}", exc_info=True)
                st.session_state.error_message = f"Ocorreu um erro inesperado: {e}"
                st.session_state.is_processing = False # Reseta flag
                st.rerun() # Executa novamente para mostrar erro na página do formulário
             

def result_page():
    """Renderiza a página de resultado exibindo o plano gerado."""
    logger.info("Renderizando página 'result'.")
    # ADD THIS DEBUG LOG
    logger.debug(f"Entering result_page. is_processing={st.session_state.get('is_processing', False)}, plan_id={st.session_state.get('plan_id')}")
    st.title("✅ Seu Plano de Estudos Gerado")

    # --- API Call Logic for Chat ---
    # Check this FIRST: If processing is active (triggered by chat input rerun), call the API
    if st.session_state.get('is_processing', False) and st.session_state.get('plan_id') is not None:
         logger.info(f"Flag de processamento é True e plan_id existe ({st.session_state.get('plan_id')}), tentando chamada de API /continue_chat.")
         with st.spinner("Pensando... 🧠"): # Spinner should show now
            try:
                # Prepare payload using the latest chat history from session state
                chat_payload = {
                    "plan_id": st.session_state.plan_id,
                    "messages": st.session_state.chat_history # History already includes user's last message
                }
                logger.info(f"Enviando requisição POST para {BACKEND_URL}/continue_chat")
                logger.debug(f"Chat Payload Snippet: {str(chat_payload)[:200]}...") # Truncated log

                response = requests.post(f"{BACKEND_URL}/continue_chat", json=chat_payload, timeout=180)
                response.raise_for_status()

                api_response = response.json()
                logger.info("Chamada de API /continue_chat bem-sucedida.")
                logger.debug(f"API /continue_chat Response Snippet: {str(api_response)[:200]}...") # Truncated log

                # Update the chat history with the full history from the backend response
                st.session_state.chat_history = api_response.get("chat", [])
                st.session_state.is_processing = False # Reset flag BEFORE rerunning
                st.rerun() # Rerun to display the new assistant message

            except requests.exceptions.RequestException as e:
                logger.error(f"Falha na requisição da API /continue_chat: {e}", exc_info=True)
                error_detail = f"Erro de comunicação com o servidor: {e}"
                try:
                    error_data = e.response.json()
                    error_detail = error_data.get("detail", error_detail)
                except Exception:
                    pass
                st.error(f"⚠️ Erro ao contatar o assistente: {error_detail}")
                # Consider removing last user message if needed, or just show error
                # if st.session_state.chat_history and st.session_state.chat_history[-1]["role"] == "user":
                #     st.session_state.chat_history.pop()
                st.session_state.is_processing = False # Reset flag
                st.rerun() # Rerun to show error and re-enable input

            except Exception as e:
                logger.error(f"Ocorreu um erro inesperado durante o processamento do chat: {e}", exc_info=True)
                st.error(f"⚠️ Ocorreu um erro inesperado: {e}")
                st.session_state.is_processing = False # Reset flag
                st.rerun() # Rerun to show error and re-enable input

    # --- Display Chat History and Input ---
    # Check this SECOND: If NOT processing, display the chat interface
    elif 'chat_history' in st.session_state and st.session_state.chat_history:
        logger.info("Histórico de chat encontrado no estado da sessão. Exibindo.")
        user_info = st.session_state.get('form_data', {}) # Get form data for context if needed

        # Extrair o plano de estudos da primeira mensagem do assistente
        if st.session_state.study_plan is None and len(st.session_state.chat_history) > 1:
            for message in st.session_state.chat_history:
                if message["role"] == "assistant":
                    st.session_state.study_plan = message["content"]
                    logger.info("Plano de estudos extraído e armazenado no estado da sessão.")
                    break
        
        # Display Chat History
        st.subheader("💬 Conversa com o Assistente")
        # Skip the first message (initial user prompt) when displaying
        for message in st.session_state.chat_history[1:]:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

                # Se for uma mensagem do assistente, procura por diagramas Mermaid
                if message["role"] == "assistant":
                    mermaid_blocks = extract_mermaid_blocks(message["content"])
                    if mermaid_blocks:
                        st.subheader("📊 Visualização do Plano")
                        for mermaid_code in mermaid_blocks:
                            render_mermaid(mermaid_code)

        st.markdown("---")

        # Chat Input (disabled during API call by the logic above)
        logger.debug("About to render st.chat_input")
        if prompt := st.chat_input("Faça uma pergunta sobre o plano ou peça modificações..."): # Input enabled when is_processing is False
            logger.info(f"Chat input recebido: '{prompt}'")
            # Append user message to session state and display it immediately
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"): # Display user message right away
                 st.markdown(prompt)

            # Set flag and rerun to trigger the API call block above
            st.session_state.is_processing = True
            st.session_state.error_message = None # Clear previous errors
            st.rerun()

    else:
        logger.warning("Navegou para página 'result', mas nenhum histórico de chat encontrado no estado da sessão.")
        st.warning("🤔 Nenhum plano ou conversa encontrada. Por favor, gere um novo plano usando o formulário.")


def main():
    """Função principal para configurar a barra lateral e controlar a renderização da página."""

    # --- Navegação da Barra Lateral (Movida PARA DENTRO do main) ---
    st.sidebar.title("Navegação")
    page_options = ["Formulário de Entrada", "Visualizar Plano"]
    current_page_display = "Formulário de Entrada" if st.session_state.page == 'form' else "Visualizar Plano"

    try:
        current_page_index = page_options.index(current_page_display)
    except ValueError:
        logger.warning(f"Página inválida '{st.session_state.page}' mapeada para '{current_page_display}'. Índice padrão usado.")
        current_page_index = 0

    # Desabilita navegação durante o processamento
    nav_disabled = st.session_state.is_processing
    if nav_disabled:
        st.sidebar.warning("⚠️ Processando...")

    selected_page_display = st.sidebar.radio(
        "Ir para",
        page_options,
        index=current_page_index,
        key='sidebar_nav',
        disabled=nav_disabled # Desabilita botões de rádio
    )

    # Permite mudança de navegação apenas se não estiver processando
    if not nav_disabled:
        new_page_state = 'form' if selected_page_display == "Formulário de Entrada" else 'result'
        if new_page_state != st.session_state.page:
            logger.info(f"Navegando da página '{st.session_state.page}' para '{new_page_state}' via barra lateral.")
            st.session_state.page = new_page_state
            st.session_state.error_message = None # Limpa erros na navegação
            st.rerun()

    # Botão de voltar condicional (também desabilitado se estiver processando)
    if st.session_state.page == 'result':
        st.sidebar.markdown("---")
        # Rename button to "Novo Plano" and add reset logic
        if st.sidebar.button("✨ Novo Plano de Estudos", disabled=nav_disabled):
            logger.info("Usuário clicou no botão 'Novo Plano de Estudos'. Resetando estado.")
            # Reset relevant session state variables
            st.session_state.page = 'form'
            st.session_state.plan_id = None
            st.session_state.chat_history = []
            st.session_state.form_data = {} # Clear form data as well
            st.session_state.error_message = None
            st.session_state.is_processing = False # Ensure processing is stopped
            st.rerun()
        
        if st.session_state.study_plan:
            st.sidebar.markdown("---")
            # Criar o nome do arquivo baseado no nome do usuário e data atual
            user_name = st.session_state.form_data.get('name', 'Aluno')
            current_date = datetime.date.today().strftime("%Y-%m-%d")
            filename = f"plano_estudos_{user_name.replace(' ', '_')}_{current_date}.md"
            
            # Adicionar botão de download
            st.sidebar.download_button(
                label="📥 Baixar Plano de Estudos",
                data=st.session_state.study_plan,
                file_name=filename,
                mime="text/markdown",
                help="Baixe seu plano de estudos personalizado em formato Markdown",
                disabled=nav_disabled  # Desabilita durante o processamento
            )
    # --- Fim da Navegação da Barra Lateral ---


    # --- Roteamento de Página ---
    # Renderiza conteúdo da página *após* lidar com navegação e estado de processamento
    if st.session_state.page == 'form':
        form_page() # Esta função agora lida com a chamada de API se is_processing for True
    elif st.session_state.page == 'result':
        result_page()
    else:
        # Fallback se o estado estiver de alguma forma inválido
        logger.error(f"Estado de página inválido encontrado: {st.session_state.page}. Voltando para o padrão.")
        st.session_state.page = 'form'
        st.rerun()


# --- Execução Principal ---
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # Capturar erros potenciais durante configuração inicial ou renderização fora de manipuladores específicos
        logger.critical(f"Uma exceção não capturada ocorreu na execução principal: {e}", exc_info=True)
        try:
            st.error(f"Ocorreu um erro crítico na aplicação: {e}. Por favor, verifique os logs.")
        except Exception:
             print(f"Erro crítico antes da UI Streamlit poder exibi-lo: {e}")
    finally:
        # Este log pode aparecer frequentemente devido a reexecuções, considere nível ou posicionamento
        logger.debug("--- Ciclo de Execução da Aplicação Encerrado (ou Reexecução Acionada) ---")