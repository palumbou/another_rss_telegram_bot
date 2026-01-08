# Test dei Modelli AI

Questa guida spiega come testare i diversi modelli AI per verificare che funzionino correttamente.

> **Lingue disponibili**: [English](TEST-MODELS.md) | [Italiano (corrente)](TEST-MODELS.it.md)

## Test Rapido con AWS CLI

### Test Nova Micro

```bash
aws bedrock-runtime invoke-model \
  --model-id amazon.nova-micro-v1:0 \
  --region eu-west-1 \
  --body '{
    "messages": [{"role": "user", "content": [{"text": "Riassumi in italiano: AWS ha lanciato un nuovo servizio"}]}],
    "inferenceConfig": {"max_new_tokens": 500, "temperature": 0.3}
  }' \
  --cli-binary-format raw-in-base64-out \
  output.json

cat output.json
```

### Test Llama 3.2 3B

```bash
aws bedrock-runtime invoke-model \
  --model-id us.meta.llama3-2-3b-instruct-v1:0 \
  --region us-east-1 \
  --body '{
    "prompt": "Riassumi in italiano: AWS ha lanciato un nuovo servizio",
    "max_gen_len": 500,
    "temperature": 0.3
  }' \
  --cli-binary-format raw-in-base64-out \
  output.json

cat output.json
```

## Test con Python

Crea un file `test_model.py`:

```python
import boto3
import json

def test_nova_micro():
    """Test Amazon Nova Micro"""
    client = boto3.client('bedrock-runtime', region_name='eu-west-1')
    
    request = {
        "messages": [{"role": "user", "content": [{"text": "Riassumi in italiano: AWS ha lanciato un nuovo servizio di machine learning"}]}],
        "inferenceConfig": {"max_new_tokens": 500, "temperature": 0.3}
    }
    
    response = client.invoke_model(
        modelId='amazon.nova-micro-v1:0',
        body=json.dumps(request)
    )
    
    result = json.loads(response['body'].read())
    print("Nova Micro Response:")
    print(result['output']['message']['content'][0]['text'])
    print("\n" + "="*50 + "\n")

def test_llama():
    """Test Llama 3.2 3B"""
    client = boto3.client('bedrock-runtime', region_name='us-east-1')
    
    request = {
        "prompt": "Riassumi in italiano: AWS ha lanciato un nuovo servizio di machine learning",
        "max_gen_len": 500,
        "temperature": 0.3
    }
    
    response = client.invoke_model(
        modelId='us.meta.llama3-2-3b-instruct-v1:0',
        body=json.dumps(request)
    )
    
    result = json.loads(response['body'].read())
    print("Llama 3.2 Response:")
    print(result['generation'])
    print("\n" + "="*50 + "\n")

if __name__ == "__main__":
    print("Testing models...\n")
    
    try:
        test_nova_micro()
    except Exception as e:
        print(f"Nova Micro failed: {e}\n")
    
    try:
        test_llama()
    except Exception as e:
        print(f"Llama failed: {e}\n")
```

Esegui:
```bash
python test_model.py
```

## Test del Bot Completo

### 1. Test Locale (senza deploy)

Usa lo script di test fornito:

```bash
# Test con Nova Micro (default)
python test_summarizer.py

# Test con Llama 3.2 3B
python test_summarizer.py us.meta.llama3-2-3b-instruct-v1:0
```

### 2. Test Lambda Deployed

Invoca la Lambda con un evento di test:

```bash
aws lambda invoke \
  --function-name another-rss-telegram-bot-processor \
  --payload '{"test": true}' \
  --region eu-west-1 \
  response.json

cat response.json
```

### 3. Verifica Logs

Controlla i log CloudWatch per vedere quale modello è stato usato:

```bash
aws logs tail /aws/lambda/another-rss-telegram-bot-processor \
  --follow \
  --region eu-west-1
```

Cerca linee come:
- `Successfully generated summary using Bedrock Nova`
- `Successfully generated summary using Bedrock Llama`
- `Using enhanced fallback summarization`

## Checklist Verifica

- [ ] Il modello è disponibile nella tua regione AWS
- [ ] Hai richiesto accesso al modello in Bedrock console
- [ ] I permessi IAM includono il modello
- [ ] La variabile `BEDROCK_MODEL_ID` è impostata correttamente
- [ ] Il riassunto contiene "Perché ti può interessare:" (non "Perché conta:")
- [ ] Il formato del riassunto è corretto (titolo + 3 bullet + why it matters)
- [ ] I messaggi vengono inviati correttamente su Telegram

## Risoluzione Problemi

### AccessDeniedException

**Causa**: Non hai accesso al modello nella tua regione.

**Soluzione**:
1. Vai alla console AWS Bedrock
2. Richiedi accesso al modello desiderato
3. Attendi l'approvazione (di solito immediata per modelli standard)

### ValidationException

**Causa**: Formato della richiesta non valido per il modello.

**Soluzione**:
1. Verifica che il model ID sia corretto
2. Il codice rileva automaticamente il tipo di modello (Nova vs Llama)
3. Se usi un modello diverso, potrebbe essere necessario aggiornare `src/summarize.py`

## Metriche da Monitorare

1. **Tasso di successo Bedrock**: Quante volte usa Bedrock vs fallback
2. **Latenza**: Tempo di risposta del modello
3. **Costi**: Token consumati per modello
4. **Qualità**: Verifica manuale dei riassunti generati
5. **Formato corretto**: "Perché ti può interessare" presente

## Prossimi Passi

Dopo aver verificato che tutto funziona:

1. Monitora per alcuni giorni
2. Confronta qualità tra Nova e Llama
3. Analizza i costi effettivi
4. Scegli il modello migliore per il tuo caso d'uso
5. Considera di testare modelli più grandi se necessario
