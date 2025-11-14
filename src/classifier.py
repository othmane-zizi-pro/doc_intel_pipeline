"""
Document classification module using Ollama LLM.
"""

import requests
import json
import logging
from typing import Dict, Tuple
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DocumentClassifier:
    """Classifies documents using Qwen LLM via Ollama"""

    def __init__(self, model_name: str = "qwen2.5:7b", ollama_url: str = "http://localhost:11434"):
        self.model_name = model_name
        self.ollama_url = ollama_url
        self.api_endpoint = f"{ollama_url}/api/generate"

        # Load classification prompt
        self.prompt_template = self._load_prompt_template()

    def _load_prompt_template(self) -> str:
        """Load classification prompt template"""
        prompt_path = Path("prompts/classification.txt")
        if prompt_path.exists():
            with open(prompt_path, 'r') as f:
                return f.read()
        else:
            # Default prompt if file doesn't exist yet
            return """You are a document classifier for a legal firm. Analyze the following document text and classify it into one of these types:

INVOICE: Contains billing information, line items, amounts, payment details, vendor/client information
CONTRACT: Contains legal agreements, terms and conditions, parties involved, signatures, effective dates
EMAIL: Contains to/from fields, subject line, email addresses, informal communication
MEETING_MINUTES: Contains attendees, agenda items, decisions made, action items, meeting date

Document text:
{text}

Respond ONLY with a JSON object in this exact format:
{{"type": "invoice", "confidence": 0.95}}

Valid types are: invoice, contract, email, meeting_minutes"""

    def classify(self, text: str) -> Tuple[str, float]:
        """
        Classify a document based on its text content.

        Args:
            text: The document text to classify

        Returns:
            Tuple of (document_type, confidence_score)
        """
        # Truncate text if too long (keep first 3000 chars for classification)
        text_sample = text[:3000] if len(text) > 3000 else text

        # Create the prompt
        prompt = self.prompt_template.format(text=text_sample)

        try:
            # Call Ollama API
            response = requests.post(
                self.api_endpoint,
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.1,  # Low temperature for consistent classification
                }
            )

            if response.status_code == 200:
                result = response.json()
                response_text = result.get('response', '')

                # Parse the JSON response
                classification = self._parse_classification_response(response_text)

                logger.info(f"Classification: {classification['type']} (confidence: {classification['confidence']:.2f})")
                return classification['type'], classification['confidence']
            else:
                logger.error(f"Ollama API error: {response.status_code}")
                return "unknown", 0.0

        except Exception as e:
            logger.error(f"Error during classification: {str(e)}")
            return "unknown", 0.0

    def _parse_classification_response(self, response_text: str) -> Dict:
        """Parse the LLM response to extract classification"""
        try:
            # Try to find JSON in the response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1

            if start_idx != -1 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx]
                result = json.loads(json_str)

                # Validate and normalize
                doc_type = result.get('type', 'unknown').lower()
                confidence = float(result.get('confidence', 0.5))

                # Ensure confidence is between 0 and 1
                confidence = max(0.0, min(1.0, confidence))

                return {'type': doc_type, 'confidence': confidence}
            else:
                # Fallback: look for keywords in response
                response_lower = response_text.lower()
                if 'invoice' in response_lower:
                    return {'type': 'invoice', 'confidence': 0.7}
                elif 'contract' in response_lower:
                    return {'type': 'contract', 'confidence': 0.7}
                elif 'email' in response_lower:
                    return {'type': 'email', 'confidence': 0.7}
                elif 'meeting' in response_lower:
                    return {'type': 'meeting_minutes', 'confidence': 0.7}
                else:
                    return {'type': 'unknown', 'confidence': 0.5}

        except Exception as e:
            logger.error(f"Error parsing classification response: {str(e)}")
            return {'type': 'unknown', 'confidence': 0.0}

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
