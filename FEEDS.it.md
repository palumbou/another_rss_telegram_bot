# Configurazione Feed RSS

> **Lingue disponibili**: [English](FEEDS.md) | [Italiano (corrente)](FEEDS.it.md)

## Panoramica

Il file `feeds.json` contiene la lista dei feed RSS che il bot monitorerà. Questo file è incluso nel package di deployment e letto dalla funzione Lambda a runtime.

## Formato File

```json
{
  "feeds": [
    {
      "url": "https://example.com/feed.xml",
      "name": "Feed Esempio",
      "enabled": true
    }
  ]
}
```

### Campi

- **url** (richiesto): L'URL del feed RSS/Atom
- **name** (opzionale): Nome leggibile per il feed
- **enabled** (opzionale): Se questo feed è attivo (default: true)

## Feed Predefiniti

Il `feeds.json` predefinito include feed relativi ad AWS:

- AWS Blog
- AWS What's New
- AWS Security Blog
- AWS Compute Blog
- AWS Database Blog

## Personalizzazione

### Opzione 1: Modifica feeds.json

Modifica il file `feeds.json` nella root del progetto:

```json
{
  "feeds": [
    {
      "url": "https://techcrunch.com/feed/",
      "name": "TechCrunch",
      "enabled": true
    },
    {
      "url": "https://www.theverge.com/rss/index.xml",
      "name": "The Verge",
      "enabled": true
    }
  ]
}
```

Poi deploya con:

```bash
./scripts/deploy.sh --update-code
```

### Opzione 2: Usa File Feed Personalizzato

Crea il tuo file feeds e specificalo durante il deployment:

```bash
./scripts/deploy.sh \
  --telegram-token "TUO_TOKEN" \
  --chat-id "TUO_CHAT_ID" \
  --feeds-file /percorso/al/mio-feeds.json
```

## Disabilitare Feed

Per disabilitare temporaneamente un feed senza rimuoverlo:

```json
{
  "feeds": [
    {
      "url": "https://example.com/feed.xml",
      "name": "Feed Esempio",
      "enabled": false
    }
  ]
}
```

## Validazione

Lo script di deployment valida automaticamente il file feeds:

- Controlla la sintassi JSON
- Verifica la struttura richiesta
- Conta i feed abilitati
- Riporta errori di validazione

## Best Practices

1. **Testa prima i feed**: Verifica che gli URL dei feed siano accessibili prima del deployment
2. **Usa nomi descrittivi**: Aiuta a identificare i feed nei log
3. **Inizia con pochi**: Comincia con pochi feed e aggiungine gradualmente
4. **Monitora le performance**: Più feed = tempo di esecuzione più lungo
5. **Controlla i formati**: Assicurati che i feed siano compatibili RSS 2.0 o Atom

## Risoluzione Problemi

### Errore Feed Non Trovato

Se vedi "Feeds file not found" nei log:
- Assicurati che `feeds.json` sia nella root del progetto
- Verifica che il file sia incluso nel package di deployment
- Controlla i permessi del file

### Nessun Feed Abilitato

Se vedi "No enabled feeds found":
- Controlla che almeno un feed abbia `"enabled": true`
- Verifica che la struttura JSON sia corretta
- Assicurati che l'array feeds non sia vuoto

### JSON Non Valido

Se il deployment fallisce con errore di validazione JSON:
- Usa un validatore JSON (es. jsonlint.com)
- Controlla virgole o parentesi mancanti
- Verifica che le virgolette siano correttamente escaped

## Esempi

### Feed Notizie Tech

```json
{
  "feeds": [
    {
      "url": "https://techcrunch.com/feed/",
      "name": "TechCrunch",
      "enabled": true
    },
    {
      "url": "https://www.theverge.com/rss/index.xml",
      "name": "The Verge",
      "enabled": true
    },
    {
      "url": "https://arstechnica.com/feed/",
      "name": "Ars Technica",
      "enabled": true
    }
  ]
}
```

### Blog Sviluppo

```json
{
  "feeds": [
    {
      "url": "https://github.blog/feed/",
      "name": "GitHub Blog",
      "enabled": true
    },
    {
      "url": "https://stackoverflow.blog/feed/",
      "name": "Stack Overflow Blog",
      "enabled": true
    },
    {
      "url": "https://dev.to/feed",
      "name": "DEV Community",
      "enabled": true
    }
  ]
}
```