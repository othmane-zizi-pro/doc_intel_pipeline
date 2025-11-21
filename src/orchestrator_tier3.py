"""
Tier 3 Advanced Orchestrator: Ensemble + DSPy Optimization
"""

import logging
from typing import Dict, Any, Tuple, List, Optional
from openai import OpenAI
import google.generativeai as genai
import requests
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import dspy
from collections import Counter

from .config import (
    OPENAI_API_KEY, OPENAI_MODEL,
    GEMINI_API_KEY, GEMINI_MODEL,
    OLLAMA_URL, OLLAMA_MODEL
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FieldMerger:
    """Merges extraction results from multiple models using voting and quality scoring"""

    @staticmethod
    def merge_extractions(results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Merge multiple extraction results into one best result.

        Strategy:
        1. For each field, collect all non-null values
        2. Use voting for strings (most common)
        3. Use average for numbers
        4. Merge arrays by taking union
        """
        if not results:
            return {}

        if len(results) == 1:
            return results[0]

        # Get all unique keys
        all_keys = set()
        for result in results:
            all_keys.update(result.keys())

        merged = {}

        for key in all_keys:
            values = [r.get(key) for r in results if r.get(key) is not None]

            if not values:
                merged[key] = None
                continue

            # Determine field type
            sample_value = values[0]

            if isinstance(sample_value, (int, float)):
                # Numeric: use average
                merged[key] = sum(values) / len(values)

            elif isinstance(sample_value, list):
                # Array: take union
                all_items = []
                for v in values:
                    if isinstance(v, list):
                        all_items.extend(v)
                merged[key] = list(set(all_items))

            elif isinstance(sample_value, str):
                # String: use voting (most common)
                counter = Counter(values)
                merged[key] = counter.most_common(1)[0][0]

            else:
                # Default: take first non-null
                merged[key] = values[0]

        logger.info(f"Merged {len(results)} results → {len(merged)} fields")
        return merged


class DSPyOptimizer:
    """DSPy-based prompt optimizer"""

    def __init__(self):
        # Configure DSPy with OpenAI
        self.lm = dspy.LM(model=f'openai/{OPENAI_MODEL}', api_key=OPENAI_API_KEY)
        dspy.configure(lm=self.lm)

        # Define DSPy signature for extraction
        self.extraction_module = None

    def create_extraction_signature(self, doc_type: str):
        """Create DSPy signature for extraction"""

        if doc_type == "invoice":
            class InvoiceExtraction(dspy.Signature):
                """Extract structured invoice data from document text."""
                document_text = dspy.InputField(desc="The full document text from OCR")
                invoice_number = dspy.OutputField(desc="Invoice or receipt number")
                invoice_date = dspy.OutputField(desc="Date of invoice in YYYY-MM-DD format")
                client_name = dspy.OutputField(desc="Name of the client or customer")
                vendor_name = dspy.OutputField(desc="Name of the vendor or service provider")
                total_amount = dspy.OutputField(desc="Total amount as a number")
                currency = dspy.OutputField(desc="Currency code (USD, CAD, etc)")
                subtotal = dspy.OutputField(desc="Subtotal before tax")
                tax = dspy.OutputField(desc="Tax amount")
                payment_method = dspy.OutputField(desc="Method of payment")
                involved_parties = dspy.OutputField(desc="All parties mentioned as comma-separated list")

            return InvoiceExtraction

        # Add more doc types as needed
        return None

    def optimize_extraction(self, examples: List[Tuple[str, Dict]], doc_type: str):
        """
        Optimize extraction using DSPy with example data.

        Args:
            examples: List of (text, expected_output) tuples
            doc_type: Document type
        """
        signature = self.create_extraction_signature(doc_type)
        if not signature:
            return None

        # Create predictor
        predictor = dspy.ChainOfThought(signature)

        # Compile with optimizer (BootstrapFewShot)
        optimizer = dspy.BootstrapFewShot(metric=self._extraction_metric)

        # Convert examples to DSPy format
        dspy_examples = []
        for text, expected in examples:
            example = dspy.Example(
                document_text=text,
                **expected
            ).with_inputs('document_text')
            dspy_examples.append(example)

        # Optimize
        if dspy_examples:
            optimized = optimizer.compile(predictor, trainset=dspy_examples[:3])
            self.extraction_module = optimized
            logger.info(f"DSPy optimization complete for {doc_type}")
            return optimized

        return predictor

    def _extraction_metric(self, example, prediction, trace=None):
        """Metric to evaluate extraction quality"""
        score = 0
        total = 0

        for key in example.keys():
            if key == 'document_text':
                continue
            total += 1
            expected = getattr(example, key, None)
            predicted = getattr(prediction, key, None)

            if expected and predicted:
                if str(expected).lower() in str(predicted).lower() or str(predicted).lower() in str(expected).lower():
                    score += 1

        return score / total if total > 0 else 0


class Tier3Orchestrator:
    """Advanced orchestrator with ensemble extraction and DSPy optimization"""

    def __init__(self):
        self.clients = self._initialize_clients()
        self.merger = FieldMerger()
        self.dspy_optimizer = DSPyOptimizer()
        self.extraction_history = []  # For DSPy learning
        logger.info("✓ Tier 3 Orchestrator initialized (Ensemble + DSPy)")

    def _initialize_clients(self) -> Dict[str, Any]:
        """Initialize all available LLM clients"""
        clients = {}

        # OpenAI
        try:
            clients["openai"] = {
                "client": OpenAI(api_key=OPENAI_API_KEY),
                "model": OPENAI_MODEL
            }
            logger.info("✓ OpenAI initialized")
        except Exception as e:
            logger.warning(f"OpenAI failed: {e}")

        # Gemini
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            clients["gemini"] = {
                "client": genai.GenerativeModel(GEMINI_MODEL),
                "model": GEMINI_MODEL
            }
            logger.info("✓ Gemini initialized")
        except Exception as e:
            logger.warning(f"Gemini failed: {e}")

        # Ollama
        try:
            response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=2)
            if response.status_code == 200:
                clients["ollama"] = {
                    "url": OLLAMA_URL,
                    "model": OLLAMA_MODEL
                }
                logger.info("✓ Ollama initialized")
        except Exception:
            logger.info("Ollama not available")

        return clients

    def ensemble_extract(self, text: str, doc_type: str, prompt_template: str) -> Tuple[Dict[str, Any], List[str]]:
        """
        Extract using ALL models in parallel, then merge results.

        Returns:
            (merged_result, providers_used)
        """
        logger.info(f"🚀 ENSEMBLE EXTRACTION: Running {len(self.clients)} models in parallel")

        results = []
        providers_used = []

        # Run all extractions in parallel
        with ThreadPoolExecutor(max_workers=len(self.clients)) as executor:
            future_to_provider = {
                executor.submit(self._extract_single, text, doc_type, prompt_template, provider): provider
                for provider in self.clients.keys()
            }

            for future in as_completed(future_to_provider):
                provider = future_to_provider[future]
                try:
                    result = future.result()
                    if result and len(result) > 0:
                        results.append(result)
                        providers_used.append(provider)
                        logger.info(f"  ✓ {provider}: {len(result)} fields extracted")
                    else:
                        logger.warning(f"  ✗ {provider}: No fields extracted")
                except Exception as e:
                    logger.error(f"  ✗ {provider}: {str(e)}")

        # Merge all results
        if not results:
            logger.error("❌ All models failed extraction")
            return {}, []

        merged = self.merger.merge_extractions(results)
        logger.info(f"✅ ENSEMBLE COMPLETE: Merged {len(results)} results from {providers_used}")

        # Store for DSPy learning
        self.extraction_history.append({
            'text': text,
            'doc_type': doc_type,
            'merged_result': merged,
            'individual_results': results
        })

        return merged, providers_used

    def _extract_single(self, text: str, doc_type: str, prompt_template: str, provider: str) -> Dict[str, Any]:
        """Extract using a single provider"""
        prompt = prompt_template.format(text=text)

        if provider == "openai":
            client = self.clients["openai"]["client"]
            model = self.clients["openai"]["model"]

            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a precise data extraction specialist. Extract all fields accurately and respond only with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )

            return json.loads(response.choices[0].message.content)

        elif provider == "gemini":
            model = self.clients["gemini"]["client"]

            generation_config = genai.GenerationConfig(
                temperature=0.1,
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
                json={"model": model, "prompt": prompt, "stream": False, "temperature": 0.1},
                timeout=60
            )

            response_text = response.json().get('response', '')
            json_str = response_text[response_text.find('{'):response_text.rfind('}')+1]
            return json.loads(json_str)

        raise ValueError(f"Unknown provider: {provider}")

    def classify_ensemble(self, text: str, prompt_template: str) -> Tuple[str, float, List[str]]:
        """
        Classify using ensemble approach.

        Returns:
            (doc_type, confidence, providers_used)
        """
        logger.info(f"🚀 ENSEMBLE CLASSIFICATION: Running {len(self.clients)} models in parallel")

        classifications = []
        providers_used = []

        # Run all classifications in parallel
        with ThreadPoolExecutor(max_workers=len(self.clients)) as executor:
            future_to_provider = {
                executor.submit(self._classify_single, text, prompt_template, provider): provider
                for provider in self.clients.keys()
            }

            for future in as_completed(future_to_provider):
                provider = future_to_provider[future]
                try:
                    doc_type, confidence = future.result()
                    classifications.append((doc_type, confidence))
                    providers_used.append(provider)
                    logger.info(f"  ✓ {provider}: {doc_type} ({confidence:.1%})")
                except Exception as e:
                    logger.error(f"  ✗ {provider}: {str(e)}")

        # Voting: most common classification
        if not classifications:
            return "unknown", 0.0, []

        doc_types = [c[0] for c in classifications]
        confidences = [c[1] for c in classifications]

        counter = Counter(doc_types)
        most_common_type = counter.most_common(1)[0][0]
        avg_confidence = sum(confidences) / len(confidences)

        logger.info(f"✅ ENSEMBLE VOTE: {most_common_type} ({avg_confidence:.1%})")

        return most_common_type, avg_confidence, providers_used

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

            generation_config = genai.GenerationConfig(temperature=0.1, max_output_tokens=512)
            from google.generativeai.types import HarmCategory, HarmBlockThreshold
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }

            response = model.generate_content(prompt, generation_config=generation_config, safety_settings=safety_settings)

            if not response.candidates or not response.text:
                raise ValueError("Response blocked")

            json_str = response.text[response.text.find('{'):response.text.rfind('}')+1]
            result = json.loads(json_str)
            return result.get("type", "unknown"), float(result.get("confidence", 0.5))

        elif provider == "ollama":
            url = self.clients["ollama"]["url"]
            model = self.clients["ollama"]["model"]

            response = requests.post(
                f"{url}/api/generate",
                json={"model": model, "prompt": prompt, "stream": False, "temperature": 0.1},
                timeout=30
            )

            response_text = response.json().get('response', '')
            json_str = response_text[response_text.find('{'):response_text.rfind('}')+1]
            result = json.loads(json_str)
            return result.get("type", "unknown"), float(result.get("confidence", 0.5))

        raise ValueError(f"Unknown provider: {provider}")

    def optimize_prompts_with_dspy(self, doc_type: str):
        """
        Use DSPy to optimize prompts based on extraction history.
        """
        if len(self.extraction_history) < 3:
            logger.info("Not enough history for DSPy optimization yet")
            return

        # Prepare training examples from successful extractions
        examples = []
        for item in self.extraction_history:
            if item['doc_type'] == doc_type and item['merged_result']:
                examples.append((item['text'], item['merged_result']))

        if examples:
            logger.info(f"🧠 DSPy: Optimizing prompts with {len(examples)} examples")
            self.dspy_optimizer.optimize_extraction(examples, doc_type)
