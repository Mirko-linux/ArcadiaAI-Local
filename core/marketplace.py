# arcadiaai_marketplace.py
import streamlit as st
import requests
from pathlib import Path

# --- CONFIG ---
MODELS_DIR = Path("models")
MODELS_DIR.mkdir(exist_ok=True)

HF_BASE = "https://huggingface.co"
THE_BLOKE = "TheBloke"

# --- FUNZIONI ---
@st.cache_data(ttl=600)
def get_gguf_models():
    """Ottieni tutti i modelli TheBloke con 'gguf' nel modelId"""
    url = f"{HF_BASE}/api/models"
    params = {"author": THE_BLOKE, "search": "gguf"}
    headers = {"User-Agent": "ArcadiaAI/1.0"}

    try:
        r = requests.get(url, params=params, headers=headers, timeout=15)
        if r.status_code != 200:
            st.error(f"Errore Hugging Face: {r.status_code}")
            return []

        data = r.json()
        models_list = data["models"] if isinstance(data, dict) and "models" in data else data

        results = []
        for m in models_list:
            if not isinstance(m, dict):
                continue
            model_id = m.get("modelId") or m.get("id")
            if not model_id or "gguf" not in model_id.lower():
                continue

            results.append({
                "id": model_id,
                "name": model_id.split("/")[-1],
                "downloads": m.get("downloads", 0),
                "likes": m.get("likes", 0),
                "lastModified": m.get("lastModified", "").split("T")[0]
            })
        return sorted(results, key=lambda x: x["downloads"], reverse=True)
    except Exception as e:
        st.error(f"❌ Errore connessione: {str(e)}")
        return []

@st.cache_data(ttl=300)
def get_model_files(model_id):
    try:
        r = requests.get(f"{HF_BASE}/api/models/{model_id}/tree/main", timeout=10)
        if r.status_code == 200:
            files = r.json()
            return [f["path"] for f in files if f.get("type") == "file" and f["path"].endswith(".gguf")]
        return []
    except:
        return []

def scarica_modello(file_url, filename):
    filepath = MODELS_DIR / filename
    try:
        with requests.get(file_url, stream=True, timeout=30) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            block_size = 8192
            progress_bar = st.progress(0)
            written = 0
            with open(filepath, 'wb') as f:
                for chunk in r.iter_content(chunk_size=block_size):
                    f.write(chunk)
                    written += len(chunk)
                    if total_size > 0:
                        progress = min(100, int((written / total_size) * 100))
                        progress_bar.progress(progress)
            progress_bar.empty()
        return str(filepath)
    except Exception as e:
        st.error(f"❌ Download fallito: {e}")
        return None

# --- STILE LM STUDIO ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    #MainMenu { visibility: hidden; }
    header { visibility: hidden; }
    .stApp { padding-top: 1rem; }
    .sidebar .sidebar-content {
        width: 220px !important;
        background: #f8f9fa;
        border-right: 1px solid #dee2e6;
    }
    .nav-item {
        padding: 12px 16px;
        margin: 4px 0;
        border-radius: 8px;
        color: #495057;
        display: flex;
        align-items: center;
        gap: 10px;
        font-weight: 500;
        cursor: pointer;
    }
    .nav-item:hover {
        background: #e9ecef;
    }
    .nav-item.active {
        background: #00cc99;
        color: white;
    }
    .model-row {
        padding: 12px;
        border-bottom: 1px solid #eee;
        cursor: pointer;
        transition: background 0.2s;
    }
    .model-row:hover {
        background: #f8f9fa;
    }
    .model-row.selected {
        background: #e3f2fd;
        border-left: 4px solid #00cc99;
    }
    .download-btn {
        background: #00cc99;
        color: white;
        border: none;
        padding: 12px 20px;
        border-radius: 8px;
        font-weight: bold;
        width: 100%;
        font-size: 14px;
        cursor: pointer;
    }
    .download-btn:hover {
        background: #00aa77;
    }
</style>
""", unsafe_allow_html=True)

# --- LAYOUT LM STUDIO ---

# Sidebar sinistra (menu)
with st.sidebar:
    st.markdown("<h2 style='color:#00cc99;'>ArcadiaAI</h2>", unsafe_allow_html=True)
    st.markdown("---")

    nav_items = ["🏠 Home", "📚 Libreria", "📦 Marketplace", "⚙️ Impostazioni"]
    icons = ["󠀠", "󠀠", "󠀠", "󠀠"]  # Spaziatori (simula icone)

    for item in nav_items:
        is_active = "Marketplace" in item
        extra = "active" if is_active else ""
        st.markdown(f"<div class='nav-item {extra}'>{item}</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.caption("© 2025 ArcadiaAI — Open Source")

# Layout principale: 3 colonne
col1, col2, col3 = st.columns([1.5, 1, 1], gap="medium")

# Colonna 1: Lista modelli (centrale)
with col1:
    st.markdown("### 🔍 Marketplace")
    query = st.text_input("", placeholder="Cerca modelli...", label_visibility="collapsed")

    models = get_gguf_models()
    if query:
        models = [m for m in models if query.lower() in m['name'].lower()]

    if not models:
        st.info("Nessun modello trovato.")
    else:
        for model in models:
            with st.container():
                # Usa expander per simulare clic sul modello
                exp = st.expander(f"🧠 {model['name']}", expanded=False)
                with exp:
                    st.markdown(f"**Downloads:** {model['downloads']:,}")
                    st.markdown(f"**Likes:** ⭐ {model['likes']}")
                    st.markdown(f"**Aggiornato:** {model['lastModified']}")

                    if st.button("Seleziona", key=f"sel_{model['id']}"):
                        st.session_state.selected_model = model

# Colonna 2: Dettagli modello
with col2:
    if "selected_model" in st.session_state:
        model = st.session_state.selected_model
        st.markdown(f"### 📄 {model['name'][:30]}...")
        files = get_model_files(model["id"])

        if files:
            st.markdown("**File disponibili:**")
            selected_file = st.selectbox("Versione:", files, key="file_select")
            size = "~4-8 GB" if "Q4" in selected_file or "Q5" in selected_file else "~8-12 GB"
            st.markdown(f"**Dimensione stimata:** {size}")
        else:
            st.info("Nessun file .gguf disponibile.")

# Colonna 3: Pulsante Download
with col3:
    if "selected_model" in st.session_state and "file_select" in st.session_state:
        model = st.session_state.selected_model
        selected_file = st.session_state.file_select
        file_url = f"https://huggingface.co/{model['id']}/resolve/main/{selected_file}"

        st.markdown("### 💾 Download")
        st.markdown(f"<small>File: `{selected_file}`</small>", unsafe_allow_html=True)

        if st.button("⬇️ SCARICA MODELLO", key="dl_main", help="Clicca per avviare il download"):
            with st.spinner("📥 Download in corso..."):
                path = scarica_modello(file_url, selected_file)
                if path:
                    st.success("✅ Completato!")
                    st.balloons()

# Footer nascosto
st.markdown("<br><br>", unsafe_allow_html=True)
st.caption("Powered by Hugging Face • Tutti i modelli sono open source")