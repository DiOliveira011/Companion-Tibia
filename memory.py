"""
Memória persistente por usuário — salva em arquivos JSON em disco.
Sobrevive a reinicializações do bot.
Armazena: histórico de conversa, perfil do jogador (vocação, nível, personagem).
"""

import os
import json
import time
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

MEMORY_DIR = Path("data/memory")
MEMORY_DIR.mkdir(parents=True, exist_ok=True)

MAX_MESSAGES = 10        # Máximo de mensagens salvas por usuário
MAX_PROFILE_AGE = 86400  # Perfil expira após 24h sem interação (em segundos)


def _path(user_id: int) -> Path:
    return MEMORY_DIR / f"{user_id}.json"


def load_user(user_id: int) -> dict:
    """Carrega memória do usuário do disco. Retorna estrutura padrão se não existir."""
    path = _path(user_id)
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Erro ao ler memória do usuário %s: %s", user_id, e)
    return _default_memory()


def save_user(user_id: int, memory: dict):
    """Salva memória do usuário em disco."""
    memory["last_seen"] = time.time()
    try:
        with open(_path(user_id), "w", encoding="utf-8") as f:
            json.dump(memory, f, ensure_ascii=False, indent=2)
    except OSError as e:
        logger.error("Erro ao salvar memória do usuário %s: %s", user_id, e)


def _default_memory() -> dict:
    return {
        "messages": [],
        "profile": {
            "char_name": None,
            "vocation": None,
            "level": None,
            "preferred_ai": "groq",   # groq | claude
            "guild": None,
        },
        "last_seen": time.time(),
    }


# ── Histórico de conversa ─────────────────────────────────────────────────────

def get_history(user_id: int) -> list[dict]:
    """Retorna histórico de mensagens do usuário (para injetar no prompt)."""
    mem = load_user(user_id)
    return mem.get("messages", [])


def add_message(user_id: int, role: str, content: str):
    """Adiciona mensagem ao histórico e salva em disco."""
    mem = load_user(user_id)
    mem["messages"].append({"role": role, "content": content})
    # Mantém apenas as últimas MAX_MESSAGES mensagens
    if len(mem["messages"]) > MAX_MESSAGES:
        mem["messages"] = mem["messages"][-MAX_MESSAGES:]
    save_user(user_id, mem)


def clear_history(user_id: int):
    """Limpa histórico de conversa mas mantém perfil."""
    mem = load_user(user_id)
    mem["messages"] = []
    save_user(user_id, mem)


# ── Perfil do jogador ─────────────────────────────────────────────────────────

def get_profile(user_id: int) -> dict:
    """Retorna perfil do jogador."""
    return load_user(user_id).get("profile", {})


def update_profile(user_id: int, **kwargs):
    """Atualiza campos do perfil (char_name, vocation, level, preferred_ai, guild)."""
    mem = load_user(user_id)
    for key, value in kwargs.items():
        if key in mem["profile"]:
            mem["profile"][key] = value
    save_user(user_id, mem)


def get_preferred_ai(user_id: int) -> str:
    """Retorna a IA preferida do usuário: 'groq' ou 'claude'."""
    return get_profile(user_id).get("preferred_ai", "groq")


def set_preferred_ai(user_id: int, ai: str):
    """Define a IA preferida: 'groq' ou 'claude'."""
    update_profile(user_id, preferred_ai=ai)


def build_profile_context(user_id: int) -> str:
    """Constrói string de contexto do perfil para injetar no prompt."""
    profile = get_profile(user_id)
    parts = []
    if profile.get("char_name"):
        parts.append(f"Personagem: {profile['char_name']}")
    if profile.get("vocation"):
        parts.append(f"Vocação: {profile['vocation']}")
    if profile.get("level"):
        parts.append(f"Nível: {profile['level']}")
    if profile.get("guild"):
        parts.append(f"Guild: {profile['guild']}")
    if not parts:
        return ""
    return f"[Perfil do jogador: {' | '.join(parts)}]"


# ── Estatísticas ──────────────────────────────────────────────────────────────

def count_users() -> int:
    """Retorna número de usuários com memória salva."""
    return len(list(MEMORY_DIR.glob("*.json")))


def list_active_users(hours: int = 24) -> list[int]:
    """Retorna IDs de usuários ativos nas últimas N horas."""
    cutoff = time.time() - hours * 3600
    active = []
    for path in MEMORY_DIR.glob("*.json"):
        try:
            with open(path, "r", encoding="utf-8") as f:
                mem = json.load(f)
            if mem.get("last_seen", 0) > cutoff:
                active.append(int(path.stem))
        except Exception:
            pass
    return active
