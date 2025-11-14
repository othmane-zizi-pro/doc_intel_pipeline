#!/usr/bin/env python3
"""
Convert HTML slides to PDF.
Requires: pip install weasyprint
"""

try:
    from weasyprint import HTML, CSS
    from pathlib import Path

    print("🎨 Converting HTML slides to PDF...")

    html_file = Path(__file__).parent / "presentation.html"
    pdf_file = Path(__file__).parent / "presentation.pdf"

    # Read HTML content
    with open(html_file, 'r') as f:
        html_content = f.read()

    # Create PDF
    HTML(string=html_content).write_pdf(
        pdf_file,
        stylesheets=[CSS(string='''
            @page {
                size: 1920px 1080px;
                margin: 0;
            }
            body {
                margin: 0;
            }
        ''')]
    )

    print(f"✅ PDF created successfully: {pdf_file}")
    print(f"📄 File size: {pdf_file.stat().st_size / 1024:.1f} KB")

except ImportError:
    print("⚠️  WeasyPrint not installed.")
    print("\nInstall it with:")
    print("  pip install weasyprint")
    print("\nOr use browser method:")
    print("  1. Open slides/presentation.html in your browser")
    print("  2. Press Cmd+P (Mac) or Ctrl+P (Windows)")
    print("  3. Select 'Save as PDF'")
    print("  4. Make sure to select 'Background graphics' in print options")
