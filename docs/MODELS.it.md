# Guida ai Modelli AI per Riassunti

Questo documento spiega come configurare e utilizzare diversi modelli Amazon Bedrock per generare riassunti in italiano.

> **Lingue disponibili**: [English](MODELS.md) | [Italiano (corrente)](MODELS.it.md)

## Modelli Supportati

Il bot supporta due modelli Amazon Bedrock che puoi scegliere al momento del deployment:

### 1. Amazon Nova Micro (Default)
- **Model ID**: `amazon.nova-micro-v1:0`
- **Selezione**: `nova-micro`
- **Vantaggi**: 
  - Economico per alto volume
  - Veloce (< 1 secondo per riassunto)
  - Buona qualità in italiano
  - Disponibile tramite inference profile cross-region
- **Costo**: ~$0.000035 per 1000 token input, ~$0.00014 per 1000 token output
- **Ideale per**: Deployment in produzione con alto volume

### 2. Llama 3.2 3B Instruct
- **Model ID**: `us.meta.llama3-2-3b-instruct-v1:0`
- **Selezione**: `llama-3b`
- **Vantaggi**:
  - Eccellente per riassunti e traduzioni
  - Comprensione del contesto superiore
  - Supporto multilingua nativo
  - Migliore nell'eseguire istruzioni
- **Costo**: ~$0.00015 per 1000 token input, ~$0.0002 per 1000 token output
- **Ideale per**: Deployment focalizzati sulla qualità
- **Nota**: Richiede accesso al modello nella tua regione AWS

## Come Scegliere un Modello al Deployment

Puoi selezionare quale modello utilizzare quando fai il deployment dello stack usando il parametro `-m` dello script di deployment.

### Deploy con Nova Micro (Default)

```bash
./scripts/deploy.sh -m nova-micro
```

Oppure ometti semplicemente il parametro (Nova Micro è il default):

```bash
./scripts/deploy.sh
```

### Deploy con Llama 3.2 3B

```bash
./scripts/deploy.sh -m llama-3b
```

### Esempi Completi di Deployment

**Deployment con Nova Micro:**
```bash
./scripts/deploy.sh \
  -b another-rss-telegram-bot \
  -t YOUR_TELEGRAM_BOT_TOKEN \
  -c YOUR_TELEGRAM_CHAT_ID \
  -m nova-micro
```

**Deployment con Llama 3.2 3B:**
```bash
./scripts/deploy.sh \
  -b another-rss-telegram-bot \
  -t YOUR_TELEGRAM_BOT_TOKEN \
  -c YOUR_TELEGRAM_CHAT_ID \
  -m llama-3b
```

Lo script di deployment automaticamente:
- Valida la tua selezione del modello
- Configura CloudFormation con il model ID corretto
- Imposta i permessi IAM per il modello selezionato
- Passa la configurazione del modello alla funzione Lambda

## Comprendere le Frasi "Perché Conta"

Il bot usa diverse frasi italiane per indicare la fonte del riassunto:

### "Perché ti può interessare:" (Bedrock AI)
- **Usato da**: Tutti i modelli Bedrock (Nova Micro, Llama 3.2 3B)
- **Significato**: "Perché ti può interessare:"
- **Indica**: Riassunto generato dall'AI usando Amazon Bedrock
- **Qualità**: Spiegazione contestuale di alta qualità

**Esempio:**
```
📰 Titolo: Nuova Scoperta nell'Intelligenza Artificiale
• Primo punto elenco
• Secondo punto elenco

💡 Perché ti può interessare: Questo progresso potrebbe rivoluzionare il settore...
```

### "Perché conta:" (Fallback)
- **Usato da**: Riassunto estrattivo locale (quando Bedrock non è disponibile)
- **Significato**: "Perché conta:"
- **Indica**: Riassunto di fallback senza AI esterna
- **Qualità**: Affidabile ma meno contestuale

**Esempio:**
```
📰 Titolo: Nuova Scoperta nell'Intelligenza Artificiale
• Primo punto elenco
• Secondo punto elenco

💡 Perché conta: Questo rappresenta uno sviluppo significativo nel campo...
```

Questa distinzione aiuta gli utenti a capire se stanno leggendo un riassunto generato dall'AI o un riassunto di fallback.

## Permessi IAM Necessari

I template CloudFormation configurano automaticamente i permessi IAM per entrambi i modelli. Il ruolo di esecuzione Lambda include:

```yaml
- PolicyName: BedrockAccess
  PolicyDocument:
    Version: '2012-10-17'
    Statement:
      - Effect: Allow
        Action:
          - bedrock:InvokeModel
        Resource: 
          - !Sub 'arn:aws:bedrock:${AWS::Region}::foundation-model/amazon.nova-micro-v1:0'
          - !Sub 'arn:aws:bedrock:${AWS::Region}::foundation-model/us.meta.llama3-2-3b-instruct-v1:0'
```

**Punti chiave:**
- Entrambi gli ARN dei modelli sono esplicitamente inclusi
- I permessi sono concessi indipendentemente dal modello selezionato
- Questo ti permette di cambiare modello ridistribuendo senza modifiche IAM
- Il pattern wildcard `arn:aws:bedrock:*::foundation-model/*` fornisce flessibilità aggiuntiva

## Verifica Disponibilità Modello

Prima di fare il deployment con un modello specifico, verifica che sia disponibile nella tua regione AWS:

**Verifica disponibilità Nova Micro:**
```bash
aws bedrock list-foundation-models \
  --region eu-west-1 \
  --query "modelSummaries[?contains(modelId, 'nova-micro')]"
```

**Verifica disponibilità Llama 3.2 3B:**
```bash
aws bedrock list-foundation-models \
  --region us-east-1 \
  --query "modelSummaries[?contains(modelId, 'llama3-2-3b')]"
```

**Nota**: Llama 3.2 3B è principalmente disponibile nelle regioni US (us-east-1, us-west-2). Nova Micro è disponibile globalmente tramite cross-region inference.

## Confronto Modelli

| Caratteristica | Nova Micro | Llama 3.2 3B |
|----------------|------------|--------------|
| **Velocità** | ⭐⭐⭐⭐⭐ Molto Veloce | ⭐⭐⭐⭐ Veloce |
| **Costo** | ⭐⭐⭐⭐⭐ Più Economico | ⭐⭐⭐⭐ Economico |
| **Qualità Italiano** | ⭐⭐⭐⭐ Buona | ⭐⭐⭐⭐⭐ Eccellente |
| **Seguire Istruzioni** | ⭐⭐⭐ Adeguato | ⭐⭐⭐⭐⭐ Superiore |
| **Disponibilità Regionale** | ⭐⭐⭐⭐⭐ Mondiale | ⭐⭐⭐⭐ Regioni US |
| **Caso d'Uso Ideale** | Produzione alto volume | Deployment focalizzati sulla qualità |
| **Deployment** | `./scripts/deploy.sh -m nova-micro` | `./scripts/deploy.sh -m llama-3b` |

### Scegliere il Modello Giusto

**Scegli Nova Micro se:**
- Hai bisogno del costo più basso per riassunto
- Stai processando alti volumi (1000+ articoli/giorno)
- La velocità è critica
- Hai bisogno di inference profile cross-region

**Scegli Llama 3.2 3B se:**
- La qualità del riassunto è la tua priorità principale
- Hai bisogno di una migliore esecuzione delle istruzioni
- Vuoi una comprensione superiore della lingua italiana
- Il costo è meno preoccupante

## Configurazione Avanzata

### Cambiare Modello Dopo il Deployment

Per cambiare modello dopo il deployment iniziale, ridistribuisci semplicemente con un parametro `-m` diverso:

```bash
# Passa da Nova Micro a Llama 3.2 3B
./scripts/deploy.sh -m llama-3b

# Torna a Nova Micro
./scripts/deploy.sh -m nova-micro
```

L'aggiornamento dello stack CloudFormation cambierà la variabile d'ambiente `BEDROCK_MODEL_ID` senza influenzare altre risorse.

### Configurazione Manuale del Modello

Se hai bisogno di configurare manualmente il modello (non raccomandato), puoi aggiornare la variabile d'ambiente Lambda:

```bash
aws lambda update-function-configuration \
  --function-name another-rss-telegram-bot-processor \
  --environment Variables={BEDROCK_MODEL_ID=us.meta.llama3-2-3b-instruct-v1:0}
```

Tuttavia, usare lo script di deployment è preferibile perché garantisce coerenza tra tutti i componenti dell'infrastruttura.

## Raccomandazioni

**Per deployment in produzione:**
- Inizia con Nova Micro per il miglior rapporto costo/prestazioni
- Monitora la qualità dei riassunti nel tuo caso d'uso specifico
- Passa a Llama 3.2 3B se i miglioramenti di qualità giustificano il costo

**Per deployment focalizzati sulla qualità:**
- Usa Llama 3.2 3B per una comprensione superiore della lingua italiana
- Aspettati costi ~4x superiori rispetto a Nova Micro
- Migliore esecuzione delle istruzioni e riassunti contestuali

**Per deployment con budget limitato:**
- Nova Micro è la scelta più economica
- Fornisce comunque riassunti di buona qualità in italiano
- Tempi di risposta più veloci riducono i costi di esecuzione Lambda

## Riassunto di Fallback

Se Bedrock non è disponibile o fallisce, il bot usa automaticamente un sistema di riassunto estrattivo locale:

**Caratteristiche:**
- Nessuna dipendenza da API esterne
- Sempre disponibile come backup
- Usa la frase "Perché conta:" (diversa da "Perché ti può interessare:" di Bedrock)
- Qualità inferiore ma affidabile
- Nessun costo aggiuntivo

**Quando viene attivato il fallback:**
- Errori o timeout dell'API Bedrock
- Accesso al modello negato (problemi IAM o regionali)
- Problemi di connettività di rete
- Rate limiting o quota superata

Il fallback garantisce che il tuo bot continui a funzionare anche quando Bedrock non è disponibile.
