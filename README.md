# Another RSS Telegram Bot

## Descrizione

Questo è un bot Telegram che monitora feed RSS e invia aggiornamenti automatici ai canali configurati. Il bot include funzionalità di deduplicazione, riassunto automatico dei contenuti e gestione intelligente degli aggiornamenti.

## Esperimento Kiro

**Questo progetto è un esperimento per testare le capacità di Kiro**, l'assistente AI per sviluppatori. L'obiettivo è esplorare come Kiro può assistere nello sviluppo di applicazioni complete, dalla specifica dei requisiti all'implementazione e testing.

### Caratteristiche del progetto sviluppate con Kiro:

- ✅ Specifica completa dei requisiti usando il formato EARS
- ✅ Design architetturale con proprietà di correttezza
- ✅ Implementazione guidata da property-based testing
- ✅ Test automatizzati con Hypothesis per Python
- ✅ Struttura modulare e manutenibile

## Funzionalità

- **Monitoraggio RSS**: Controllo periodico di feed RSS configurabili
- **Deduplicazione**: Evita l'invio di contenuti duplicati
- **Riassunto automatico**: Genera riassunti dei contenuti usando AI
- **Integrazione Telegram**: Invio automatico di messaggi ai canali
- **Gestione errori**: Handling robusto degli errori e retry logic
- **Logging strutturato**: Sistema di logging completo per debugging

## Architettura

Il progetto è strutturato come una funzione AWS Lambda con i seguenti componenti:

- `src/lambda_handler.py`: Entry point principale
- `src/rss.py`: Gestione dei feed RSS
- `src/telegram.py`: Integrazione con Telegram Bot API
- `src/summarize.py`: Generazione riassunti con AI
- `src/dedup.py`: Sistema di deduplicazione
- `src/config.py`: Gestione configurazione
- `src/models.py`: Modelli dati

## Testing

Il progetto utilizza un approccio dual-testing:

- **Unit tests**: Test specifici per casi d'uso e edge cases
- **Property-based tests**: Test con Hypothesis per validare proprietà universali

```bash
# Esegui tutti i test
pytest

# Esegui solo i property tests
pytest -k "properties"

# Esegui solo i unit tests  
pytest -k "unit"
```

## Deployment

Il progetto è configurato per il deployment su AWS Lambda usando SAM (Serverless Application Model).

```bash
# Build
sam build

# Deploy
sam deploy --guided
```

## Configurazione

Il bot richiede le seguenti variabili d'ambiente:

- `TELEGRAM_BOT_TOKEN`: Token del bot Telegram
- `TELEGRAM_CHAT_ID`: ID del canale/chat di destinazione
- `RSS_FEEDS`: Lista dei feed RSS da monitorare (JSON)
- `BEDROCK_MODEL_ID`: ID del modello AWS Bedrock per i riassunti

## Licenza

Questo progetto è rilasciato sotto licenza MIT.

---

*Sviluppato come esperimento con Kiro AI Assistant*