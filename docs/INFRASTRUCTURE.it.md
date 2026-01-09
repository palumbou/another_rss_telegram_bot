# Guida Infrastruttura

> **Lingue disponibili**: [English](INFRASTRUCTURE.md) | [Italiano (corrente)](INFRASTRUCTURE.it.md)

## Panoramica

Questo documento descrive l'infrastruttura AWS completa per Another RSS Telegram Bot, inclusa la pipeline CI/CD con CodePipeline.

## Diagramma Architettura

```
┌───────────────────────────────────────────────────┐
│              Script Deploy                        │
│         (carica sorgente su S3)                   │
└──────────────────┬────────────────────────────────┘
                   │
                   ▼
┌───────────────────────────────────────────────────┐
│           Bucket S3 Artifact                      │
│         (source/source.zip)                       │
└──────────────────┬────────────────────────────────┘
                   │ (trigger evento S3)
                   ▼
┌───────────────────────────────────────────────────┐
│           AWS CodePipeline                        │
├───────────────────────────────────────────────────┤
│  Source Stage  →  Build Stage  →  Deploy Stage    │
│     (S3)          (CodeBuild)     (CloudFormation)│
└──────────────────────┬────────────────────────────┘
                       │
                       ▼
┌───────────────────────────────────────────────────┐
│         Infrastruttura Applicazione               │
├───────────────────────────────────────────────────┤
│  EventBridge  →  Lambda  →  DynamoDB              │
│                    ↓                              │
│              Bedrock + Telegram                   │
│                    ↓                              │
│              CloudWatch + SQS DLQ                 │
└───────────────────────────────────────────────────┘
```

## Componenti

### Pipeline CI/CD

#### 1. Bucket S3 Artifact
- **Scopo**: Memorizza artifact della pipeline e package Lambda
- **Caratteristiche**:
  - Versioning abilitato
  - Crittografia server-side (AES256)
  - Policy di lifecycle per pulizia
- **Naming**: `{bot-name}-artifacts-{account-id}-{region}`

#### 2. CodePipeline
- **Fasi**:
  1. **Source**: Preleva codice da repository GitHub
  2. **Build**: Pacchettizza funzione Lambda con dipendenze
  3. **Deploy**: Aggiorna stack CloudFormation

#### 3. Progetto CodeBuild
- **Runtime**: Python 3.12
- **Processo Build**:
  1. Installa dipendenze da `requirements.txt`
  2. Pacchettizza codice sorgente
  3. Crea artifact di deployment
  4. Upload su S3
- **Build Spec**: Definito in `buildspec.yml`

### Infrastruttura Applicazione

#### 1. Funzione Lambda
- **Runtime**: Python 3.12
- **Memoria**: 512 MB (configurabile)
- **Timeout**: 300 secondi (configurabile)
- **Trigger**: EventBridge Scheduler (giornaliero)
- **Sorgente Codice**: Bucket S3 (aggiornato dalla pipeline)

#### 2. Tabella DynamoDB
- **Scopo**: Storage deduplicazione
- **Chiave**: `item_id` (String)
- **TTL**: 90 giorni (configurabile)
- **Billing**: Pay-per-request

#### 3. EventBridge Scheduler
- **Schedule Default**: Giornaliero alle 9:00
- **Timezone**: Europe/Rome (configurabile)
- **Target**: Funzione Lambda

#### 4. Secrets Manager
- **Secret**: Token bot Telegram
- **Accesso**: Solo funzione Lambda
- **Rotazione**: Manuale (automatizzabile)

#### 5. SQS Dead Letter Queue
- **Scopo**: Gestione esecuzioni fallite
- **Retention**: 14 giorni
- **Visibility Timeout**: 60 secondi

#### 6. CloudWatch
- **Log Group**: `/aws/lambda/{bot-name}-processor`
- **Retention**: 30 giorni (configurabile)
- **Dashboard**: Dashboard monitoraggio personalizzata
- **Metriche**: Metriche applicazione personalizzate

## Deployment

### Setup Iniziale

1. **Prepara Parametri CloudFormation**
   ```yaml
   BotName: another-rss-telegram-bot
   TelegramBotToken: "TUO_BOT_TOKEN"
   TelegramChatId: "TUO_CHAT_ID"
   RSSFeedUrls: "https://aws.amazon.com/blogs/aws/feed/,..."
   ```

2. **Deploy Stack Pipeline**
   ```bash
   ./scripts/deploy.sh \
     --telegram-token "TUO_BOT_TOKEN" \
     --chat-id "TUO_CHAT_ID" \
     --region eu-west-1
   ```

   Questo:
   - Crea bucket S3 per artifact
   - Deploya infrastruttura CodePipeline
   - Pacchettizza e carica codice sorgente
   - Triggera build e deployment automatici

### Aggiornamenti Automatici

Una volta configurata la pipeline:

1. **Aggiorna Codice**: Modifica il tuo codice
2. **Deploy Aggiornamento**:
   ```bash
   ./scripts/deploy.sh --update-code --region eu-west-1
   ```
3. **Processo Automatico**: 
   - Script pacchettizza e carica sorgente su S3
   - Evento S3 triggera CodePipeline
   - CodeBuild pacchettizza l'applicazione
   - CloudFormation aggiorna lo stack
4. **Verifica**: Controlla log CloudWatch per deployment riuscito

### Deployment Manuale

Per test o aggiornamenti di emergenza:

```bash
# Build locale
python3 -m pip install -r requirements.txt -t build/
cp -r src build/
cd build && zip -r ../lambda.zip . && cd ..

# Upload su S3
aws s3 cp lambda.zip s3://{bucket-name}/lambda-packages/

# Aggiorna funzione Lambda
aws lambda update-function-code \
  --function-name {bot-name}-processor \
  --s3-bucket {bucket-name} \
  --s3-key lambda-packages/lambda.zip
```

## Configurazione

### Variabili Ambiente

La funzione Lambda usa queste variabili (gestite da CloudFormation):

- `TELEGRAM_SECRET_NAME`: Nome secret Secrets Manager
- `TELEGRAM_CHAT_ID`: ID chat/canale target
- `DYNAMODB_TABLE`: Nome tabella DynamoDB
- `RSS_FEED_URLS`: URL feed separati da virgola
- `CURRENT_AWS_REGION`: Regione AWS
- `LOG_LEVEL`: Livello logging (INFO, DEBUG, ERROR)

### Parametri CloudFormation

| Parametro | Descrizione | Default |
|-----------|-------------|---------|
| `BotName` | Prefisso naming risorse | `another-rss-telegram-bot` |
| `TelegramBotToken` | Token bot (in Secrets Manager) | Richiesto |
| `TelegramChatId` | ID chat target | Richiesto |
| `RSSFeedUrls` | URL feed separati da virgola | Feed AWS |
| `ScheduleExpression` | Espressione cron | `cron(0 9 * * ? *)` |
| `ScheduleTimezone` | Timezone | `Europe/Rome` |

## Monitoraggio

### Dashboard CloudWatch

Accedi alla dashboard su:
```
https://{region}.console.aws.amazon.com/cloudwatch/home?region={region}#dashboards:name={bot-name}-monitoring
```

**Widget**:
- Tassi successo/fallimento esecuzioni
- Metriche elaborazione (feed, item, messaggi)
- Conteggi errori e statistiche deduplicazione
- Log errori recenti

### Metriche Personalizzate

L'applicazione pubblica queste metriche su CloudWatch:

- `ExecutionSuccess` / `ExecutionFailure`
- `FeedsProcessed`
- `ItemsFound`
- `ItemsSummarized`
- `MessagesSent`
- `ItemsDeduplicated`
- `Errors`

### Allarmi

Considera di configurare Allarmi CloudWatch per:
- Fallimenti esecuzione Lambda
- Conteggio messaggi DLQ
- Soglia tasso errori
- Durata Lambda che si avvicina al timeout

## Sicurezza

### Ruoli IAM

#### Ruolo Esecuzione Lambda
- **DynamoDB**: GetItem, PutItem su tabella dedup
- **Secrets Manager**: GetSecretValue per token bot
- **Bedrock**: InvokeModel per riassunti
- **CloudWatch**: PutMetricData, CreateLogStream, PutLogEvents
- **SQS**: SendMessage a DLQ

#### Ruolo Servizio CodeBuild
- **S3**: GetObject, PutObject su bucket artifact
- **CloudWatch**: CreateLogGroup, CreateLogStream, PutLogEvents
- **ECR**: Pull immagini base (se necessario)

#### Ruolo Servizio CodePipeline
- **S3**: GetObject, PutObject su bucket artifact
- **CodeBuild**: StartBuild, BatchGetBuilds
- **CloudFormation**: CreateStack, UpdateStack, DescribeStacks
- **IAM**: PassRole per CloudFormation

### Best Practice

1. **Secrets**: Non committare mai token o credenziali
2. **Least Privilege**: I ruoli IAM hanno i permessi minimi richiesti
3. **Crittografia**: I bucket S3 usano crittografia server-side
4. **Logging**: Nessun dato sensibile nei log CloudWatch
5. **Network**: Lambda esegue in VPC gestito da AWS (nessun VPC custom necessario)

## Ottimizzazione Costi

### Costi Mensili Stimati

Per esecuzione giornaliera (30 esecuzioni/mese):

- **Lambda**: ~$0.20 (128MB, 30s esecuzione media)
- **DynamoDB**: ~$0.25 (on-demand, traffico basso)
- **EventBridge**: $0.00 (free tier)
- **Secrets Manager**: $0.40 (1 secret)
- **CloudWatch**: ~$0.50 (log + metriche)
- **CodePipeline**: $1.00 (1 pipeline attiva)
- **CodeBuild**: ~$0.10 (30 build, 1 min ciascuna)
- **S3**: ~$0.10 (storage artifact)

**Totale**: ~$2.55/mese

### Suggerimenti Riduzione Costi

1. Riduci memoria Lambda se possibile
2. Regola periodo retention log
3. Usa policy lifecycle S3 per vecchi artifact
4. Considera capacità riservata per DynamoDB se il traffico aumenta
5. Disabilita CodePipeline se sufficienti deployment manuali

## Troubleshooting

### Fallimenti Pipeline

**Source Stage**:
- Verifica che la connessione GitHub sia attiva
- Controlla nomi repository e branch
- Assicurati che il webhook sia configurato

**Build Stage**:
- Rivedi log CodeBuild in CloudWatch
- Verifica sintassi `buildspec.yml`
- Controlla compatibilità dipendenze Python

**Deploy Stage**:
- Rivedi eventi CloudFormation
- Controlla permessi IAM
- Verifica valori parametri

### Fallimenti Esecuzione Lambda

1. **Controlla Log CloudWatch**:
   ```bash
   aws logs tail /aws/lambda/{bot-name}-processor --follow
   ```

2. **Controlla Messaggi DLQ**:
   ```bash
   aws sqs receive-message \
     --queue-url {dlq-url} \
     --max-number-of-messages 10
   ```

3. **Test Manuale**:
   ```bash
   aws lambda invoke \
     --function-name {bot-name}-processor \
     --payload '{}' \
     response.json
   ```

### Problemi Comuni

| Problema | Causa | Soluzione |
|----------|-------|-----------|
| AccessDenied a Bedrock | Regione non abilitata | Abilita Bedrock nella regione o usa fallback |
| Timeout API Telegram | Problemi di rete | Controlla logica retry, aumenta timeout |
| Throttling DynamoDB | Traffico elevato | Passa a capacità provisionata |
| Timeout Lambda | Feed lenti | Aumenta timeout, ottimizza codice |

## Manutenzione

### Task Regolari

- **Settimanale**: Rivedi log CloudWatch per errori
- **Mensile**: Controlla DLQ per messaggi falliti
- **Trimestrale**: Rivedi e aggiorna dipendenze
- **Annuale**: Ruota token bot Telegram

### Aggiornamenti

1. **Modifiche Codice**: Push su GitHub (deployment automatico)
2. **Modifiche Infrastruttura**: Aggiorna template CloudFormation
3. **Modifiche Configurazione**: Aggiorna parametri stack
4. **Aggiornamenti Dipendenze**: Aggiorna `requirements.txt` e push

## Pulizia

Per rimuovere tutte le risorse:

```bash
# Elimina stack applicazione
aws cloudformation delete-stack --stack-name {stack-name}

# Elimina stack pipeline
aws cloudformation delete-stack --stack-name rss-bot-pipeline

# Svuota ed elimina bucket S3
aws s3 rm s3://{bucket-name} --recursive
aws s3 rb s3://{bucket-name}

# Elimina secrets
aws secretsmanager delete-secret \
  --secret-id {secret-name} \
  --recovery-window-in-days 7
```