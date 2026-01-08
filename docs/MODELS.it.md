# Guida ai Modelli AI per Riassunti

Questo documento spiega come configurare e utilizzare diversi modelli Amazon Bedrock per generare riassunti in italiano.

> **Lingue disponibili**: [English](MODELS.md) | [Italiano (corrente)](MODELS.it.md)

## Modelli Supportati

Il bot supporta automaticamente due tipi di modelli:

### 1. Amazon Nova Micro (Default)
- **Model ID**: `amazon.nova-micro-v1:0` o `eu.amazon.nova-micro-v1:0`
- **Vantaggi**: 
  - Economico per alto volume
  - Veloce (< 1 secondo per riassunto)
  - Buona qualità in italiano
  - Disponibile tramite inference profile cross-region
- **Costo**: ~$0.000035 per 1000 token input, ~$0.00014 per 1000 token output

### 2. Llama 3.2 3B Instruct
- **Model ID**: `us.meta.llama3-2-3b-instruct-v1:0`
- **Vantaggi**:
  - Ottimo per riassunti e traduzioni
  - Buona comprensione del contesto
  - Supporto multilingua nativo
- **Costo**: ~$0.00015 per 1000 token input, ~$0.0002 per 1000 token output
- **Nota**: Richiede accesso al modello nella tua regione AWS

## Come Cambiare Modello

### Opzione 1: Modifica Infrastructure Template

Modifica il file `infrastructure/template.yaml`:

```yaml
Parameters:
  BedrockModelId:
    Type: String
    Default: 'us.meta.llama3-2-3b-instruct-v1:0'  # Cambia qui
    Description: 'Amazon Bedrock model ID for AI summarization'
```

### Opzione 2: Modifica Pipeline Template

Se usi CodePipeline, modifica `infrastructure/pipeline-template.yaml`:

```yaml
Environment:
  Variables:
    BEDROCK_MODEL_ID: 'us.meta.llama3-2-3b-instruct-v1:0'  # Cambia qui
```

### Opzione 3: Variabile d'Ambiente

Imposta la variabile d'ambiente direttamente nella Lambda:

```bash
aws lambda update-function-configuration \
  --function-name another-rss-telegram-bot-processor \
  --environment Variables={BEDROCK_MODEL_ID=us.meta.llama3-2-3b-instruct-v1:0}
```

## Permessi IAM Necessari

Il ruolo Lambda include già i permessi per entrambi i modelli Nova Micro e Llama 3.2.

La policy IAM in `infrastructure/template.yaml` include:

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
          - !Sub 'arn:aws:bedrock:*::foundation-model/*'
```

## Verifica Disponibilità Modello

Prima di usare un modello, verifica che sia disponibile nella tua regione:

```bash
aws bedrock list-foundation-models \
  --region eu-west-1 \
  --query "modelSummaries[?contains(modelId, 'llama3-2-3b')]"
```

## Risoluzione Problemi

### Problema: "Perché conta" invece di "Perché ti può interessare"

**Causa**: Il modello non segue esattamente le istruzioni del prompt.

**Soluzione**: 
1. Il template è stato aggiornato con istruzioni più esplicite
2. Se il problema persiste, considera di usare un modello più grande (es. Llama 3.2 11B o Claude)
3. Il fallback locale usa sempre "Perché ti può interessare"

### Problema: AccessDeniedException

**Causa**: Non hai accesso al modello nella tua regione.

**Soluzione**:
1. Vai alla console AWS Bedrock
2. Richiedi accesso al modello desiderato
3. Attendi l'approvazione (di solito immediata per modelli standard)

### Problema: ValidationException

**Causa**: Formato della richiesta non valido per il modello.

**Soluzione**:
1. Verifica che il model ID sia corretto
2. Il codice rileva automaticamente il tipo di modello (Nova vs Llama)
3. Se usi un modello diverso, potrebbe essere necessario aggiornare `src/summarize.py`

## Confronto Modelli

| Caratteristica | Nova Micro | Llama 3.2 3B |
|----------------|------------|--------------|
| Velocità | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Costo | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Qualità IT | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Seguire istruzioni | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| Disponibilità | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |

## Aggiungere Altri Modelli

Per supportare altri modelli Bedrock (es. Claude, Mistral):

1. Identifica il formato API del modello nella [documentazione AWS](https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters.html)

2. Modifica `src/summarize.py` nel metodo `bedrock_summarize()`:

```python
# Esempio per Claude
if "claude" in self.config.model_id.lower():
    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": self.config.max_tokens,
        "temperature": 0.3
    }
    # Parse response
    summary_text = response_body["content"][0]["text"]
```

3. Aggiorna i permessi IAM per includere il nuovo modello

4. Testa accuratamente prima del deployment in produzione

## Raccomandazioni

- **Per produzione**: Usa Nova Micro per il miglior rapporto costo/prestazioni
- **Per qualità massima**: Usa Llama 3.2 3B o modelli più grandi
- **Per multilingua**: Llama 3.2 ha supporto nativo migliore
- **Per budget limitato**: Nova Micro è la scelta più economica

## Fallback Locale

Se Bedrock non è disponibile o fallisce, il bot usa automaticamente un sistema di riassunto estrattivo locale che:
- Non richiede API esterne
- È sempre disponibile
- Usa sempre "Perché ti può interessare" (corretto)
- Ha qualità inferiore ma è affidabile
