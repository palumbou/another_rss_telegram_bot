# Another RSS Telegram Bot

Un bot serverless generico e riutilizzabile che monitora feed RSS e invia aggiornamenti automatici ai canali Telegram configurati.

> **Lingue disponibili**: [English](README.md) | [Italiano (corrente)](README.it.md)

## Panoramica

Questo progetto è un **esperimento con Kiro AI** per esplorare lo sviluppo assistito dall'AI dalla specifica dei requisiti all'implementazione e testing. Il sistema è completamente generico e deployabile su AWS con automazione dell'infrastruttura.

### Caratteristiche Principali

- **Monitoraggio RSS**: Controllo periodico di feed RSS configurabili
- **Filtro 24 Ore**: Elabora solo item pubblicati nelle ultime 24 ore
- **Deduplicazione**: Evita contenuti duplicati usando DynamoDB
- **Riassunti AI**: Genera riassunti in italiano usando Amazon Bedrock Nova Micro con fallback
- **Integrazione Telegram**: Invio automatico di messaggi formattati
- **Gestione Errori**: Gestione robusta degli errori con Dead Letter Queue
- **Logging Strutturato**: Sistema di logging completo per debugging
- **Monitoraggio**: Dashboard CloudWatch e metriche personalizzate
- **Pipeline CI/CD**: Deployment automatizzato con AWS CodePipeline e S3

### Modelli AI

Il bot supporta tre modelli Amazon Bedrock per generare riassunti in italiano. Puoi scegliere quale modello utilizzare al momento del deployment:

**Default: Amazon Nova Micro** (`amazon.nova-micro-v1:0`)
- Economico per riassunti ad alto volume
- Tempi di risposta rapidi (< 1 secondo per riassunto)
- Buona qualità nelle traduzioni italiane
- Disponibile tramite profilo di inferenza cross-region
- Deploy con: `./scripts/deploy.sh -m nova-micro`

**Premium: Mistral Large** (selezione regionale intelligente)
- Eccellente traduzione multilingua (EN→IT, FR, ES, DE)
- Reasoning e comprensione del contesto superiori
- Usa Mistral Large 3 (675B MoE) in 6 regioni, Large 24.02 nelle altre
- Ideale per deployment focalizzati sulla qualità
- Costo: ~$0.78/mese per 150 articoli
- Deploy con: `./scripts/deploy.sh -m mistral-large`

**Alternativa: Llama 3.2 3B Instruct** (`us.meta.llama3-2-3b-instruct-v1:0`)
- Eccellente per riassunti e traduzioni
- Migliore nel seguire le istruzioni
- Qualità italiana superiore
- Costo leggermente più alto ma risultati migliori
- Deploy con: `./scripts/deploy.sh -m llama-3b`

Per un confronto dettagliato dei modelli, opzioni di configurazione e come scegliere il modello giusto per il tuo caso d'uso, vedi la [Guida Modelli AI](docs/MODELS.it.md).

### Esempio di Output

Ecco come appaiono i messaggi del bot su Telegram:

![Esempio Messaggi Telegram](docs/images/telegram-messages-example.png)

Ogni messaggio include:
- Un titolo conciso in italiano
- Tre punti elenco con le informazioni chiave
- Una sezione "Perché conta:" che spiega la rilevanza
- Link alla fonte dell'articolo originale

## Architettura

Sistema serverless su AWS con i seguenti componenti:

### Componenti AWS
- **Lambda Function**: Logica di elaborazione principale (Python 3.12)
- **DynamoDB**: Storage per deduplicazione con TTL di 90 giorni
- **EventBridge Scheduler**: Esecuzione programmata giornaliera
- **Secrets Manager**: Storage sicuro per token Telegram
- **Amazon Bedrock**: Generazione riassunti AI con modello Nova Micro
- **SQS Dead Letter Queue**: Gestione errori e retry
- **CloudWatch**: Logging, metriche e dashboard di monitoraggio
- **CodePipeline**: Build e deployment automatizzati (CI/CD)
- **S3**: Storage artifact e automazione pipeline

### Gestione dei Costi
Tutte le risorse AWS sono taggate con un tag `CostCenter` (impostato al nome del bot) per il tracciamento e l'allocazione dei costi. Questo permette:
- Analisi dei costi per istanza del bot
- Alert di budget per deployment
- Raggruppamento risorse in AWS Cost Explorer

### Componenti Codice
- `src/lambda_handler.py`: Entry point principale e orchestrazione
- `src/rss.py`: Gestione dei feed RSS con feedparser
- `src/telegram.py`: Integrazione con Telegram Bot API
- `src/summarize.py`: Generazione riassunti con Bedrock e fallback
- `src/dedup.py`: Sistema di deduplicazione con DynamoDB
- `src/config.py`: Gestione configurazione e variabili ambiente
- `src/models.py`: Modelli dati e strutture

## Avvio Rapido

### Prerequisiti

- AWS CLI configurato con credenziali appropriate
- Python 3.12 o compatibile
- Bot creato tramite @BotFather di Telegram
- Repository GitHub (per integrazione CodePipeline)

### Deployment

Il sistema utilizza uno stack CloudFormation unificato con AWS CodePipeline per il deployment automatizzato. Un singolo stack contiene tutte le risorse (Lambda, DynamoDB, EventBridge, CodePipeline, CodeBuild, ecc.). Vedi [docs/INFRASTRUCTURE.it.md](docs/INFRASTRUCTURE.it.md) per le istruzioni complete di setup.

## Configurazione

### Feed RSS

Il bot legge i feed RSS da un file `feeds.json`. Puoi personalizzare quali feed monitorare modificando questo file o fornendo il tuo.

**I feed predefiniti** includono contenuti relativi ad AWS. Vedi [FEEDS.IT.md](FEEDS.IT.md) per la documentazione completa su:
- Formato del file feed
- Come personalizzare i feed
- Esempi per diversi casi d'uso

### Feed RSS Predefiniti

Il `feeds.json` predefinito include questi feed AWS:
- AWS Blog: `https://aws.amazon.com/blogs/aws/feed/`
- AWS What's New: `https://aws.amazon.com/about-aws/whats-new/recent/feed/`
- AWS Security Blog: `https://aws.amazon.com/blogs/security/feed/`
- AWS Compute Blog: `https://aws.amazon.com/blogs/compute/feed/`
- AWS Database Blog: `https://aws.amazon.com/blogs/database/feed/`

### Personalizzazione

Puoi personalizzare i feed:
1. Modificando il file `feeds.json` nella root del progetto
2. Fornendo un file feeds personalizzato durante il deployment

Vedi [FEEDS.IT.md](FEEDS.it.md) per istruzioni dettagliate ed esempi.

## Avvio Rapido

### Prerequisiti

- **Account AWS**: Account AWS attivo con permessi appropriati
- **AWS CLI**: Installato e configurato con le tue credenziali
  ```bash
  # Configura AWS CLI con le tue credenziali
  aws configure
  # Oppure usa la variabile ambiente AWS_PROFILE
  export AWS_PROFILE=nome-tuo-profilo
  ```
- **Python 3.12** o compatibile
- **Bot creato** tramite @BotFather di Telegram
- **Accesso Bedrock**: Assicurati di avere accesso ai modelli Amazon Bedrock nella tua regione

### Deployment

```bash
# Deployment iniziale con modello predefinito (Nova Micro)
./scripts/deploy.sh \
  --telegram-token "TUO_BOT_TOKEN" \
  --chat-id "TUO_CHAT_ID"

# Deploy con Llama 3.2 3B per qualità superiore
./scripts/deploy.sh \
  --telegram-token "TUO_BOT_TOKEN" \
  --chat-id "TUO_CHAT_ID" \
  --model llama-3b

# Oppure con file feeds personalizzato
./scripts/deploy.sh \
  --telegram-token "TUO_BOT_TOKEN" \
  --chat-id "TUO_CHAT_ID" \
  --feeds-file /percorso/al/mio-feeds.json

# Salta prompt di conferma
./scripts/deploy.sh \
  --telegram-token "TUO_BOT_TOKEN" \
  --chat-id "TUO_CHAT_ID" \
  --yes
```

**Selezione Modello:**
- Ometti `--model` o usa `--model nova-micro` per deployment economico (default)
- Usa `--model llama-3b` per riassunti in italiano di qualità superiore

Per istruzioni complete di deployment e confronto dei modelli, vedi [docs/INFRASTRUCTURE.it.md](docs/INFRASTRUCTURE.it.md) e [docs/MODELS.it.md](docs/MODELS.it.md).

## Documentazione

- [Configurazione Feed RSS](FEEDS.it.md) - Come configurare e personalizzare i feed RSS
- [Guida Infrastruttura](docs/INFRASTRUCTURE.it.md) - Setup completo dell'infrastruttura
- [Guida Modelli AI](docs/MODELS.it.md) - Confronto modelli, selezione e configurazione
- [Processo di Sviluppo Kiro](docs/KIRO-PROMPT.it.md) - Metodologia di sviluppo assistito da AI
- [Prompts](prompts/README.it.md) - Template dei prompt AI
- [Script di Deployment](scripts/README.it.md) - Documentazione automazione deployment

## Metodologia di Sviluppo

Questo progetto è stato sviluppato usando lo **spec-driven development** con Kiro AI:

- ✅ Specifica completa dei requisiti usando il formato EARS
- ✅ Design architetturale con proprietà di correttezza
- ✅ Implementazione guidata da property-based testing
- ✅ Test automatizzati con Hypothesis per Python
- ✅ Infrastructure-as-Code con CloudFormation
- ✅ Deployment automatizzato con CodePipeline

## Licenza

Questo progetto è rilasciato sotto [Licenza Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)](LICENSE).

Sei libero di:
- Usare, copiare e modificare questo software per scopi non commerciali
- Condividere e distribuire il software

Alle seguenti condizioni:
- Attribuzione: Devi dare credito appropriato
- Non Commerciale: Non puoi usare il materiale per scopi commerciali

Per uso commerciale, contatta l'autore.

---

*Sviluppato come esperimento con Kiro AI Assistant*
