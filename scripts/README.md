# Scripts Directory

Questa directory contiene gli script di automazione per il progetto Another RSS Telegram Bot.

## deploy.sh

Script di deployment automatizzato per AWS che gestisce l'intero processo di distribuzione del bot.

### Funzionalità

Lo script automatizza i seguenti passaggi:

1. **Verifica prerequisiti**: Controlla che AWS CLI, Python 3, e zip siano installati
2. **Creazione bucket S3**: Crea un bucket per gli artifact di deployment (opzionale)
3. **Build del package Lambda**: Installa dipendenze e crea il package di deployment
4. **Upload su S3**: Carica il package Lambda su S3
5. **Gestione segreti**: Memorizza il token Telegram in AWS Secrets Manager
6. **Deploy CloudFormation**: Distribuisce l'infrastruttura AWS
7. **Aggiornamento codice**: Aggiorna il codice della funzione Lambda

### Prerequisiti

- AWS CLI configurato con credenziali appropriate
- Python 3.8 o superiore
- Comando `zip` disponibile
- Connessione internet per scaricare le dipendenze

### Utilizzo Base

```bash
# Deployment minimo (richiede solo token e chat ID)
./scripts/deploy.sh \
  --telegram-token "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11" \
  --chat-id "-1001234567890"
```

### Opzioni Avanzate

```bash
# Deployment personalizzato completo
./scripts/deploy.sh \
  --stack-name "my-rss-bot" \
  --region "eu-west-1" \
  --bot-name "my-custom-bot" \
  --telegram-token "123456:ABC-DEF..." \
  --chat-id "-1001234567890" \
  --feeds "https://example.com/feed1.xml,https://example.com/feed2.xml" \
  --schedule "cron(0 8 * * ? *)" \
  --timezone "Europe/London" \
  --bucket "my-custom-bucket"
```

### Parametri Disponibili

| Parametro | Descrizione | Default | Richiesto |
|-----------|-------------|---------|-----------|
| `--stack-name` | Nome dello stack CloudFormation | `another-rss-telegram-bot` | No |
| `--region` | Regione AWS | `us-east-1` | No |
| `--bot-name` | Nome del bot per le risorse | `another-rss-telegram-bot` | No |
| `--telegram-token` | Token del bot Telegram | - | **Sì** |
| `--chat-id` | ID del canale/chat Telegram | - | **Sì** |
| `--feeds` | URL dei feed RSS (separati da virgola) | Feed AWS predefiniti | No |
| `--schedule` | Espressione cron per la schedulazione | `cron(0 9 * * ? *)` (9:00 AM daily) | No |
| `--timezone` | Timezone per la schedulazione | `Europe/Rome` | No |
| `--bucket` | Nome bucket S3 per artifact | Auto-generato | No |
| `--no-create-bucket` | Non creare il bucket S3 (assume esista) | false | No |
| `--dry-run` | Simula il deployment senza eseguirlo | false | No |
| `--help` | Mostra l'help completo | - | No |

### Esempi d'Uso

#### 1. Deployment di Test (Dry Run)
```bash
./scripts/deploy.sh \
  --telegram-token "YOUR_TOKEN" \
  --chat-id "YOUR_CHAT_ID" \
  --dry-run
```

#### 2. Deployment in Europa con Feed Personalizzati
```bash
./scripts/deploy.sh \
  --region "eu-west-1" \
  --telegram-token "YOUR_TOKEN" \
  --chat-id "YOUR_CHAT_ID" \
  --feeds "https://techcrunch.com/feed/,https://www.theverge.com/rss/index.xml" \
  --timezone "Europe/London"
```

#### 3. Deployment con Schedulazione Personalizzata
```bash
./scripts/deploy.sh \
  --telegram-token "YOUR_TOKEN" \
  --chat-id "YOUR_CHAT_ID" \
  --schedule "cron(0 */6 * * ? *)" \  # Ogni 6 ore
  --timezone "America/New_York"
```

### Come Ottenere i Parametri Richiesti

#### Token Telegram Bot
1. Contatta [@BotFather](https://t.me/botfather) su Telegram
2. Usa il comando `/newbot` per creare un nuovo bot
3. Segui le istruzioni per scegliere nome e username
4. Copia il token fornito (formato: `123456:ABC-DEF...`)

#### Chat ID Telegram
1. Aggiungi il bot al canale/gruppo desiderato
2. Invia un messaggio nel canale/gruppo
3. Visita: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
4. Cerca il campo `"chat":{"id":...}` nella risposta
5. Usa l'ID trovato (per i canali inizia con `-100`)

### Output del Deployment

Lo script fornisce informazioni dettagliate durante l'esecuzione:

- ✅ **Controlli prerequisiti**: Verifica delle dipendenze
- 📦 **Build package**: Creazione del package Lambda
- ☁️ **Upload S3**: Caricamento degli artifact
- 🔐 **Secrets Manager**: Gestione sicura del token
- 🚀 **CloudFormation**: Deployment dell'infrastruttura
- 📊 **Risultati**: Link utili per monitoraggio

### Troubleshooting

#### Errori Comuni

1. **AWS credentials not configured**
   ```bash
   aws configure
   # Inserisci Access Key ID, Secret Access Key, e region
   ```

2. **Bucket already exists**
   - Usa `--bucket` con un nome diverso
   - Oppure usa `--no-create-bucket` se il bucket esiste già

3. **Lambda package too large**
   - Verifica che `requirements.txt` contenga solo dipendenze necessarie
   - Considera l'uso di Lambda Layers per dipendenze pesanti

4. **CloudFormation stack update failed**
   - Controlla i log di CloudFormation nella console AWS
   - Verifica che i parametri siano corretti
   - Usa `--dry-run` per testare la configurazione

#### Log e Monitoraggio

Dopo il deployment, puoi monitorare il bot tramite:

- **CloudWatch Logs**: `/aws/lambda/{bot-name}-processor`
- **CloudWatch Dashboard**: `{bot-name}-monitoring`
- **AWS Console**: Link fornito nell'output del deployment

### Sicurezza

Lo script implementa le seguenti misure di sicurezza:

- 🔐 Token Telegram memorizzato in AWS Secrets Manager
- 🛡️ Bucket S3 con crittografia server-side abilitata
- 🔒 Versioning abilitato per gli artifact
- 👤 Principio del minimo privilegio per i ruoli IAM

### Personalizzazione

Per modificare il comportamento dello script:

1. **Feed RSS predefiniti**: Modifica la variabile `feed_urls` nel codice
2. **Configurazione regioni**: Aggiorna la logica di creazione bucket per nuove regioni
3. **Parametri CloudFormation**: Estendi l'array `cf_params` per nuovi parametri

---

*Questo script è parte dell'esperimento Kiro per l'automazione del deployment*