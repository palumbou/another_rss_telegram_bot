# GitHub Actions Workflows

Questo progetto utilizza GitHub Actions per automazione CI/CD, controlli di qualità e deployment.

## Workflows Disponibili

### 1. CI (ci.yml)
**Trigger**: Push su main/develop, Pull Request su main

**Jobs**:
- **lint**: Controllo stile codice con Ruff
- **test**: Esecuzione test unitari e property-based con pytest
- **security**: Scansione sicurezza con Bandit e Safety
- **validate-cloudformation**: Validazione template CloudFormation
- **build-package**: Creazione pacchetto Lambda per deployment

**Caratteristiche**:
- Python 3.12
- Coverage report con Codecov
- Artifact Lambda package
- Validazione YAML CloudFormation

### 2. Deploy (deploy.yml)
**Trigger**: Push su main, tag v*, workflow_dispatch

**Environments**:
- **staging**: Deploy automatico da main
- **production**: Deploy da tag o manuale

**Features**:
- Deploy automatico con script bash
- Smoke tests post-deployment
- GitHub releases per tag
- Configurazione multi-environment

### 3. Code Quality (code-quality.yml)
**Trigger**: Push, PR, schedule settimanale

**Analisi**:
- Linting completo con Ruff
- Type checking con MyPy
- Security analysis con Bandit/Safety
- Dead code detection con Vulture
- Complexity analysis con Radon
- Test coverage con report HTML

### 4. Dependabot Auto-merge (dependabot-auto-merge.yml)
**Trigger**: PR da Dependabot

**Funzionalità**:
- Auto-merge per aggiornamenti minor/patch
- Attesa completamento CI
- Merge con squash commit

## Configurazione Secrets

### Repository Secrets
```
# AWS Credentials
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
AWS_ACCESS_KEY_ID_PROD
AWS_SECRET_ACCESS_KEY_PROD

# Telegram Bot Tokens
TELEGRAM_BOT_TOKEN_STAGING
TELEGRAM_BOT_TOKEN_PROD

# Telegram Chat IDs
TELEGRAM_CHAT_ID_STAGING
TELEGRAM_CHAT_ID_PROD

# Optional: Codecov
CODECOV_TOKEN
```

### Environment Configuration

#### Staging Environment
- **Nome**: `staging`
- **Branch**: `main`
- **Stack**: `rss-telegram-bot-staging`
- **Protezioni**: Nessuna

#### Production Environment
- **Nome**: `production`
- **Branch**: `main` (tag v*) o manuale
- **Stack**: `rss-telegram-bot-prod`
- **Protezioni**: Review richiesta

## Badge Status

Aggiungi questi badge al README principale:

```markdown
[![CI](https://github.com/username/another-rss-telegram-bot/workflows/CI/badge.svg)](https://github.com/username/another-rss-telegram-bot/actions/workflows/ci.yml)
[![Deploy](https://github.com/username/another-rss-telegram-bot/workflows/Deploy/badge.svg)](https://github.com/username/another-rss-telegram-bot/actions/workflows/deploy.yml)
[![Code Quality](https://github.com/username/another-rss-telegram-bot/workflows/Code%20Quality/badge.svg)](https://github.com/username/another-rss-telegram-bot/actions/workflows/code-quality.yml)
[![codecov](https://codecov.io/gh/username/another-rss-telegram-bot/branch/main/graph/badge.svg)](https://codecov.io/gh/username/another-rss-telegram-bot)
```

## Personalizzazione

### Modifica Schedule
```yaml
schedule:
  - cron: '0 9 * * 1'  # Lunedì alle 9:00 UTC
```

### Aggiungere Nuovi Jobs
1. Crea nuovo file in `.github/workflows/`
2. Definisci trigger appropriati
3. Aggiungi secrets necessari
4. Testa con workflow_dispatch

### Configurare Notifications
```yaml
- name: Notify Slack
  if: failure()
  uses: 8398a7/action-slack@v3
  with:
    status: failure
    webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

## Best Practices

1. **Secrets Management**: Mai hardcodare credenziali
2. **Environment Protection**: Usa environment per production
3. **Artifact Retention**: Limita retention days per costi
4. **Conditional Execution**: Usa `if` per ottimizzare esecuzioni
5. **Matrix Builds**: Testa su multiple versioni Python se necessario

## Troubleshooting

### Errori Comuni

**AWS Credentials Invalid**:
```bash
# Verifica secrets configurati
# Controlla permessi IAM
# Verifica regione AWS
```

**Test Failures**:
```bash
# Controlla log dettagliati
# Verifica dipendenze aggiornate
# Esegui test localmente
```

**Deployment Failures**:
```bash
# Verifica CloudFormation template
# Controlla limiti AWS account
# Verifica nomi risorse univoci
```

### Debug Workflows

1. Abilita debug logging:
```yaml
env:
  ACTIONS_STEP_DEBUG: true
  ACTIONS_RUNNER_DEBUG: true
```

2. Usa workflow_dispatch per test manuali
3. Controlla Actions tab per log dettagliati
4. Usa `continue-on-error: true` per step informativi