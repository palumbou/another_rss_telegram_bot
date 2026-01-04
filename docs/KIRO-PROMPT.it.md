# Kiro Development Prompt

> **Lingue disponibili**: [English](KIRO-PROMPT.md) | [Italiano (corrente)](KIRO-PROMPT.it.md)

## Prompt Originale

Questo progetto è stato sviluppato utilizzando Kiro AI assistant seguendo la metodologia spec-driven development.

**Richiesta iniziale dell'utente:**
```
Agisci come un senior AWS Serverless Engineer. Devi generare un repository completo e pronto al deploy per un bot Telegram generico (riutilizzabile) che ogni giorno legge una lista di feed RSS/Atom e pubblica nel canale/gruppo Telegram un riassunto in italiano + link.

REQUISITI NON NEGOZIABILI
1) Infrastructure as Code: SOLO AWS CloudFormation (template YAML o JSON). Niente CDK, niente Terraform.
2) Lambda: Python (preferenza 3.12).
3) Deploy "one command" tramite SCRIPT BASH: l'utente non deve creare nulla a mano in AWS.
Deve solo fornire:
- credenziali AWS già disponibili nel terminale (es. AWS_PROFILE o env vars standard AWS)
- TELEGRAM_BOT_TOKEN
- TELEGRAM_CHAT_ID (o target canale/gruppo)
Tutto il resto (bucket artefatti, secret, stack CloudFormation) deve essere creato automaticamente dallo script.

NOME PROGETTO (IMPORTANTE)
- Il nome del progetto deve essere GENERICO e riutilizzabile, perché:
- la lista feed RSS può essere cambiata per qualunque fonte
- il target Telegram può essere cambiato per qualunque canale/gruppo
- Evita nomi legati ad AWS User Group o a "AWS-only". Usa un naming neutro (es. rss-to-telegram-summarizer o simile).

ARCHITETTURA
- EventBridge Scheduler (o EventBridge Rule cron) -> Lambda (Python)
- DynamoDB per deduplicazione/stato con TTL (es. 90 giorni)
- Secrets Manager per TELEGRAM_BOT_TOKEN (creato/aggiornato dallo script)
- CloudWatch Logs + metriche custom
- SQS DLQ per error handling (collegata alla Lambda)
- S3 artifact bucket per caricare lo zip della Lambda (creato dallo script)

FUNZIONAMENTO
- Ogni giorno (default 09:00, timezone Europe/Rome) la Lambda:
1) legge FEED_URLS configurabile (JSON array)
2) scarica RSS/Atom via HTTPS e normalizza item: title, link, published, summary/content (ripulisci HTML)
3) deduplica:
- usa GUID se presente, altrimenti SHA256(feedUrl + link + published)
- se già presente in DynamoDB: skip
- se nuovo: salva in DynamoDB con TTL
4) genera riassunto in italiano:
- preferenza: Amazon Bedrock (boto3 bedrock-runtime) con prompt controllato:
- 1 riga titolo
- 3 bullet in italiano (<= 15 parole ciascuno)
- riga finale "Perché conta:" (<= 20 parole)
- niente invenzioni: se info mancante, sii prudente
- IMPORTANTISSIMO: fallback automatico se Bedrock non disponibile o AccessDenied:
- riassunto estrattivo semplice e stabile (senza dipendenze pesanti)
5) invia su Telegram via Bot API sendMessage (parse_mode HTML consigliato)
- include sempre link originale
- gestisce errori (429/timeouts) con retry + backoff

DEFAULT FEED LIST (AWS)
- Nel progetto deve essere inclusa una lista di feed di default orientata ad AWS (modificabile dall'utente), ad esempio:
- AWS Blog / News Blog (o feed equivalenti disponibili)
- AWS "What's New" (o feed equivalente)
- AWS Security Blog / Security Bulletins (o feed equivalente)
- Eventuali feed ufficiali di announcements se disponibili in RSS/Atom
- La lista deve essere impostata come default nel template (o come parametro di default) e documentata nel README.
- Il progetto però deve restare GENERICO: spiegare chiaramente come sostituire i feed con qualsiasi altro RSS.

SICUREZZA / CONFIG
- TELEGRAM_BOT_TOKEN in Secrets Manager (mai in chiaro nel repo, mai nei log)
- Chat ID/Target e FEED_URLS: come parametri CloudFormation (o SSM), ma gestiti dal deploy script (senza click in console)
- IAM least privilege per:
- dynamodb PutItem/GetItem
- secretsmanager GetSecretValue
- logs CreateLogStream/PutLogEvents
- (opzionale) bedrock:InvokeModel
- Non loggare segreti.

CLOUDFORMATION TEMPLATE
- Fornisci un template CloudFormation completo che crea:
- DynamoDB table con TTL
- Lambda function (code da S3)
- IAM Role + policies minime
- EventBridge Scheduler/Rule giornaliero (timezone Europe/Rome)
- SQS DLQ e configurazione associata
- LogGroup (opzionale con retention)
- Outputs utili (FunctionName, LogGroupName, ecc.)

DEPLOY AUTOMATION (SCRIPT BASH)
- Nel repo deve esserci uno script bash "one shot" (es. scripts/deploy.sh) che:
1) verifica prerequisiti (aws cli, python3, zip)
2) determina account id e region (aws sts get-caller-identity)
3) crea un S3 bucket per artefatti se non esiste (nome univoco con account+region)
4) builda la Lambda (zip con sorgenti e requirements)
5) carica zip su S3 e ottiene S3Key (eventuale version id)
6) crea/aggiorna secret in Secrets Manager con TELEGRAM_BOT_TOKEN (da env var)
7) esegue `aws cloudformation deploy` con parametri:
- TelegramSecretArn
- TelegramChatId
- FeedUrls (JSON)
- Schedule (default giornaliero)
- Timezone (default Europe/Rome)
- BedrockModelId (default configurabile)
8) stampa gli outputs dello stack e indica dove vedere i log in CloudWatch

STRUTTURA REPO
- /infra/template.yaml (CloudFormation)
- /src/ (lambda handler + moduli: rss.py, dedup.py, summarize.py, telegram.py, config.py)
- /scripts/deploy.sh
- /tests/ (pytest: itemId hash, dedup, formatter HTML telegram)
- /prompts (file prompt riassunto)
- /docs/kiro-prompt.md (OBBLIGATORIO): contiene questo prompt integrale
- README.md:
- spiega che il progetto è GENERICO e riutilizzabile (RSS + Telegram configurabili)
- elenca la DEFAULT FEED LIST AWS inclusa
- spiega come cambiare FEED_URLS per usare fonti diverse
- spiega come impostare TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_ID
- fornisce istruzioni copy/paste "deploy in meno di 5 minuti":
export AWS_PROFILE=... (opzionale)
export TELEGRAM_BOT_TOKEN=...
export TELEGRAM_CHAT_ID=...
/scripts/deploy.sh
- include una sezione "Prompt usato / Provenance" che LINKA /docs/kiro-prompt.md e spiega che quello è il prompt usato per generare il progetto.
- GitHub Actions: lint + test (ruff + pytest)

OUTPUT ATTESO
- Genera TUTTI i file del repo con contenuto completo.
- Assicurati che il deploy funzioni senza click in console AWS.
```

## Processo di Sviluppo

Il progetto è stato sviluppato seguendo il workflow Kiro per la creazione di specifiche:

### 1. Fase Requirements
- Analisi dei requisiti funzionali e non funzionali
- Definizione di criteri di accettazione utilizzando pattern EARS
- Identificazione di proprietà di correttezza testabili

### 2. Fase Design  
- Architettura serverless su AWS
- Definizione componenti e interfacce
- Mappatura proprietà di correttezza da requisiti
- Strategia di testing dual (unit + property-based)

### 3. Fase Tasks
- Suddivisione in task implementabili incrementalmente
- Definizione checkpoint per validazione
- Marcatura task opzionali per MVP veloce

## Metodologia Utilizzata

### Spec-Driven Development
- **Requirements First**: Definizione chiara di cosa il sistema deve fare
- **Property-Based Testing**: Validazione di proprietà universali
- **Infrastructure as Code**: Deployment riproducibile
- **Incremental Implementation**: Sviluppo per task discreti

### Principi di Design
- **Genericità**: Sistema riutilizzabile per qualsiasi feed RSS
- **Sicurezza**: Privilegi minimi e protezione informazioni sensibili  
- **Resilienza**: Gestione errori robusta e meccanismi fallback
- **Monitoraggio**: Logging completo e metriche osservabilità

## Tecnologie Scelte

### Core Stack
- **Python 3.12**: Linguaggio principale
- **AWS Lambda**: Compute serverless
- **DynamoDB**: Storage deduplicazione
- **Amazon Bedrock**: Servizio AI per riassunti
- **EventBridge**: Scheduling esecuzione

### Testing Framework
- **pytest**: Framework testing principale
- **hypothesis**: Property-based testing
- **ruff**: Linting e formatting

### Infrastructure
- **CloudFormation**: Infrastructure as Code
- **AWS Secrets Manager**: Gestione sicura credenziali
- **CloudWatch**: Logging e monitoraggio

## Decisioni Architetturali

### 1. Serverless vs Container
**Scelta**: AWS Lambda serverless
**Motivazione**: 
- Costi ottimali per esecuzione giornaliera
- Scaling automatico
- Manutenzione ridotta

### 2. AI Service
**Scelta**: Amazon Bedrock con fallback estrattivo
**Motivazione**:
- Qualità riassunti superiore
- Integrazione nativa AWS
- Fallback per resilienza

### 3. Storage Deduplicazione
**Scelta**: DynamoDB con TTL
**Motivazione**:
- Performance elevate per lookup
- TTL automatico per pulizia
- Integrazione serverless

### 4. Testing Strategy
**Scelta**: Dual testing (unit + property-based)
**Motivazione**:
- Property tests per correttezza universale
- Unit tests per casi specifici
- Coverage completa con approccio complementare

## Proprietà di Correttezza

Il sistema implementa 18 proprietà di correttezza testabili che garantiscono:
- Configurabilità feed personalizzabili
- Sicurezza token e informazioni sensibili
- Resilienza errori e fallback
- Formato consistente riassunti
- Deduplicazione affidabile

## Risultati

### Caratteristiche Implementate
- ✅ Sistema generico RSS-to-Telegram
- ✅ Deployment a comando singolo
- ✅ Riassunti AI in italiano con fallback
- ✅ Deduplicazione DynamoDB con TTL
- ✅ Monitoraggio CloudWatch completo
- ✅ Test suite completa (unit + property-based)
- ✅ Infrastructure as Code
- ✅ Documentazione completa

### Metriche Progetto
- **Linee di codice**: ~2000 LOC
- **Test coverage**: >90%
- **Proprietà testate**: 18
- **Componenti**: 6 moduli principali
- **Tempo sviluppo**: Processo iterativo spec-driven

## Riproducibilità

Questo documento serve come riferimento per:
1. Comprendere le decisioni prese durante lo sviluppo
2. Replicare l'approccio per progetti simili
3. Mantenere traccia del processo di sviluppo AI-assisted
4. Fornire contesto per future modifiche o estensioni

## Note per Sviluppatori Futuri

- Il sistema è progettato per essere generico e riutilizzabile
- La configurazione è completamente esternalizzata
- I test property-based validano comportamenti universali
- L'architettura supporta estensioni future (nuovi formati feed, servizi AI, etc.)
- La documentazione è mantenuta sincronizzata con il codice