# Piano di Implementazione: Another RSS Telegram Bot

## Panoramica

Implementazione di un sistema serverless generico RSS-to-Telegram utilizzando Python 3.12, AWS Lambda, DynamoDB, EventBridge Scheduler e Amazon Bedrock. Il sistema è progettato per essere completamente deployabile con un singolo comando bash.

## Task

- [x] 1. Configurazione struttura progetto e dipendenze core
  - Creare struttura directory del progetto
  - Configurare requirements.txt con dipendenze Python
  - Creare file di configurazione base
  - _Requisiti: 1.3, 3.1_

- [ ] 2. Implementazione Feed Processor
  - [x] 2.1 Creare modulo RSS parser con feedparser
    - Implementare FeedProcessor class con metodi fetch_feeds e parse_feed
    - Gestire download HTTPS e parsing RSS/Atom
    - _Requisiti: 4.1, 4.2, 4.4_

  - [x] 2.2 Scrivere test property per Feed Processor
    - **Proprietà 3: Download HTTPS Obbligatorio**
    - **Valida: Requisiti 4.1**

  - [x] 2.3 Scrivere test property per estrazione campi
    - **Proprietà 4: Estrazione Campi Completa**
    - **Valida: Requisiti 4.2**

  - [x] 2.4 Implementare pulizia HTML e normalizzazione
    - Aggiungere metodo clean_html_content per rimuovere tag HTML
    - Implementare normalize_item per struttura dati consistente
    - _Requisiti: 4.3_

  - [x] 2.5 Scrivere test property per pulizia HTML
    - **Proprietà 5: Pulizia HTML**
    - **Valida: Requisiti 4.3**

  - [x] 2.6 Scrivere test unitari per formati feed specifici
    - Test parsing RSS 2.0 con esempio specifico
    - Test parsing Atom 1.0 con esempio specifico
    - _Requisiti: 4.4_

- [x] 3. Implementazione Deduplicator
  - [x] 3.1 Creare modulo deduplicazione con DynamoDB
    - Implementare Deduplicator class con generate_item_id
    - Configurare connessione DynamoDB con boto3
    - _Requisiti: 5.1, 5.2_

  - [x] 3.2 Scrivere test property per generazione ID con GUID
    - **Proprietà 7: Utilizzo GUID per Deduplicazione**
    - **Valida: Requisiti 5.1**

  - [x] 3.3 Scrivere test property per hash fallback
    - **Proprietà 8: Hash Fallback per Deduplicazione**
    - **Valida: Requisiti 5.2**

  - [x] 3.4 Implementare controllo duplicati e storage
    - Aggiungere metodi is_duplicate e store_item
    - Configurare TTL di 90 giorni per elementi DynamoDB
    - _Requisiti: 5.3, 5.4, 5.5_

  - [x] 3.5 Scrivere test property per prevenzione duplicati
    - **Proprietà 9: Prevenzione Duplicati**
    - **Valida: Requisiti 5.3, 5.4**

  - [x] 3.6 Scrivere test property per storage con TTL
    - **Proprietà 10: Storage con TTL**
    - **Valida: Requisiti 5.5**

- [x] 4. Checkpoint - Verifica elaborazione feed base
  - Assicurarsi che tutti i test passino, chiedere all'utente se sorgono domande.

- [x] 5. Implementazione Summarizer con Bedrock
  - [x] 5.1 Creare modulo riassunto con Amazon Bedrock
    - Implementare Summarizer class con bedrock_summarize
    - Configurare client Bedrock con Claude 3 Haiku
    - Implementare template prompt in italiano
    - _Requisiti: 6.1, 6.2_

  - [x] 5.2 Scrivere test property per formato riassunto
    - **Proprietà 11: Formato Riassunto Consistente**
    - **Valida: Requisiti 6.2**

  - [x] 5.3 Implementare fallback estrattivo
    - Aggiungere metodo fallback_summarize senza dipendenze esterne
    - Implementare ranking frasi per riassunto estrattivo
    - _Requisiti: 6.3_

  - [x] 5.4 Scrivere test property per fallback Bedrock
    - **Proprietà 12: Fallback Summarizer**
    - **Valida: Requisiti 6.3**

  - [x] 5.5 Scrivere test unitari per riassunto specifico
    - Test con contenuto italiano specifico
    - Test gestione errori Bedrock
    - _Requisiti: 6.1, 6.3_

- [x] 6. Implementazione Telegram Publisher
  - [x] 6.1 Creare modulo pubblicazione Telegram
    - Implementare TelegramPublisher class con send_message
    - Configurare Bot API con parsing HTML
    - _Requisiti: 7.1, 7.2_

  - [x] 6.2 Scrivere test property per inclusione link
    - **Proprietà 13: Inclusione Link Originale**
    - **Valida: Requisiti 7.2**

  - [x] 6.3 Implementare gestione rate limiting e retry
    - Aggiungere handle_rate_limit con backoff esponenziale
    - Gestire errori 429 con retry automatico
    - _Requisiti: 7.3, 7.4_

  - [x] 6.4 Scrivere test property per retry rate limiting
    - **Proprietà 14: Retry Rate Limiting**
    - **Valida: Requisiti 7.3**

  - [x] 6.5 Scrivere test property per resilienza errori
    - **Proprietà 15: Resilienza Errori Telegram**
    - **Valida: Requisiti 7.4**

  - [x] 6.6 Scrivere test unitari per formattazione messaggio
    - Test formato HTML specifico
    - Test gestione caratteri speciali
    - _Requisiti: 7.1, 7.2_

- [-] 7. Implementazione Configuration Manager
  - [x] 7.1 Creare modulo gestione configurazione
    - Implementare Config class per variabili ambiente
    - Configurare feed AWS di default
    - _Requisiti: 1.1, 1.2, 11.1, 11.2, 11.3_

  - [x] 7.2 Scrivere test property per configurazione feed personalizzabili
    - **Proprietà 1: Configurazione Feed Personalizzabili**
    - **Valida: Requisiti 1.1, 11.5**

  - [x] 7.3 Scrivere test property per chat ID configurabile
    - **Proprietà 2: Utilizzo Chat ID Configurabile**
    - **Valida: Requisiti 1.2**

  - [x] 7.4 Scrivere test unitari per feed AWS di default
    - Verificare presenza URL AWS Blog, What's New, Security
    - _Requisiti: 11.1, 11.2, 11.3_

- [-] 8. Implementazione Lambda Handler principale
  - [x] 8.1 Creare handler Lambda con orchestrazione componenti
    - Implementare lambda_handler con flusso completo
    - Integrare tutti i componenti (Feed → Dedup → Summary → Telegram)
    - _Requisiti: 4.5, 10.4_

  - [x] 8.2 Scrivere test property per resilienza errori feed
    - **Proprietà 6: Resilienza Errori Feed**
    - **Valida: Requisiti 4.5, 10.4**

  - [x] 8.3 Implementare gestione Secrets Manager
    - Aggiungere recupero sicuro token Telegram
    - Configurare client AWS Secrets Manager
    - _Requisiti: 9.1, 9.2_

  - [x] 8.4 Scrivere test property per sicurezza token
    - **Proprietà 16: Sicurezza Token**
    - **Valida: Requisiti 9.1**

  - [x] 8.5 Scrivere test property per protezione informazioni sensibili
    - **Proprietà 17: Protezione Informazioni Sensibili**
    - **Valida: Requisiti 9.2**

- [x] 9. Implementazione logging e monitoraggio
  - [x] 9.1 Configurare logging strutturato
    - Implementare logging per tutti i componenti
    - Aggiungere timestamp inizio/fine esecuzione
    - _Requisiti: 8.4, 10.3_

  - [x] 9.2 Scrivere test property per logging completo
    - **Proprietà 18: Logging Completo**
    - **Valida: Requisiti 8.4, 10.3**

  - [x] 9.3 Implementare metriche CloudWatch personalizzate
    - Aggiungere metriche per successi/fallimenti
    - Configurare invio metriche custom
    - _Requisiti: 10.2_

  - [x] 9.4 Scrivere test unitari per metriche
    - Test pubblicazione metriche CloudWatch
    - _Requisiti: 10.2_

- [x] 10. Checkpoint - Verifica funzionalità complete
  - Assicurarsi che tutti i test passino, chiedere all'utente se sorgono domande.

- [x] 11. Creazione template CloudFormation
  - [x] 11.1 Creare template infrastruttura AWS
    - Definire risorse DynamoDB con TTL
    - Configurare Lambda function con ruoli IAM
    - Aggiungere EventBridge Scheduler per Europe/Rome
    - _Requisiti: 3.2, 3.3, 3.4, 8.1_

  - [x] 11.2 Configurare SQS Dead Letter Queue
    - Aggiungere coda DLQ per gestione errori
    - Collegare DLQ alla Lambda function
    - _Requisiti: 3.5, 8.3, 10.1_

  - [x] 11.3 Aggiungere CloudWatch Log Groups
    - Configurare gruppi log con retention policy
    - Definire output per monitoraggio
    - _Requisiti: 3.6, 10.5_

  - [x] 11.4 Scrivere test unitari per template CloudFormation
    - Validazione sintassi YAML
    - Verifica risorse richieste
    - _Requisiti: 3.1_

- [x] 12. Creazione script deployment automatico
  - [x] 12.1 Creare script bash deploy.sh
    - Implementare verifica prerequisiti (aws cli, python3, zip)
    - Aggiungere creazione bucket S3 artefatti
    - _Requisiti: 2.1, 2.3_

  - [x] 12.2 Implementare build e upload Lambda
    - Aggiungere packaging dipendenze Python
    - Configurare upload zip su S3
    - _Requisiti: 2.2_

  - [x] 12.3 Aggiungere gestione Secrets Manager
    - Implementare creazione/aggiornamento secret bot token
    - Configurare parametri CloudFormation
    - _Requisiti: 2.4, 2.5_

  - [x] 12.4 Finalizzare deployment CloudFormation
    - Aggiungere esecuzione aws cloudformation deploy
    - Implementare output informativi per utente
    - _Requisiti: 2.6_

  - [x] 12.5 Scrivere test unitari per script deployment
    - Test verifica prerequisiti
    - Test creazione bucket S3
    - _Requisiti: 2.1, 2.3_

- [x] 13. Creazione documentazione e file supporto
  - [x] 13.1 Creare README.md completo
    - Documentare configurazione feed personalizzabili
    - Aggiungere istruzioni deployment "copy/paste"
    - Spiegare feed AWS di default inclusi
    - _Requisiti: 1.5, 11.4_

  - [x] 13.2 Creare file prompt template
    - Aggiungere template prompt Bedrock in directory prompts/
    - Documentare formato riassunto richiesto
    - _Requisiti: 6.2_

  - [x] 13.3 Creare file kiro-prompt.md obbligatorio
    - Copiare prompt originale utente in docs/kiro-prompt.md
    - Aggiungere sezione provenance nel README
    - _Requisiti: Documentazione_

  - [x] 13.4 Configurare GitHub Actions
    - Aggiungere workflow per linting con ruff
    - Configurare esecuzione test automatizzata con pytest
    - _Requisiti: 12.4, 12.5_

- [x] 14. Checkpoint finale - Verifica sistema completo
  - Assicurarsi che tutti i test passino, chiedere all'utente se sorgono domande.

## Note

- Tutti i task sono obbligatori per un sistema completo e robusto
- Ogni task referenzia requisiti specifici per tracciabilità
- I checkpoint assicurano validazione incrementale
- I test property validano proprietà di correttezza universali
- I test unitari validano esempi specifici e casi limite
- Il sistema utilizza Python 3.12 come specificato nei requisiti