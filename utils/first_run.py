# utils/first_run.py
import os
import streamlit as st
import requests
from pathlib import Path

MODELS_DIR = Path("models")
MODEL_PATH = MODELS_DIR / "phi-4-mini-q4_k_m.gguf"
MODEL_URL = "https://huggingface.co/TheBloke/phi-4-mini-GGUF/resolve/main/phi-4-mini-Q4_K_M.gguf"

def check_and_install_phi4():
    """Controlla e installa Phi-4 al primo avvio"""
    if not MODEL_PATH.exists():
        st.markdown("### 🤖 Benvenuto in ArcadiaAI Local!")
        st.markdown("""
        Per funzionare, ho bisogno di un modello linguistico locale.
        
        **Microsoft Phi-4 Mini** è il modello consigliato: veloce, leggero (~3.8 GB) e ottimizzato per CPU.
        """)

        col1, col2 = st.columns(2)
        with col1:
            install = st.button("✅ Sì, installa Phi-4", key="install_phi")
        with col2:
            skip = st.button("❌ No, lo installerò dopo", key="skip_phi")

        if install:
            st.session_state.phi4_installing = True
            _download_model()
            return False  # Non proseguire finché non è installato

        if skip:
            st.info("Puoi installare il modello più tardi dal Marketplace.")
            st.session_state.phi4_required = False
            return True  # Prosegui comunque

        return False  # Aspetta una scelta

    return True  # Modello già presente, vai avanti

def _download_model():
    """Scarica il modello con progress bar"""
    try:
        response = requests.get(MODEL_URL, stream=True, timeout=30)
        response.raise_for_status()
        total_size = int(response.headers.get('content-length', 0))
        block_size = 8192
        written = 0

        progress_bar = st.progress(0)
        status_text = st.empty()

        status_text.info("📥 Download in corso... Questo può richiedere alcuni minuti.")

        with open(MODEL_PATH, 'wb') as f:
            for chunk in response.iter_content(chunk_size=block_size):
                f.write(chunk)
                written += len(chunk)
                if total_size > 0:
                    progress = min(100, int((written / total_size) * 100))
                    progress_bar.progress(progress)

        progress_bar.empty()
        status_text.success(f"✅ Modello scaricato: `{MODEL_PATH}`")
        st.balloons()

        # Forza il refresh
        st.session_state.phi4_installed = True

    except Exception as e:
        st.error(f"❌ Errore download: {str(e)}")
        st.info("Riprova o scaricalo manualmente da Hugging Face.")