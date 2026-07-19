# Directory Scripts

> **Lingue disponibili**: [English](README.md) | [Italiano (corrente)](README.it.md)

Questa directory contiene gli script di automazione per il progetto Another RSS Telegram Bot.

## deploy.sh

Script di deployment automatizzato per AWS che gestisce l'intero processo di deployment della pipeline CI/CD.

### Funzionalità

Lo script automatizza i seguenti passaggi:

1. **Verifica Prerequisiti**: Controlla che AWS CLI, Python 3 e zip siano installati
2. **Creazione Bucket S3**: Crea bucket per artifact (se necessario)
3. **Deployment Pipeline**: Deploya infrastruttura CodePipeline
4. **Pacchettizzazione Sorgente**: Crea package del codice sorgente
5. **Upload S3**: Carica sorgente su S3, triggerando la pipeline
6. **Build Automatica**: CodeBuild pacchettizza la funzione Lambda
7. **Deploy Automatico**: CloudFormation deploya l'applicazione

### Prerequisiti

- AWS CLI configurato con credenziali appropriate
- Python 3.12 o superiore
- Comando `zip` disponibile
- Connessione internet
- **Configurazione feed RSS**: Vedi [FEEDS.it.md](../FEEDS.IT.md) per la configurazione dei feed

### Utilizzo Base

```bash
# Deployment iniziale (crea pipeline e deploya applicazione)
./scripts/deploy.sh \
  --telegram-token "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11" \
  --chat-id "-1001234567890"
```

### Aggiornamento Codice

```bash
# Aggiorna solo il codice (triggera pipeline)
./scripts/deploy.sh --update-code
```

### Opzioni Disponibili

| Parametro | Descrizione | Default | Richiesto |
|-----------|-------------|---------|-----------|
| `--stack-name` | Nome stack pipeline | `another-rss-telegram-bot-pipeline` | No |
| `--app-stack` | Nome stack applicazione | `another-rss-telegram-bot-app` | No |
| `--region` | Regione AWS | `us-east-1` | No |
| `--bot-name` | Nome bot per risorse | `another-rss-telegram-bot` | No |
| `--telegram-token` | Token bot Telegram | - | **Sì** (iniziale) |
| `--chat-id` | ID chat Telegram | - | **Sì** (iniziale) |
| `--topic-id` | ID topic del forum (invia i messaggi in uno specifico topic di un supergruppo con topic abilitati) | Vuoto (chat/topic General) | No |
| `--feeds-file` | Percorso file feeds.json | Feed predefiniti | No |
| `--bucket` | Nome bucket S3 | Auto-generato | No |
| `--update-code` | Aggiorna solo codice | false | No |
| `--cleanup` | Elimina tutte le risorse | false | No |
| `--yes` | Salta prompt di conferma | false | No |
| `--dry-run` | Simula senza eseguire | false | No |
| `--help` | Mostra aiuto | - | No |

### Esempi d'Uso

#### 1. Deployment Iniziale
```bash
./scripts/deploy.sh \
  --telegram-token "TUO_TOKEN" \
  --chat-id "TUO_CHAT_ID" \
  --region "eu-west-1"
```

#### 2. Aggiornamento Codice
```bash
./scripts/deploy.sh --update-code --region "eu-west-1"
```

#### 3. Feed Personalizzati
```bash
./scripts/deploy.sh \
  --telegram-token "TUO_TOKEN" \
  --chat-id "TUO_CHAT_ID" \
  --feeds-file /percorso/al/mio-feeds.json
```

Vedi [FEEDS.IT.md](../FEEDS.IT.md) per il formato del file feed ed esempi.

#### 4. Dry Run
```bash
./scripts/deploy.sh \
  --telegram-token "TUO_TOKEN" \
  --chat-id "TUO_CHAT_ID" \
  --dry-run
```

#### 5. Salta Prompt di Conferma
```bash
./scripts/deploy.sh \
  --telegram-token "TUO_TOKEN" \
  --chat-id "TUO_CHAT_ID" \
  --yes
```

#### 6. Pulizia
```bash
./scripts/deploy.sh --cleanup --region "eu-west-1" --yes
```

#### 7. Invio in un Topic del Forum
```bash
# Deployment iniziale con invio in uno specifico topic
./scripts/deploy.sh \
  --telegram-token "TUO_TOKEN" \
  --chat-id "TUO_CHAT_ID" \
  --topic-id "13"

# Spostare un deployment esistente su un topic (o tornare indietro: ometti --topic-id)
./scripts/deploy.sh --update-stack --topic-id "13"
```

> Nota: `--update-stack` reimposta il topic se non passi esplicitamente `--topic-id`. Se con `--update-stack` fornisci anche `--chat-id`, viene aggiornata anche la chat; altrimenti viene mantenuta quella attuale.

### Come Ottenere i Parametri Richiesti

#### Token Bot Telegram
1. Contatta [@BotFather](https://t.me/botfather) su Telegram
2. Usa il comando `/newbot` per creare un nuovo bot
3. Segui le istruzioni per scegliere nome e username
4. Copia il token fornito (formato: `123456:ABC-DEF...`)

#### ID Chat Telegram
1. Aggiungi il bot al tuo canale/gruppo
2. Invia un messaggio nel canale/gruppo
3. Visita: `https://api.telegram.org/bot<TUO_BOT_TOKEN>/getUpdates`
4. Trova il campo `"chat":{"id":...}` nella risposta
5. Usa l'ID trovato (i canali iniziano con `-100`)

#### ID Topic Telegram (opzionale)
1. Abilita i topic (forum) nel tuo supergruppo e apri il topic desiderato
2. Copia il link del topic: l'ID del topic è il secondo segmento numerico (es. `https://t.me/c/1234567890/13` → topic ID `13`)
3. Rendi il bot amministratore del gruppo con il permesso **Gestisci argomenti** (`can_manage_topics`), altrimenti l'API Telegram restituisce `TOPIC_CLOSED` sui topic chiusi
4. Passalo con `--topic-id "13"`; lascialo non impostato per inviare sulla chat o sul topic General

### Workflow di Deployment

#### Deployment Iniziale
1. Script crea bucket S3 per artifact
2. Deploya stack infrastruttura CodePipeline
3. Pacchettizza codice sorgente in zip
4. Carica sorgente su S3 (`source/source.zip`)
5. Evento S3 triggera CodePipeline
6. CodeBuild costruisce package Lambda
7. CloudFormation deploya applicazione

#### Aggiornamenti Codice
1. Script pacchettizza codice sorgente aggiornato
2. Carica su S3 (`source/source.zip`)
3. Evento S3 triggera CodePipeline
4. Pipeline ricostruisce e redeploya automaticamente

### Output

Lo script fornisce informazioni dettagliate durante l'esecuzione:

- ✅ **Controlli prerequisiti**: Verifica dipendenze
- 📦 **Pacchettizzazione sorgente**: Creazione archivio sorgente
- ☁️ **Upload S3**: Caricamento artifact
- 🚀 **Deployment pipeline**: Setup infrastruttura
- 📊 **Risultati**: Link per monitoraggio

### Risoluzione Problemi

#### Problemi Comuni

1. **Credenziali AWS non configurate**
   ```bash
   aws configure
   # Inserisci Access Key ID, Secret Access Key e region
   ```

2. **Bucket già esistente**
   - Usa `--bucket` con un nome diverso
   - Oppure elimina prima il bucket esistente

3. **Pipeline non si triggera**
   - Controlla che la notifica evento S3 sia configurata
   - Verifica che la regola EventBridge sia abilitata
   - Controlla i log CloudWatch per errori

4. **Aggiornamento stack fallito**
   - Controlla gli eventi CloudFormation nella Console AWS
   - Verifica che i parametri siano corretti
   - Usa `--dry-run` per testare la configurazione

### Monitoraggio

Dopo il deployment, monitora il bot tramite:

- **Console CodePipeline**: Controlla stato esecuzione pipeline
- **CloudWatch Logs**: `/aws/lambda/{bot-name}-processor`
- **CloudWatch Dashboard**: `{bot-name}-monitoring`
- **Console AWS**: Link forniti nell'output dello script

### Sicurezza

Lo script implementa best practice di sicurezza:

- 🔐 Token Telegram memorizzato in AWS Secrets Manager
- 🛡️ Bucket S3 con crittografia server-side
- 🔒 Versioning abilitato per artifact
- 👤 Ruoli IAM con privilegi minimi

### Personalizzazione

Per modificare il comportamento dello script:

1. **Feed RSS**: Modifica il file `feeds.json` (vedi [FEEDS.IT.md](../FEEDS.IT.md))
2. **Naming bucket**: Modifica logica generazione nome bucket
3. **Nomi stack**: Cambia costanti nome stack predefinite

---

*Questo script fa parte dell'esperimento Kiro AI per l'automazione del deployment*
