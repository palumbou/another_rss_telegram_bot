# Guida ai Modelli AI per Riassunti

Questo documento spiega come configurare e utilizzare diversi modelli Amazon Bedrock per generare riassunti in italiano.

> **Lingue disponibili**: [English](MODELS.md) | [Italiano (corrente)](MODELS.it.md)

## Modelli Supportati

Il bot supporta tre modelli Amazon Bedrock che puoi scegliere al momento del deployment:

### 1. Amazon Nova Micro (Default)
- **Model ID**: `amazon.nova-micro-v1:0`
- **Selezione**: `nova-micro`
- **Vantaggi**: 
  - Più economico per alto volume
  - Veloce (< 1 secondo per riassunto)
  - Buona qualità in italiano
  - Disponibile tramite inference profile cross-region
- **Costo**: ~$0.000035 per 1000 token input, ~$0.00014 per 1000 token output
- **Costo mensile (150 articoli)**: ~$0.015
- **Ideale per**: Deployment in produzione con alto volume e budget limitato

### 2. Mistral Large (Selezione Regionale Intelligente)
- **Model IDs**: 
  - `mistral.mistral-large-3-675b-instruct` (preferito, 6 regioni)
  - `mistral.mistral-large-2402-v1:0` (fallback, 9 regioni)
- **Selezione**: `mistral-large`
- **Vantaggi**:
  - Eccellente traduzione multilingua (EN→IT, FR, ES, DE)
  - Comprensione del contesto e reasoning superiori
  - Mistral Large 3: 675B parametri (41B attivi - MoE), supporto multimodale
  - Mistral Large 24.02: Stabilità provata, solo testo
  - Supporto multilingua nativo (non traduzione come fallback)
- **Costo**: ~$2.00 per 1M token input, ~$6.00 per 1M token output
- **Costo mensile (150 articoli)**: ~$0.78
- **Disponibilità regionale**:
  - **Mistral Large 3** (più recente): us-east-1, us-east-2, us-west-2, ap-northeast-1, ap-south-1, sa-east-1
  - **Mistral Large 24.02** (fallback): us-west-1, ap-southeast-2, ca-central-1, eu-west-1/2/3, e altre 20+ regioni
- **Ideale per**: Deployment focalizzati sulla qualità che richiedono eccellente traduzione e reasoning

### 3. Llama 3.2 3B Instruct
- **Inference Profile ID**: Specifico per regione (selezionato automaticamente)
  - Regioni US: `us.meta.llama3-2-3b-instruct-v1:0`
  - Regioni EU: `eu.meta.llama3-2-3b-instruct-v1:0`
- **Selezione**: `llama-3b`
- **Vantaggi**:
  - Eccellente per riassunti e traduzioni
  - Comprensione del contesto superiore
  - Supporto multilingua nativo
  - Migliore nell'eseguire istruzioni rispetto a Nova Micro
- **Costo**: ~$0.00015 per 1000 token input, ~$0.0002 per 1000 token output
- **Costo mensile (150 articoli)**: ~$0.06
- **Ideale per**: Bilanciamento tra qualità e costo
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
          - !Sub 'arn:aws:bedrock:*:${AWS::AccountId}:inference-profile/*'
          - !Sub 'arn:aws:bedrock:*::foundation-model/*'
```

**Punti chiave:**
- Nova Micro usa un ARN di foundation model (specifico per regione)
- Llama 3.2 3B usa ARN di inference profile (wildcard per tutti i profile nel tuo account)
- I permessi sono concessi per tutti gli inference profile indipendentemente dalla regione di deployment
- CloudFormation seleziona automaticamente il profile corretto in base alla tua regione
- I pattern wildcard forniscono flessibilità mantenendo la sicurezza (limitati al tuo account)

## Supporto Multi-Regione

Il bot supporta automaticamente il deployment in **tutte le regioni AWS** dove Bedrock è disponibile:

### Rilevamento Automatico della Regione

Quando fai il deployment con Llama 3.2 3B, CloudFormation seleziona automaticamente l'inference profile corretto per la tua regione:

**Regioni Supportate:**
- **US**: us-east-1, us-east-2, us-west-1, us-west-2
- **EU**: eu-west-1, eu-west-2, eu-west-3, eu-central-1, eu-central-2, eu-north-1, eu-south-1, eu-south-2
- **APAC**: ap-northeast-1, ap-northeast-2, ap-northeast-3, ap-south-1, ap-south-2, ap-southeast-1, ap-southeast-2, ap-southeast-3, ap-southeast-4, ap-southeast-5, ap-southeast-7, ap-east-2
- **Canada**: ca-central-1, ca-west-1
- **Sud America**: sa-east-1
- **Medio Oriente**: me-central-1, me-south-1, il-central-1
- **Africa**: af-south-1
- **Messico**: mx-central-1

### Come Funziona

1. **Deploy in qualsiasi regione**: `./scripts/deploy.sh --region TUA_REGIONE -m llama-3b`
2. **Mappatura CloudFormation**: Seleziona automaticamente il profile US o EU
3. **Routing cross-region**: Bedrock instrada le richieste agli endpoint disponibili
4. **Nessuna configurazione manuale**: Tutto è gestito automaticamente

### Inference Profile Regionali

Llama 3.2 3B usa due inference profile regionali:
- **Profile US** (`us.meta.llama3-2-3b-instruct-v1:0`): Usato in US, Canada, APAC, Sud America, Medio Oriente, Messico
- **Profile EU** (`eu.meta.llama3-2-3b-instruct-v1:0`): Usato in EU, Israele, Africa

Il template CloudFormation include una mappatura completa per tutte le regioni commerciali AWS.

## Verifica Disponibilità Modello

Prima di fare il deployment con un modello specifico, verifica che sia disponibile nella tua regione AWS:

**Verifica disponibilità Nova Micro:**
```bash
aws bedrock list-foundation-models \
  --region eu-west-1 \
  --query "modelSummaries[?contains(modelId, 'nova-micro')]"
```

**Verifica inference profile Llama 3.2 3B (specifico per regione):**
```bash
# Per le regioni EU
aws bedrock get-inference-profile \
  --region eu-west-1 \
  --inference-profile-identifier eu.meta.llama3-2-3b-instruct-v1:0

# Per le regioni US
aws bedrock get-inference-profile \
  --region us-east-1 \
  --inference-profile-identifier us.meta.llama3-2-3b-instruct-v1:0
```

**Nota**: Llama 3.2 3B usa inference profile specifici per regione che vengono selezionati automaticamente in base alla regione di deployment:
- **Regioni US** (us-east-1, us-west-2, ecc.): Usa `us.meta.llama3-2-3b-instruct-v1:0`
- **Regioni EU** (eu-west-1, eu-central-1, ecc.): Usa `eu.meta.llama3-2-3b-instruct-v1:0`
- **Altre regioni** (APAC, CA, SA, ME, ecc.): Instrada automaticamente al profile più vicino

Nova Micro è disponibile globalmente come foundation model senza profile regionali.

## Confronto Modelli

| Caratteristica | Nova Micro | Mistral Large | Llama 3.2 3B |
|----------------|------------|---------------|--------------|
| **Velocità** | ⭐⭐⭐⭐⭐ Molto Veloce | ⭐⭐⭐⭐ Veloce | ⭐⭐⭐⭐ Veloce |
| **Costo** | ⭐⭐⭐⭐⭐ Più Economico | ⭐⭐⭐ Moderato | ⭐⭐⭐⭐ Economico |
| **Qualità Italiano** | ⭐⭐⭐⭐ Buona | ⭐⭐⭐⭐⭐ Eccellente | ⭐⭐⭐⭐⭐ Eccellente |
| **Multilingua** | ⭐⭐⭐ Adeguato | ⭐⭐⭐⭐⭐ Nativo | ⭐⭐⭐⭐ Buono |
| **Seguire Istruzioni** | ⭐⭐⭐ Adeguato | ⭐⭐⭐⭐⭐ Superiore | ⭐⭐⭐⭐⭐ Superiore |
| **Disponibilità Regionale** | ⭐⭐⭐⭐⭐ Mondiale | ⭐⭐⭐⭐ 15+ Regioni | ⭐⭐⭐⭐⭐ Tutte le Regioni |
| **Costo Mensile (150 articoli)** | $0.015 | $0.78 | $0.06 |
| **Caso d'Uso Ideale** | Produzione alto volume | Traduzioni di qualità | Qualità/costo bilanciato |
| **Deployment** | `./scripts/deploy.sh -m nova-micro` | `./scripts/deploy.sh -m mistral-large` | `./scripts/deploy.sh -m llama-3b` |

### Dettaglio Costi (5 articoli/giorno, 150/mese)

**Assunzioni per articolo:**
- Input: ~2000 token (articolo + prompt)
- Output: ~200 token (riassunto)

| Modello | Costo/Articolo | Costo Mensile | Costo Annuale |
|---------|----------------|---------------|---------------|
| **Nova Micro** | $0.0001 | **$0.015** | **$0.18** |
| **Llama 3.2 3B** | $0.0004 | **$0.06** | **$0.72** |
| **Mistral Large** | $0.0052 | **$0.78** | **$9.36** |

**Nota**: Mistral Large costa ~50x più di Nova Micro ma fornisce qualità di traduzione e capacità di reasoning significativamente superiori.

### Scegliere il Modello Giusto

**Scegli Nova Micro se:**
- Hai bisogno del costo più basso per riassunto
- Stai processando alti volumi (1000+ articoli/giorno)
- La velocità è critica
- Hai bisogno di inference profile cross-region
- Il budget è la preoccupazione principale

**Scegli Mistral Large se:**
- La qualità della traduzione è la tua priorità principale
- Hai bisogno di comprensione multilingua superiore (EN→IT, FR, ES, DE)
- Vuoi il miglior reasoning e comprensione del contesto
- Sei disposto a pagare ~50x di più per una qualità significativamente migliore
- Hai bisogno di supporto multimodale (solo Large 3, in 6 regioni)

**Scegli Llama 3.2 3B se:**
- Vuoi un bilanciamento tra qualità e costo
- La qualità del riassunto è importante ma il budget conta
- Hai bisogno di una migliore esecuzione delle istruzioni rispetto a Nova Micro
- Il costo è ~4x Nova Micro ma la qualità è molto migliore

## Mistral Large: Selezione Regionale Intelligente

Quando selezioni `mistral-large`, il bot sceglie automaticamente il miglior modello Mistral disponibile per la tua regione di deployment:

### Mistral Large 3 (Preferito - 6 Regioni)
**Model ID**: `mistral.mistral-large-3-675b-instruct`

**Disponibile in:**
- 🇺🇸 US: us-east-1, us-east-2, us-west-2
- 🌏 APAC: ap-northeast-1 (Tokyo), ap-south-1 (Mumbai)
- 🇧🇷 Sud America: sa-east-1 (São Paulo)

**Caratteristiche:**
- ✅ 675B parametri (41B attivi - Mixture of Experts)
- ✅ Supporto multimodale (testo + immagini)
- ✅ Modello più recente (Dicembre 2025)
- ✅ Migliori capacità di reasoning
- ✅ Pensiero esteso con reasoning step-by-step

### Mistral Large 24.02 (Fallback - 9+ Regioni)
**Model ID**: `mistral.mistral-large-2402-v1:0`

**Disponibile in:**
- 🇺🇸 US: us-west-1
- 🇨🇦 Canada: ca-central-1
- 🇪🇺 Europa: eu-west-1 (Irlanda), eu-west-2 (Londra), eu-west-3 (Parigi)
- 🌏 APAC: ap-southeast-2 (Sydney), e altre 20+ regioni

**Caratteristiche:**
- ✅ Solo testo (no multimodale)
- ✅ Stabilità e affidabilità provate
- ✅ Stesse eccellenti capacità multilingua
- ✅ Disponibilità regionale più ampia

**Come funziona:**
1. Fai il deployment con `--model mistral-large`
2. CloudFormation controlla la tua regione di deployment
3. Se la regione ha Mistral Large 3 → usa Large 3 (più recente, multimodale)
4. Se la regione non ha Large 3 → usa Large 24.02 (stabile, solo testo)
5. Entrambe le versioni forniscono eccellente qualità di traduzione

**Esempio:**
```bash
# Deploy in us-east-1 → Ottiene Mistral Large 3 (675B MoE, multimodale)
./scripts/deploy.sh --region us-east-1 --model mistral-large

# Deploy in eu-west-1 → Ottiene Mistral Large 24.02 (solo testo, stabile)
./scripts/deploy.sh --region eu-west-1 --model mistral-large
```

Entrambe le versioni mostreranno nei messaggi Telegram quale modello specifico è stato usato.

## Configurazione Avanzata

### Cambiare Modello Dopo il Deployment

Per cambiare modello dopo il deployment iniziale, usa il flag `--update-stack` con il modello desiderato:

```bash
# Passa da Nova Micro a Mistral Large
./scripts/deploy.sh --update-stack --model mistral-large

# Passa da Mistral Large a Llama 3.2 3B
./scripts/deploy.sh --update-stack --model llama-3b

# Torna a Nova Micro
./scripts/deploy.sh --update-stack --model nova-micro
```

Il flag `--update-stack` aggiorna solo i parametri dello stack CloudFormation senza ridistribuire il codice. Questo è più veloce e sicuro di un ridistribuzione completa. La funzione Lambda userà il nuovo modello alla prossima esecuzione.

**Alternativa: Ridistribuzione completa** (non raccomandato solo per cambiare modello):

```bash
# Questo funziona ma ridistribuisce tutto (più lento)
./scripts/deploy.sh -m mistral-large
```

L'aggiornamento dello stack CloudFormation cambierà la variabile d'ambiente `BEDROCK_MODEL_ID` senza influenzare altre risorse.

### Configurazione Manuale del Modello

Se hai bisogno di configurare manualmente il modello (non raccomandato), puoi aggiornare la variabile d'ambiente Lambda:

```bash
aws lambda update-function-configuration \
  --function-name another-rss-telegram-bot-processor \
  --environment Variables={BEDROCK_MODEL_ID=us.meta.llama3-2-3b-instruct-v1:0}
```

**Nota**: L'inference profile ID dipende dalla tua regione. Usa `us.meta.llama3-2-3b-instruct-v1:0` per le regioni US o `eu.meta.llama3-2-3b-instruct-v1:0` per le regioni EU.

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

### Come Funziona il Fallback

Il sistema di fallback usa la **summarization estrattiva** - estrae frasi esistenti dall'articolo senza comprendere o tradurre il contenuto:

**Processo:**
1. **Pulizia del Testo**: Rimuove tag HTML e normalizza gli spazi
2. **Divisione in Frasi**: Divide il testo sui segni di punteggiatura `.!?`
3. **Ranking Semplice**: Assegna punteggi alle frasi basandosi su:
   - Posizione (frasi iniziali = punteggio più alto, peso 60%)
   - Lunghezza (frasi più lunghe = punteggio più alto, peso 40%)
4. **Selezione**: Prende le 3 frasi con punteggio più alto come punti elenco
5. **Generazione Titolo**: Usa le prime 8 parole della frase migliore
6. **"Perché Conta"**: Generato tramite keyword matching (cerca "ai", "security", "aws", ecc.)

**Limitazioni Importanti:**
- ❌ **Nessuna Traduzione**: Se l'articolo è in inglese, il riassunto rimane in inglese
- ❌ **Nessuna Comprensione**: Non comprende il contesto o il significato
- ❌ **Nessun Testo Nuovo**: Estrae solo frasi esistenti, non genera nuovo contenuto
- ✅ **Sempre Disponibile**: Funziona senza dipendenze esterne
- ✅ **Veloce**: Nessuna chiamata API, elaborazione istantanea

**Esempio:**

*Articolo Originale in Inglese:*
```
AWS announces new machine learning service. 
The service is fully managed for deep learning models.
Integration with S3 and other AWS services.
Pay-per-use pricing with no fixed costs.
```

*Output Fallback (rimane in inglese):*
```
AWS announces new machine learning service

• AWS announces new machine learning service...
• The service is fully managed for deep learning models...
• Integration with S3 and other AWS services...

Perché conta: Novità cloud che potrebbero ottimizzare la tua infrastruttura

Fonte: https://...
```

Nota che solo "Perché conta:" è in italiano (hardcoded), mentre il contenuto rimane nella lingua originale.

**Raccomandazione:** Assicurati che Bedrock sia configurato correttamente per evitare di affidarti al fallback in produzione. Il fallback è progettato come backup di emergenza, non come metodo primario di riassunto.

Il fallback garantisce che il tuo bot continui a funzionare anche quando Bedrock non è disponibile.
