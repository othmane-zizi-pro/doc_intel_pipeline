#!/usr/bin/env python3
"""
Quick test script for the document intelligence pipeline.
Run this to verify everything works before using the full Jupyter notebook.

This script auto-detects if 'rich' is installed and uses enhanced logging if available.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent))

# Try to use enhanced logging if rich is available
try:
    import rich
    # If rich is available, run the enhanced version
    print("✨ Rich library detected! Using enhanced logging experience...")
    import subprocess
    subprocess.run([sys.executable, "test_pipeline_enhanced.py"])
    sys.exit(0)
except ImportError:
    print("ℹ️  Running basic version (install 'rich' for enhanced experience)")
    print("   pip install rich\n")

from src.ingestion import DocumentIngestor
from src.classifier import DocumentClassifier
from src.extractor import FieldExtractor
from src.schemas import DocumentType, create_document
from src.utils import validate_ollama_connection, save_to_json, save_to_csv

def main():
    print("=" * 80)
    print("DOCUMENT INTELLIGENCE PIPELINE - QUICK TEST")
    print("=" * 80)

    # Step 1: Verify Ollama
    print("\n1. Checking Ollama connection...")
    if not validate_ollama_connection("qwen2.5:7b"):
        print("\n❌ Ollama check failed. Please ensure:")
        print("   - Ollama is running: ollama serve")
        print("   - Model is installed: ollama pull qwen2.5:7b")
        return

    # Step 2: Ingest documents
    print("\n2. Ingesting documents...")
    ingestor = DocumentIngestor()
    documents = ingestor.batch_ingest("data/input")

    if not documents:
        print("❌ No documents found in data/input/")
        return

    print(f"✓ Ingested {len(documents)} documents")

    # Step 3: Classify documents
    print("\n3. Classifying documents...")
    classifier = DocumentClassifier(model_name="qwen2.5:7b")

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
    print("\n4. Extracting fields...")
    extractor = FieldExtractor(model_name="qwen2.5:7b")

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
    print("\nRun the Jupyter notebook for full demo with analytics!")
    print("  jupyter notebook notebooks/document_pipeline_demo.ipynb")
    print("=" * 80)

if __name__ == "__main__":
    main()
