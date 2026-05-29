"""
Carrega conhecimento extra do GitHub (arquivo Markdown público).
Permite atualizar a KB sem fazer novo deploy do bot — basta editar o arquivo no GitHub.
Usa cache de 30 minutos para não bater na API do GitHub a todo momento.
"""

import os
import logging
import requests
from cache import TTLCache

logger = logging.getLogger(__name__)

# URL do arquivo Markdown no GitHub (raw content)
# Configure KB_GITHUB_URL no .env apontando para seu arquivo raw do GitHub
# Exemplo: https://raw.githubusercontent.com/SEU_USER/companion-tibia-kb/main/kb_extra.md
KB_GITHUB_URL = os.getenv(
    "KB_GITHUB_URL",
    ""   # Vazio = desativado até o usuário configurar
)

_cache = TTLCache()
_session = requests.Session()
_session.headers.update({
    "User-Agent": "CompanionTibia/2.0 (Discord Bot; Rubinot)",
    "Accept": "text/plain",
})


def load_extra_kb() -> str:
    """
    Carrega KB extra do GitHub.
    Retorna string vazia se KB_GITHUB_URL não estiver configurada ou se falhar.
    Cache de 30 minutos para evitar chamadas repetidas.
    """
    if not KB_GITHUB_URL:
        return ""

    cache_key = "kb:github_extra"
    cached = _cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        resp = _session.get(KB_GITHUB_URL, timeout=8)
        if resp.status_code == 200:
            content = resp.text.strip()
            if content:
                _cache.set(cache_key, content, ttl_seconds=1800)   # 30 min
                logger.info("KB extra carregada do GitHub: %d chars", len(content))
                return content
            return ""
        else:
            logger.warning("KB GitHub retornou %s", resp.status_code)
    except Exception as e:
        # Tenta sem verificação SSL (proxy corporativo)
        try:
            resp = _session.get(KB_GITHUB_URL, timeout=8, verify=False)
            if resp.status_code == 200:
                content = resp.text.strip()
                _cache.set(cache_key, content, ttl_seconds=1800)
                return content
        except Exception:
            pass
        logger.warning("KB GitHub indisponível: %s — usando apenas KB local", e)

    return ""


def build_full_system_prompt(base_prompt: str) -> str:
    """
    Combina o system prompt base (knowledge_base.py) com o extra do GitHub.
    Se o GitHub estiver configurado e disponível, adiciona o conteúdo extra ao final.
    """
    extra = load_extra_kb()
    if extra:
        return (
            base_prompt
            + "\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            + "## INFORMAÇÕES EXTRAS (Atualizadas via GitHub)\n\n"
            + extra
        )
    return base_prompt


def reload_kb():
    """Força o recarregamento da KB do GitHub (limpa o cache)."""
    _cache.delete("kb:github_extra")
    return load_extra_kb()


def kb_status() -> str:
    """Retorna status da KB extra para o comando /status."""
    if not KB_GITHUB_URL:
        return "⚪ KB GitHub: não configurada"
    cached = _cache.get("kb:github_extra")
    if cached is not None:
        return f"✅ KB GitHub: carregada ({len(cached):,} chars em cache)"
    return "🔄 KB GitHub: configurada, aguardando primeira carga"
