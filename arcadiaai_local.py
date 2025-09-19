# arcadiaai_local.py
import streamlit as st
import os
from pathlib import Path
from core.chatbot import ArcadiaAICore
from utils.first_run import check_and_install_phi4

# --- CONFIG ---
st.set_page_config(page_title="ArcadiaAI Local", layout="wide")

# --- PRIMO AVVIO ---
if "phi4_required" not in st.session_state:
    st.session_state.phi4_required = True

if st.session_state.phi4_required:
    ready = check_and_install_phi4()
    if not ready:
        st.stop()

# --- CARICA IL CHATBOT ---
if "bot" not in st.session_state:
    try:
        st.session_state.bot = ArcadiaAICore()
        st.success("🟢 Modello locale caricato!")
    except Exception as e:
        st.error(f"❌ Errore caricamento modello: {e}")
        st.stop()

# --- STILE LM STUDIO ---
st.markdown("""
<style>
    .main {
        background: #f7f7f7;
        color: #2d2d2d;
        font-family: 'Segoe UI', sans-serif;
    }
    .sidebar {
        width: 200px;
        background: white;
        border-right: 1px solid #ddd;
        padding: 16px 0;
    }
    .nav-item {
        padding: 8px 16px;
        margin-bottom: 8px;
        cursor: pointer;
        font-size: 14px;
        color: #555;
    }
    .nav-item:hover {
        background: #f0f0f0;
    }
    .nav-item.active {
        background: #00cc99;
        color: white;
    }
    .chat-container {
        flex: 1;
        display: flex;
        flex-direction: column;
        overflow: hidden;
    }
    .message {
        max-width: 80%;
        padding: 12px 16px;
        margin-bottom: 12px;
        border-radius: 8px;
        line-height: 1.5;
    }
    .user-message {
        align-self: flex-end;
        background: #f0f0f0;
        border-bottom-right-radius: 4px;
    }
    .ai-message {
        align-self: flex-start;
        background: #f8f9fa;
        border-bottom-left-radius: 4px;
    }
    .input-area {
        padding: 16px;
        border-top: 1px solid #ddd;
        display: flex;
        gap: 8px;
        align-items: center;
    }
    .input-box {
        flex: 1;
        padding: 12px;
        border: 1px solid #ddd;
        border-radius: 8px;
        outline: none;
        font-size: 14px;
    }
    .send-btn {
        background: #00cc99;
        color: white;
        border: none;
        padding: 12px 20px;
        border-radius: 8px;
        cursor: pointer;
    }
    .send-btn:hover {
        background: #00aa77;
    }
    .header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px 16px;
        background: #0066cc;
        color: white;
        font-weight: bold;
        height: 40px;
    }
</style>
""", unsafe_allow_html=True)

# --- INTERFACCIA ---
st.markdown("<div class='header'>ArcadiaAI Local <span style='font-size:12px;'>v1.0</span></div>", unsafe_allow_html=True)

col1, col2 = st.columns([0.25, 0.75])

with col1:
    st.markdown("<div class='sidebar'>", unsafe_allow_html=True)
    st.markdown("<div class='nav-item active'>💬 Chat</div>", unsafe_allow_html=True)
    st.markdown("<div class='nav-item'>📦 Marketplace</div>", unsafe_allow_html=True)
    st.markdown("<div class='nav-item'>📚 Libreria</div>", unsafe_allow_html=True)
    st.markdown("<div class='nav-item'>⚙️ Impostazioni</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.markdown("<div class='chat-container'>", unsafe_allow_html=True)

    # Cronologia chat
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.container():
            st.markdown(f"<div class='message {'user-message' if msg['role'] == 'user' else 'ai-message'}'>{msg['content']}</div>", unsafe_allow_html=True)

    # Input utente
    prompt = st.text_input("Invia un messaggio...", key="input_box", placeholder="Scrivi qui...")

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.container():
            st.markdown(f"<div class='message user-message'>{prompt}</div>", unsafe_allow_html=True)

        with st.spinner("🧠 Pensando..."):
            response = st.session_state.bot.rispondi(prompt)
            st.session_state.messages.append({"role": "assistant", "content": response})
            with st.container():
                st.markdown(f"<div class='message ai-message'>{response}</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)