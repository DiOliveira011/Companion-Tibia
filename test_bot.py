"""
Suite de testes do Companion Tibia.
Executa: python test_bot.py

Testa: cache, scraper, TibiaWiki API, knowledge base, keep_alive.
Nao precisa de token Discord para rodar.
"""

import sys
import time
import io

# Força UTF-8 no stdout para compatibilidade com Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

PASS = "[OK]"
FAIL = "[FAIL]"
WARN = "[WARN]"
results = []


def test(name: str, fn):
    """Executa um teste e registra resultado."""
    try:
        result = fn()
        if result is True or result is None:
            print(f"  {PASS} {name}")
            results.append((name, True, None))
        elif result is False:
            print(f"  {FAIL} {name} — retornou False")
            results.append((name, False, "retornou False"))
        else:
            print(f"  {PASS} {name} → {result}")
            results.append((name, True, result))
    except Exception as e:
        print(f"  {FAIL} {name} — {e}")
        results.append((name, False, str(e)))


# ── Cache ─────────────────────────────────────────────────────────────────────

print("\n--- Testando cache.py ---")

def test_cache_set_get():
    from cache import TTLCache
    c = TTLCache()
    c.set("key1", "value1", ttl_seconds=10)
    return c.get("key1") == "value1"

def test_cache_expiry():
    from cache import TTLCache
    c = TTLCache()
    c.set("key2", "value2", ttl_seconds=1)
    time.sleep(1.1)
    return c.get("key2") is None

def test_cache_delete():
    from cache import TTLCache
    c = TTLCache()
    c.set("key3", "value3")
    c.delete("key3")
    return c.get("key3") is None

def test_cache_size():
    from cache import TTLCache
    c = TTLCache()
    c.set("a", 1); c.set("b", 2); c.set("c", 3)
    return c.size() == 3

test("set/get básico", test_cache_set_get)
test("expiração por TTL", test_cache_expiry)
test("delete de chave", test_cache_delete)
test("contagem de entradas", test_cache_size)


# ── Knowledge Base ────────────────────────────────────────────────────────────

print("\n📚 Testando knowledge_base.py...")

def test_kb_system_prompt():
    from knowledge_base import SYSTEM_PROMPT
    assert len(SYSTEM_PROMPT) > 5000, "System prompt muito curto"
    assert "Rubinot" in SYSTEM_PROMPT
    assert "Knight" in SYSTEM_PROMPT
    assert "Monk" in SYSTEM_PROMPT
    assert "Harmony" in SYSTEM_PROMPT
    return f"{len(SYSTEM_PROMPT):,} chars"

def test_kb_aliases():
    from knowledge_base import VOCATION_ALIASES
    assert "ek" in VOCATION_ALIASES
    assert "monk" in VOCATION_ALIASES
    assert "ms" in VOCATION_ALIASES

def test_kb_emojis():
    from knowledge_base import VOCATION_EMOJIS
    assert VOCATION_EMOJIS["knight"] == "⚔️"
    assert VOCATION_EMOJIS["monk"] == "🥊"

def test_kb_help_text():
    from knowledge_base import HELP_TEXT
    assert "/hunt" in HELP_TEXT
    assert "/personagem" in HELP_TEXT
    assert "/party" in HELP_TEXT
    return f"{len(HELP_TEXT)} chars"

test("system prompt tamanho e conteúdo", test_kb_system_prompt)
test("aliases de vocação", test_kb_aliases)
test("emojis de vocação", test_kb_emojis)
test("help text com todos os comandos", test_kb_help_text)


# ── Scraper ───────────────────────────────────────────────────────────────────

print("\n🌐 Testando scraper.py...")

def test_scraper_import():
    from scraper import get_character, format_character_embed, get_party_data

def test_scraper_not_found():
    from scraper import get_character
    # Personagem que certamente não existe
    result = get_character("xXXNOMEQUENAOEXISTEXXx_12345")
    return result is None

def test_scraper_format_not_found():
    from scraper import format_character_embed
    result = format_character_embed({"name": "Teste", "found": False})
    assert "❌" in result["title"] or "não encontrado" in result["description"].lower()

def test_scraper_extract_number():
    from scraper import _extract_number
    assert _extract_number("Level: 250") == 250
    assert _extract_number("nada") is None
    assert _extract_number("1.000") == 1000

test("importação dos módulos", test_scraper_import)
test("personagem inexistente retorna None", test_scraper_not_found)
test("format_character_embed para não encontrado", test_scraper_format_not_found)
test("_extract_number parse correto", test_scraper_extract_number)


# ── TibiaWiki API ─────────────────────────────────────────────────────────────

print("\n🐉 Testando tibia_api.py (requer internet)...")

def test_tibia_api_import():
    from tibia_api import get_item, get_creature, format_item_embed, format_creature_embed

def test_tibia_api_item():
    from tibia_api import get_item
    item = get_item("Dragon Scale Mail")
    if item is None:
        print(f"    {WARN} API indisponível ou item não encontrado (pode ser instabilidade)")
        return True  # não falha o teste por API externa
    assert item.get("name")
    assert "image_url" in item
    return f"Encontrado: {item.get('name')}, slots={item.get('imbueslots', '?')}"

def test_tibia_api_creature():
    from tibia_api import get_creature
    creature = get_creature("Dragon")
    if creature is None:
        print(f"    {WARN} API indisponível (pode ser instabilidade)")
        return True
    assert creature.get("name")
    assert "image_url" in creature
    hp = creature.get("hp", "?")
    exp = creature.get("exp", "?")
    return f"Encontrado: {creature.get('name')}, HP={hp}, EXP={exp}"

def test_tibia_api_not_found():
    from tibia_api import get_item
    result = get_item("ItemQueNaoExiste12345XYZ")
    return result is None

def test_tibia_api_format_creature():
    from tibia_api import format_creature_embed
    fake_creature = {
        "name": "Test Dragon",
        "hp": 1000,
        "exp": 500,
        "maxdmg": 200,
        "loot": [{"item": "Dragon Lore", "rarity": "rare"}],
        "image_url": "http://test.com/img.gif",
    }
    result = format_creature_embed(fake_creature)
    assert "Test Dragon" in result["title"]
    assert "1,000" in result["description"] or "1000" in result["description"]

test("importação dos módulos", test_tibia_api_import)
test("buscar item (Dragon Scale Mail)", test_tibia_api_item)
test("buscar criatura (Dragon)", test_tibia_api_creature)
test("item inexistente retorna None", test_tibia_api_not_found)
test("format_creature_embed com dados fake", test_tibia_api_format_creature)


# ── Keep Alive ────────────────────────────────────────────────────────────────

print("\n🔄 Testando keep_alive.py...")

def test_keep_alive_start():
    from keep_alive import start_keep_alive
    thread = start_keep_alive(port=19999)
    time.sleep(0.3)
    import urllib.request
    resp = urllib.request.urlopen("http://localhost:19999/health", timeout=3)
    body = resp.read()
    assert b"online" in body
    return "HTTP health check respondeu OK"

test("servidor HTTP sobe e responde /health", test_keep_alive_start)


# ── Relatório Final ───────────────────────────────────────────────────────────

total = len(results)
passed = sum(1 for _, ok, _ in results if ok)
failed = total - passed

print(f"\n{'='*50}")
print(f"  Resultado: {passed}/{total} testes passaram")
if failed:
    print(f"\n  {FAIL} Falhas:")
    for name, ok, msg in results:
        if not ok:
            print(f"    - {name}: {msg}")
else:
    print(f"  {PASS} Todos os testes passaram!")
print(f"{'='*50}\n")

sys.exit(0 if failed == 0 else 1)
