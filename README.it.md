# Another RSS Telegram Bot

Un bot serverless generico e riutilizzabile che monitora feed RSS e invia aggiornamenti automatici ai canali Telegram configurati.

> **Lingue disponibili**: [English](README.md) | [Italiano (corrente)](README.it.md)

## Panoramica

Questo progetto è un **esperimento con Kiro AI** per esplorare lo sviluppo assistito dall'AI dalla specifica dei requisiti all'implementazione e testing. Il sistema è completamente generico e deployabile su AWS con automazione dell'infrastruttura.

### Caratteristiche Principali

- **Monitoraggio RSS**: Controllo periodico di feed RSS configurabili
- **Deduplicazione**: Evita contenuti duplicati usando DynamoDB
- **Riassunti AI**: Genera riassunti in italiano usando Amazon Bedrock con fallback
- **Integrazione Telegram**: Invio automatico di messaggi formattati
- **Gestione Errori**: Gestione robusta degli errori con Dead Letter Queue
- **Logging Strutturato**: Sistema di logging completo per debugging
- **Monitoraggio**: Dashboard CloudWatch e metriche personalizzate

## Architettura

Sistema serverless su AWS con i seguenti componenti:

### Componenti AWS
- **Lambda Function**: Logica di elaborazione principale (Python 3.12)
- **DynamoDB**: Storage per deduplicazione con TTL di 90 giorni
- **EventBridge Scheduler**: Esecuzione programmata giornaliera
- **Secrets Manager**: Storage sicuro per token Telegram
- **Amazon Bedrock**: Generazione riassunti AI con Claude 3 Haiku
- **SQS Dead Letter Queue**: Gestione errori e retry
- **CloudWatch**: Logging, metriche e dashboard di monitoraggio
- **CodePipeline**: Build e deployment automatizzati (CI/CD)
- **S3**: Storage artifact e automazione pipeline

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

Il sistema utilizza AWS CodePipeline per il deployment automatizzato. Vedi [docs/infrastructure.it.md](docs/infrastructure.it.md) per le istruzioni complete di setup.

## Configurazione

### Feed RSS Predefiniti

Il sistema include questi feed AWS per default:
- AWS Blog: `https://aws.amazon.com/blogs/aws/feed/`
- AWS What's New: `https://aws.amazon.com/about-aws/whats-new/recent/feed/`
- AWS Security Blog: `https://aws.amazon.com/blogs/security/feed/`
- AWS Compute Blog: `https://aws.amazon.com/blogs/compute/feed/`
- AWS Database Blog: `https://aws.amazon.com/blogs/database/feed/`

### Personalizzazione

Puoi sostituire completamente i feed usando i parametri CloudFormation. Vedi la documentazione per i dettagli.

## Documentazione

- [Guida Infrastruttura](docs/infrastructure.it.md) - Setup completo dell'infrastruttura
- [Processo di Sviluppo Kiro](docs/kiro-prompt.md) - Metodologia di sviluppo assistito da AI
- [Prompts](prompts/README.md) - Template dei prompt AI

## Metodologia di Sviluppo

Questo progetto è stato sviluppato usando lo **spec-driven development** con Kiro AI:

- ✅ Specifica completa dei requisiti usando il formato EARS
- ✅ Design architetturale con proprietà di correttezza
- ✅ Implementazione guidata da property-based testing
- ✅ Test automatizzati con Hypothesis per Python
- ✅ Infrastructure-as-Code con CloudFormation
- ✅ Deployment automatizzato con CodePipeline

## Licenza

Questo progetto è rilasciato sotto licenza MIT.

---

*Sviluppato come esperimento con Kiro AI Assistant*
