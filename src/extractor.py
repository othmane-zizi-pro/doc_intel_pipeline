"""
Field extraction module using Ollama LLM.
"""

import requests
import json
import logging
from typing import Dict, Any
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FieldExtractor:
    """Extracts structured fields from documents using Qwen LLM"""

    def __init__(self, model_name: str = "qwen2.5:7b", ollama_url: str = "http://localhost:11434"):
        self.model_name = model_name
        self.ollama_url = ollama_url
        self.api_endpoint = f"{ollama_url}/api/generate"

        # Load extraction prompts
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
  "invoice_date": "the invoice date",
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
        Extract structured fields from document text.

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

        # Create the prompt
        prompt = prompt_template.format(text=text)

        try:
            # Call Ollama API
            response = requests.post(
                self.api_endpoint,
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.2,  # Low temperature for consistent extraction
                }
            )

            if response.status_code == 200:
                result = response.json()
                response_text = result.get('response', '')

                # Parse the JSON response
                extracted_data = self._parse_extraction_response(response_text)

                logger.info(f"Extracted {len(extracted_data)} fields from {doc_type}")
                return extracted_data
            else:
                logger.error(f"Ollama API error: {response.status_code}")
                return {}

        except Exception as e:
            logger.error(f"Error during extraction: {str(e)}")
            return {}

    def _parse_extraction_response(self, response_text: str) -> Dict[str, Any]:
        """Parse the LLM response to extract structured data"""
        try:
            # Try to find JSON in the response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1

            if start_idx != -1 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx]
                result = json.loads(json_str)
                return result
            else:
                logger.warning("No JSON found in extraction response")
                return {}

        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON from response: {str(e)}")
            # Try to extract partial data
            return self._fallback_parse(response_text)
        except Exception as e:
            logger.error(f"Error parsing extraction response: {str(e)}")
            return {}

    def _fallback_parse(self, response_text: str) -> Dict[str, Any]:
        """Attempt to extract data even if JSON parsing fails"""
        # This is a simple fallback - in production you'd want more sophisticated parsing
        data = {}
        lines = response_text.split('\n')

        for line in lines:
            if ':' in line:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    key = parts[0].strip().strip('"').strip()
                    value = parts[1].strip().strip(',').strip('"')
                    if value and value not in ['null', 'None']:
                        data[key] = value

        return data

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
