#!/usr/bin/env python3
"""
Script di test per verificare il funzionamento dei modelli AI.
Uso: python test_summarizer.py [model_id]

Esempi:
  python test_summarizer.py                                    # Usa Nova Micro (default)
  python test_summarizer.py us.meta.llama3-2-3b-instruct-v1:0 # Usa Llama 3.2 3B
"""

import os
import sys
from datetime import datetime, UTC

# Imposta il modello da testare
if len(sys.argv) > 1:
    model_id = sys.argv[1]
else:
    model_id = "amazon.nova-micro-v1:0"  # Default

# Configura environment
os.environ['BEDROCK_MODEL_ID'] = model_id
os.environ['CURRENT_AWS_REGION'] = 'eu-west-1' if 'nova' in model_id else 'us-east-1'

# Import dopo aver impostato le variabili d'ambiente
from src.summarize import Summarizer
from src.config import BedrockConfig
from src.models import FeedItem

def test_summarizer():
    """Test del summarizer con un articolo di esempio."""
    
    print(f"\n{'='*70}")
    print(f"Test Summarizer - Modello: {model_id}")
    print(f"Regione: {os.environ['CURRENT_AWS_REGION']}")
    print(f"{'='*70}\n")
    
    # Crea un item di test realistico
    item = FeedItem(
        title="AWS Announces New Serverless Database Service",
        link="https://aws.amazon.com/blogs/aws/example-article",
        published=datetime.now(UTC),
        content="""
        Amazon Web Services (AWS) today announced the general availability of Amazon Aurora Serverless v3, 
        a new version of the on-demand, auto-scaling configuration for Amazon Aurora. Aurora Serverless v3 
        scales instantly from hundreds to hundreds of thousands of transactions in a fraction of a second. 
        
        The new version provides improved scaling capabilities, supporting up to 128 TB of storage and 
        scaling in increments as small as 0.5 Aurora Capacity Units (ACUs). This fine-grained scaling 
        helps optimize costs for variable workloads.
        
        Key features include:
        - Instant scaling without connection drops
        - Support for all Aurora features including Global Database
        - Multi-AZ deployments for high availability
        - Integration with AWS Lambda and other serverless services
        
        Pricing is based on the database capacity used, measured in ACUs. Customers pay only for the 
        database capacity, storage, and I/O their database consumes while it's active.
        """,
        feed_url="https://aws.amazon.com/blogs/aws/feed/"
    )
    
    # Crea il summarizer
    config = BedrockConfig(
        model_id=model_id,
        region=os.environ['CURRENT_AWS_REGION']
    )
    
    print("Inizializzazione summarizer...")
    summarizer = Summarizer(config, execution_id="test")
    
    print("Generazione riassunto...\n")
    
    try:
        # Genera il riassunto
        summary = summarizer.summarize(item)
        
        # Mostra il risultato
        print(f"{'='*70}")
        print("RISULTATO:")
        print(f"{'='*70}\n")
        
        print(f"📌 TITOLO:\n{summary.title}\n")
        
        print("📝 PUNTI CHIAVE:")
        for i, bullet in enumerate(summary.bullets, 1):
            print(f"  {i}. {bullet}")
        
        print(f"\n💡 {summary.why_it_matters}\n")
        
        # Verifica che contenga "Perché ti può interessare"
        if "Perché ti può interessare:" in summary.why_it_matters:
            print("✅ SUCCESSO: Formato corretto con 'Perché ti può interessare:'")
        elif "Perché conta:" in summary.why_it_matters:
            print("⚠️  ATTENZIONE: Usa 'Perché conta:' invece di 'Perché ti può interessare:'")
        else:
            print("⚠️  ATTENZIONE: Formato 'Perché ti può interessare:' non trovato")
        
        print(f"\n{'='*70}\n")
        
    except Exception as e:
        print(f"\n❌ ERRORE durante la generazione del riassunto:")
        print(f"   {type(e).__name__}: {e}\n")
        
        if "AccessDeniedException" in str(e):
            print("💡 Suggerimento: Richiedi accesso al modello nella console AWS Bedrock")
        elif "ValidationException" in str(e):
            print("💡 Suggerimento: Verifica che il model ID sia corretto e disponibile nella regione")
        
        print(f"\n{'='*70}\n")
        return False
    
    return True

if __name__ == "__main__":
    print("\n🚀 Avvio test summarizer...")
    
    success = test_summarizer()
    
    if success:
        print("✅ Test completato con successo!\n")
        sys.exit(0)
    else:
        print("❌ Test fallito. Controlla gli errori sopra.\n")
        sys.exit(1)
