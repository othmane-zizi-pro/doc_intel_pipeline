"""
Document ingestion module - extracts text from PDF files using OCR when needed.
"""

import pdfplumber
from pathlib import Path
from typing import List, Dict, Optional
import logging

# OCR imports
try:
    import pytesseract
    from pdf2image import convert_from_path
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DocumentIngestor:
    """Handles PDF document ingestion and text extraction with OCR fallback"""

    def __init__(self, use_ocr: bool = True, ocr_threshold: int = 999999, prefer_ocr: bool = True):
        """
        Initialize the DocumentIngestor.

        Args:
            use_ocr: Whether to use OCR
            ocr_threshold: Character count threshold to trigger OCR fallback (default: very high to always use OCR)
            prefer_ocr: If True, always use OCR regardless of text extraction results (default: True)
        """
        self.supported_formats = ['.pdf']
        self.use_ocr = use_ocr and OCR_AVAILABLE
        self.ocr_threshold = ocr_threshold
        self.prefer_ocr = prefer_ocr

        if use_ocr and not OCR_AVAILABLE:
            logger.warning("OCR libraries not available. Install: pip install pytesseract pdf2image")

    def extract_text_with_ocr(self, file_path: Path) -> str:
        """
        Extract text from PDF using OCR.

        Args:
            file_path: Path to the PDF file

        Returns:
            Extracted text from all pages
        """
        if not self.use_ocr:
            return ""

        try:
            logger.info(f"Using OCR to extract text from {file_path.name}")

            # Convert PDF to images
            images = convert_from_path(str(file_path), dpi=300)

            # Extract text from each image
            text_content = []
            for i, image in enumerate(images, 1):
                logger.debug(f"OCR processing page {i}/{len(images)}")
                page_text = pytesseract.image_to_string(image)
                if page_text.strip():
                    text_content.append(page_text)

            full_text = "\n\n".join(text_content)
            logger.info(f"OCR extracted {len(full_text)} characters from {len(images)} pages")

            return full_text

        except Exception as e:
            logger.error(f"OCR failed for {file_path}: {str(e)}")
            return ""

    def ingest_pdf(self, file_path: str) -> Optional[Dict]:
        """
        Extract text and metadata from a single PDF file.
        Uses OCR fallback if normal text extraction yields poor results.

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

                # Check if we need OCR
                needs_ocr = False
                if self.prefer_ocr:
                    # Always use OCR when prefer_ocr is True
                    needs_ocr = True
                    logger.info(f"{file_path.name}: Using OCR (systematic mode)")
                elif len(full_text.strip()) < self.ocr_threshold:
                    # Fallback to OCR if text extraction is poor
                    needs_ocr = True
                    logger.warning(
                        f"{file_path.name}: Low text extraction "
                        f"({len(full_text)} chars). Attempting OCR..."
                    )

                # Use OCR if needed
                if needs_ocr and self.use_ocr:
                    ocr_text = self.extract_text_with_ocr(file_path)
                    if len(ocr_text) > len(full_text):
                        full_text = ocr_text
                        logger.info(f"OCR provided better results for {file_path.name}")
                    elif self.prefer_ocr:
                        # Use OCR text even if not longer, when in prefer_ocr mode
                        full_text = ocr_text
                        logger.info(f"Using OCR text for {file_path.name}")

                # Extract metadata
                metadata = {
                    'file_name': file_path.name,
                    'file_path': str(file_path),
                    'num_pages': len(pdf.pages),
                    'file_size': file_path.stat().st_size,
                    'has_tables': len(tables) > 0,
                    'used_ocr': needs_ocr and self.use_ocr,
                    'text_length': len(full_text)
                }

                result = {
                    'text': full_text,
                    'metadata': metadata,
                    'tables': tables
                }

                logger.info(
                    f"Successfully ingested: {file_path.name} "
                    f"({len(pdf.pages)} pages, {len(full_text)} chars)"
                )
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
