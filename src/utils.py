"""
Utility functions for the document intelligence pipeline.
"""

import json
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def save_to_json(documents: List[Any], output_dir: str = "data/output/json"):
    """
    Save documents to individual JSON files.

    Args:
        documents: List of document objects
        output_dir: Directory to save JSON files
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    for doc in documents:
        # Convert Pydantic model to dict
        if hasattr(doc, 'dict'):
            doc_dict = doc.dict()
        else:
            doc_dict = doc

        # Create filename from document type and ID
        doc_id = doc_dict.get('document_id', 'unknown')
        doc_type = doc_dict.get('document_type', 'unknown')
        filename = f"{doc_type}_{doc_id[:8]}.json"

        file_path = output_path / filename

        with open(file_path, 'w') as f:
            json.dump(doc_dict, f, indent=2, default=str)

        logger.info(f"Saved: {filename}")

    logger.info(f"Saved {len(documents)} documents to {output_dir}")


def save_to_csv(documents: List[Any], output_file: str = "data/output/master_data.csv"):
    """
    Save documents to a single CSV file.

    Args:
        documents: List of document objects
        output_file: Path to output CSV file
    """
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert documents to list of dicts
    records = []
    for doc in documents:
        if hasattr(doc, 'dict'):
            doc_dict = doc.dict()
        else:
            doc_dict = doc

        # Flatten nested structures for CSV
        flattened = flatten_dict(doc_dict)
        records.append(flattened)

    # Create DataFrame and save
    df = pd.DataFrame(records)
    df.to_csv(output_path, index=False)

    logger.info(f"Saved {len(documents)} documents to {output_file}")
    return df


def flatten_dict(d: Dict, parent_key: str = '', sep: str = '_') -> Dict:
    """
    Flatten a nested dictionary.

    Args:
        d: Dictionary to flatten
        parent_key: Parent key for recursion
        sep: Separator for nested keys

    Returns:
        Flattened dictionary
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k

        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            # Convert lists to JSON strings for CSV compatibility
            items.append((new_key, json.dumps(v)))
        else:
            items.append((new_key, v))

    return dict(items)


def load_documents_from_json(json_dir: str = "data/output/json") -> List[Dict]:
    """
    Load all documents from JSON directory.

    Args:
        json_dir: Directory containing JSON files

    Returns:
        List of document dictionaries
    """
    json_path = Path(json_dir)

    if not json_path.exists():
        logger.warning(f"Directory not found: {json_dir}")
        return []

    documents = []
    for json_file in json_path.glob("*.json"):
        with open(json_file, 'r') as f:
            doc = json.load(f)
            documents.append(doc)

    logger.info(f"Loaded {len(documents)} documents from {json_dir}")
    return documents


def create_summary_report(documents: List[Any]) -> Dict[str, Any]:
    """
    Create a summary report of processed documents.

    Args:
        documents: List of document objects

    Returns:
        Dictionary containing summary statistics
    """
    if not documents:
        return {"total_documents": 0}

    # Convert to dicts if needed
    docs_list = []
    for doc in documents:
        if hasattr(doc, 'dict'):
            docs_list.append(doc.dict())
        else:
            docs_list.append(doc)

    # Count by type
    type_counts = {}
    for doc in docs_list:
        doc_type = doc.get('document_type', 'unknown')
        type_counts[doc_type] = type_counts.get(doc_type, 0) + 1

    # Calculate average confidence
    confidences = [doc.get('confidence_score', 0) for doc in docs_list]
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0

    # Extract financial data
    total_amounts = []
    for doc in docs_list:
        if doc.get('document_type') == 'invoice':
            amount = doc.get('total_amount')
            if amount:
                total_amounts.append(amount)

    summary = {
        'total_documents': len(documents),
        'documents_by_type': type_counts,
        'average_confidence': round(avg_confidence, 3),
        'total_invoice_amount': sum(total_amounts) if total_amounts else 0,
        'num_invoices_with_amounts': len(total_amounts)
    }

    return summary


def display_document_table(documents: List[Any]) -> pd.DataFrame:
    """
    Create a summary table of documents for display.

    Args:
        documents: List of document objects

    Returns:
        Pandas DataFrame with key document info
    """
    records = []
    for doc in documents:
        if hasattr(doc, 'dict'):
            doc_dict = doc.dict()
        else:
            doc_dict = doc

        # Extract key fields based on document type
        record = {
            'Type': doc_dict.get('document_type', 'unknown'),
            'File': doc_dict.get('file_name', 'unknown'),
            'Confidence': f"{doc_dict.get('confidence_score', 0):.2f}"
        }

        # Add type-specific fields
        doc_type = doc_dict.get('document_type')
        if doc_type == 'invoice':
            record['Client'] = doc_dict.get('client_name', 'N/A')
            record['Amount'] = doc_dict.get('total_amount', 'N/A')
            record['Date'] = doc_dict.get('invoice_date', 'N/A')
        elif doc_type == 'contract':
            parties = doc_dict.get('parties', [])
            record['Parties'] = ', '.join(parties[:2]) if parties else 'N/A'
            record['Value'] = doc_dict.get('contract_value', 'N/A')
            record['Date'] = doc_dict.get('contract_date', 'N/A')
        elif doc_type == 'email':
            record['From'] = doc_dict.get('sender', 'N/A')
            record['Subject'] = doc_dict.get('subject', 'N/A')
            record['Date'] = doc_dict.get('email_date', 'N/A')
        elif doc_type == 'meeting_minutes':
            attendees = doc_dict.get('attendees', [])
            record['Attendees'] = len(attendees)
            record['Title'] = doc_dict.get('meeting_title', 'N/A')
            record['Date'] = doc_dict.get('meeting_date', 'N/A')

        records.append(record)

    return pd.DataFrame(records)


def validate_ollama_connection(model_name: str = "qwen2.5:7b", url: str = "http://localhost:11434") -> bool:
    """
    Check if Ollama is running and the model is available.

    Args:
        model_name: Name of the Ollama model
        url: Ollama server URL

    Returns:
        True if connection successful, False otherwise
    """
    import requests

    try:
        # Check if Ollama is running
        response = requests.get(f"{url}/api/tags")
        if response.status_code == 200:
            models = response.json().get('models', [])
            model_names = [m['name'] for m in models]

            if model_name in model_names:
                logger.info(f"✓ Ollama is running and {model_name} is available")
                return True
            else:
                logger.error(f"✗ Model {model_name} not found. Available models: {model_names}")
                return False
        else:
            logger.error(f"✗ Cannot connect to Ollama at {url}")
            return False

    except Exception as e:
        logger.error(f"✗ Error connecting to Ollama: {str(e)}")
        return False
