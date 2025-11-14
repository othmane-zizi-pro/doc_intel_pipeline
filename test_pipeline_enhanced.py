#!/usr/bin/env python3
"""
Enhanced test script with beautiful logging for the document intelligence pipeline.
"""

import sys
from pathlib import Path
import time

# Add src to path
sys.path.append(str(Path(__file__).parent))

from src.ingestion import DocumentIngestor
from src.classifier import DocumentClassifier
from src.extractor import FieldExtractor
from src.schemas import DocumentType, create_document
from src.utils import validate_ollama_connection, save_to_json, save_to_csv
from src.logger import logger, console
from rich.progress import track


def main():
    # Print header
    logger.print_header()

    # Step 1: Verify Ollama
    logger.step(1, "Verifying Ollama Connection", "🔌")

    if not validate_ollama_connection("qwen2.5:7b"):
        logger.error("Ollama connection failed")
        console.print("\n[yellow]Please ensure:[/yellow]")
        console.print("  • Ollama is running: [cyan]ollama serve[/cyan]")
        console.print("  • Model is installed: [cyan]ollama pull qwen2.5:7b[/cyan]")
        return

    logger.success("Ollama connected successfully", "Model: qwen2.5:7b")

    # Step 2: Ingest documents
    logger.step(2, "Ingesting PDF Documents", "📄")

    ingestor = DocumentIngestor()

    # Track ingestion with timing
    start_time = time.time()
    documents = ingestor.batch_ingest("data/input")
    ingestion_time = time.time() - start_time

    if not documents:
        logger.error("No documents found in data/input/")
        return

    total_pages = sum(doc['metadata']['num_pages'] for doc in documents)
    logger.success(
        f"Ingested {len(documents)} document(s)",
        f"{total_pages} pages in {ingestion_time:.2f}s"
    )

    # Show document details
    for doc in documents:
        metadata = doc['metadata']
        logger.info(
            f"{metadata['file_name']} - {metadata['num_pages']} pages, "
            f"{metadata['file_size'] / 1024:.1f} KB",
            indent=1
        )

    # Step 3: Classify documents
    logger.step(3, "Classifying Documents", "🤖")

    classifier = DocumentClassifier(model_name="qwen2.5:7b")
    classifications = []

    console.print()
    for doc in track(documents, description="[cyan]Classifying...", console=console):
        start_time = time.time()
        doc_type, confidence = classifier.classify(doc['text'])
        duration = time.time() - start_time

        classifications.append({
            'document': doc,
            'type': doc_type,
            'confidence': confidence
        })

        logger.classification_result(
            doc['metadata']['file_name'],
            doc_type,
            confidence,
            duration
        )

    avg_confidence = sum(c['confidence'] for c in classifications) / len(classifications)
    logger.success(
        f"Classification complete",
        f"Average confidence: {avg_confidence:.1%}"
    )

    # Step 4: Extract fields
    logger.step(4, "Extracting Structured Fields", "🔍")

    extractor = FieldExtractor(model_name="qwen2.5:7b")
    extracted_documents = []

    console.print()
    for item in track(classifications, description="[cyan]Extracting...", console=console):
        doc = item['document']
        doc_type = item['type']
        confidence = item['confidence']

        start_time = time.time()
        extracted_fields = extractor.extract(doc['text'], doc_type)
        duration = time.time() - start_time

        try:
            document_obj = create_document(
                doc_type=DocumentType(doc_type),
                file_name=doc['metadata']['file_name'],
                confidence_score=confidence,
                **extracted_fields
            )
            extracted_documents.append(document_obj)

            logger.extraction_result(
                doc['metadata']['file_name'],
                len(extracted_fields),
                duration
            )
        except Exception as e:
            logger.error(f"Error creating document object: {str(e)}")

    logger.success(
        f"Extraction complete",
        f"{len(extracted_documents)} documents processed"
    )

    # Step 5: Display extracted data
    logger.step(5, "Validating & Displaying Results", "✨")

    # Show detailed extraction results
    logger.print_extracted_data(extracted_documents)

    # Step 6: Save results
    logger.step(6, "Saving to Storage", "💾")

    save_to_json(extracted_documents)
    logger.success("Saved individual JSON files", "Location: data/output/json/")

    save_to_csv(extracted_documents)
    logger.success("Saved master CSV file", "Location: data/output/master_data.csv")

    # Print summary table
    logger.print_summary_table(extracted_documents)

    # Print analytics
    logger.print_analytics(extracted_documents)

    # Print output file locations
    console.print("[bold cyan]📂 Output Files:[/bold cyan]")
    console.print("  • [cyan]data/output/json/[/cyan] - Individual document JSONs")
    console.print("  • [cyan]data/output/master_data.csv[/cyan] - Aggregated data")
    console.print("  • [cyan]data/output/invoice_report.csv[/cyan] - Invoice-specific report")
    console.print()

    console.print("[bold cyan]🚀 Next Steps:[/bold cyan]")
    console.print("  • Run the Jupyter notebook for full analytics demo:")
    console.print("    [dim]jupyter notebook notebooks/document_pipeline_demo.ipynb[/dim]")
    console.print()

    # Print footer with timing
    logger.print_footer()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n\n[yellow]⚠️  Pipeline interrupted by user[/yellow]\n")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n\n[bold red]❌ Pipeline failed with error:[/bold red]")
        console.print(f"[red]{str(e)}[/red]\n")
        import traceback
        console.print("[dim]" + traceback.format_exc() + "[/dim]")
        sys.exit(1)
