# --- INÍCIO DO ARQUIVO streamlit_app_final.py ---

import streamlit as st
import sys
import time
import datetime
from pathlib import Path
from loguru import logger
from dotenv import load_dotenv

# --- Configuração do Loguru ---
logger.remove()
logger.add(
    sys.stderr,
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
    level="INFO" # Alterado para INFO para produção, DEBUG para desenvolvimento
)
logger.info("--- Aplicativo Streamlit Iniciando ---")

# --- Configuração de Ambiente e Caminho ---
# Adiciona o diretório raiz ao PYTHONPATH se necessário para módulos personalizados
# Garanta que este caminho esteja correto em relação a onde você executa o streamlit
try:
    # Assume que sua pasta src está um nível acima de onde streamlit_app_final.py está
    sys.path.append(str(Path(__file__).resolve().parent.parent))
    from src.prompt_maker import make_final_prompt
    from src.llm_service import initialize_llm_service
    logger.info("Importados com sucesso 'make_final_prompt' e 'initialize_llm_service'.")
except ImportError as e:
    logger.error(f"Falha ao importar módulos personalizados: {e}. Verifique PYTHONPATH e localizações de arquivos.")
    st.error(f"Erro: Não foi possível carregar funções necessárias. Por favor, verifique a configuração da aplicação. Detalhes: {e}")
    # Opcionalmente, sair se funções principais estiverem faltando
    # sys.exit(1)
    # Ou fornecer funções fictícias para permitir testes de interface:
    def make_final_prompt(data):
        logger.warning("Usando 'make_final_prompt' fictício.")
        return f"Prompt fictício baseado em: {data}"
    def initialize_llm_service():
        logger.warning("Usando 'initialize_llm_service' fictício.")
        class DummyLLM:
            def chat_completion(self, prompt):
                logger.warning("Usando 'chat_completion' fictício.")
                time.sleep(2)
                return f"Esta é uma resposta fictícia para o prompt:\n```\n{prompt}\n```"
        return DummyLLM()


load_dotenv()
logger.info("Variáveis de ambiente carregadas (se o arquivo .env existir).")

# --- page_configuration (precisa ser o primeiro comando) ---
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

# --- Navegação da Barra Lateral ---
st.sidebar.title("Navegação")
page_options = ["Formulário de Entrada", "Visualizar Plano"]
current_page_display = "Formulário de Entrada" if st.session_state.page == 'form' else "Visualizar Plano"

try:
    current_page_index = page_options.index(current_page_display)
except ValueError:
    logger.warning(f"Página inválida '{st.session_state.page}' mapeada para '{current_page_display}'. Índice padrão usado.")
    current_page_index = 0

# Desabilite a navegação se estiver processando
if st.session_state.is_processing:
    st.sidebar.warning("⚠️ Processando sua solicitação... Por favor, aguarde.")
    st.sidebar.radio(
        "Navegação desabilitada durante processamento",
        page_options,
        index=current_page_index,
        key='sidebar_nav',
        disabled=True
    )
else:
    selected_page_display = st.sidebar.radio(
        "Ir para",
        page_options,
        index=current_page_index,
        key='sidebar_nav'
    )
    new_page_state = 'form' if selected_page_display == "Formulário de Entrada" else 'result'
    if new_page_state != st.session_state.page:
        logger.info(f"Navegando da página '{st.session_state.page}' para '{new_page_state}' via barra lateral.")
        st.session_state.page = new_page_state
        st.rerun()

if st.session_state.page == 'result':
    st.sidebar.markdown("---")
    if st.sidebar.button("⬅️ Voltar ao Formulário / Editar"):
        logger.info("Usuário clicou no botão 'Voltar ao Formulário / Editar' na barra lateral.")
        st.session_state.page = 'form'
        st.rerun()

# --- Implementações das Páginas ---

def form_page():
    """Renderiza a página do formulário de entrada."""
    logger.info("Renderizando página 'form'.")
    st.title("Crie seu Plano de Estudos Personalizado 📚")
    st.markdown("""
    ### Preencha o formulário abaixo para gerar seu plano de estudos personalizado!
    Quanto mais específico você for, melhor será o plano adaptado às suas necessidades e disponibilidade.
    """)

    defaults = st.session_state.get('form_data', {})
    logger.debug(f"Usando dados padrão do formulário: {defaults}")

    with st.form(key='study_plan_input_form'):
        st.subheader("Seus Dados")
        name = st.text_input("Nome*", value=defaults.get('name', ''), key="form_name")
        email = st.text_input("Email*", value=defaults.get('email', ''), key="form_email")

        st.subheader("Disponibilidade")
        hours = st.slider(
            "Horas Disponíveis Por Dia*",
            min_value=1, max_value=8, value=defaults.get('hours_per_day', 3),
            key="form_hours"
        )

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

        st.subheader("Objetivos")
        objectives = st.text_area(
            "Objetivos Principais de Aprendizagem*",
            value=defaults.get('objectives', ''),
            height=100,
            placeholder="Ex: 'Aprender Python básico para análise de dados', 'Preparar para certificação em cloud'",
            key="form_objectives"
        )
        # --- NOVO CAMPO: Objetivos Secundários ---
        secondary_goals = st.text_area(
            "Objetivos Secundários (Opcional)",
            value=defaults.get('secondary_goals', ''),
            height=80,
            placeholder="Ex: 'Melhorar habilidades de documentação', 'Explorar bibliotecas relacionadas'",
            key="form_secondary_goals"
        )
        # --- Fim do Novo Campo ---

        st.markdown("---")
        st.markdown("*\* Campos obrigatórios*")

        submitted = st.form_submit_button("✨ Gerar Plano de Estudos")

        if submitted:
            logger.info("Formulário enviado.")
            # --- Validação de Entrada ---
            validation_passed = True
            error_messages = []
            if not name:
                error_messages.append("Por favor, insira seu Nome.")
                logger.warning("Falha na validação do formulário: Nome ausente.")
                validation_passed = False
            if not email: # Verificação básica
                error_messages.append("Por favor, insira seu Email.")
                logger.warning("Falha na validação do formulário: Email ausente.")
                validation_passed = False
            if not available_days:
                error_messages.append("Por favor, selecione pelo menos um dia disponível.")
                logger.warning("Falha na validação do formulário: Nenhum dia disponível selecionado.")
                validation_passed = False
            if not objectives: # Tornar objetivos primários obrigatórios
                error_messages.append("Por favor, insira seus Objetivos Principais de Aprendizagem.")
                logger.warning("Falha na validação do formulário: Objetivos Primários ausentes.")
                validation_passed = False

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
                
                # Ative a flag de processamento!
                st.session_state.is_processing = True
                logger.info("Definindo is_processing=True")

                # --- Preparar dados para a chamada LLM ---
                # Criar uma cópia para evitar modificar diretamente o dicionário de estado da sessão, se necessário em outro lugar
                api_data = current_form_data.copy()
                # Formatar data como string para o prompt/API, se necessário
                api_data["start_date"] = start_date.strftime("%Y-%m-%d")
                logger.debug(f"Dados preparados para LLM: {api_data}")

                # --- Mostrar Spinner e Chamar LLM Real ---
                with st.spinner("⏳ Gerando seu plano de estudos personalizado via IA... Por favor, aguarde."):
                    logger.info("Exibindo spinner e iniciando processo de geração de plano LLM.")
                    try:
                        # 1. Inicializar Serviço LLM
                        logger.info("Inicializando Serviço LLM...")
                        llm_service = initialize_llm_service()
                        if not llm_service:
                            # Lidar com caso onde inicialização retorna None ou levanta erro implicitamente
                            raise ValueError("Serviço LLM não pôde ser inicializado. Verifique chaves de API e configuração.")
                        logger.info("Serviço LLM inicializado com sucesso.")

                        # 2. Criar o Prompt
                        # Garantir que make_final_prompt manipule corretamente o dicionário api_data,
                        # incluindo o novo campo 'secondary_goals'.
                        logger.info("Gerando prompt final...")
                        final_prompt = make_final_prompt(api_data)
                        logger.debug(f"Prompt Gerado:\n{final_prompt}")

                        # 3. Chamar o LLM
                        logger.info("Enviando prompt para LLM para completação...")
                        generated_plan = llm_service.chat_completion(final_prompt)
                        logger.info("Resposta recebida com sucesso do LLM.")
                        logger.debug(f"Resposta LLM (bruta): {generated_plan[:200]}...") # Registrar trecho

                        if not generated_plan:
                            logger.warning("LLM retornou uma resposta vazia ou nula.")
                            raise ValueError("Recebeu uma resposta vazia da IA. Por favor, tente novamente.")

                        st.session_state.plan = generated_plan # Armazenar o resultado real

                        # --- Resultado obtido com sucesso, desativa a flag ---
                        st.session_state.is_processing = False
                        st.session_state.page = 'result'
                        logger.info("Estado da página definido para 'result'.")
                        st.success("✅ Plano de estudos gerado com sucesso!")
                        time.sleep(1.5) # Pequeno atraso para feedback do usuário
                        logger.info("Acionando reexecução para navegar para página 'result'.")
                        st.rerun()

                    except Exception as e:
                        st.session_state.is_processing = False
                        logger.error(f"Erro durante interação LLM ou geração de plano: {e}", exc_info=True)
                        st.error(f"❌ Ocorreu um erro: {e}. Por favor, verifique os logs ou tente novamente mais tarde.")
                        st.rerun()  # Recarregar para atualizar a UI após o erro



def result_page():
    """Renderiza a página de resultado exibindo o plano gerado."""
    logger.info("Renderizando página 'result'.")
    st.title("✅ Seu Plano de Estudos Gerado")

    if st.session_state.plan:
        logger.info("Plano de estudos encontrado no estado da sessão. Exibindo.")
        user_info = st.session_state.get('form_data', {})

        # Exibir cabeçalho de contexto
        if user_info.get('name'):
            st.markdown(f"### Plano para {user_info['name']}")
        if user_info.get('start_date') and user_info.get('available_days'):
            start_date_str = user_info['start_date'].strftime('%d de %B de %Y') if isinstance(user_info.get('start_date'), datetime.date) else "N/A"
            days_str = ', '.join(user_info['available_days'])
            st.markdown(f"*Começando em **{start_date_str}** | **{user_info.get('hours_per_day', 'N/A')}** horas/dia em **{days_str}***")
        if user_info.get('objectives'):
            st.markdown(f"**Objetivos Principais:** {user_info['objectives']}")
        # Exibir objetivos secundários se fornecidos
        if user_info.get('secondary_goals'):
            st.markdown(f"**Objetivos Secundários:** {user_info['secondary_goals']}")
        st.markdown("---")

        # Exibir o plano real do LLM
        st.markdown(st.session_state.plan)
        st.markdown("---") # Separador antes do botão de download

        # Adicionar botão de download
        try:
            user_name_for_file = user_info.get('name', 'usuario')
            safe_user_name = "".join(c if c.isalnum() or c in (' ', '_', '-') else '_' for c in user_name_for_file).replace(' ', '_')
            file_name = f"plano_estudos_{safe_user_name}_{datetime.date.today()}.md" # Alterado para .md
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
    """Função principal para controlar a renderização da página."""
    # Renderizar a página apropriada com base no estado da sessão
    if st.session_state.page == 'form':
        form_page()
    elif st.session_state.page == 'result':
        result_page()
    else:
        logger.error(f"Estado de página inválido encontrado: {st.session_state.page}. Voltando para o padrão.")
        st.session_state.page = 'form'
        st.rerun() # Reexecutar para renderizar a página de formulário padrão

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # Capturar erros potenciais durante configuração inicial ou renderização fora de manipuladores específicos
        logger.critical(f"Uma exceção não capturada ocorreu na execução principal: {e}", exc_info=True)
        st.error(f"Ocorreu um erro crítico na aplicação: {e}. Por favor, verifique os logs.")
    finally:
        # Este log pode aparecer frequentemente devido a reexecuções, considere nível ou posicionamento
        logger.debug("--- Ciclo de Execução da Aplicação Encerrado (ou Reexecução Acionada) ---")