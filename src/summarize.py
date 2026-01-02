"""Summarization module using Amazon Bedrock with fallback."""

import json
import re

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from .config import BedrockConfig
from .logging_config import create_execution_logger
from .models import FeedItem, Summary


class Summarizer:
    """Summarizer that uses Amazon Bedrock with extractive fallback."""

    def __init__(self, config: BedrockConfig, execution_id: str | None = None):
        """Initialize the summarizer with Bedrock configuration."""
        self.config = config
        self.logger = create_execution_logger("summarizer", execution_id)
        self.bedrock_client = None
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

    def summarize(self, item: FeedItem) -> Summary:
        """Generate summary for a feed item using Bedrock or fallback."""
        self.logger.info("Starting summarization", item_title=item.title)

        try:
            # Try Bedrock first
            if self.bedrock_client:
                self.logger.info(
                    "Attempting Bedrock summarization", item_title=item.title
                )
                summary_text = self.bedrock_summarize(item.content)
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
                "Using fallback extractive summarization", item_title=item.title
            )
            summary_text = self.fallback_summarize(item.content)
            summary = self.format_summary(summary_text)
            self.logger.info(
                "Successfully generated fallback summary",
                item_title=item.title,
                summary_method="extractive",
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

    def bedrock_summarize(self, content: str) -> str | None:
        """Generate summary using Amazon Bedrock Claude 3 Haiku."""
        if not self.bedrock_client:
            self.logger.warning("Bedrock client not available")
            return None

        # Italian prompt template
        prompt = f"""Riassumi questo articolo in italiano seguendo questo formato:
- Una riga di titolo (massimo 10 parole)
- Tre punti elenco, ciascuno massimo 15 parole
- Una riga finale "Perché conta:" seguita da massimo 20 parole

Articolo: {content}

Non inventare informazioni non presenti nell'articolo."""

        try:
            self.logger.debug(
                "Calling Bedrock API",
                model_id=self.config.model_id,
                content_length=len(content),
            )

            # Prepare request for Claude 3 Haiku
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": self.config.max_tokens,
                "messages": [{"role": "user", "content": prompt}],
            }

            response = self.bedrock_client.invoke_model(
                modelId=self.config.model_id,
                body=json.dumps(request_body),
                contentType="application/json",
                accept="application/json",
            )

            response_body = json.loads(response["body"].read())
            summary_text = response_body.get("content", [{}])[0].get("text", "")

            if summary_text:
                self.logger.info(
                    "Successfully generated summary using Bedrock",
                    response_length=len(summary_text),
                )
                return summary_text.strip()
            else:
                self.logger.warning("Empty response from Bedrock")
                return None

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "AccessDeniedException":
                self.logger.warning(
                    "Access denied to Bedrock - falling back to extractive summarization"
                )
            else:
                self.logger.error(f"Bedrock client error: {e}", error_code=error_code)
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error calling Bedrock: {e}", error=str(e))
            return None

    def fallback_summarize(self, content: str) -> str:
        """Generate extractive summary without external dependencies."""
        # Clean and prepare text
        text = re.sub(r"<[^>]+>", "", content)  # Remove HTML tags
        text = re.sub(r"\s+", " ", text).strip()  # Normalize whitespace

        if not text:
            return "Contenuto non disponibile\n• Articolo vuoto o non leggibile\n• Consultare il link originale\n• Informazioni potrebbero essere disponibili online\nPerché conta: Il contenuto potrebbe contenere informazioni rilevanti"

        # Split into sentences
        sentences = re.split(r"[.!?]+", text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]

        if not sentences:
            return "Contenuto breve disponibile\n• Testo troppo breve per il riassunto\n• Consultare l'articolo completo\n• Dettagli nel link originale\nPerché conta: Informazioni aggiuntive potrebbero essere importanti"

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

        # Create bullet points (max 15 words each)
        bullets = []
        for sentence in top_sentences:
            words = sentence.split()[:15]
            bullet = " ".join(words)
            if not bullet.endswith("."):
                bullet += "..."
            bullets.append(bullet)

        # Ensure we have 3 bullets
        while len(bullets) < 3:
            bullets.append("Informazioni aggiuntive nell'articolo completo...")

        # Create why it matters
        why_it_matters = "Contiene informazioni rilevanti per il settore"

        # Format as expected by format_summary
        formatted_text = f"{title}\n"
        for bullet in bullets[:3]:
            formatted_text += f"• {bullet}\n"
        formatted_text += f"Perché conta: {why_it_matters}"

        return formatted_text

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

        for line in lines[1:]:
            if line.startswith("•") or line.startswith("-"):
                bullet = line[1:].strip()
                if bullet:
                    bullets.append(bullet)
            elif line.lower().startswith("perché conta:") or line.lower().startswith(
                "why it matters:"
            ):
                why_it_matters = re.sub(
                    r"^(perché conta:|why it matters:)\s*",
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

        bullets = [" ".join(bullet.split()[:15]) for bullet in bullets]

        why_it_matters_words = why_it_matters.split()[:20]
        why_it_matters = " ".join(why_it_matters_words)

        return Summary(title=title, bullets=bullets, why_it_matters=why_it_matters)
