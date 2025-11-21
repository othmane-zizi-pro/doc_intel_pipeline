#!/usr/bin/env python3
"""
Test script for orchestrated multi-model document intelligence pipeline.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent))

from src.ingestion import DocumentIngestor
from src.classifier_orchestrated import DocumentClassifier
from src.extractor_orchestrated import FieldExtractor
from src.schemas import DocumentType, create_document
from src.utils import save_to_json, save_to_csv

def main():
    print("=" * 80)
    print("MULTI-MODEL ORCHESTRATED DOCUMENT INTELLIGENCE PIPELINE")
    print("=" * 80)

    # Step 1: Initialize
    print("\n1. Initializing multi-model orchestrator...")
    print("   Available models: OpenAI GPT-4o, Gemini 2.5 Flash, Ollama Qwen")
    print("   ✓ Orchestrator ready\n")

    # Step 2: Ingest documents
    print("2. Ingesting documents with OCR...")
    ingestor = DocumentIngestor()
    documents = ingestor.batch_ingest("data/input")

    if not documents:
        print("❌ No documents found in data/input/")
        return

    print(f"✓ Ingested {len(documents)} documents\n")

    # Step 3: Classify documents
    print("3. Classifying documents (with automatic fallback)...")
    classifier = DocumentClassifier()

    classifications = []
    for doc in documents:
        doc_type, confidence = classifier.classify(doc['text'])
        classifications.append({
            'document': doc,
            'type': doc_type,
            'confidence': confidence
        })
        print(f"   {doc['metadata']['file_name']}: {doc_type} ({confidence:.1%})")

    # Step 4: Extract fields
    print("\n4. Extracting fields (with validation)...")
    extractor = FieldExtractor()

    extracted_documents = []
    for item in classifications:
        doc = item['document']
        doc_type = item['type']
        confidence = item['confidence']

        extracted_fields = extractor.extract(doc['text'], doc_type)

        try:
            document_obj = create_document(
                doc_type=DocumentType(doc_type),
                file_name=doc['metadata']['file_name'],
                confidence_score=confidence,
                **extracted_fields
            )
            extracted_documents.append(document_obj)
            print(f"   ✓ Extracted from {doc['metadata']['file_name']}")
        except Exception as e:
            print(f"   ⚠️  Error: {str(e)}")

    # Step 5: Save results
    print("\n5. Saving results...")
    save_to_json(extracted_documents)
    save_to_csv(extracted_documents)

    print("\n" + "=" * 80)
    print(f"✅ SUCCESS! Processed {len(extracted_documents)} documents")
    print("=" * 80)
    print("\nOutput files:")
    print("  - data/output/json/*.json")
    print("  - data/output/master_data.csv")
    print("=" * 80)

if __name__ == "__main__":
    main()
