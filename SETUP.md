# Companion Tibia — Guia Completo de Setup e Deploy 24/7

> Bot Discord para Rubinot Open PvP  
> Criado por **Soneca & Shawnks**  
> Powered by Groq API (gratuita) — Custo: R$ 0

---

## O que você vai precisar

| O que | Onde pegar | Custo |
|-------|-----------|-------|
| Discord Bot Token | discord.com/developers | Grátis |
| Groq API Key | console.groq.com | Grátis |
| Python 3.10+ | python.org | Grátis |
| (Opcional) Conta Railway | railway.app | Grátis |

---

## PARTE 1 — Criar o Bot no Discord (5 minutos)

### 1.1 Criar a Application

1. Acesse: **https://discord.com/developers/applications**
2. Clique em **"New Application"**
3. Nome: `Companion Tibia`
4. Clique em **"Create"**

### 1.2 Configurar o Bot

1. No menu lateral, clique em **"Bot"**
2. Clique em **"Reset Token"** → confirme → **copie o token** (salve em lugar seguro!)
3. Role para baixo até **"Privileged Gateway Intents"**
4. Ative os três:
   - **Presence Intent** ✅
   - **Server Members Intent** ✅
   - **Message Content Intent** ✅
5. Clique em **"Save Changes"**

### 1.3 Convidar para o seu Servidor

1. No menu lateral, clique em **"OAuth2" → "URL Generator"**
2. Em **Scopes**, marque:
   - `bot`
   - `applications.commands`
3. Em **Bot Permissions**, marque:
   - `Send Messages`
   - `Embed Links`
   - `Read Message History`
   - `Use Slash Commands`
   - `Mention Everyone` (opcional)
4. Copie a URL gerada no final da página
5. Cole no navegador → escolha o servidor → **Authorize**

---

## PARTE 2 — Obter Groq API Key (2 minutos)

1. Acesse: **https://console.groq.com**
2. Clique em **"Sign Up"** → crie conta com Google ou email
3. Após entrar, clique em **"API Keys"** no menu lateral
4. Clique em **"Create API Key"** → dê um nome (ex: `companion-tibia`)
5. **Copie a chave** (aparece só uma vez!)

**Limite gratuito:** 30 requisições/minuto, 6.000 tokens/minuto  
→ Para um grupo de 20-50 jogadores, o plano gratuito é mais que suficiente.

---

## PARTE 3 — Instalar e Rodar (local, rápido)

### 3.1 Instalar Python (se não tiver)

Acesse **https://python.org/downloads** → baixe Python 3.11 ou 3.12  
Na instalação: marque **"Add Python to PATH"** ✅

### 3.2 Configurar o projeto

```
# Abra o terminal (cmd ou PowerShell) na pasta companion_tibia

# 1. Instalar dependências
pip install -r requirements.txt

# 2. Criar arquivo .env
copy .env.example .env

# 3. Abra o .env com Bloco de Notas e preencha:
# DISCORD_TOKEN=cole_seu_token_aqui
# GROQ_API_KEY=cole_sua_chave_groq_aqui
```

### 3.3 Testar se está tudo OK

```
python test_bot.py
```

Deve mostrar: `18/18 testes passaram`

### 3.4 Rodar o bot

```
# Opção A: rodar uma vez
python bot.py

# Opção B: rodar com auto-restart (recomendado)
run_forever.bat
```

Você verá no terminal:
```
[INFO] Keep-alive server rodando na porta 8080
[INFO] Companion Tibia online como Companion Tibia#1234
[INFO] Modelo: llama-3.1-70b-versatile
[INFO] Servidores: 1
```

Pronto! O bot está online no Discord. **Para desligar: Ctrl+C**

---

## PARTE 4 — Deploy 24/7 no Railway (bot fica online sozinho)

O Railway hospeda o bot de graça sem precisar do seu PC ligado.

### 4.1 Criar conta no Railway

1. Acesse: **https://railway.app**
2. Clique em **"Login"** → entre com sua conta GitHub
3. Se não tiver GitHub: crie em **github.com** (também grátis)

### 4.2 Subir o código para o GitHub

```
# No terminal, dentro da pasta companion_tibia:

git init
git add .
git commit -m "Companion Tibia - Rubinot Bot"

# Crie um repositório PRIVADO no github.com
# (privado porque o .env nunca vai junto — .gitignore já protege)

git remote add origin https://github.com/SEU_USUARIO/companion-tibia.git
git push -u origin main
```

**IMPORTANTE:** O arquivo `.env` NÃO vai para o GitHub (está no .gitignore).  
As chaves serão configuradas direto no Railway.

### 4.3 Deploy no Railway

1. No Railway, clique em **"New Project"**
2. Selecione **"Deploy from GitHub repo"**
3. Escolha o repositório `companion-tibia`
4. Railway detecta automaticamente que é Python e instala as dependências

### 4.4 Configurar variáveis de ambiente no Railway

1. No projeto criado, clique em **"Variables"**
2. Adicione uma por vez:
   - `DISCORD_TOKEN` = seu token do Discord
   - `GROQ_API_KEY` = sua chave Groq
   - `GROQ_MODEL` = `llama-3.1-70b-versatile`
3. Clique em **"Deploy"** (Railway reinicia automaticamente)

### 4.5 Verificar que está rodando

Na aba **"Logs"** do Railway você verá:
```
Companion Tibia online como Companion Tibia#1234
Keep-alive server rodando na porta 8080
```

**Pronto! Bot online 24/7 sem precisar do seu PC ligado.**

---

## PARTE 5 — Comandos disponíveis no Discord

| Comando | O que faz |
|---------|-----------|
| `/ajuda` | Lista todos os comandos |
| `/hunt [vocação] [nível]` | Melhores hunts com guia por classe e rotação de spells |
| `/nivel [vocação] [nível]` | Roadmap completo do nível atual |
| `/vocacao [nome]` | Guia completo da vocação |
| `/spells [vocação]` | Rotação de spells com prioridade |
| `/imbue [vocação] [slot]` | Melhores imbuements por slot |
| `/grupo [composição]` | Análise de composição de party |
| `/personagem [nome]` | Busca personagem no site do Rubinot com análise de IA |
| `/party [nomes]` | Busca dados reais de até 5 personagens e analisa o grupo |
| `/item [nome]` | Info do item: stats, imagem, onde dropar |
| `/monstro [nome]` | HP, EXP, loot, resistências da criatura |
| `/boss [nome]` | Guia de boss: composição, estratégia, loot |
| `/quest [nome]` | Guia de quest: requisitos, passo a passo, recompensas |
| `/rubinot [tema]` | Info do servidor (forge, transfer, soulpit, etc.) |
| `/ask [pergunta]` | Pergunta livre, IA responde sobre qualquer coisa |
| `/status` | Status do bot: ping, cache, usuários ativos |
| `/limpar` | Reseta seu histórico de conversa |
| `@Companion Tibia [mensagem]` | Mencione o bot para perguntar qualquer coisa |

---

## PARTE 6 — Atualizar a base de conhecimento

A knowledge base fica no arquivo `knowledge_base.py` — é onde você pode adicionar novas informações sem mexer na lógica do bot.

**Para adicionar uma nova hunt:**
1. Abra `knowledge_base.py`
2. Localize a seção `## GUIAS DETALHADOS DE HUNT`
3. Adicione um novo bloco seguindo o formato dos existentes
4. Salve e reinicie o bot (no Railway: basta fazer `git push`)

**Para corrigir informação errada:**
- Edite `knowledge_base.py` diretamente
- No Railway: `git commit -m "fix: atualiza hunt X" && git push`
- O Railway faz deploy automático em ~1 minuto

---

## PARTE 7 — Resolução de Problemas

### Bot não aparece online

- Verifique o `DISCORD_TOKEN` no `.env` — ele muda quando você clica "Reset Token"
- Verifique os Privileged Intents (Message Content, etc.) estão ativados

### Erro "Invalid API Key" do Groq

- A chave Groq expira ou pode ser revogada — gere uma nova em console.groq.com
- Atualize `GROQ_API_KEY` no `.env` (local) ou nas Variables do Railway

### Comandos slash não aparecem no Discord

- Após reiniciar o bot, aguarde até **1 hora** para o Discord sincronizar os comandos
- Ou use `/ajuda` — se aparecer, os outros também vão aparecer em breve

### `/personagem` não encontra o personagem

- Nomes são **case-sensitive** no Rubinot: `Soneca` ≠ `soneca`
- O site do Rubinot pode estar com lentidão — tente novamente
- Se persistir: o site pode ter mudado o HTML (abra rubinot.com.br e verifique)

### Respostas lentas

- Groq free tier tem latência de ~0.5-2s para modelos 70B
- Para respostas mais rápidas, mude `GROQ_MODEL=llama3-8b-8192` (menor, mas mais rápido)

### Limite de requisições Groq (rate limit)

- Free tier: 30 req/minuto — suficiente para grupo de até 50 pessoas casual
- Se o grupo crescer muito, considere criar uma segunda API key Groq (também gratuita)

---

## PARTE 8 — Manutenção mínima recomendada

| Frequência | O que fazer |
|------------|-------------|
| Após cada patch do Rubinot | Atualizar `knowledge_base.py` com mudanças de drop/rate |
| Mensalmente | Verificar se o site do Rubinot mudou (scraper de personagens) |
| Quando crescer | Considerar segunda API key Groq se ultrapassar 30 req/min |
| Opcional | Adicionar novos comandos conforme feedback da galera |

---

## Arquitetura do projeto

```
companion_tibia/
├── bot.py              # Bot principal — comandos slash, eventos, IA
├── knowledge_base.py   # Base de conhecimento — toda info do jogo
├── scraper.py          # Busca personagens no site do Rubinot
├── tibia_api.py        # TibiaWiki.dev — itens, criaturas, imagens
├── cache.py            # Cache TTL — evita chamadas repetidas às APIs
├── keep_alive.py       # Servidor HTTP para manter bot online no Railway
├── test_bot.py         # Testes automáticos — rodar antes de subir
├── requirements.txt    # Dependências Python
├── .env.example        # Template de variáveis de ambiente
├── .gitignore          # NUNCA commitar .env!
├── Procfile            # Comando de start para Railway
├── railway.toml        # Configuração Railway (restart, healthcheck)
├── runtime.txt         # Versão Python (Railway usa isso)
├── run_forever.bat     # Auto-restart no Windows (uso local)
└── run_forever.sh      # Auto-restart no Linux/Mac
```

---

## Custos

| Serviço | Plano | Custo |
|---------|-------|-------|
| Discord Bot | Gratuito | R$ 0 |
| Groq API (IA) | Free tier | R$ 0 |
| Railway (hosting) | Starter | R$ 0* |
| GitHub (código) | Free | R$ 0 |
| **TOTAL** | | **R$ 0** |

*Railway free tier: 500 horas/mês por serviço. Um bot 24/7 usa ~720h/mês.  
Para ultrapassar, o plano pago custa ~US$5/mês. Alternativas gratuitas: Render.com, Fly.io.

---

*Companion Tibia — Rubinot Open PvP — Criado por Soneca & Shawnks*
