"""
Field extraction using multi-model orchestration.
"""

import logging
from typing import Dict, Any
from pathlib import Path

from .orchestrator import LLMOrchestrator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FieldExtractor:
    """Extracts structured fields using orchestrated multi-model approach"""

    def __init__(self):
        self.orchestrator = LLMOrchestrator()
        self.prompts = self._load_prompts()

    def _load_prompts(self) -> Dict[str, str]:
        """Load extraction prompts for each document type"""
        prompts = {}
        prompt_files = {
            'invoice': 'prompts/invoice_extraction.txt',
            'contract': 'prompts/contract_extraction.txt',
            'email': 'prompts/email_extraction.txt',
            'meeting_minutes': 'prompts/meeting_extraction.txt'
        }

        for doc_type, file_path in prompt_files.items():
            path = Path(file_path)
            if path.exists():
                with open(path, 'r') as f:
                    prompts[doc_type] = f.read()
            else:
                prompts[doc_type] = self._get_default_prompt(doc_type)

        return prompts

    def _get_default_prompt(self, doc_type: str) -> str:
        """Get default extraction prompt for document type"""
        if doc_type == 'invoice':
            return """Extract the following fields from this invoice document:

{text}

Extract and return ONLY a JSON object with these fields:
{{
  "invoice_number": "the invoice number or ID",
  "invoice_date": "the invoice date in YYYY-MM-DD format",
  "client_name": "the client or customer name",
  "vendor_name": "the vendor or company issuing invoice",
  "total_amount": the total amount as a number,
  "currency": "the currency code (USD, CAD, etc)",
  "subtotal": the subtotal as a number,
  "tax": the tax amount as a number,
  "payment_method": "payment method used",
  "involved_parties": ["list", "of", "all", "parties"]
}}

If a field is not found, use null. For amounts, use numbers without currency symbols."""

        elif doc_type == 'contract':
            return """Extract the following fields from this contract document:

{text}

Extract and return ONLY a JSON object with these fields:
{{
  "contract_id": "contract reference number",
  "contract_date": "contract date",
  "parties": ["party 1", "party 2"],
  "contract_value": the contract value as a number,
  "currency": "currency code",
  "effective_date": "when contract starts",
  "expiry_date": "when contract ends",
  "key_terms": "brief summary of key terms",
  "contract_type": "type of contract",
  "involved_parties": ["all parties mentioned"]
}}

If a field is not found, use null."""

        elif doc_type == 'email':
            return """Extract the following fields from this email:

{text}

Extract and return ONLY a JSON object with these fields:
{{
  "sender": "sender email or name",
  "recipients": ["recipient1", "recipient2"],
  "email_date": "email date",
  "subject": "email subject line",
  "key_points": "brief summary of main points",
  "involved_parties": ["all people mentioned"]
}}

If a field is not found, use null."""

        else:  # meeting_minutes
            return """Extract the following fields from these meeting minutes:

{text}

Extract and return ONLY a JSON object with these fields:
{{
  "meeting_date": "date of meeting",
  "meeting_title": "meeting title or topic",
  "attendees": ["person1", "person2"],
  "agenda_items": ["item1", "item2"],
  "decisions": ["decision1", "decision2"],
  "action_items": [
    {{"task": "what to do", "assignee": "who", "deadline": "when"}}
  ],
  "involved_parties": ["all attendees and mentioned people"]
}}

If a field is not found, use null or empty array."""

    def extract(self, text: str, doc_type: str) -> Dict[str, Any]:
        """
        Extract structured fields using multi-model orchestration with validation.

        Args:
            text: The document text
            doc_type: The document type (invoice, contract, email, meeting_minutes)

        Returns:
            Dictionary of extracted fields
        """
        # Get the appropriate prompt
        prompt_template = self.prompts.get(doc_type)
        if not prompt_template:
            logger.error(f"No prompt found for document type: {doc_type}")
            return {}

        # Use orchestrator to extract with fallback and validation
        extracted_data, provider = self.orchestrator.extract_with_fallback(
            text,
            doc_type,
            prompt_template
        )

        logger.info(f"Extracted {len(extracted_data)} fields via {provider}")
        return extracted_data

    def batch_extract(self, documents: list, doc_types: list) -> list:
        """
        Extract fields from multiple documents.

        Args:
            documents: List of document dictionaries with 'text' field
            doc_types: List of document types corresponding to each document

        Returns:
            List of extracted field dictionaries
        """
        results = []
        for i, (doc, doc_type) in enumerate(zip(documents, doc_types), 1):
            logger.info(f"Extracting fields from document {i}/{len(documents)} ({doc_type})")
            extracted = self.extract(doc.get('text', ''), doc_type)
            results.append(extracted)

        return results
