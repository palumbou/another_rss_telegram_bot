# Template Prompt

> **Lingue disponibili**: [English](README.md) | [Italiano (corrente)](README.it.md)

Questa directory contiene i template per i prompt utilizzati dai servizi AI del sistema RSS Telegram Bot.

## bedrock_summary_template.txt

Template principale utilizzato per generare riassunti tramite Amazon Bedrock (Nova Micro).

### Formato Riassunto Richiesto

Il template è progettato per produrre riassunti con questa struttura esatta:

```
[TITOLO] (massimo 10 parole)

• [PUNTO 1] (massimo 30 parole)
• [PUNTO 2] (massimo 30 parole)  
• [PUNTO 3] (massimo 30 parole)

Perché ti può interessare: [IMPATTO] (massimo 20 parole)

Fonte: [URL]
```

### Caratteristiche del Template

1. **Struttura Rigida**: Il formato è fisso per garantire consistenza nei messaggi Telegram
2. **Limiti di Parole**: Ottimizzato per la leggibilità su dispositivi mobili
3. **Lingua Italiana**: Tutti i riassunti sono generati in italiano
4. **Accuratezza**: Enfasi sulla fedeltà al contenuto originale
5. **Praticità**: Focus sui benefici e impatti pratici per l'utente

### Modello AI

Il template è ottimizzato per **Amazon Nova Micro** (`eu.amazon.nova-micro-v1:0`), che:
- Genera riassunti in italiano di alta qualità
- Risponde rapidamente (< 1 secondo per riassunto)
- È economico per elaborazioni ad alto volume
- Disponibile tramite profilo di inferenza cross-region in EU

### Personalizzazione

Per modificare il formato dei riassunti:

1. Modifica il template in `bedrock_summary_template.txt`
2. Aggiorna la logica di parsing in `src/summarize.py` (metodo `format_summary()`)
3. Testa con diversi tipi di contenuto

**Importante**: Se modifichi il formato, assicurati che la logica di parsing in `src/summarize.py` corrisponda alla nuova struttura.

### Variabili Template

- `{content}`: Contenuto dell'articolo da riassumere (sostituito automaticamente)
- `{url}`: URL dell'articolo (sostituito automaticamente)

### Best Practices

- Mantieni istruzioni chiare e specifiche
- Includi esempi concreti nel prompt
- Specifica limiti di lunghezza precisi
- Enfatizza l'accuratezza e la fedeltà al contenuto
- Usa un tono professionale ma accessibile
- Sii esplicito sui requisiti di formato (es. "USA ESATTAMENTE 'Perché ti può interessare:'")

### Fallback

Se Bedrock non è disponibile, il sistema utilizza un riassunto estrattivo che non dipende da questo template ma mantiene un formato simile per consistenza. Il fallback usa "Perché conta:" con suggerimenti contestuali basati sulle parole chiave del contenuto.

### Testing

Testa il template:
- Deployando con feed di test (es. Hacker News, The Verge)
- Controllando i messaggi Telegram per il formato corretto
- Verificando la qualità e accuratezza dell'italiano
- Monitorando i log CloudWatch per successo/fallimento di Bedrock
