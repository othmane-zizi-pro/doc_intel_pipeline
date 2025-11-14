# 🚀 Quick Start - Presentation Slides

## ⚡ Fastest Way to View Slides

### Open HTML (Interactive)
```bash
open slides/presentation.html
```

Then use:
- **→** or **SPACE** = Next slide
- **←** = Previous slide
- **F11** = Fullscreen

---

## 📄 Convert to PDF

### Method 1: Browser Print (Easiest - 30 seconds)
1. Open `slides/presentation.html` in **Chrome**
2. Press **Cmd+P** (Mac) or **Ctrl+P** (Windows)
3. Destination: **Save as PDF**
4. **IMPORTANT:** Click "More settings" → Enable "**Background graphics**"
5. Click "Save"

### Method 2: Python Script (Best Quality)
```bash
pip install weasyprint
python slides/convert_to_pdf.py
```

### Method 3: Chrome Headless (Command Line)
```bash
# Mac
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --headless --print-to-pdf=slides/presentation.pdf \
  slides/presentation.html

# Or use the helper script
bash slides/present.sh
```

---

## 📊 What's in the Slides?

### **Slide 1: High-Level Overview** (Problem → Solution → REAL Results)
- The legal firm's document processing challenges
- Our AI-powered solution
- Technical stack (pdfplumber, Qwen 2.5, Pydantic, Pandas)
- **REAL DATA TABLE**: 3 invoices processed (Uber $64.46, WeWork $36.75, Cargo $99)
- Key metrics: 3 docs, 95% confidence, 100% success, $0 API costs

### **Slide 2: Detailed Pipeline** (5-Stage Architecture + Sample Output)
- Stage 1: Ingestion (case_dataset.pdf → 3 pages, 274KB)
- Stage 2: Classification (All 3 → "invoice" at 95%)
- Stage 3: Extraction (Invoice fields → structured data)
- Stage 4: Validation (Pydantic → type-safe objects)
- Stage 5: Storage (3 JSONs + master CSV)
- **REAL OUTPUT**: WeWork invoice sample showing actual extracted fields
- Modularity features (Pluggable, Parallel, Scalable)

### **Slide 3: Beyond POC** (Production + Real-World Use Cases)
- Production architecture (Cloud, Orchestration, Multi-model)
- **6 Downstream applications with REAL examples:**
  - Reporting: "$200.21 CAD total from 3 vendors"
  - Search: "Find all WeWork invoices"
  - Aggregation: "Uber ($64.46) + WeWork ($36.75) + Cargo ($99)"
  - Compliance: Contract tracking & alerts
  - Legal Research: "Find all Pentcho Tchomakov documents"
  - Summarization: "3 invoices from June-July 2025"
- **All 4 required fields extracted:** Client names, amounts, dates, parties
- Output files: 3 JSONs + master_data.csv + invoice_report.csv

---

## 🎯 For Your Presentation

### Before You Start:
- [ ] Open HTML in browser and test navigation
- [ ] Press F11 for fullscreen mode
- [ ] Test advancing through all 3 slides
- [ ] Have PDF backup ready

### During Presentation:
- **Slide 1:** Focus on problem/solution fit (2-3 min)
- **Slide 2:** Walk through pipeline stages (3-4 min)
- **Slide 3:** Emphasize scalability and use cases (2-3 min)

### Pro Tips:
- Use **Spacebar** to advance (easier than arrow)
- Keep browser in fullscreen (F11)
- Have terminal ready to demo actual pipeline if asked
- PDF printouts make good handouts

---

## ✅ Checklist

- [x] HTML slides created (slides/presentation.html)
- [ ] HTML opened and tested
- [ ] PDF version created
- [ ] Presentation practiced
- [ ] Demo ready (test_pipeline_enhanced.py)

---

## 📞 Quick Commands Reference

```bash
# View HTML slides
open slides/presentation.html

# Convert to PDF (Python)
python slides/convert_to_pdf.py

# Interactive helper
bash slides/present.sh

# Run pipeline demo
python test_pipeline_enhanced.py
```

---

**Ready to present!** 🎉
