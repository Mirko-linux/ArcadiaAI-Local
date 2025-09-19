import streamlit as st
import os
import json
import base64
from pathlib import Path
from PIL import Image
import pandas as pd
from core.chatbot import ArcadiaAICore
from core.deep_research import DeepResearchCore
from utils.first_run import check_and_install_phi4

# --- CONFIG ---
st.set_page_config(
    page_title="ArcadiaAI Local", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- INIZIALIZZAZIONE ---
if "phi4_required" not in st.session_state:
    st.session_state.phi4_required = True

if st.session_state.phi4_required:
    ready = check_and_install_phi4()
    if not ready:
        st.stop()

# Inizializza il bot
if "bot" not in st.session_state:
    try:
        st.session_state.bot = ArcadiaAICore()
        st.success("🟢 Modello locale caricato!")
    except Exception as e:
        st.error(f"❌ Errore caricamento modello: {e}")
        st.stop()

# Inizializza DeepResearch
if "deep_research" not in st.session_state:
    try:
        st.session_state.deep_research = DeepResearchCore()
    except Exception as e:
        st.error(f"❌ Errore caricamento DeepResearch: {e}")

# Inizializza messaggi e stato
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_mode" not in st.session_state:
    st.session_state.current_mode = "normal"
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = []

# --- CARICA MODELLI DISPONIBILI ---
def load_available_models():
    models_dir = Path("models")
    if not models_dir.exists():
        models_dir.mkdir()
        return []
    
    model_files = []
    for ext in ["*.gguf", "*.bin", "*.safetensors"]:
        model_files.extend(models_dir.glob(ext))
    
    return [f.name for f in model_files]

available_models = load_available_models()

# --- FUNZIONI UTILI ---
def encode_image_to_base64(image):
    """Converte immagine PIL in base64"""
    import io
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"

def process_uploaded_file(uploaded_file):
    """Processa file caricati"""
    if uploaded_file.type.startswith('image/'):
        image = Image.open(uploaded_file)
        return {"type": "image", "content": image, "name": uploaded_file.name}
    elif uploaded_file.type == "text/plain":
        content = uploaded_file.read().decode()
        return {"type": "text", "content": content, "name": uploaded_file.name}
    elif uploaded_file.type == "application/pdf":
        # Qui puoi aggiungere processing PDF
        return {"type": "pdf", "content": uploaded_file.read(), "name": uploaded_file.name}
    else:
        return {"type": "file", "content": uploaded_file.read(), "name": uploaded_file.name}

# --- CSS PERSONALIZZATO ---
st.markdown("""
<style>
    /* Reset e base styles */
    .main {
        background: #f5f5f5;
        color: #2d3748;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
    
    /* Header personalizzato */
    .header-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 15px 20px;
        border-radius: 10px;
        color: white;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    .header-title {
        font-size: 24px;
        font-weight: 600;
        margin-bottom: 5px;
    }
    
    .header-subtitle {
        font-size: 14px;
        opacity: 0.9;
    }
    
    /* Pulsanti modalità */
    .mode-buttons {
        display: flex;
        gap: 10px;
        margin-bottom: 20px;
        flex-wrap: wrap;
    }
    
    .mode-btn {
        background: white;
        border: 2px solid #e2e8f0;
        padding: 10px 16px;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.2s;
        font-size: 14px;
        font-weight: 500;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    .mode-btn:hover {
        border-color: #667eea;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    
    .mode-btn.active {
        background: #667eea;
        color: white;
        border-color: #667eea;
    }
    
    /* Container messaggi */
    .messages-container {
        background: white;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        max-height: 60vh;
        overflow-y: auto;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        border: 1px solid #e2e8f0;
    }
    
    /* Stili messaggi */
    .message {
        margin-bottom: 20px;
        display: flex;
        flex-direction: column;
    }
    
    .message.user {
        align-items: flex-end;
    }
    
    .message.assistant {
        align-items: flex-start;
    }
    
    .message-content {
        max-width: 80%;
        padding: 16px 20px;
        border-radius: 18px;
        line-height: 1.5;
        word-wrap: break-word;
    }
    
    .message.user .message-content {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-bottom-right-radius: 6px;
    }
    
    .message.assistant .message-content {
        background: #f8f9fa;
        color: #2d3748;
        border: 1px solid #e2e8f0;
        border-bottom-left-radius: 6px;
    }
    
    .message-time {
        font-size: 12px;
        color: #a0aec0;
        margin-top: 5px;
        padding: 0 8px;
    }
    
    /* Area input */
    .input-area {
        background: white;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        border: 1px solid #e2e8f0;
    }
    
    /* File caricati */
    .uploaded-files {
        margin-bottom: 15px;
    }
    
    .file-chip {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        background: #e2e8f0;
        padding: 5px 10px;
        border-radius: 15px;
        font-size: 12px;
        margin-right: 5px;
        margin-bottom: 5px;
    }
    
    .file-chip .remove-btn {
        cursor: pointer;
        color: #e53e3e;
        font-weight: bold;
    }
    
    /* Indicatori stato */
    .status-indicator {
        padding: 8px 15px;
        border-radius: 20px;
        font-size: 13px;
        font-weight: 500;
        display: inline-flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 15px;
    }
    
    .status-online {
        background: #c6f6d5;
        color: #22543d;
    }
    
    .status-thinking {
        background: #fef5e7;
        color: #744210;
    }
    
    .status-researching {
        background: #e6fffa;
        color: #234e52;
    }
    
    /* Sidebar personalizzata */
    .sidebar .sidebar-content {
        background: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    
    /* Animazioni */
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    .thinking {
        animation: pulse 1.5s infinite;
    }
    
    /* Responsivo */
    @media (max-width: 768px) {
        .mode-buttons {
            flex-direction: column;
        }
        
        .message-content {
            max-width: 95%;
        }
    }
</style>
""", unsafe_allow_html=True)

# --- INTERFACCIA PRINCIPALE ---

# Header
st.markdown("""
<div class="header-container">
    <div class="header-title">🤖 ArcadiaAI Local</div>
    <div class="header-subtitle">Assistente AI avanzato con capacità di ricerca e ragionamento</div>
</div>
""", unsafe_allow_html=True)

# Sidebar per configurazioni
with st.sidebar:
    st.markdown('<div class="sidebar-content">', unsafe_allow_html=True)
    
    st.markdown("### ⚙️ Configurazioni")
    
    # Selezione modello
    if available_models:
        selected_model = st.selectbox(
            "📦 Modello Locale:",
            available_models,
            help="Seleziona il modello da utilizzare"
        )
        if "current_model" not in st.session_state or st.session_state.current_model != selected_model:
            st.session_state.current_model = selected_model
            # Qui puoi ricaricare il modello se necessario
    else:
        st.warning("⚠️ Nessun modello trovato in /models")
        st.info("Aggiungi file .gguf, .bin o .safetensors nella cartella models/")
    
    st.markdown("---")
    
    # Parametri modello
    st.markdown("### 🎛️ Parametri")
    temperature = st.slider("🌡️ Temperature", 0.0, 2.0, 0.7, 0.1)
    max_tokens = st.slider("📝 Max Tokens", 50, 2048, 512, 50)
    
    st.markdown("---")
    
    # Cronologia chat
    st.markdown("### 💬 Chat History")
    if st.button("🗑️ Cancella Chat"):
        st.session_state.messages = []
        st.session_state.uploaded_files = []
        st.rerun()
    
    if st.button("💾 Salva Chat"):
        if st.session_state.messages:
            chat_data = {
                "messages": st.session_state.messages,
                "timestamp": str(pd.Timestamp.now())
            }
            st.download_button(
                "⬇️ Download JSON",
                json.dumps(chat_data, indent=2),
                f"chat_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.json",
                "application/json"
            )
    
    st.markdown("---")
    
    # Statistiche
    st.markdown("### 📊 Statistiche")
    st.metric("Messaggi", len(st.session_state.messages))
    st.metric("File Caricati", len(st.session_state.uploaded_files))
    
    st.markdown('</div>', unsafe_allow_html=True)

# Area principale
col1, col2 = st.columns([1, 3])

with col1:
    # Pulsanti modalità
    st.markdown("### 🚀 Modalità")
    
    # Normale
    if st.button("💬 Chat Normale", key="normal_mode", help="Conversazione standard"):
        st.session_state.current_mode = "normal"
    
    # Ragionamento
    if st.button("🧠 Ragionamento", key="reasoning_mode", help="Attiva ragionamento avanzato step-by-step"):
        st.session_state.current_mode = "reasoning"
    
    # Ricerca
    if st.button("🔍 Ricerca", key="research_mode", help="Utilizza DeepResearch per ricerche avanzate"):
        st.session_state.current_mode = "research"
    
    st.markdown("---")
    
    # Upload file
    st.markdown("### 📎 Allega File")
    uploaded_file = st.file_uploader(
        "Carica file o immagini",
        type=['txt', 'pdf', 'jpg', 'jpeg', 'png', 'gif', 'bmp', 'csv', 'json'],
        help="Supporta testi, PDF, immagini e dati"
    )
    
    if uploaded_file:
        processed_file = process_uploaded_file(uploaded_file)
        if processed_file not in st.session_state.uploaded_files:
            st.session_state.uploaded_files.append(processed_file)
            st.success(f"✅ {uploaded_file.name} caricato!")
            st.rerun()

with col2:
    # Indicatore stato corrente
    mode_names = {
        "normal": "💬 Chat Normale",
        "reasoning": "🧠 Ragionamento Attivo", 
        "research": "🔍 Modalità Ricerca"
    }
    
    mode_colors = {
        "normal": "status-online",
        "reasoning": "status-thinking",
        "research": "status-researching"
    }
    
    current_mode_name = mode_names.get(st.session_state.current_mode, "💬 Chat Normale")
    current_mode_color = mode_colors.get(st.session_state.current_mode, "status-online")
    
    st.markdown(f"""
    <div class="status-indicator {current_mode_color}">
        <div style="width: 8px; height: 8px; background: currentColor; border-radius: 50%;"></div>
        {current_mode_name}
    </div>
    """, unsafe_allow_html=True)
    
    # File caricati
    if st.session_state.uploaded_files:
        st.markdown('<div class="uploaded-files">', unsafe_allow_html=True)
        for i, file_info in enumerate(st.session_state.uploaded_files):
            file_type_icons = {
                "image": "🖼️",
                "text": "📄",
                "pdf": "📕",
                "file": "📎"
            }
            icon = file_type_icons.get(file_info["type"], "📎")
            
            col_file, col_remove = st.columns([4, 1])
            with col_file:
                st.markdown(f"""
                <div class="file-chip">
                    {icon} {file_info["name"]}
                </div>
                """, unsafe_allow_html=True)
            with col_remove:
                if st.button("❌", key=f"remove_file_{i}", help="Rimuovi file"):
                    st.session_state.uploaded_files.pop(i)
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Container messaggi
    st.markdown('<div class="messages-container">', unsafe_allow_html=True)
    
    for i, message in enumerate(st.session_state.messages):
        role_class = "user" if message["role"] == "user" else "assistant"
        
        st.markdown(f"""
        <div class="message {role_class}">
            <div class="message-content">
                {message["content"]}
            </div>
            <div class="message-time">
                {message.get("timestamp", "Ora")}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Area input
    st.markdown('<div class="input-area">', unsafe_allow_html=True)
    
    # Input messaggio
    user_input = st.text_area(
        "Scrivi il tuo messaggio...",
        key="user_input",
        height=100,
        placeholder="Inserisci la tua domanda o richiesta..."
    )
    
    col_send, col_clear = st.columns([3, 1])
    
    with col_send:
        if st.button("🚀 Invia Messaggio", key="send_msg", type="primary"):
            if user_input.strip():
                # Aggiungi messaggio utente
                timestamp = pd.Timestamp.now().strftime("%H:%M")
                user_message = {
                    "role": "user",
                    "content": user_input,
                    "timestamp": timestamp
                }
                st.session_state.messages.append(user_message)
                
                # Prepara il context con file caricati
                context = user_input
                if st.session_state.uploaded_files:
                    context += "\n\nFile allegati:\n"
                    for file_info in st.session_state.uploaded_files:
                        context += f"- {file_info['name']} ({file_info['type']})\n"
                        if file_info['type'] == 'text':
                            context += f"Contenuto: {file_info['content'][:500]}...\n"
                
                # Genera risposta basata sulla modalità
                with st.spinner("🤖 Elaborando..."):
                    try:
                        if st.session_state.current_mode == "reasoning":
                            # Modalità ragionamento
                            reasoning_prompt = f"""
                            Ragiona step-by-step per rispondere a questa domanda:
                            
                            {context}
                            
                            Struttura la tua risposta così:
                            1. **Analisi**: Cosa mi viene chiesto
                            2. **Ragionamento**: I passaggi logici
                            3. **Conclusione**: La risposta finale
                            """
                            response = st.session_state.bot.rispondi(reasoning_prompt)
                            
                        elif st.session_state.current_mode == "research":
                            # Modalità ricerca
                            if hasattr(st.session_state, 'deep_research'):
                                response = st.session_state.deep_research.research(context)
                            else:
                                response = "⚠️ DeepResearch non disponibile. Risposta standard:\n\n" + st.session_state.bot.rispondi(context)
                        
                        else:
                            # Modalità normale
                            response = st.session_state.bot.rispondi(context)
                        
                        # Aggiungi risposta assistant
                        assistant_message = {
                            "role": "assistant",
                            "content": response,
                            "timestamp": pd.Timestamp.now().strftime("%H:%M")
                        }
                        st.session_state.messages.append(assistant_message)
                        
                    except Exception as e:
                        error_message = {
                            "role": "assistant",
                            "content": f"❌ Errore durante l'elaborazione: {str(e)}",
                            "timestamp": pd.Timestamp.now().strftime("%H:%M")
                        }
                        st.session_state.messages.append(error_message)
                
                # Pulisci input e ricarica
                st.rerun()
    
    with col_clear:
        if st.button("🗑️ Pulisci"):
            st.session_state.user_input = ""
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

# --- FOOTER ---
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #718096; font-size: 12px;">
    🤖 ArcadiaAI Local v1.0 | Modello Locale | 
    Modalità: {mode} | 
    Messaggi: {msgs}
</div>
""".format(
    mode=current_mode_name,
    msgs=len(st.session_state.messages)
), unsafe_allow_html=True)