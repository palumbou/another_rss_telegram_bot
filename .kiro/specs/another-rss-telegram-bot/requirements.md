# Documento dei Requisiti

## Introduzione

Un sistema generico e riutilizzabile di bot Telegram che legge quotidianamente feed RSS/Atom e pubblica riassunti in italiano su canali/gruppi Telegram. Il sistema è progettato per essere infrastructure-as-code con deployment a comando singolo e configurabile per qualsiasi feed RSS e target Telegram.

## Glossario

- **RSS_Bot**: Il sistema serverless completo per l'elaborazione di feed RSS e la pubblicazione su Telegram
- **Feed_Processor**: Componente responsabile del download e parsing dei feed RSS/Atom
- **Deduplicator**: Componente che previene contenuti duplicati utilizzando storage DynamoDB
- **Summarizer**: Componente che genera riassunti in italiano utilizzando servizi AI con fallback
- **Telegram_Publisher**: Componente che invia messaggi formattati su Telegram
- **Deploy_Script**: Script bash di automazione per deployment a comando singolo
- **CloudFormation_Template**: Definizione infrastructure-as-code per le risorse AWS

## Requisiti

### Requisito 1: Architettura Generica e Riutilizzabile

**User Story:** Come sviluppatore, voglio un sistema generico di bot RSS-to-Telegram, così da poterlo deployare per qualsiasi feed RSS e qualsiasi canale Telegram senza modifiche al codice.

#### Criteri di Accettazione

1. IL RSS_Bot DEVE accettare URL di feed configurabili come parametri CloudFormation
2. IL RSS_Bot DEVE accettare ID chat Telegram configurabili come parametri CloudFormation  
3. IL RSS_Bot DEVE utilizzare convenzioni di naming generiche evitando riferimenti a organizzazioni specifiche
4. IL RSS_Bot DEVE includere URL di feed AWS di default che possono essere facilmente sostituiti
5. IL RSS_Bot DEVE fornire documentazione chiara per personalizzare feed e target

### Requisito 2: Deployment a Comando Singolo

**User Story:** Come utente, voglio deployare l'intero sistema con un singolo comando, così da non dover creare manualmente risorse AWS o configurare servizi.

#### Criteri di Accettazione

1. IL Deploy_Script DEVE creare automaticamente tutte le risorse AWS richieste
2. QUANDO l'utente fornisce credenziali AWS, token bot Telegram e chat ID, IL Deploy_Script DEVE completare il deployment senza intervento manuale
3. IL Deploy_Script DEVE creare bucket S3 per artefatti se non esistono
4. IL Deploy_Script DEVE creare o aggiornare entry in Secrets Manager per il token bot
5. IL Deploy_Script DEVE eseguire il deployment CloudFormation con tutti i parametri richiesti
6. IL Deploy_Script DEVE fornire output chiaro mostrando stato del deployment e posizioni dei log

### Requisito 3: Infrastructure as Code

**User Story:** Come ingegnere DevOps, voglio tutta l'infrastruttura definita in CloudFormation, così che il deployment sia riproducibile e segua le best practice AWS.

#### Criteri di Accettazione

1. IL CloudFormation_Template DEVE definire tutte le risorse AWS utilizzando formato YAML o JSON
2. IL CloudFormation_Template DEVE creare tabella DynamoDB con configurazione TTL
3. IL CloudFormation_Template DEVE creare funzione Lambda con ruoli IAM appropriati
4. IL CloudFormation_Template DEVE creare scheduler EventBridge per esecuzione giornaliera
5. IL CloudFormation_Template DEVE creare coda SQS dead letter per gestione errori
6. IL CloudFormation_Template DEVE creare gruppi log CloudWatch con policy di retention
7. IL CloudFormation_Template DEVE utilizzare policy IAM con privilegi minimi

### Requisito 4: Elaborazione Feed RSS

**User Story:** Come consumatore di contenuti, voglio che il sistema elabori feed RSS/Atom in modo affidabile, così da ricevere aggiornamenti da più fonti senza duplicati.

#### Criteri di Accettazione

1. QUANDO il sistema elabora feed, IL Feed_Processor DEVE scaricare contenuti via HTTPS
2. IL Feed_Processor DEVE normalizzare elementi RSS/Atom estraendo titolo, link, data pubblicazione e contenuto
3. IL Feed_Processor DEVE pulire contenuto HTML dalle descrizioni dei feed
4. IL Feed_Processor DEVE gestire sia formati RSS che Atom
5. QUANDO il parsing del feed fallisce, IL Feed_Processor DEVE loggare errori e continuare con altri feed

### Requisito 5: Deduplicazione Contenuti

**User Story:** Come utente, voglio evitare di ricevere contenuti duplicati, così che il mio canale Telegram rimanga pulito e rilevante.

#### Criteri di Accettazione

1. IL Deduplicator DEVE generare identificatori unici utilizzando GUID quando disponibile
2. QUANDO GUID non è disponibile, IL Deduplicator DEVE creare hash SHA256 da URL feed, link e data pubblicazione
3. IL Deduplicator DEVE controllare DynamoDB per contenuti esistenti prima dell'elaborazione
4. QUANDO il contenuto esiste già, IL Deduplicator DEVE saltare l'elaborazione
5. QUANDO il contenuto è nuovo, IL Deduplicator DEVE memorizzarlo in DynamoDB con TTL di 90 giorni

### Requisito 6: Generazione Riassunti in Italiano

**User Story:** Come parlante italiano, voglio contenuti riassunti in italiano con formato consistente, così da poter comprendere rapidamente i punti chiave.

#### Criteri di Accettazione

1. IL Summarizer DEVE generare riassunti utilizzando Amazon Bedrock come servizio primario
2. IL Summarizer DEVE formattare riassunti con una riga titolo, tre punti elenco (≤15 parole ciascuno) e riga "Perché conta:" (≤20 parole)
3. QUANDO Bedrock non è disponibile o restituisce AccessDenied, IL Summarizer DEVE utilizzare metodo fallback estrattivo
4. IL Summarizer DEVE evitare di generare informazioni non presenti nel contenuto sorgente
5. IL Summarizer DEVE mantenere output consistente in lingua italiana

### Requisito 7: Pubblicazione Telegram

**User Story:** Come utente Telegram, voglio ricevere messaggi formattati con riassunti e link, così da poter accedere sia a insights rapidi che al contenuto originale.

#### Criteri di Accettazione

1. IL Telegram_Publisher DEVE inviare messaggi utilizzando Bot API sendMessage con parsing HTML
2. IL Telegram_Publisher DEVE includere link articoli originali in ogni messaggio
3. QUANDO l'API Telegram restituisce rate limiting (429), IL Telegram_Publisher DEVE implementare retry con backoff
4. QUANDO l'API Telegram restituisce errori, IL Telegram_Publisher DEVE loggare errori e continuare l'elaborazione
5. IL Telegram_Publisher DEVE formattare messaggi per leggibilità ottimale in Telegram

### Requisito 8: Esecuzione Programmata

**User Story:** Come utente, voglio che il bot funzioni automaticamente ogni giorno, così da ricevere aggiornamenti regolari senza intervento manuale.

#### Criteri di Accettazione

1. IL RSS_Bot DEVE eseguire giornalmente alle 09:00 timezone Europe/Rome per default
2. IL RSS_Bot DEVE permettere schedule configurabile via parametri CloudFormation
3. QUANDO l'esecuzione programmata fallisce, IL RSS_Bot DEVE inviare messaggi falliti alla coda dead letter
4. IL RSS_Bot DEVE loggare tempi di inizio e completamento esecuzione
5. IL RSS_Bot DEVE gestire automaticamente cambi di timezone

### Requisito 9: Sicurezza e Gestione Configurazione

**User Story:** Come utente attento alla sicurezza, voglio informazioni sensibili protette e accesso con privilegi minimi, così che il sistema sia sicuro per default.

#### Criteri di Accettazione

1. IL RSS_Bot DEVE memorizzare il token bot Telegram solo in AWS Secrets Manager
2. IL RSS_Bot NON DEVE mai loggare informazioni sensibili in CloudWatch
3. IL RSS_Bot DEVE utilizzare ruoli IAM con permessi minimi richiesti
4. IL RSS_Bot DEVE accedere a DynamoDB solo con permessi PutItem e GetItem
5. IL RSS_Bot DEVE accedere a Secrets Manager solo con permesso GetSecretValue
6. DOVE Bedrock è abilitato, IL RSS_Bot DEVE includere permesso bedrock:InvokeModel

### Requisito 10: Gestione Errori e Monitoraggio

**User Story:** Come amministratore di sistema, voglio gestione errori completa e monitoraggio, così da poter risolvere problemi e assicurare affidabilità del sistema.

#### Criteri di Accettazione

1. IL RSS_Bot DEVE inviare esecuzioni fallite alla coda SQS dead letter
2. IL RSS_Bot DEVE creare metriche CloudWatch personalizzate per elaborazioni riuscite/fallite
3. IL RSS_Bot DEVE loggare tutti i passi di elaborazione con livelli di log appropriati
4. QUANDO si verificano errori critici, IL RSS_Bot DEVE continuare l'elaborazione dei feed rimanenti
5. IL RSS_Bot DEVE fornire output CloudFormation per risorse di monitoraggio

### Requisito 11: Configurazione Feed AWS di Default

**User Story:** Come professionista AWS, voglio feed AWS di default inclusi, così da poter iniziare immediatamente a ricevere aggiornamenti AWS mantenendo la possibilità di personalizzare.

#### Criteri di Accettazione

1. IL RSS_Bot DEVE includere URL feed AWS Blog come configurazione di default
2. IL RSS_Bot DEVE includere feed AWS "What's New" come configurazione di default  
3. IL RSS_Bot DEVE includere feed AWS Security Blog come configurazione di default
4. IL RSS_Bot DEVE documentare tutti i feed di default nel README con istruzioni di sostituzione
5. IL RSS_Bot DEVE permettere sostituzione completa della lista feed via parametri di configurazione

### Requisito 12: Testing e Assicurazione Qualità

**User Story:** Come sviluppatore, voglio testing completo e controlli di qualità del codice, così che il sistema sia affidabile e manutenibile.

#### Criteri di Accettazione

1. IL RSS_Bot DEVE includere test pytest per tutti i componenti core
2. IL RSS_Bot DEVE includere test per hashing ID elementi e logica deduplicazione
3. IL RSS_Bot DEVE includere test per formattazione HTML e formattazione messaggi Telegram
4. IL RSS_Bot DEVE includere GitHub Actions per linting con ruff
5. IL RSS_Bot DEVE includere GitHub Actions per esecuzione test automatizzata