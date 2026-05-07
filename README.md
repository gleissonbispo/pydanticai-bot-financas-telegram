# FinBot — Bot de Finanças Pessoais com IA

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![PydanticAI](https://img.shields.io/badge/PydanticAI-0.2+-E92063?logo=pydantic&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![Ollama](https://img.shields.io/badge/Ollama-Local-black)
![Status](https://img.shields.io/badge/Status-Portfolio-brightgreen)

> Bot para o Telegram que registra gastos a partir de **textos, fotos e PDFs** usando um LLM multimodal rodando 100% localmente — sem custos de API, rodando no Raspberry Pi 5.

---

## Demo

```
┌─────────────────────────────────────────────────────┐
│  FinBot                                             │
│                                                     │
│  Você: Gastei 45 reais de uber                      │
│                                                     │
│  [Agente de extração processa o texto]              │
│  [Salva no PostgreSQL]                              │
│                                                     │
│  Bot: ✅ Gasto registrado!                          │
│       💰 Valor: R$ 45.00                            │
│       📁 Categoria: transporte                      │
│       📝 Descrição: Corrida de Uber                 │
│       🔖 ID: #12                                    │
│                                                     │
│  Você: Com o que gastei mais esse mês?              │
│                                                     │
│  [Agente de análise busca dados reais no banco]     │
│                                                     │
│  Bot: Seu maior gasto foi alimentação: R$ 850,00   │
│       (35% do total). Transporte veio em segundo   │
│       com R$ 320,50...                              │
└─────────────────────────────────────────────────────┘
```

### 📸 Registro por foto
![Registro por foto](docs/demo/foto_registro.png)

### 📊 Gráfico de gastos (/grafico)
![Gráfico](docs/demo/grafico.png)

---

## Arquitetura

```
┌──────────────────┐  Mensagem   ┌─────────────────────────────────────────┐
│  Usuário         │────────────►│           handlers.py (Bot)             │
│  (Telegram)      │             │                                         │
└──────────────────┘             │  tem palavra-chave?  ── SIM ──► Agente  │
                                 │  ("gastei", "paguei")         Extração  │
                                 │                                         │
                                 │  é uma pergunta?     ── SIM ──► Agente  │
                                 │  ("quanto gastei?")           Análise   │
                                 └──────────────┬──────────────────────────┘
                                                │
                                 ┌──────────────▼──────────────────────────┐
                                 │  PydanticAI Agents                      │
                                 │                                         │
                                 │  Extração → ExtractedExpense (schema)   │
                                 │  Análise  → 3 tools com dados reais     │
                                 └──────────────┬──────────────────────────┘
                                                │
                          ┌─────────────────────▼─────────────────────┐
                          │  ExpenseRepository (SQLAlchemy async)      │
                          │  PostgreSQL 16                             │
                          └─────────────────────────────────────────-─┘
                                                ▲
                          ┌─────────────────────┴─────────────────────┐
                          │  Ollama — gemma4:e2b (local, no Raspberry) │
                          └───────────────────────────────────────────┘
```

### Fluxo de uma mensagem de foto

```
1. Usuário manda foto de comprovante
2. handler_photo() baixa os bytes da imagem
3. extract_from_image(bytes) chama extraction_agent.run()
4. Ollama processa com Gemma 4 E2B (lê texto na imagem)
5. PydanticAI valida a saída → ExtractedExpense(amount, category, description)
6. repo.save_expense() faz INSERT no PostgreSQL
7. Bot responde com confirmação
```

---

## O problema que este projeto resolve

Controlar gastos manualmente é chato. Você para de fazer isso depois de 3 dias.

Este bot resolve isso deixando o registro ser **natural**: você manda a foto do comprovante direto do celular, ou digita "gastei 30 reais de almoço" como se estivesse mandando uma mensagem para um amigo — e a IA cuida do resto.

A parte interessante tecnicamente: o LLM não apenas "responde" — ele **extrai dados estruturados** de entradas não estruturadas (textos ambíguos, fotos de cupons, PDFs de notas fiscais) e **busca dados reais no banco** antes de responder perguntas, sem inventar números.

---

## Stack Tecnológica

| Tecnologia | Papel | Por que esta escolha |
|-----------|-------|---------------------|
| **PydanticAI** | Framework de agentes | Schema-first: a saída do LLM é validada por um modelo Pydantic. Se o modelo retornar formato inválido, o framework retenta automaticamente |
| **Ollama + Gemma 4 E2B** | LLM local | Zero custo de API. Roda nos 8 GB do Raspberry Pi 5. Dados financeiros nunca saem da rede local |
| **python-telegram-bot** | Interface com o usuário | Biblioteca oficial do Telegram, com suporte a fotos, PDFs e comandos |
| **PostgreSQL 16** | Banco de dados | Robusto, com suporte async nativo via asyncpg |
| **SQLAlchemy 2.0 async** | ORM | Queries assíncronas sem bloquear o bot enquanto aguarda o banco |
| **matplotlib** | Gráficos | Gera PNG de pizza + barras que o bot envia como foto |
| **pypdf** | Leitura de PDF | Extrai texto de notas fiscais para o LLM processar |
| **structlog** | Logging | Logs em JSON estruturado — fácil de filtrar e monitorar |
| **Docker Compose** | Orquestração | Sobe PostgreSQL + Ollama + Bot com um único comando |

---

## Funcionalidades

- [x] Registro de gasto por **texto natural** ("Gastei 50 reais no mercado")
- [x] Registro por **foto de comprovante** (OCR multimodal via Gemma 4)
- [x] Registro por **PDF de nota fiscal** (extração de texto com pypdf)
- [x] Comando `/resumo` — resumo mensal gerado por IA
- [x] Comando `/categorias` — breakdown por categoria com barras ASCII
- [x] Comando `/grafico` — gráfico de pizza + barras como imagem PNG
- [x] Comando `/historico` — últimos 10 gastos com data e valor
- [x] Comando `/dica` — dica personalizada de economia baseada nos seus dados
- [x] Perguntas em linguagem natural ("Com o que gastei mais?")
- [x] Validação de dados: amount > 0, category restrita a enum definido
- [x] Logging estruturado com latência por operação

---

## Como rodar localmente

### Pré-requisitos

- Docker + Docker Compose instalados
- Token do bot Telegram (crie em [@BotFather](https://t.me/BotFather))
- Ollama instalado (para baixar o modelo)

### 1. Clone o repositório

```bash
git clone https://github.com/gleissonbispo/pydanticai-bot-financas-telegram.git
cd pydanticai-bot-financas-telegram
```

### 2. Configure as variáveis de ambiente

```bash
cp .env.example .env
```

Edite o `.env` e preencha:
```env
TELEGRAM_BOT_TOKEN=seu_token_aqui
POSTGRES_PASSWORD=uma_senha_forte_aqui
```

### 3. Baixe o modelo de IA

```bash
ollama pull gemma4:e2b
```

> Isso baixa ~1.5 GB na primeira vez. O modelo fica salvo em volume Docker.

### 4. Suba todos os serviços

```bash
docker compose up -d
```

O Docker vai subir PostgreSQL, Ollama e o bot. O bot começa a responder automaticamente.

### 5. Verifique se está funcionando

```bash
docker compose logs -f finbot
```

Deve aparecer `{"event": "bot_starting", "mode": "polling"}` nos logs.

### Troubleshooting comum

**Bot não responde:** verifique se `TELEGRAM_BOT_TOKEN` está correto no `.env`.

**Erro de banco:** aguarde o PostgreSQL terminar de inicializar (health check leva ~10s).

**Ollama demora:** a primeira inferência pode demorar 30-60s enquanto o modelo carrega na memória.

---

## Estrutura do Projeto

```
pydanticai-bot-financas-telegram/
│
├── .env.example              # template — copie para .env e preencha
├── docker-compose.yml        # sobe PostgreSQL + Ollama + bot
├── Dockerfile                # imagem do bot Python
├── requirements.txt          # dependências Python
│
├── backend/
│   ├── main.py               # ponto de entrada — registra handlers e inicia o bot
│   ├── config.py             # lê variáveis de ambiente com validação (pydantic-settings)
│   │
│   ├── agents/               # agentes de IA (PydanticAI)
│   │   ├── extraction_agent.py  # extrai dados de texto/foto/PDF → ExtractedExpense
│   │   ├── analysis_agent.py    # responde perguntas usando dados reais do banco
│   │   └── model_provider.py    # configura conexão com Ollama
│   │
│   ├── bot/
│   │   └── handlers.py       # funções que tratam cada tipo de mensagem do Telegram
│   │
│   ├── database/
│   │   ├── models.py         # tabela "expenses" (SQLAlchemy ORM)
│   │   ├── connection.py     # engine assíncrona do PostgreSQL
│   │   └── repository.py     # queries ao banco (salvar, buscar, agrupar)
│   │
│   └── utils/
│       ├── charts.py         # gera gráfico matplotlib como PNG
│       └── logger.py         # configura structlog
│
└── tests/
    ├── test_extraction_agent.py  # testa validadores do schema Pydantic
    └── test_charts.py            # testa geração de PNG
```

---

## Decisões Técnicas e Trade-offs

### Por que PydanticAI e não LangChain?

LangChain é a opção mais conhecida, mas tem muita "mágica implícita" — é difícil entender o que está acontecendo por baixo. O PydanticAI é mais explícito: você define o schema de saída como um modelo Pydantic e o framework cuida da validação. Para aprender como agentes funcionam de verdade, isso é muito melhor.

### Por que Ollama (local) em vez de OpenAI?

Dois motivos: custo zero e privacidade. Dados financeiros nunca saem da rede local. O Gemma 4 E2B (modelo quantizado) roda confortavelmente nos 8 GB do Raspberry Pi 5 com latência de 5-30 segundos por inferência — aceitável para uso pessoal.

### Por que async em todo lugar?

O bot pode receber mensagens de múltiplos usuários ao mesmo tempo. Se uma operação de banco de dados ou chamada ao Ollama fosse síncrona (bloqueante), o bot ficaria travado para todos os outros usuários enquanto processa uma mensagem. Com `asyncio`, `asyncpg` e SQLAlchemy async, o bot fica livre para atender outros enquanto aguarda respostas de I/O.

### Por que polling e não webhook?

Webhook (o Telegram envia mensagens para seu servidor) é mais eficiente, mas exige HTTPS e um domínio público. Para um bot pessoal rodando no Raspberry Pi em rede local, polling (o bot pergunta ao Telegram a cada segundo se tem mensagem nova) é a opção mais simples e funcional.

---

*Projeto construído como portfólio e uso pessoal. Não é código de produção — é um demonstrador de conceitos de AI Engineering com Python.*
