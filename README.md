# Document Intelligence Pipeline for Legal Analytics

A proof-of-concept automated document processing pipeline that ingests, classifies, and extracts structured information from legal documents (invoices, contracts, emails, meeting minutes) using local LLM technology.

## 🎯 Project Overview

This pipeline demonstrates:
- **Automated PDF ingestion** with text extraction
- **AI-powered classification** using Google Gemini API
- **Structured field extraction** (client names, amounts, dates, involved parties)
- **Data validation** using Pydantic schemas
- **Multi-format storage** (JSON, CSV) for downstream analytics

## 📋 Features

✅ Processes multiple document types (invoice, contract, email, meeting minutes)
✅ Extracts 4 key fields required by assignment:
   - Client Name
   - Invoice Amount / Contract Value
   - Date(s)
   - Involved Parties

✅ Modular architecture (easy to extend)
✅ Cloud-based LLM via Google Gemini API
✅ Export-ready data for reporting and analytics

## 🛠 Technical Stack

- **Language**: Python 3.10+
- **PDF Processing**: pdfplumber
- **LLM**: Google Gemini (gemini-1.5-flash or gemini-1.5-pro)
- **Validation**: Pydantic
- **Data Processing**: Pandas
- **Interface**: Jupyter Notebook

## 📁 Project Structure

```
doc_intel_pipeline/
├── src/
│   ├── ingestion.py          # PDF text extraction
│   ├── classifier.py         # Document classification
│   ├── extractor.py          # Field extraction
│   ├── schemas.py            # Pydantic data models
│   └── utils.py              # Helper functions
├── notebooks/
│   └── document_pipeline_demo.ipynb  # Main demo
├── prompts/
│   ├── classification.txt
│   ├── invoice_extraction.txt
│   ├── contract_extraction.txt
│   ├── email_extraction.txt
│   └── meeting_extraction.txt
├── data/
│   ├── input/                # Raw PDFs
│   └── output/
│       ├── json/             # Individual documents
│       ├── master_data.csv   # Aggregated data
│       └── invoice_report.csv # Invoice-specific report
├── requirements.txt
└── README.md
```

## 🚀 Quick Start

### Prerequisites

1. **Python 3.10+**
2. **OpenAI API Key** (Get one at [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys))
3. **Google Gemini API Key** (Get one at [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey))

### Installation

```bash
# 1. Clone/navigate to project directory
cd doc_intel_pipeline

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Configure your API keys
# Copy the example environment file
cp .env.example .env

# Edit .env and add your API keys:
# OPENAI_API_KEY=your_openai_key_here
# GEMINI_API_KEY=your_gemini_key_here

# 4. Run the Tier 3 pipeline
python test_tier3.py
```

### Running the Pipeline

```bash
# Start Jupyter notebook
jupyter notebook notebooks/document_pipeline_demo.ipynb
```

Then run all cells in the notebook to:
1. Ingest PDFs from `data/input/`
2. Classify documents by type
3. Extract structured fields
4. Save results to `data/output/`
5. View analytics and examples

## 📊 Output Formats

### 1. Individual JSON Files
Each document saved as structured JSON in `data/output/json/`

```json
{
  "document_id": "abc123...",
  "document_type": "invoice",
  "file_name": "case_dataset.pdf",
  "confidence_score": 0.95,
  "invoice_number": "PXC7PUAWY2HY-1",
  "invoice_date": "2025-06-17",
  "client_name": "Pentcho Tchomakov",
  "vendor_name": "WeWork",
  "total_amount": 36.75,
  "currency": "CAD",
  "involved_parties": ["Pentcho Tchomakov", "WeWork"]
}
```

### 2. Master CSV
All documents in tabular format at `data/output/master_data.csv`

### 3. Type-specific Reports
Invoice-only data in `data/output/invoice_report.csv` for easy Excel/PowerBI import

## 🎓 Downstream Use Cases

The structured data enables:

- **Reporting**: Export to Excel, PowerBI, Tableau
- **Search**: Query by client, amount, date range
- **Aggregation**: Total spending by vendor, monthly trends
- **Compliance**: Track contract expiry dates
- **Legal Research**: Find precedents by party or term
- **Summarization**: Generate executive summaries from meeting minutes

## 🏗 Architecture

### Current POC Pipeline:
```
PDF Input → Text Extraction → Classification → Field Extraction → Validation → Storage
```

### Production-Ready Architecture:
```
Document Lake (S3)
    ↓
Orchestration (Airflow/Prefect)
    ↓
Parallel Processing
    ├─ OCR Service (for scanned docs)
    ├─ Layout Analysis
    └─ Vision LLM
    ↓
Classification Service
    ↓
Extraction Service (Multi-model)
    ↓
Storage Layer
    ├─ Vector DB (semantic search)
    ├─ SQL Database (analytics)
    └─ Search Engine (Elasticsearch)
```

## 📝 Notes on Agentic AI

**Current Implementation**: This POC uses a **tool-based LLM approach**, not autonomous agents. The LLM acts as a function for classification and extraction, with deterministic control flow managed by Python code.

**For Production**: An agentic architecture could add:
- Self-healing extraction (agents retry with different strategies)
- Intelligent routing (agents choose optimal extraction method)
- Continuous learning (agents improve prompts based on failures)

## 🔧 Customization

### Adding New Document Types

1. Add schema to `src/schemas.py`
2. Create prompt in `prompts/{type}_extraction.txt`
3. Update `DOCUMENT_TYPE_MAP` in schemas
4. Run pipeline

### Changing LLM Model

Edit model name in notebook or src/config.py:
```python
# In notebook or scripts:
classifier = DocumentClassifier(model_name="gemini-1.5-pro")  # Use pro for better quality
extractor = FieldExtractor(model_name="gemini-1.5-pro")

# Or edit GEMINI_MODEL in src/config.py:
GEMINI_MODEL = "gemini-1.5-pro"  # Options: "gemini-1.5-flash", "gemini-1.5-pro"
```

## 📈 Performance

On the sample 3-page PDF (3 invoices):
- Ingestion: ~1 second
- Classification: ~2-4 seconds per document (Gemini API)
- Extraction: ~3-6 seconds per document (Gemini API)
- **Total**: ~20-40 seconds for complete pipeline

Scales linearly with document count (can parallelize for production). Gemini API provides faster response times compared to local models.

## 🐛 Troubleshooting

**API Key Error**:
- Verify your API key in `src/config.py` is correct
- Get a new key at [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)

**Rate Limit Error**:
- Gemini has free tier rate limits. Wait a moment and retry
- Consider upgrading to Gemini API paid tier for higher limits

**JSON parsing errors**:
- Check prompt templates in `prompts/` directory
- Lower LLM temperature in extractor/classifier (already set to 0.1-0.2)

## 📄 License

This is a proof-of-concept for educational purposes.

## 👥 Contributors

Group 13

---

**Note**: This is a POC demonstrating core workflow logic. For production use, add proper error handling, logging, monitoring, testing, and security measures.
