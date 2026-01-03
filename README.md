# Another RSS Telegram Bot

## Descrizione

Questo è un bot Telegram serverless che monitora feed RSS e invia aggiornamenti automatici ai canali configurati. Il sistema è completamente generico e riutilizzabile, deployabile con un singolo comando su AWS.

## Esperimento Kiro

**Questo progetto è un esperimento per testare le capacità di Kiro**, l'assistente AI per sviluppatori. L'obiettivo è esplorare come Kiro può assistere nello sviluppo di applicazioni complete, dalla specifica dei requisiti all'implementazione e testing.

### Caratteristiche del progetto sviluppate con Kiro:

- ✅ Specifica completa dei requisiti usando il formato EARS
- ✅ Design architetturale con proprietà di correttezza
- ✅ Implementazione guidata da property-based testing
- ✅ Test automatizzati con Hypothesis per Python
- ✅ Infrastructure-as-Code con CloudFormation
- ✅ Deployment automatizzato con script bash
- ✅ Sistema di cleanup completo

## Funzionalità

- **Monitoraggio RSS**: Controllo periodico di feed RSS configurabili
- **Deduplicazione**: Evita l'invio di contenuti duplicati usando DynamoDB
- **Riassunto automatico**: Genera riassunti in italiano usando Amazon Bedrock con fallback
- **Integrazione Telegram**: Invio automatico di messaggi formattati ai canali
- **Gestione errori**: Handling robusto degli errori con Dead Letter Queue
- **Logging strutturato**: Sistema di logging completo per debugging
- **Monitoraggio**: Dashboard CloudWatch e metriche personalizzate

## Architettura

Sistema serverless su AWS con i seguenti componenti:

### Componenti AWS:
- **Lambda Function**: Logica di elaborazione principale (Python 3.12)
- **DynamoDB**: Storage per deduplicazione con TTL di 90 giorni
- **EventBridge Scheduler**: Esecuzione giornaliera programmata
- **Secrets Manager**: Storage sicuro per token Telegram
- **Amazon Bedrock**: Generazione riassunti AI con Claude 3 Haiku
- **SQS Dead Letter Queue**: Gestione errori e retry
- **CloudWatch**: Logging, metriche e dashboard di monitoraggio

### Componenti Codice:
- `src/lambda_handler.py`: Entry point principale e orchestrazione
- `src/rss.py`: Gestione dei feed RSS con feedparser
- `src/telegram.py`: Integrazione con Telegram Bot API
- `src/summarize.py`: Generazione riassunti con Bedrock e fallback
- `src/dedup.py`: Sistema di deduplicazione con DynamoDB
- `src/config.py`: Gestione configurazione e variabili ambiente
- `src/models.py`: Modelli dati e strutture

## Quick Start

### 1. Prerequisiti

- AWS CLI configurato con credenziali appropriate
- Python 3.12 o compatibile
- Comando `zip` disponibile
- Bot Telegram creato tramite @BotFather

### 2. Deployment

```bash
# Deployment base con feed AWS di default
./scripts/deploy.sh \
  --telegram-token "YOUR_BOT_TOKEN" \
  --chat-id "YOUR_CHAT_ID" \
  --region "eu-west-1"

# Deployment con feed personalizzati
./scripts/deploy.sh \
  --telegram-token "YOUR_BOT_TOKEN" \
  --chat-id "YOUR_CHAT_ID" \
  --region "eu-west-1" \
  --feeds "https://example.com/feed1.xml,https://example.com/feed2.xml"

# Dry run per vedere cosa verrebbe deployato
./scripts/deploy.sh \
  --telegram-token "YOUR_BOT_TOKEN" \
  --chat-id "YOUR_CHAT_ID" \
  --dry-run
```

### 3. Cleanup

```bash
# Rimuovi tutte le risorse AWS create
./scripts/deploy.sh --cleanup --region "eu-west-1"

# Dry run del cleanup
./scripts/deploy.sh --cleanup --region "eu-west-1" --dry-run
```

## Configurazione

### Feed RSS di Default

Il sistema include questi feed AWS per default:
- AWS Blog: `https://aws.amazon.com/blogs/aws/feed/`
- AWS What's New: `https://aws.amazon.com/about-aws/whats-new/recent/feed/`
- AWS Security Blog: `https://aws.amazon.com/blogs/security/feed/`
- AWS Compute Blog: `https://aws.amazon.com/blogs/compute/feed/`
- AWS Database Blog: `https://aws.amazon.com/blogs/database/feed/`

### Personalizzazione

Puoi sostituire completamente i feed usando il parametro `--feeds`:

```bash
./scripts/deploy.sh \
  --telegram-token "YOUR_TOKEN" \
  --chat-id "YOUR_CHAT_ID" \
  --feeds "https://your-site.com/feed.xml,https://another-site.com/rss.xml"
```

### Parametri Avanzati

```bash
./scripts/deploy.sh \
  --stack-name "my-custom-bot" \
  --bot-name "my-rss-bot" \
  --schedule "cron(0 8 * * ? *)" \
  --timezone "America/New_York" \
  --telegram-token "YOUR_TOKEN" \
  --chat-id "YOUR_CHAT_ID"
```

## Testing

Il progetto utilizza un approccio dual-testing:

- **Unit tests**: Test specifici per casi d'uso e edge cases
- **Property-based tests**: Test con Hypothesis per validare proprietà universali

```bash
# Esegui tutti i test
pytest

# Esegui solo i test unitari
pytest -m unit

# Esegui solo i property-based tests
pytest -m property

# Esegui solo i property tests
pytest -k "properties"

# Esegui solo i unit tests  
pytest -k "unit"
```

## Deployment

Il progetto è configurato per il deployment su AWS Lambda usando SAM (Serverless Application Model).

```bash
# Build
sam build

# Deploy
sam deploy --guided
```

## Configurazione

Il bot richiede le seguenti variabili d'ambiente:

- `TELEGRAM_BOT_TOKEN`: Token del bot Telegram
- `TELEGRAM_CHAT_ID`: ID del canale/chat di destinazione
- `RSS_FEEDS`: Lista dei feed RSS da monitorare (JSON)
- `BEDROCK_MODEL_ID`: ID del modello AWS Bedrock per i riassunti

## Licenza

Questo progetto è rilasciato sotto licenza MIT.

---

*Sviluppato come esperimento con Kiro AI Assistant*