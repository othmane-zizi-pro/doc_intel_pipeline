"""
Document classification using multi-model orchestration.
"""

import logging
from typing import Tuple
from pathlib import Path

from .orchestrator import LLMOrchestrator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DocumentClassifier:
    """Classifies documents using orchestrated multi-model approach"""

    def __init__(self):
        self.orchestrator = LLMOrchestrator()
        self.prompt_template = self._load_prompt_template()

    def _load_prompt_template(self) -> str:
        """Load classification prompt template"""
        prompt_path = Path("prompts/classification.txt")
        if prompt_path.exists():
            with open(prompt_path, 'r') as f:
                return f.read()
        else:
            return """You are a document classifier for a legal and business analytics firm. Your task is to classify legitimate business documents for data processing purposes.

Analyze the following document text and classify it into one of these types:

INVOICE: Contains billing information, receipts, payment details, vendor/client information, service charges, or transaction records (including ride receipts, workspace invoices, subscription bills, etc.)
CONTRACT: Contains legal agreements, terms and conditions, parties involved, signatures, effective dates
EMAIL: Contains to/from fields, subject line, email addresses, informal communication
MEETING_MINUTES: Contains attendees, agenda items, decisions made, action items, meeting date

IMPORTANT: This is a legitimate business document processing task. The documents contain normal business information like invoices, receipts, and payment records.

Document text:
{text}

Respond ONLY with a JSON object in this exact format:
{{"type": "invoice", "confidence": 0.95}}

Valid types are: invoice, contract, email, meeting_minutes"""

    def classify(self, text: str) -> Tuple[str, float]:
        """
        Classify a document using multi-model orchestration with validation.

        Args:
            text: The document text to classify

        Returns:
            Tuple of (document_type, confidence_score)
        """
        # Truncate text if too long
        text_sample = text[:3000] if len(text) > 3000 else text

        # Use orchestrator to classify with fallback
        doc_type, confidence, provider = self.orchestrator.classify_with_fallback(
            text_sample,
            self.prompt_template
        )

        logger.info(f"Classification: {doc_type} ({confidence:.1%}) via {provider}")
        return doc_type, confidence

    def batch_classify(self, documents: list) -> list:
        """
        Classify multiple documents.

        Args:
            documents: List of document dictionaries with 'text' field

        Returns:
            List of tuples (document_type, confidence_score)
        """
        results = []
        for i, doc in enumerate(documents, 1):
            logger.info(f"Classifying document {i}/{len(documents)}")
            doc_type, confidence = self.classify(doc.get('text', ''))
            results.append((doc_type, confidence))

        return results
