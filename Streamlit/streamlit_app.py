import streamlit as st

def main():
    # Configuração da página
    st.set_page_config(
        page_title="AI Agent Interface",
        page_icon="🤖",
        layout="wide"
    )

    # Título principal
    st.title("Bem-vindo ao Assistente IA! 🤖")
    
    # Subtítulo
    st.markdown("### Esta é uma interface para interagir com um agente de IA")
    
    # Área de texto para input do usuário
    user_input = st.text_area("Digite sua mensagem:", height=150)
    
    # Botão de envio
    if st.button("Enviar"):
        if user_input:
            st.write("Você digitou:", user_input)
            # Aqui posteriormente será adicionada a lógica de interação com o agente de IA
        else:
            st.warning("Por favor, digite uma mensagem antes de enviar.")

if __name__ == "__main__":
    main()