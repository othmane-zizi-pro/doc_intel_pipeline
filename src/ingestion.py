"""
Document ingestion module - extracts text from PDF files.
"""

import pdfplumber
from pathlib import Path
from typing import List, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DocumentIngestor:
    """Handles PDF document ingestion and text extraction"""

    def __init__(self):
        self.supported_formats = ['.pdf']

    def ingest_pdf(self, file_path: str) -> Optional[Dict]:
        """
        Extract text and metadata from a single PDF file.

        Args:
            file_path: Path to the PDF file

        Returns:
            Dictionary containing extracted text and metadata
        """
        file_path = Path(file_path)

        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return None

        if file_path.suffix.lower() not in self.supported_formats:
            logger.error(f"Unsupported format: {file_path.suffix}")
            return None

        try:
            with pdfplumber.open(file_path) as pdf:
                # Extract text from all pages
                text_content = []
                tables = []

                for page_num, page in enumerate(pdf.pages, start=1):
                    # Extract text
                    page_text = page.extract_text()
                    if page_text:
                        text_content.append(page_text)

                    # Extract tables (important for invoices)
                    page_tables = page.extract_tables()
                    if page_tables:
                        tables.extend(page_tables)

                full_text = "\n\n".join(text_content)

                # Extract metadata
                metadata = {
                    'file_name': file_path.name,
                    'file_path': str(file_path),
                    'num_pages': len(pdf.pages),
                    'file_size': file_path.stat().st_size,
                    'has_tables': len(tables) > 0
                }

                result = {
                    'text': full_text,
                    'metadata': metadata,
                    'tables': tables
                }

                logger.info(f"Successfully ingested: {file_path.name} ({len(pdf.pages)} pages)")
                return result

        except Exception as e:
            logger.error(f"Error processing {file_path}: {str(e)}")
            return None

    def batch_ingest(self, directory: str, pattern: str = "*.pdf") -> List[Dict]:
        """
        Ingest all PDF files from a directory.

        Args:
            directory: Path to directory containing PDFs
            pattern: File pattern to match (default: *.pdf)

        Returns:
            List of dictionaries containing extracted documents
        """
        directory = Path(directory)

        if not directory.exists():
            logger.error(f"Directory not found: {directory}")
            return []

        pdf_files = list(directory.glob(pattern))

        if not pdf_files:
            logger.warning(f"No PDF files found in {directory}")
            return []

        logger.info(f"Found {len(pdf_files)} PDF files to process")

        results = []
        for pdf_file in pdf_files:
            result = self.ingest_pdf(pdf_file)
            if result:
                results.append(result)

        logger.info(f"Successfully ingested {len(results)}/{len(pdf_files)} documents")
        return results

    def extract_text_from_pages(self, file_path: str, start_page: int = 0, end_page: Optional[int] = None) -> str:
        """
        Extract text from specific pages of a PDF.

        Args:
            file_path: Path to PDF file
            start_page: Starting page (0-indexed)
            end_page: Ending page (exclusive)

        Returns:
            Extracted text from specified pages
        """
        file_path = Path(file_path)

        try:
            with pdfplumber.open(file_path) as pdf:
                pages = pdf.pages[start_page:end_page]
                text_content = []

                for page in pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_content.append(page_text)

                return "\n\n".join(text_content)

        except Exception as e:
            logger.error(f"Error extracting pages from {file_path}: {str(e)}")
            return ""
