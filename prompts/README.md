# Prompt Templates

Questa directory contiene i template per i prompt utilizzati dai servizi AI del sistema RSS Telegram Bot.

## bedrock_summary_template.txt

Template principale utilizzato per generare riassunti tramite Amazon Bedrock (Claude 3 Haiku).

### Formato Riassunto Richiesto

Il template è progettato per produrre riassunti con questa struttura esatta:

```
[TITOLO] (massimo 10 parole)

• [PUNTO 1] (massimo 15 parole)
• [PUNTO 2] (massimo 15 parole)  
• [PUNTO 3] (massimo 15 parole)

Perché conta: [IMPATTO] (massimo 20 parole)
```

### Caratteristiche del Template

1. **Struttura Rigida**: Il formato è fisso per garantire consistenza nei messaggi Telegram
2. **Limiti di Parole**: Ottimizzato per la leggibilità su dispositivi mobili
3. **Lingua Italiana**: Tutti i riassunti sono generati in italiano
4. **Accuratezza**: Enfasi sulla fedeltà al contenuto originale
5. **Praticità**: Focus sui benefici e impatti pratici per l'utente

### Personalizzazione

Per modificare il formato dei riassunti:

1. Modifica il template in `bedrock_summary_template.txt`
2. Aggiorna la logica di parsing in `src/summarize.py`
3. Aggiorna i test in `tests/test_summarize_*.py`
4. Testa con diversi tipi di contenuto

### Variabili Template

- `{content}`: Il contenuto dell'articolo da riassumere (automaticamente sostituito)

### Best Practices

- Mantieni istruzioni chiare e specifiche
- Includi esempi concreti nel prompt
- Specifica limiti di lunghezza precisi
- Enfatizza l'accuratezza e la fedeltà al contenuto
- Usa un tono professionale ma accessibile

### Testing

Il template è testato tramite:
- Test unitari con contenuti specifici
- Test property-based per formato consistente
- Validazione manuale con diversi tipi di articoli

### Fallback

Se Bedrock non è disponibile, il sistema utilizza un riassunto estrattivo che non dipende da questo template ma mantiene un formato simile per consistenza.