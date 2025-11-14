# 🎨 Presentation Slides

Professional slide deck for the Document Intelligence Pipeline POC.

## 📁 Files

- **presentation.html** - Interactive HTML slides (recommended for presenting)
- **convert_to_pdf.py** - Script to convert HTML to PDF
- **README.md** - This file

## 🎯 Slide Content

### Slide 1: High-Level Overview
- Problem statement
- Proposed solution
- Technical stack
- Key results and metrics

### Slide 2: Detailed Execution Pipeline
- 5-stage pipeline architecture
- Detailed process flow
- Modularity and scalability features

### Slide 3: Beyond POC & Downstream Applications
- Production architecture
- Enterprise-grade features
- 6 downstream use cases
- POC achievements summary

## 🚀 How to Present (HTML)

### Option 1: Open in Browser (Recommended)
```bash
# Mac
open slides/presentation.html

# Linux
xdg-open slides/presentation.html

# Windows
start slides/presentation.html
```

### Navigation
- **Next slide:** Click "Next" button, press → or Spacebar
- **Previous slide:** Click "Previous" button or press ←
- **Full screen:** Press F11 (most browsers)

## 📄 Convert to PDF

### Method 1: Using Python Script (High Quality)
```bash
# Install weasyprint
pip install weasyprint

# Run conversion script
python slides/convert_to_pdf.py
```

### Method 2: Browser Print (Easy)
1. Open `slides/presentation.html` in Chrome/Firefox
2. Press `Cmd+P` (Mac) or `Ctrl+P` (Windows)
3. Choose "Save as PDF" as destination
4. **Important:** Enable "Background graphics" in print options
5. Set margins to "None"
6. Save

### Method 3: Using Chrome Headless (Command Line)
```bash
# Mac/Linux
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --headless --disable-gpu \
  --print-to-pdf=slides/presentation.pdf \
  --print-to-pdf-no-header \
  slides/presentation.html

# Windows
"C:\Program Files\Google\Chrome\Application\chrome.exe" ^
  --headless --disable-gpu ^
  --print-to-pdf=slides/presentation.pdf ^
  --print-to-pdf-no-header ^
  slides/presentation.html
```

## 🎨 Customization

### Change Colors
Edit the CSS gradient in `presentation.html`:
```css
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
```

### Change Content
Each slide is in a `<div class="slide-container">` block. Edit the HTML directly.

### Add More Slides
1. Copy an existing `<div class="slide-container">` block
2. Update `totalSlides` variable in JavaScript
3. Update slide counter display

## 💡 Tips for Presenting

1. **Full Screen Mode:** Press F11 for distraction-free presentation
2. **Practice Navigation:** Test slide transitions before presenting
3. **Backup:** Have PDF version ready as backup
4. **Print Handouts:** Export to PDF and print for audience notes
5. **Screen Share:** HTML version works great for Zoom/Teams

## 📊 Slide Statistics

- **Total Slides:** 3
- **Format:** Responsive HTML5 + CSS3
- **File Size:** ~25 KB (HTML)
- **PDF Size:** ~500 KB (estimated)
- **Resolution:** Optimized for 1920x1080 (Full HD)

## 🎭 Features

✨ **Interactive Navigation**
- Click buttons or use keyboard
- Smooth transitions
- Progress indicator

🎨 **Beautiful Design**
- Gradient backgrounds
- Card layouts
- Color-coded sections
- Professional typography

📱 **Responsive**
- Works on desktop, tablet, and projector
- Print-friendly CSS

♿ **Accessible**
- Keyboard navigation
- High contrast text
- Clear hierarchy

## 🐛 Troubleshooting

**Slides don't advance:**
- Check JavaScript console for errors
- Try refreshing the page

**PDF looks wrong:**
- Make sure "Background graphics" is enabled in print dialog
- Try different browser (Chrome works best)

**Fonts look different:**
- System fonts may vary; main fonts are: Segoe UI, Tahoma, Verdana

## 📦 Requirements

- Modern web browser (Chrome, Firefox, Safari, Edge)
- For PDF conversion: Python 3 + weasyprint or Chrome browser

## 📄 License

Created for Group 13 - Document Intelligence Pipeline POC
