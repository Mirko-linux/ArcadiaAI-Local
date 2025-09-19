# core/memory.py
import json
import os
from datetime import datetime
from pathlib import Path

# --- CONFIG ---
MEMORY_DIR = Path("memory")
MEMORY_DIR.mkdir(exist_ok=True)

def set_nested(d, path, value):
    """Imposta un valore annidato: set_nested(data, 'user.preferences.food', 'pizza')"""
    keys = path.split('.')
    for key in keys[:-1]:
        d = d.setdefault(key, {})
    d[keys[-1]] = value

def get_nested(d, path, default=None):
    """Ottiene un valore annidato"""
    keys = path.split('.')
    for key in keys:
        if isinstance(d, dict) and key in d:
            d = d[key]
        else:
            return default
    return d

class MemoryManager:
    def __init__(self, user_id="default"):
        self.user_id = user_id
        self.storage_key = MEMORY_DIR / f"{user_id}.json"
        self.data = {}
        self.load()

    def load(self):
        """Carica la memoria dal file"""
        if not self.storage_key.exists():
            self.data = self.default_memory()
            return
        try:
            with open(self.storage_key, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
        except Exception:
            self.data = self.default_memory()

    def default_memory(self):
        return {
            "user": {},
            "conversations": {"frequent_topics": []},
            "system": {
                "memory_enabled": True,
                "version": "1.0",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
        }

    def update(self, path, value):
        """Aggiorna un campo nella memoria"""
        if not self.is_enabled():
            return False
        set_nested(self.data, path, value)
        self.log_change("update", path, value)
        self.save()
        return True

    def get(self, path, default=None):
        """Legge un valore dalla memoria"""
        if not self.is_enabled():
            return default
        return get_nested(self.data, path, default)

    def delete(self, key):
        """Cancella una chiave sotto 'user' o 'conversations'"""
        section = "user" if key in self.data.get("user", {}) else \
                  "conversations" if key in self.data.get("conversations", {}) else None
        if section:
            del self.data[section][key]
            self.save()

    def save(self):
        """Salva la memoria su disco"""
        data_to_save = self.data.copy()
        data_to_save["system"]["updated_at"] = datetime.now().isoformat()
        with open(self.storage_key, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, indent=2, ensure_ascii=False)

    def is_enabled(self):
        return self.data["system"].get("memory_enabled", True)

    def clear(self):
        """Resetta completamente la memoria"""
        if self.storage_key.exists():
            os.remove(self.storage_key)
        self.data = self.default_memory()

    def log_change(self, action, key, value):
        """Registra le modifiche (opzionale)"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "key": key,
            "value_preview": str(value)[:50]
        }
        log_file = MEMORY_DIR / "log.json"
        logs = []
        if log_file.exists():
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
            except:
                pass
        logs.append(log_entry)
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(logs[-100:], f, indent=2) 