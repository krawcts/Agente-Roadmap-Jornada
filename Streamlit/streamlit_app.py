import streamlit as st
import sys
from pathlib import Path
from loguru import logger
from dotenv import load_dotenv

# Adicione o diretório raiz ao PYTHONPATH
sys.path.append(str(Path(__file__).parent.parent))

from src.prompt_maker import make_final_prompt
from src.llm_service import initialize_llm_service

load_dotenv()

# Inicializa o estado da sessão se não existir
if 'page' not in st.session_state:
    st.session_state.page = 'form'
    st.session_state.plan = None

def submit_form():
    # Validar dados do formulário
    if not st.session_state.nome or not st.session_state.dias:
        st.error("Por favor, preencha todos os campos obrigatórios.")
        return
    
    # Atualizar o questionário com os dados do usuário
    user_data = f"""
    Nome: {st.session_state.nome}
    Dias da semana: {st.session_state.dias}
    Horas disponíveis por dia: {st.session_state.horas_disponiveis}
    """
    
    try:
        # Mostrar indicador de progresso durante o processamento
        with st.spinner("Gerando seu plano de estudos personalizado... Isso pode levar um minuto."):
            # Inicializa o serviço LLM
            llm_service = initialize_llm_service()
            
            if not llm_service:
                st.error("Não foi possível inicializar o serviço LLM.")
                return
            
            # Gera o prompt e obtém o resultado do LLM
            prompt_final = make_final_prompt(user_data)
            
            st.session_state.plan = llm_service.chat_completion(prompt_final)
            st.session_state.page = 'result'
        
        # Força recarregar a página para mostrar a nova página
        st.rerun()
    except Exception as e:
        st.error(f"Ocorreu um erro ao gerar o plano: {str(e)}")
        logger.exception(f"Erro ao gerar plano de estudos: {e}")

def form_page():
    st.title("Crie seu Plano de Estudos Personalizado 📚")
    
    st.markdown("""
    ### Preencha o formulário abaixo para gerar seu plano de estudos
    Vamos usar seus dados para criar um plano adaptado às suas necessidades e disponibilidade.
    """)
    
    with st.form("user_form"):
        st.text_input("Nome completo", key="nome")
        st.text_input("Dias da semana", key="dias")
        st.selectbox(
            "Horas disponíveis por dia", 
            options=list(range(1, 13)),
            key="horas_disponiveis"
        )
        
        submitted = st.form_submit_button("Gerar meu plano de estudos")
        if submitted:
            submit_form()

def result_page():
    st.title("Seu Plano de Estudos Personalizado 🎓")
    
    st.markdown(f"""
    ### Olá, {st.session_state.nome}!
    
    Aqui está seu plano de estudos personalizado, baseado nas suas {st.session_state.horas_disponiveis} horas disponíveis por dia.
    """)
    
    st.markdown("## Plano de Estudos")
    st.markdown(st.session_state.plan)
    
    if st.button("Criar novo plano"):
        # Redefinir valores da sessão para começar um novo plano
        st.session_state.page = 'form'
        st.session_state.nome = ""
        st.session_state.dias = ""
        st.session_state.horas_disponiveis = 1
        st.rerun()

def main():
    # Configuração da página
    st.set_page_config(
        page_title="Gerador de Plano de Estudos",
        page_icon="📚",
        layout="wide"
    )
    
    # Renderiza a página apropriada com base no estado
    if st.session_state.page == 'form':
        form_page()
    elif st.session_state.page == 'result':
        result_page()

if __name__ == "__main__":
    main()