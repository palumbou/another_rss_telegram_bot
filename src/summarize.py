"""Summarization module using Amazon Bedrock with fallback."""

import json
import re
from pathlib import Path

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from .config import BedrockConfig
from .logging_config import create_execution_logger
from .models import FeedItem, Summary


class Summarizer:
    """Summarizer that uses Amazon Bedrock with extractive fallback."""

    TEMPLATE_FILE = "prompts/bedrock_summary_template.txt"

    def __init__(self, config: BedrockConfig, execution_id: str | None = None):
        """Initialize the summarizer with Bedrock configuration."""
        self.config = config
        self.logger = create_execution_logger("summarizer", execution_id)
        self.bedrock_client = None
        self.prompt_template = self._load_prompt_template()
        self._initialize_bedrock_client()

    def _initialize_bedrock_client(self) -> None:
        """Initialize Bedrock client with error handling."""
        try:
            self.bedrock_client = boto3.client(
                "bedrock-runtime", region_name=self.config.region
            )
            self.logger.info("Initialized Bedrock client", region=self.config.region)
        except (NoCredentialsError, ClientError) as e:
            self.logger.warning(
                f"Failed to initialize Bedrock client: {e}", error=str(e)
            )
            self.bedrock_client = None

    def _load_prompt_template(self) -> str:
        """Load prompt template from file."""
        # Try to find template in current directory or Lambda root
        template_file = Path(self.TEMPLATE_FILE)
        if not template_file.exists():
            # Try in Lambda root directory
            template_file = Path("/var/task") / self.TEMPLATE_FILE
        
        if template_file.exists():
            try:
                with open(template_file, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception as e:
                self.logger.warning(f"Failed to load template file: {e}")
        
        # Fallback to default template (matches bedrock_summary_template.txt)
        return """Riassumi questo articolo in italiano seguendo ESATTAMENTE questo formato:

FORMATO RICHIESTO:
- Una riga di titolo (massimo 10 parole, senza prefissi come "Titolo:")
- Tre punti elenco, ciascuno massimo 30 parole
- Una riga finale che inizia ESATTAMENTE con "Perché ti può interessare:" seguita da massimo 20 parole
- Alla fine inserisci la fonte

ESEMPIO OUTPUT:
AWS lancia nuovo servizio di machine learning

• Servizio completamente gestito per modelli di deep learning
• Integrazione nativa con S3 e altri servizi AWS esistenti  
• Pricing pay-per-use senza costi fissi o minimi

Perché ti può interessare: Democratizza l'accesso al machine learning per sviluppatori senza esperienza specifica in AI.

Fonte: https://aws.amazon.com/blogs/aws/example-article

REGOLE CRITICHE:
1. Usa SOLO informazioni presenti nell'articolo originale
2. Non inventare dettagli, date o informazioni non menzionate
3. Mantieni il tono professionale ma accessibile
4. Usa terminologia tecnica appropriata quando necessaria
5. Concentrati sui benefici pratici e l'impatto per gli utenti
6. Includi SEMPRE la fonte (URL) alla fine del riassunto
7. ATTENZIONE: Devi scrivere ESATTAMENTE "Perché ti può interessare:" - NON usare "Perché conta:", "Why it matters:", o altre varianti
8. La frase "Perché ti può interessare:" è OBBLIGATORIA e deve essere scritta ESATTAMENTE così

ARTICOLO DA RIASSUMERE:
{content}

URL ARTICOLO:
{url}

Inizia il riassunto ora, ricordando di usare ESATTAMENTE "Perché ti può interessare:" nella riga finale:"""

    def summarize(self, item: FeedItem) -> Summary:
        """Generate summary for a feed item using Bedrock with fallback."""
        self.logger.info("Starting summarization", item_title=item.title)

        try:
            # Try Bedrock first
            if self.bedrock_client:
                self.logger.info("Attempting Bedrock summarization", item_title=item.title)
                summary_text = self.bedrock_summarize(item.content, item.link)
                
                if summary_text:
                    summary = self.format_summary(summary_text)
                    self.logger.info(
                        "Successfully generated Bedrock summary",
                        item_title=item.title,
                        summary_method="bedrock",
                    )
                    return summary
            
            # Fallback to extractive summarization
            self.logger.info(
                "Using enhanced fallback summarization", item_title=item.title
            )
            summary_text = self.fallback_summarize(item.content, item.link)
            summary = self.format_summary(summary_text)
            self.logger.info(
                "Successfully generated fallback summary",
                item_title=item.title,
                summary_method="enhanced_fallback",
            )
            return summary

        except Exception as e:
            self.logger.error(
                f"Error in summarization: {e}", item_title=item.title, error=str(e)
            )
            # Emergency fallback - use title and truncated content
            return Summary(
                title=item.title[:50] + "..." if len(item.title) > 50 else item.title,
                bullets=[
                    "Contenuto non disponibile per il riassunto",
                    "Consultare l'articolo originale per dettagli",
                    "Errore durante l'elaborazione del testo",
                ],
                why_it_matters="Informazioni importanti disponibili nell'articolo completo",
            )

    def bedrock_summarize(self, content: str, url: str) -> str | None:
        """Generate summary using Amazon Bedrock (supports Nova Micro and Llama models)."""
        if not self.bedrock_client:
            self.logger.warning("Bedrock client not available")
            return None

        # Use template and substitute content and URL
        prompt = self.prompt_template.format(content=content, url=url)

        try:
            self.logger.debug(
                "Calling Bedrock API",
                model_id=self.config.model_id,
                content_length=len(content),
            )

            # Detect model type and prepare appropriate request
            if "llama" in self.config.model_id.lower():
                # Llama 3.2 format
                request_body = {
                    "prompt": prompt,
                    "max_gen_len": self.config.max_tokens,
                    "temperature": 0.3,
                    "top_p": 0.9
                }
            else:
                # Amazon Nova Micro format (default)
                request_body = {
                    "messages": [{"role": "user", "content": [{"text": prompt}]}],
                    "inferenceConfig": {
                        "max_new_tokens": self.config.max_tokens,
                        "temperature": 0.3
                    }
                }

            response = self.bedrock_client.invoke_model(
                modelId=self.config.model_id,
                body=json.dumps(request_body),
                contentType="application/json",
                accept="application/json",
            )

            response_body = json.loads(response["body"].read())
            
            # Parse response based on model type
            summary_text = None
            
            if "llama" in self.config.model_id.lower():
                # Llama response format
                if "generation" in response_body:
                    summary_text = response_body["generation"]
                    self.logger.info(
                        "Successfully generated summary using Bedrock Llama",
                        response_length=len(summary_text),
                    )
            else:
                # Nova response format
                if "output" in response_body and "message" in response_body["output"]:
                    message = response_body["output"]["message"]
                    if "content" in message and len(message["content"]) > 0:
                        summary_text = message["content"][0].get("text", "")
                        self.logger.info(
                            "Successfully generated summary using Bedrock Nova",
                            response_length=len(summary_text),
                        )
            
            if summary_text and summary_text.strip():
                return summary_text.strip()
            else:
                self.logger.warning(f"Empty or invalid response from model {self.config.model_id}")
                return None

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "AccessDeniedException":
                self.logger.warning(
                    "Access denied to Bedrock - falling back to extractive summarization"
                )
            elif error_code == "ValidationException":
                self.logger.warning(
                    f"Validation error with {self.config.model_id}: {e} - falling back to extractive summarization"
                )
            else:
                self.logger.error(f"Bedrock client error: {e}", error_code=error_code)
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error calling Bedrock: {e}", error=str(e))
            return None

    def fallback_summarize(self, content: str, url: str) -> str:
        """Generate extractive summary without external dependencies."""
        # Clean and prepare text
        text = re.sub(r"<[^>]+>", "", content)  # Remove HTML tags
        text = re.sub(r"\s+", " ", text).strip()  # Normalize whitespace

        if not text:
            return f"Contenuto non disponibile\n• Articolo vuoto o non leggibile\n• Consultare il link originale\n• Informazioni potrebbero essere disponibili online\nPerché conta: Il contenuto potrebbe contenere informazioni rilevanti\n\nFonte: {url}"

        # Split into sentences
        sentences = re.split(r"[.!?]+", text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]

        if not sentences:
            return f"Contenuto breve disponibile\n• Testo troppo breve per il riassunto\n• Consultare l'articolo completo\n• Dettagli nel link originale\nPerché conta: Informazioni aggiuntive potrebbero essere importanti\n\nFonte: {url}"

        # Simple sentence ranking by length and position
        scored_sentences = []
        for i, sentence in enumerate(sentences[:10]):  # Limit to first 10 sentences
            # Score based on position (earlier = higher) and length
            position_score = 1.0 - (i / len(sentences))
            length_score = min(len(sentence) / 100, 1.0)  # Normalize length
            total_score = position_score * 0.6 + length_score * 0.4
            scored_sentences.append((sentence, total_score))

        # Sort by score and take top sentences
        scored_sentences.sort(key=lambda x: x[1], reverse=True)
        top_sentences = [s[0] for s in scored_sentences[:3]]

        # Create title from first sentence
        title_words = (
            top_sentences[0].split()[:8] if top_sentences else ["Riassunto", "articolo"]
        )
        title = " ".join(title_words)

        # Create bullet points (max 30 words each)
        bullets = []
        for sentence in top_sentences:
            words = sentence.split()[:30]
            bullet = " ".join(words)
            if not bullet.endswith("."):
                bullet += "..."
            bullets.append(bullet)

        # Ensure we have 3 bullets
        while len(bullets) < 3:
            bullets.append("Informazioni aggiuntive nell'articolo completo...")

        # Create more specific why it matters based on content (FALLBACK only)
        why_it_matters = self._generate_why_it_matters(text)

        # Format as expected by format_summary
        # Use "Perché conta:" for fallback (different from Bedrock's "Perché ti può interessare:")
        formatted_text = f"{title}\n"
        for bullet in bullets[:3]:
            formatted_text += f"• {bullet}\n"
        formatted_text += f"Perché conta: {why_it_matters}\n\nFonte: {url}"

        return formatted_text

    def _generate_why_it_matters(self, content: str) -> str:
        """Generate a more specific 'why it matters' based on content keywords."""
        content_lower = content.lower()
        
        # Technology keywords
        if any(word in content_lower for word in ['ai', 'artificial intelligence', 'machine learning', 'ml']):
            return "Aggiornamenti sull'intelligenza artificiale che potrebbero influenzare il tuo lavoro"
        elif any(word in content_lower for word in ['security', 'sicurezza', 'vulnerability', 'breach']):
            return "Informazioni di sicurezza importanti per proteggere i tuoi sistemi"
        elif any(word in content_lower for word in ['aws', 'cloud', 'serverless', 'lambda']):
            return "Novità cloud che potrebbero ottimizzare la tua infrastruttura"
        elif any(word in content_lower for word in ['github', 'git', 'repository', 'open source']):
            return "Sviluppi nel mondo open source che potrebbero interessare i developer"
        elif any(word in content_lower for word in ['performance', 'optimization', 'speed', 'faster']):
            return "Miglioramenti delle prestazioni che potrebbero accelerare i tuoi progetti"
        elif any(word in content_lower for word in ['cost', 'pricing', 'save', 'budget']):
            return "Informazioni sui costi che potrebbero far risparmiare la tua azienda"
        elif any(word in content_lower for word in ['new', 'launch', 'announce', 'release']):
            return "Nuovi strumenti o servizi che potrebbero essere utili per il tuo lavoro"
        elif any(word in content_lower for word in ['update', 'version', 'feature']):
            return "Aggiornamenti che potrebbero migliorare i tuoi flussi di lavoro"
        else:
            return "Sviluppi tecnologici che potrebbero impattare il settore"

    def format_summary(self, raw_summary: str) -> Summary:
        """Parse and format raw summary text into Summary object."""
        lines = [line.strip() for line in raw_summary.split("\n") if line.strip()]

        if not lines:
            return Summary(
                title="Riassunto non disponibile",
                bullets=[
                    "Errore nella formattazione",
                    "Consultare articolo originale",
                    "Contenuto non elaborabile",
                ],
                why_it_matters="Informazioni potrebbero essere importanti",
            )

        # Extract title (first line)
        title = lines[0]
        # Remove common prefixes
        title = re.sub(r"^(Titolo:|Title:)\s*", "", title, flags=re.IGNORECASE)

        # Extract bullets (lines starting with • or -)
        bullets = []
        why_it_matters = ""
        source = ""

        for line in lines[1:]:
            if line.startswith("•") or line.startswith("-"):
                bullet = line[1:].strip()
                if bullet:
                    bullets.append(bullet)
            elif line.lower().startswith("perché ti può interessare:") or line.lower().startswith("perché conta:") or line.lower().startswith("why it matters:"):
                why_it_matters = re.sub(
                    r"^(perché ti può interessare:|perché conta:|why it matters:)\s*",
                    "",
                    line,
                    flags=re.IGNORECASE,
                )
            elif line.lower().startswith("fonte:") or line.lower().startswith("source:"):
                source = re.sub(
                    r"^(fonte:|source:)\s*",
                    "",
                    line,
                    flags=re.IGNORECASE,
                )

        # Ensure we have exactly 3 bullets
        if len(bullets) < 3:
            bullets.extend(["Dettagli nell'articolo completo"] * (3 - len(bullets)))
        bullets = bullets[:3]

        # Ensure why_it_matters is not empty
        if not why_it_matters:
            why_it_matters = "Informazioni rilevanti per il settore"

        # Truncate to word limits
        title_words = title.split()[:10]
        title = " ".join(title_words)

        bullets = [" ".join(bullet.split()[:30]) for bullet in bullets]

        why_it_matters_words = why_it_matters.split()[:20]
        why_it_matters = " ".join(why_it_matters_words)
        
        # Add source to why_it_matters if present
        if source:
            why_it_matters = f"{why_it_matters}\n\nFonte: {source}"

        return Summary(title=title, bullets=bullets, why_it_matters=why_it_matters)