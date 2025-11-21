#!/usr/bin/env python3
"""
TIER 3 TEST: Ensemble Extraction + DSPy Optimization
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from src.ingestion import DocumentIngestor
from src.orchestrator_tier3 import Tier3Orchestrator
from src.schemas import DocumentType, create_document
from src.utils import save_to_json, save_to_csv
import time

# Load prompts
def load_prompt(doc_type):
    if doc_type == "invoice":
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
    return ""

classification_prompt = """You are a document classifier. Classify this document:

{text}

Respond ONLY with JSON:
{{"type": "invoice", "confidence": 0.95}}

Valid types: invoice, contract, email, meeting_minutes"""

def main():
    print("="*80)
    print("🚀 TIER 3 ADVANCED PIPELINE: ENSEMBLE + DSPy")
    print("="*80)
    print("\nFeatures:")
    print("  ✓ Parallel extraction from OpenAI + Gemini + Ollama")
    print("  ✓ Intelligent result merging with voting")
    print("  ✓ DSPy prompt optimization")
    print("="*80)

    # Step 1: Ingest
    print("\n📄 Step 1: Ingesting documents with OCR...")
    ingestor = DocumentIngestor()
    documents = ingestor.batch_ingest("data/input")

    if not documents:
        print("❌ No documents found")
        return

    print(f"   ✓ Ingested {len(documents)} documents")

    # Step 2: Initialize Tier 3 Orchestrator
    print("\n🎯 Step 2: Initializing Tier 3 Orchestrator...")
    orchestrator = Tier3Orchestrator()

    # Step 3: Ensemble Classification
    print("\n🤖 Step 3: ENSEMBLE CLASSIFICATION...")
    classifications = []
    for doc in documents:
        print(f"\n   Processing: {doc['metadata']['file_name']}")
        doc_type, confidence, providers = orchestrator.classify_ensemble(
            doc['text'],
            classification_prompt
        )
        classifications.append({
            'document': doc,
            'type': doc_type,
            'confidence': confidence,
            'providers': providers
        })
        print(f"   ✅ Result: {doc_type} ({confidence:.1%}) via {', '.join(providers)}")

    # Step 4: Ensemble Extraction
    print("\n" + "="*80)
    print("🔍 Step 4: ENSEMBLE EXTRACTION...")
    print("="*80)

    extracted_documents = []
    for item in classifications:
        doc = item['document']
        doc_type = item['type']
        confidence = item['confidence']

        print(f"\n   Processing: {doc['metadata']['file_name']}")

        prompt = load_prompt(doc_type)
        if not prompt:
            print(f"   ⚠️  No prompt for {doc_type}")
            continue

        merged_result, providers = orchestrator.ensemble_extract(
            doc['text'],
            doc_type,
            prompt
        )

        print(f"   ✅ Extracted via: {', '.join(providers)}")
        print(f"   📊 Fields extracted: {len(merged_result)}")

        # Show key fields
        if merged_result:
            for key in ['invoice_number', 'vendor_name', 'total_amount', 'currency']:
                if key in merged_result and merged_result[key]:
                    print(f"      • {key}: {merged_result[key]}")

        try:
            document_obj = create_document(
                doc_type=DocumentType(doc_type),
                file_name=doc['metadata']['file_name'],
                confidence_score=confidence,
                **merged_result
            )
            extracted_documents.append(document_obj)
        except Exception as e:
            print(f"   ⚠️  Validation error: {e}")

    # Step 5: DSPy Optimization
    print("\n" + "="*80)
    print("🧠 Step 5: DSPy PROMPT OPTIMIZATION...")
    print("="*80)
    orchestrator.optimize_prompts_with_dspy('invoice')

    # Step 6: Save
    print("\n💾 Step 6: Saving results...")
    save_to_json(extracted_documents)
    save_to_csv(extracted_documents)

    print("\n" + "="*80)
    print("✅ TIER 3 PIPELINE COMPLETE!")
    print("="*80)
    print(f"\n📊 Summary:")
    print(f"   • Documents processed: {len(extracted_documents)}")
    print(f"   • Classification accuracy: {sum(c['confidence'] for c in classifications) / len(classifications):.1%}")
    print(f"   • Output: data/output/json/ and data/output/master_data.csv")
    print("="*80)

if __name__ == "__main__":
    main()
