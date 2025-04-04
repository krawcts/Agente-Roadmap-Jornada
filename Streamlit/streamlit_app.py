import streamlit as st
import os
import sys
import time
import datetime
from pathlib import Path
from loguru import logger
from dotenv import load_dotenv
import requests

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
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000") # Default for local dev
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
if 'plan' not in st.session_state:
    st.session_state.plan = None
    logger.debug("Estado da sessão 'plan' inicializado para None.")
if 'form_data' not in st.session_state:
    # Armazena os dados enviados para pré-preenchimento do formulário no retorno
    st.session_state.form_data = {}
    logger.debug("Estado da sessão 'form_data' inicializado como dicionário vazio.")
if 'is_processing' not in st.session_state:
    st.session_state.is_processing = False
if 'error_message' not in st.session_state:
    st.session_state.error_message = None # Armazena erros do backend

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

        # Horas por dia disponíveis
        st.subheader("Disponibilidade")
        hours = st.slider(
            "Horas Disponíveis Por Dia*",
            min_value=1, max_value=8, value=defaults.get('hours_per_day', 3),
            key="form_hours"
        )

        # Dias da semana disponíveis
        st.write("Selecione Dias Disponíveis (Seg-Dom)*")
        days_of_week = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
        weekdays = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta"]
        # Se não houver dias selecionados anteriormente, pré-selecionar dias de semana
        if not defaults.get('available_days'):
            selected_days_values = weekdays
        else:
            selected_days_values = defaults.get('available_days', [])
        available_days = []
        cols = st.columns(len(days_of_week))
        for i, day in enumerate(days_of_week):
            with cols[i]:
                # Verificar se é um dia da semana (seg-sex) para marcar por padrão
                is_checked = day in selected_days_values
                if st.checkbox(day[:3], value=is_checked, key=f"form_day_{day}"):
                    available_days.append(day)

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

        # Objetivos principais
        st.subheader("Objetivos")
        objectives = st.text_area(
            "Objetivos Principais de Aprendizagem*",
            value=defaults.get('objectives', ''),
            height=100,
            placeholder="Ex: 'Aprender Python básico para análise de dados', 'Preparar para certificação em cloud'",
            key="form_objectives"
        )

        # Informações extras
        secondary_goals = st.text_area(
            "Objetivos Secundários (Opcional)",
            value=defaults.get('secondary_goals', ''),
            height=80,
            placeholder="Ex: 'Melhorar habilidades de documentação', 'Explorar bibliotecas relacionadas'",
            key="form_secondary_goals"
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
            if not available_days: error_messages.append("Por favor, selecione pelo menos um dia disponível."); validation_passed = False
            if not objectives: error_messages.append("Por favor, insira seus Objetivos Principais de Aprendizagem."); validation_passed = False

            if not validation_passed:
                for msg in error_messages:
                    st.error(f"⚠️ {msg}")
            else:
                logger.info("Validação do formulário bem-sucedida.")
                # --- Armazenar entradas atuais para possível pré-preenchimento ---
                current_form_data = {
                    "name": name,
                    "email": email,
                    "hours_per_day": hours,
                    "available_days": available_days,
                    "start_date": start_date,
                    "objectives": objectives,
                    "secondary_goals": secondary_goals 
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
        with st.spinner("⏳ Gerando seu plano de estudos personalizado via IA... Por favor, aguarde."):
            try:
                # Prepara payload de dados para a API backend
                payload = st.session_state.form_data.copy()
                # Converte data para string para serialização JSON
                payload['start_date'] = payload['start_date'].isoformat()

                logger.info(f"Enviando requisição POST para {BACKEND_URL}/generate_plan")
                logger.debug(f"Payload: {payload}")

                # Faz a chamada de API para o backend
                response = requests.post(f"{BACKEND_URL}/generate_plan", json=payload, timeout=180) # Timeout aumentado para LLM
                response.raise_for_status() # Levanta HTTPError para respostas ruins (4xx ou 5xx)

                # Processa resposta bem-sucedida
                api_response = response.json()
                logger.info("Chamada de API bem-sucedida.")
                logger.debug(f"Resposta da API: {api_response}")

                st.session_state.plan = api_response.get("generated_plan")
                st.session_state.page = 'result'
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
    st.title("✅ Seu Plano de Estudos Gerado")

    if st.session_state.plan:
        logger.info("Plano de estudos encontrado no estado da sessão. Exibindo.")
        user_info = st.session_state.get('form_data', {})

        # Exibe cabeçalho de contexto
        if user_info.get('name'):
            st.markdown(f"### Plano para {user_info['name']}")
        if user_info.get('start_date') and user_info.get('available_days'):
            # Garante que start_date seja um objeto de data para formatação
            start_date_obj = user_info['start_date']
            if isinstance(start_date_obj, str):
                try:
                    start_date_obj = datetime.date.fromisoformat(start_date_obj)
                except ValueError:
                    start_date_obj = None # Trata erro se o formato estiver errado

            start_date_str = start_date_obj.strftime('%d de %B de %Y') if start_date_obj else "N/A"
            days_str = ', '.join(user_info['available_days'])
            st.markdown(f"*Começando em **{start_date_str}** | **{user_info.get('hours_per_day', 'N/A')}** horas/dia em **{days_str}***")
        if user_info.get('objectives'):
            st.markdown(f"**Objetivos Principais:** {user_info['objectives']}")
        if user_info.get('secondary_goals'):
            st.markdown(f"**Objetivos Secundários:** {user_info['secondary_goals']}")
        st.markdown("---")

        # Exibe o plano real do LLM
        st.markdown(st.session_state.plan)
        st.markdown("---") # Separador antes do botão de download

        # Adiciona botão de download
        try:
            user_name_for_file = user_info.get('name', 'usuario')
            safe_user_name = "".join(c if c.isalnum() or c in (' ', '_', '-') else '_' for c in user_name_for_file).replace(' ', '_')
            file_name = f"plano_estudos_{safe_user_name}_{datetime.date.today()}.md"
            logger.debug(f"Nome de arquivo para download gerado: {file_name}")
            st.download_button(
                label="📥 Baixar Plano como Markdown",
                data=st.session_state.plan, # Assume que o plano está formatado em Markdown pelo LLM
                file_name=file_name,
                mime="text/markdown" # Usar tipo mime markdown
            )
        except Exception as e:
            logger.error(f"Falha ao criar botão de download: {e}")
            st.warning("Não foi possível gerar link de download.")

    else:
        logger.warning("Navegou para página 'result', mas nenhum plano de estudos encontrado no estado da sessão.")
        st.warning("🤔 Nenhum plano de estudos encontrado. Por favor, volte para a página 'Formulário de Entrada' usando a barra lateral e gere um.")


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
        if st.sidebar.button("⬅️ Voltar ao Formulário / Editar", disabled=nav_disabled):
            logger.info("Usuário clicou no botão 'Voltar ao Formulário / Editar' na barra lateral.")
            st.session_state.page = 'form'
            st.session_state.error_message = None # Limpa erros na navegação
            st.rerun()
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