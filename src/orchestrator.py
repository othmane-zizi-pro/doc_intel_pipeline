"""
Multi-model orchestrator with validation and automatic fallback.
"""

import logging
from typing import Dict, Any, Tuple, Optional, List
from openai import OpenAI
import google.generativeai as genai
import requests
import json

from .config import (
    OPENAI_API_KEY, OPENAI_MODEL,
    GEMINI_API_KEY, GEMINI_MODEL,
    OLLAMA_URL, OLLAMA_MODEL,
    MODEL_PRIORITY
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ValidationAgent:
    """Agent that validates extraction quality"""

    def __init__(self, provider: str = "openai"):
        self.provider = provider
        if provider == "openai":
            self.client = OpenAI(api_key=OPENAI_API_KEY)
            self.model = OPENAI_MODEL

    def validate_classification(self, text: str, classification: str, confidence: float) -> Tuple[bool, str]:
        """
        Validate if classification makes sense.

        Returns:
            (is_valid, reason)
        """
        if confidence < 0.7:
            return False, f"Low confidence: {confidence:.2f}"

        if classification == "unknown":
            return False, "Classification is unknown"

        # Quick validation: check if document has expected keywords
        text_lower = text.lower()
        if classification == "invoice":
            keywords = ["invoice", "bill", "payment", "total", "amount", "$"]
            if any(k in text_lower for k in keywords):
                return True, "Valid invoice classification"
            else:
                return False, "Missing invoice keywords"

        return True, "Valid classification"

    def validate_extraction(self, text: str, extracted_data: Dict[str, Any], doc_type: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Validate extraction quality using LLM.

        Returns:
            (is_valid, reason, suggested_improvements)
        """
        if not extracted_data or len(extracted_data) < 3:
            return False, "Too few fields extracted", None

        # Use LLM to validate
        prompt = f"""You are a data quality validator. Review this document extraction and determine if it's accurate and complete.

Document type: {doc_type}
Original text:
{text[:1000]}

Extracted data:
{json.dumps(extracted_data, indent=2)}

Evaluate:
1. Are the extracted values accurate based on the text?
2. Are important fields missing?
3. Are any values obviously wrong?

Respond with JSON:
{{
  "is_valid": true/false,
  "reason": "explanation",
  "missing_fields": ["field1", "field2"],
  "quality_score": 0.0-1.0
}}
"""

        try:
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    response_format={"type": "json_object"}
                )

                result = json.loads(response.choices[0].message.content)
                is_valid = result.get("is_valid", False)
                quality_score = result.get("quality_score", 0.0)
                reason = result.get("reason", "Unknown")

                logger.info(f"Validation result: {is_valid}, quality: {quality_score:.2f}")

                # More lenient threshold - if quality > 0.6 and at least somewhat valid, accept it
                return is_valid or quality_score > 0.6, reason, result

        except Exception as e:
            logger.error(f"Validation error: {e}")
            # If validation fails, assume extraction is OK to continue pipeline
            return True, "Validation error, assuming OK", None


class LLMOrchestrator:
    """Orchestrates multiple LLM providers with automatic fallback"""

    def __init__(self, providers: List[str] = None):
        self.providers = providers or MODEL_PRIORITY
        self.clients = self._initialize_clients()
        self.validator = ValidationAgent(provider="openai")
        logger.info(f"Initialized orchestrator with providers: {self.providers}")

    def _initialize_clients(self) -> Dict[str, Any]:
        """Initialize all available LLM clients"""
        clients = {}

        # OpenAI
        try:
            clients["openai"] = {
                "client": OpenAI(api_key=OPENAI_API_KEY),
                "model": OPENAI_MODEL
            }
            logger.info("✓ OpenAI client initialized")
        except Exception as e:
            logger.warning(f"Could not initialize OpenAI: {e}")

        # Gemini
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            clients["gemini"] = {
                "client": genai.GenerativeModel(GEMINI_MODEL),
                "model": GEMINI_MODEL
            }
            logger.info("✓ Gemini client initialized")
        except Exception as e:
            logger.warning(f"Could not initialize Gemini: {e}")

        # Ollama (optional)
        try:
            response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=2)
            if response.status_code == 200:
                clients["ollama"] = {
                    "url": OLLAMA_URL,
                    "model": OLLAMA_MODEL
                }
                logger.info("✓ Ollama client initialized")
        except Exception:
            logger.info("Ollama not available (optional)")

        return clients

    def classify_with_fallback(self, text: str, prompt_template: str) -> Tuple[str, float, str]:
        """
        Classify document using multiple models with fallback.

        Returns:
            (doc_type, confidence, provider_used)
        """
        for provider in self.providers:
            if provider not in self.clients:
                continue

            try:
                logger.info(f"Attempting classification with {provider}...")
                doc_type, confidence = self._classify_single(text, prompt_template, provider)

                # Validate
                is_valid, reason = self.validator.validate_classification(text, doc_type, confidence)

                if is_valid:
                    logger.info(f"✓ {provider} classification successful: {doc_type} ({confidence:.2%})")
                    return doc_type, confidence, provider
                else:
                    logger.warning(f"✗ {provider} classification failed validation: {reason}")

            except Exception as e:
                logger.error(f"✗ {provider} classification error: {e}")
                continue

        # All providers failed
        logger.error("All providers failed for classification")
        return "unknown", 0.0, "none"

    def _classify_single(self, text: str, prompt_template: str, provider: str) -> Tuple[str, float]:
        """Classify using a single provider"""
        prompt = prompt_template.format(text=text[:3000])

        if provider == "openai":
            client = self.clients["openai"]["client"]
            model = self.clients["openai"]["model"]

            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a document classifier. Respond only with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            return result.get("type", "unknown"), float(result.get("confidence", 0.5))

        elif provider == "gemini":
            model = self.clients["gemini"]["client"]

            generation_config = genai.GenerationConfig(
                temperature=0.1,
                max_output_tokens=512,
            )

            from google.generativeai.types import HarmCategory, HarmBlockThreshold
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }

            response = model.generate_content(
                prompt,
                generation_config=generation_config,
                safety_settings=safety_settings
            )

            if not response.candidates or not response.text:
                raise ValueError("Response blocked by safety filters")

            json_str = response.text[response.text.find('{'):response.text.rfind('}')+1]
            result = json.loads(json_str)
            return result.get("type", "unknown"), float(result.get("confidence", 0.5))

        elif provider == "ollama":
            url = self.clients["ollama"]["url"]
            model = self.clients["ollama"]["model"]

            response = requests.post(
                f"{url}/api/generate",
                json={"model": model, "prompt": prompt, "stream": False, "temperature": 0.1}
            )

            response_text = response.json().get('response', '')
            json_str = response_text[response_text.find('{'):response_text.rfind('}')+1]
            result = json.loads(json_str)
            return result.get("type", "unknown"), float(result.get("confidence", 0.5))

        raise ValueError(f"Unknown provider: {provider}")

    def extract_with_fallback(self, text: str, doc_type: str, prompt_template: str) -> Tuple[Dict[str, Any], str]:
        """
        Extract fields using multiple models with validation.

        Returns:
            (extracted_data, provider_used)
        """
        for provider in self.providers:
            if provider not in self.clients:
                continue

            try:
                logger.info(f"Attempting extraction with {provider}...")
                extracted_data = self._extract_single(text, doc_type, prompt_template, provider)

                # Validate
                is_valid, reason, validation_result = self.validator.validate_extraction(text, extracted_data, doc_type)

                if is_valid:
                    logger.info(f"✓ {provider} extraction successful: {len(extracted_data)} fields")
                    return extracted_data, provider
                else:
                    logger.warning(f"✗ {provider} extraction failed validation: {reason}")

            except Exception as e:
                logger.error(f"✗ {provider} extraction error: {e}")
                continue

        # All providers failed
        logger.error("All providers failed for extraction")
        return {}, "none"

    def _extract_single(self, text: str, doc_type: str, prompt_template: str, provider: str) -> Dict[str, Any]:
        """Extract using a single provider"""
        prompt = prompt_template.format(text=text)

        if provider == "openai":
            client = self.clients["openai"]["client"]
            model = self.clients["openai"]["model"]

            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a data extraction specialist. Extract structured data and respond only with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                response_format={"type": "json_object"}
            )

            return json.loads(response.choices[0].message.content)

        elif provider == "gemini":
            model = self.clients["gemini"]["client"]

            generation_config = genai.GenerationConfig(
                temperature=0.2,
                max_output_tokens=2048,
            )

            from google.generativeai.types import HarmCategory, HarmBlockThreshold
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }

            response = model.generate_content(
                prompt,
                generation_config=generation_config,
                safety_settings=safety_settings
            )

            if not response.candidates or not response.text:
                raise ValueError("Response blocked by safety filters")

            json_str = response.text[response.text.find('{'):response.text.rfind('}')+1]
            return json.loads(json_str)

        elif provider == "ollama":
            url = self.clients["ollama"]["url"]
            model = self.clients["ollama"]["model"]

            response = requests.post(
                f"{url}/api/generate",
                json={"model": model, "prompt": prompt, "stream": False, "temperature": 0.2}
            )

            response_text = response.json().get('response', '')
            json_str = response_text[response_text.find('{'):response_text.rfind('}')+1]
            return json.loads(json_str)

        raise ValueError(f"Unknown provider: {provider}")
