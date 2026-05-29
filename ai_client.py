"""
Abstração de cliente de IA dual: Groq (gratuito, padrão) + Claude (opcional, pago).
Se ANTHROPIC_API_KEY não estiver configurado, Claude não fica disponível.
O usuário pode escolher o modelo preferido por sessão com /modelo.
"""

import os
import logging
from groq import Groq

logger = logging.getLogger(__name__)

GROQ_API_KEY     = os.getenv("GROQ_API_KEY")
GROQ_MODEL       = os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CLAUDE_MODEL     = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")

# Inicializa clientes disponíveis
_groq = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

_claude = None
if ANTHROPIC_API_KEY:
    try:
        import anthropic
        _claude = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        logger.info("Claude disponível (%s)", CLAUDE_MODEL)
    except ImportError:
        logger.warning("anthropic não instalado — modo Claude desativado. Execute: pip install anthropic")
else:
    logger.info("ANTHROPIC_API_KEY não configurada — apenas Groq disponível")

CLAUDE_AVAILABLE = _claude is not None


def chat(
    messages: list[dict],
    system_prompt: str,
    preferred: str = "groq",
    max_tokens: int = 1200,
) -> tuple[str, str]:
    """
    Envia mensagem para a IA escolhida.

    Args:
        messages: histórico de conversa [{"role": "user"|"assistant", "content": "..."}]
        system_prompt: contexto injetado como system message
        preferred: "groq" ou "claude"
        max_tokens: limite de tokens na resposta

    Returns:
        tuple(resposta_texto, modelo_usado)
    """
    use_claude = preferred == "claude" and CLAUDE_AVAILABLE

    if use_claude:
        return _chat_claude(messages, system_prompt, max_tokens)
    else:
        return _chat_groq(messages, system_prompt, max_tokens)


def _chat_groq(messages: list[dict], system_prompt: str, max_tokens: int) -> tuple[str, str]:
    """Chama Groq API (gratuita)."""
    if not _groq:
        return "❌ GROQ_API_KEY não configurada.", "erro"
    try:
        full_messages = [{"role": "system", "content": system_prompt}] + messages
        resp = _groq.chat.completions.create(
            model=GROQ_MODEL,
            messages=full_messages,
            max_tokens=max_tokens,
            temperature=0.35,
        )
        return resp.choices[0].message.content, f"groq/{GROQ_MODEL}"
    except Exception as e:
        logger.error("Groq error: %s", e)
        return f"❌ Erro na IA (Groq): `{e}`\nTente novamente.", "erro"


def _chat_claude(messages: list[dict], system_prompt: str, max_tokens: int) -> tuple[str, str]:
    """Chama Claude API (Anthropic — requer chave paga)."""
    try:
        # Claude usa system separado da lista de mensagens
        resp = _claude.messages.create(
            model=CLAUDE_MODEL,
            system=system_prompt,
            messages=messages,
            max_tokens=max_tokens,
        )
        return resp.content[0].text, f"claude/{CLAUDE_MODEL}"
    except Exception as e:
        logger.error("Claude error: %s — fazendo fallback para Groq", e)
        # Fallback automático para Groq se Claude falhar
        answer, model = _chat_groq(messages, system_prompt, max_tokens)
        return answer + "\n\n*⚠️ Falhou no Claude, respondido via Groq.*", model


def status_text() -> str:
    """Retorna string de status dos modelos disponíveis."""
    lines = [f"✅ Groq: `{GROQ_MODEL}` (gratuito)"]
    if CLAUDE_AVAILABLE:
        lines.append(f"✅ Claude: `{CLAUDE_MODEL}` (pago — disponível)")
    else:
        lines.append("⚪ Claude: não configurado (opcional)")
    return "\n".join(lines)
