#!/bin/bash

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  🎨 DOCUMENT INTELLIGENCE PIPELINE - PRESENTATION SLIDES     ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "Choose an option:"
echo ""
echo "  1) 🌐 Open HTML slides in browser (for presenting)"
echo "  2) 📄 Convert HTML to PDF"
echo "  3) 📊 Open HTML and convert to PDF"
echo "  4) ℹ️  Show instructions"
echo ""
read -p "Enter your choice (1-4): " choice

case $choice in
    1)
        echo ""
        echo "🌐 Opening slides in browser..."
        if [[ "$OSTYPE" == "darwin"* ]]; then
            open presentation.html
        elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
            xdg-open presentation.html
        else
            echo "Please open slides/presentation.html in your browser"
        fi
        echo ""
        echo "💡 Navigation Tips:"
        echo "   • Press → or SPACE for next slide"
        echo "   • Press ← for previous slide"
        echo "   • Press F11 for fullscreen"
        ;;
    2)
        echo ""
        echo "📄 Converting to PDF..."
        if command -v python3 &> /dev/null; then
            python3 convert_to_pdf.py
        else
            echo "⚠️  Python 3 not found."
            echo ""
            echo "Alternative: Use browser to print"
            echo "  1. Open presentation.html"
            echo "  2. Press Cmd+P or Ctrl+P"
            echo "  3. Select 'Save as PDF'"
            echo "  4. Enable 'Background graphics'"
        fi
        ;;
    3)
        echo ""
        echo "🌐 Opening slides..."
        if [[ "$OSTYPE" == "darwin"* ]]; then
            open presentation.html
        elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
            xdg-open presentation.html
        fi
        echo ""
        echo "📄 Converting to PDF..."
        sleep 2
        python3 convert_to_pdf.py
        ;;
    4)
        echo ""
        echo "📖 PRESENTATION INSTRUCTIONS"
        echo ""
        echo "HTML Presentation (Interactive):"
        echo "  • Open: presentation.html"
        echo "  • Navigate: Arrow keys or click buttons"
        echo "  • Fullscreen: F11"
        echo ""
        echo "PDF Creation (3 Methods):"
        echo ""
        echo "  Method 1 - Python Script:"
        echo "    pip install weasyprint"
        echo "    python slides/convert_to_pdf.py"
        echo ""
        echo "  Method 2 - Browser Print:"
        echo "    1. Open presentation.html in Chrome"
        echo "    2. Cmd+P or Ctrl+P"
        echo "    3. Save as PDF (enable background graphics)"
        echo ""
        echo "  Method 3 - Chrome Headless:"
        echo "    chrome --headless --print-to-pdf=slides.pdf presentation.html"
        echo ""
        echo "📊 Slide Content:"
        echo "  Slide 1: High-Level Overview"
        echo "  Slide 2: Detailed Execution Pipeline"
        echo "  Slide 3: Beyond POC & Downstream Apps"
        ;;
    *)
        echo ""
        echo "❌ Invalid choice. Please run again and choose 1-4."
        ;;
esac

echo ""
