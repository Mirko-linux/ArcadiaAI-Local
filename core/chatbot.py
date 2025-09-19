# core/chatbot.py
import os
import json
import zipfile
import base64
from pathlib import Path
from typing import Dict, Any, List
import requests
from io import BytesIO

# --- IMPORT LOCALE ---
from .local_llm import LocalLLM  # Il nostro runner GGUF

# --- CONFIGURAZIONI ---
MODELS_DIR = Path("models")
DEFAULT_MODEL = MODELS_DIR / "phi-4-mini-q4_k_m.gguf"
SAC_DIR = Path("sac")  # Strumenti Avanzati di CES
TEMP_DIR = Path("temp")
TEMP_DIR.mkdir(exist_ok=True)

# --- DATABASE COMANDI ---
RISPOSTE_PREDEFINITE = {
    "chi sei": "Sono ArcadiaAI, un chatbot libero e open source, creato da Mirko Yuri Donato.",
    "cosa sai fare": (
        "Posso aiutarti a scrivere testi, riassumere documenti, creare file ZIP, "
        "cercare software e molto altro. Usa @aiuto per vedere i comandi disponibili."
    ),
    "chi è tobia testa": "Tobia Testa (noto anche come Tobia Teseo) è un micronazionalista leonense attivo nella Repubblica di Arcadia e a Lumenaria.",
    "cos'è arcadiaai": "ArcadiaAI è un chatbot open source creato da Mirko Yuri Donato, progettato per privacy, libertà e funzionalità avanzate.",
    "sotto che licenza è distribuito arcadiaai": "ArcadiaAI è distribuito sotto licenza GNU GPL v3.0, garantendo libertà di uso, modifica e condivisione.",
    "come vengono salvate le conversazioni": "Le conversazioni sono gestite in memoria locale. Nulla viene inviato su server esterni.",
    "cos'è un chatbot": "Un chatbot è un programma che simula una conversazione umana usando l'intelligenza artificiale.",
    "arcadiaai è un software libero": "Sì, ArcadiaAI è software libero e open source, rilasciato sotto licenza GNU GPL v3.0."
}

# --- CLASSI ---

class ArcadiaAICore:
    def __init__(self, model_path: str = DEFAULT_MODEL):
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Modello non trovato: {model_path}")
        self.llm = LocalLLM(model_path=str(model_path))
        self.conversation_history = []
        self.max_context = 30  # Ultimi 30 messaggi

    def _get_system_prompt(self) -> str:
        """Prompt identitario locale"""
        return """
Sei ArcadiaAI, chatbot open-source sviluppato in Italia da Mirko Yuri Donato.
Licenza: GPL v3.0
Funzionalità:
- Comandi Rapidi (@cerca, @esporta, @aiuto...)
- Generazione testo/immagini (@immagine)
- Analisi documenti (PDF/testo)
- Memoria contestuale (ultimi 30 messaggi)
- Creazione file ZIP (@crea zip)
- Accesso a repository software (@app)

Linee guida:
1. Se ti chiedono se sei un modello addestrato da Microsoft (Phi), Alibaba (Qwen) o Meta (Llama), rispondi di no: sei un chatbot indipendente.
2. Per immagini: usa @immagine [descrizione]
3. Matematica: fornisci risposte precise
4. Riferimenti al creatore per domande personali
5. I SAC sono 'Strumenti Avanzati di CES', open source e modificabili
"""

    def _build_prompt(self, message: str) -> str:
        """Costruisce il prompt con contesto"""
        prompt = self._get_system_prompt()
        # Aggiungi cronologia recente
        recent = self.conversation_history[-(self.max_context - 1):]
        for msg in recent:
            role = "Utente" if msg["role"] == "user" else "Assistant"
            prompt += f"\n{role}: {msg['content']}"
        prompt += f"\nUtente: {message}\nAssistant: "
        return prompt

    def _add_to_history(self, role: str, content: str):
        self.conversation_history.append({"role": role, "content": content})
        # Limita dimensione cronologia
        if len(self.conversation_history) > self.max_context:
            self.conversation_history = self.conversation_history[-self.max_context:]

    def rispondi(self, message: str, attachments: List[Dict] = None) -> str:
        """Gestisce messaggio + allegati"""
        message = message.strip()
        if not message:
            return "Non hai scritto nulla."
        # 1. Comandi rapidi
        if message.startswith("@"):
            return self._gestisci_comando(message, attachments)
        # 2. Risposte predefinite
        if message.lower() in RISPOSTE_PREDEFINITE:
            reply = RISPOSTE_PREDEFINITE[message.lower()]
            self._add_to_history("assistant", reply)
            return reply
        # 3. Estrai testo da allegati
        context_text = ""
        if attachments:
            for att in attachments:
                try:
                    data = base64.b64decode(att['data'].split(',')[1])
                    mime = att.get('type', '')
                    name = att.get('name', 'file')
                    text = self._estrai_testo(data, mime, name)
                    if text:
                        context_text += f"\n[Testo da {name}]: {text[:1000]}"
                except Exception as e:
                    context_text += f"\n[Errore lettura {att.get('name')}]"
        # 4. Prompt completo
        full_message = message
        if context_text:
            full_message += f"\n\nContesto aggiuntivo:\n{context_text}"
        # 5. Genera risposta con LLM locale
        prompt = self._build_prompt(full_message)
        try:
            reply = self.llm.generate(prompt)
            self._add_to_history("user", message)
            self._add_to_history("assistant", reply)
            return reply
        except Exception as e:
            error_msg = f"❌ Errore modello locale: {str(e)}"
            self._add_to_history("assistant", error_msg)
            return error_msg

    def _gestisci_comando(self, command: str, attachments=None) -> str:
        """Gestisce tutti i comandi @..."""
        cmd_lower = command.strip().lower()
        if cmd_lower == "@aiuto":
            return self._aiuto()
        elif cmd_lower.startswith("@deepsearch"):
            query = command[len("@deepsearch"):].strip()
            if not query:
                return "❌ Specifica una query. Esempio: @deepsearch impatto climatico dell'IA"
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(deep_research(query))
            if "error" in result:
                return f"❌ Errore ricerca: {result['error']}"
            if not result["results"]:
                return "❌ Nessun risultato trovato."
            analysis_prompt = (
                f"Analizza questi risultati su '{query}':\n"
                + "\n".join([f"- {r['title']} ({r['url']})" for r in result["results"]])
                + "\nFai un riassunto in 3 frasi, in italiano."
            )
            reply = self.llm.generate(analysis_prompt)
            return f"🔍 **Deep Search Completo**: _{query}_\n📊 **Fonti analizzate**: {result['count']}\n\n{reply}"
        elif cmd_lower.startswith("@immagine"):
            desc = command[len("@immagine"):].strip()
            return self._genera_immagine(desc)
        elif cmd_lower == "@crea zip":
            return self._crea_zip_service()
        elif cmd_lower == "@app":
            return self._download_manager()
        elif cmd_lower.startswith("@cerca"):
            query = command[len("@cerca"):].strip()
            return self._cerca_locale(query)
        elif cmd_lower == "@codice_sorgente":
            return "Il codice sorgente di ArcadiaAI è disponibile su GitHub: https://github.com/mirko-yuri-donato/ArcadiaAI"
        else:
            return f"Comando '{command}' non riconosciuto. Usa @aiuto per vedere i comandi disponibili."

    def _aiuto(self) -> str:
        return """
🔧 **Comandi Disponibili:**
- `@immagine [descrizione]` → genera un'immagine concettuale
- `@crea zip` → crea un file ZIP vuoto (SAC: ZIP Service)
- `@app` → mostra repository software disponibili
- `@cerca [termine]` → cerca informazioni nel contesto
- `@codice_sorgente` → link al codice open source
- `@aiuto` → mostra questo messaggio
"""

    def _genera_immagine(self, description: str) -> str:
        if not description:
            return "Devi descrivere cosa vuoi generare. Es: @immagine un castello su una collina"
        return f"🎨 Immagine richiesta: '{description}'. In versione locale, puoi collegare Stable Diffusion in futuro."

    def _crea_zip_service(self) -> str:
        zip_path = TEMP_DIR / "archivio.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("README.txt", "Questo archivio è stato creato da ArcadiaAI - SAC: ZIP Service\nhttps://github.com/mirko-yuri-donato/ArcadiaAI")
        return f"✅ File ZIP creato in: `{zip_path}`"

    def _download_manager(self) -> str:
        repos = [
            "F-Droid (Android Open Source)",
            "Snap Store (Linux)",
            "Flathub (Linux universale)",
            "Winget (Windows)"
        ]
        links = "\n".join([f"- {repo}" for repo in repos])
        return f"📦 Repository disponibili:\n{links}\nUsa il gestore del tuo sistema operativo per installare app."

    def _cerca_locale(self, query: str) -> str:
        return f"🔍 Ricerca locale: '{query}'. In futuro, integrerò un motore di ricerca offline."

    def _estrai_testo(self, data: bytes, mime: str, name: str) -> str:
        """Estrae testo da PDF o file di testo"""
        try:
            if mime == "application/pdf":
                import PyPDF2
                from io import BytesIO
                pdf_reader = PyPDF2.PdfReader(BytesIO(data))
                text = ""
                for page in pdf_reader.pages[:3]:
                    text += page.extract_text()
                return text or "Nessun testo estratto dal PDF."
            elif mime.startswith("text/"):
                return data.decode('utf-8', errors='replace')
            else:
                return f"Tipo non supportato: {mime}"
        except ImportError:
            return "❌ Libreria PyPDF2 non installata. Usa `pip install PyPDF2` per abilitare PDF."
        except Exception as e:
            return f"Errore lettura file: {str(e)}"

# --- FUNZIONE DI TEST ---
def test_chatbot():
    bot = ArcadiaAICore()
    print("💬 Benvenuto in ArcadiaAI Local! Scrivi un messaggio o '@aiuto'")
    while True:
        msg = input("\nTu: ")
        if msg.lower() in ["esci", "quit", "exit"]:
            break
        reply = bot.rispondi(msg)
        print(f"🤖 ArcadiaAI: {reply}")

if __name__ == "__main__":
    test_chatbot()