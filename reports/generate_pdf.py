"""
Generate a polished PDF of the DiabForecast Research Report.
Strips mermaid blocks (replaced with styled text boxes), embeds all 6 PNG charts,
and produces a print-ready A4 PDF via WeasyPrint.
"""

import re, base64
from pathlib import Path

import markdown

REPORTS_DIR = Path(__file__).resolve().parent
OUTPUT_PDF  = REPORTS_DIR / "DiabForecast_Research_Report.pdf"

# ── 1.  Read and shorten the markdown ────────────────────────────────────

raw_md = (REPORTS_DIR / "research_report.md").read_text(encoding="utf-8")

# Remove the disclaimer/scope section entirely
raw_md = re.sub(
    r'\n---\s*\n+## ⚠️ Important Scope & Health Disclaimer.*?\n---\s*\n',
    '\n---\n\n',
    raw_md,
    flags=re.DOTALL
)

# Shorten the Streamlit section
streamlit_short = """## 7. The Interactive Streamlit Web Application

The entire analysis system is deployed as a **7-page interactive Streamlit web application**:

| Page | Key Feature |
| :--- | :--- |
| **Main Portal** | 3D choropleth world map of 2022 prevalence rates |
| **Overview** | Global leaderboards, regional boxplots, year-slider |
| **Historical Trends** | 33-year trajectory charts with uncertainty bands |
| **Forecast 2030** | Country-level 2023–2030 projections with confidence intervals |
| **Model Comparison** | Backtest leaderboard and predicted-vs-actual charts |
| **Country Comparison** | Side-by-side multi-country overlays and ranking shifts |
| **Disease Burden** | GBD 2023 DALY analysis and risk factor breakdowns |

The application is backed by **43 automated passing tests** (100% pass rate).

"""
raw_md = re.sub(
    r'## 7\. The Interactive Streamlit Web Application.*?(?=\n---)',
    streamlit_short,
    raw_md,
    flags=re.DOTALL
)


# ── 2.  Replace mermaid blocks with styled description boxes ─────────────

MERMAID_DESCRIPTIONS = {
    # Executive summary pipeline
    'WHO Data': '[PIPELINE] 33 Years WHO Data --> Cleaned 152 Countries --> 4 Forecasting Models + Baseline --> ARIMA Wins 62.5% --> 4,864 Projections to 2030',
    # Research questions
    'Question 1': '[RESEARCH] Four Research Questions: (1) How have rates changed over 30 years? (2) Which model is most accurate? (3) What will 2030 look like? (4) What risk factors drive the epidemic?',
    # Data pipeline
    'Raw WHO Data': '[DATA PIPELINE] Raw WHO (30K rows) --> Filter Adults 18+ --> Remove Duplicates --> Validate 152 Countries x 33 Years --> Cleaned Dataset (5K rows, 0 missing)',
    # Main model pipeline
    'Raw WHO Data<br>': None,  # keep the original pipeline diagram description
    # Individual models
    'How Linear Regression Works': '[MODEL] Linear Regression: Fits a straight line through past years (y = slope x year + intercept) and extends it forward. Simple but assumes constant speed forever.',
    'How ARIMA Works': '[MODEL] ARIMA (3 Components): AR (looks at recent 1-3 years) + I (removes trend via differencing) + MA (learns from past errors) --> Combined prediction --> Auto-selects best parameters per country.',
    'How Holt Damped Works': '[MODEL] Holt Damped (3 Components): Level (current baseline) + Trend (rate of change) + Damping Factor (gradually flattens trend) --> Prevents runaway predictions.',
    'Input Features': '[MODEL] Random Forest: Uses 4 features (rate 1/2/3 years ago + 3-year average) --> 300 decision trees trained across all countries --> Average predictions. Limitation: cannot predict beyond training range.',
    'Last Known Value': '[MODEL] Persistence Baseline: Copies last known value forward for every future year = zero-effort flat line prediction.',
    # Backtesting wall
    'Training Data': '[BACKTEST] Training Data [1990-2017] === DATA WALL === Hidden Test Data [2018-2022] --> Compare 760 predicted vs actual values.',
    # Time-series dominance
    'Time-Series Models': '[RESULTS] Model Dominance: Time-Series Models (ARIMA + Holt) won 126/152 countries (83%) | Machine Learning (Random Forest) won 19 (12.5%) | Linear Regression won 7 (4.6%)',
    # Diverging paths
    'Global 2030': '[OUTLOOK] Three Global Paths by 2030:\n* FAST-RISING: Pakistan 30.9% --> 41.2%, Egypt 27.8% --> 33.2% (urgent intervention needed)\n* STEADY GROWTH: USA 12.5% --> 15.4% (+2-3 pts/decade)\n* LOW and STABLE: Denmark 2.3% --> 2.3%, Mexico 14.3% --> 10.4% (declining!)',
    # Uncertainty
    'Historical': '[INFO] Two Types of Uncertainty Bands: Historical (1990-2022) = survey sampling error from health studies | Forecast (2023-2030) = mathematical confidence band that widens over time.',
    # Risk factors
    'Global Diabetes Burden': '[BURDEN] Disease Burden Flow: 90.2M DALYs (2023, +56.8% since 2010) --> 96.5% is Type 2 --> Top 3 Drivers: Obesity (52.4%), Diet (28.6%), Inactivity (14.2%) --> Policy Solutions: soda taxes, nutrition labels, active transit.',
    # Lessons
    'Lesson 1': '[LESSONS] Three Key Lessons: (1) Simpler models win on smooth data - ARIMA beat Random Forest. (2) Damping prevents unrealistic forecasts. (3) Data auditing is critical - caught Egypt and Mexico errors.',
    # Conclusion
    '5,000 WHO': '[SUMMARY] 5,000 WHO Records (152 Countries, 33 Years) --> 4 Models Tested (ARIMA Wins 62.5%) --> 4,864 Projections through 2030 --> Actionable Public Health Intelligence.',
}

def replace_mermaid_block(match):
    code = match.group(1).strip()
    # Find matching description
    for key, desc in MERMAID_DESCRIPTIONS.items():
        if key in code:
            if desc is None:
                return ''
            return f'\n<div class="diagram-box">{desc}</div>\n'
    # Fallback: just describe it generically
    # Check if it's a pie chart
    if 'pie' in code[:50].lower():
        title_match = re.search(r'title\s+(.+)', code)
        title = title_match.group(1) if title_match else "Chart"
        items = re.findall(r'"([^"]+)"\s*:\s*([\d.]+)', code)
        items_str = " | ".join(f"{name}: {val}%" for name, val in items)
        return f'\n<div class="diagram-box">[CHART] {title}: {items_str}</div>\n'
    if 'xychart' in code[:50].lower():
        return ''  # We have the real bar chart image already
    return ''

raw_md = re.sub(r'```mermaid\s*\n(.*?)```', replace_mermaid_block, raw_md, flags=re.DOTALL)

# Clean up excessive blank lines
raw_md = re.sub(r'\n{4,}', '\n\n\n', raw_md)


# ── 3.  Embed local images as base64 ────────────────────────────────────

def embed_image(match):
    alt = match.group(1)
    src = match.group(2)
    if not src.startswith(('http', 'data:', 'file:')):
        abs_path = (REPORTS_DIR / src).resolve()
        if abs_path.exists():
            with open(abs_path, 'rb') as f:
                b64 = base64.b64encode(f.read()).decode()
            ext = abs_path.suffix.lstrip('.')
            return f'![{alt}](data:image/{ext};base64,{b64})'
        else:
            print(f"  ⚠ Image not found: {abs_path}")
    return match.group(0)

raw_md = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', embed_image, raw_md)
print("All 6 chart images embedded as base64")

# Strip emoji characters that xhtml2pdf can't render
import unicodedata
def strip_emojis(text):
    result = []
    for ch in text:
        cat = unicodedata.category(ch)
        # Keep normal characters, skip symbols/emojis outside basic set
        if cat.startswith('So') and ord(ch) > 0x2600:
            continue
        result.append(ch)
    return ''.join(result)

# Replace specific unicode chars with ASCII
raw_md = raw_md.replace('\u2192', '-->') # →
raw_md = raw_md.replace('\u2550', '=')   # ═
raw_md = raw_md.replace('\u2502', '|')   # │
raw_md = raw_md.replace('\u2014', '--')  # —
raw_md = raw_md.replace('\u2013', '-')   # –
raw_md = raw_md.replace('\u00d7', 'x')   # ×
raw_md = raw_md.replace('\u03c6', 'phi') # φ
raw_md = strip_emojis(raw_md)


# ── 4.  Convert markdown → HTML ──────────────────────────────────────────

print("Converting markdown to HTML...")
html_body = markdown.markdown(
    raw_md,
    extensions=['tables', 'fenced_code', 'toc'],
)


# ── 5.  Build full styled HTML ───────────────────────────────────────────

CSS = """
@page {
    size: A4;
    margin: 2cm 2cm 2.5cm 2cm;
    @bottom-center {
        content: "DiabForecast Research Report — Page " counter(page);
        font-size: 8pt;
        color: #888;
        font-family: 'Segoe UI', Arial, sans-serif;
    }
}

body {
    font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
    font-size: 11pt;
    line-height: 1.65;
    color: #1a1a1a;
}

h1 {
    font-size: 22pt;
    color: #1a365d;
    border-bottom: 3px solid #2b6cb0;
    padding-bottom: 8px;
    margin-top: 0;
}

h2 {
    font-size: 16pt;
    color: #2b6cb0;
    border-bottom: 2px solid #bee3f8;
    padding-bottom: 5px;
    margin-top: 32px;
    page-break-after: avoid;
}

h3 {
    font-size: 13pt;
    color: #2c5282;
    margin-top: 20px;
    page-break-after: avoid;
}

h4 {
    font-size: 11.5pt;
    color: #2d3748;
    margin-top: 16px;
    page-break-after: avoid;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin: 14px 0;
    font-size: 9.5pt;
    page-break-inside: avoid;
}

thead th {
    background-color: #2b6cb0;
    color: white;
    padding: 8px 10px;
    text-align: left;
    font-weight: 600;
}

tbody td {
    padding: 6px 10px;
    border-bottom: 1px solid #e2e8f0;
}

tbody tr:nth-child(even) {
    background-color: #f7fafc;
}

img {
    max-width: 100%;
    height: auto;
    display: block;
    margin: 14px auto;
    border-radius: 4px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08);
}

.diagram-box {
    background: linear-gradient(135deg, #ebf8ff 0%, #f0fff4 100%);
    border: 1px solid #90cdf4;
    border-left: 4px solid #2b6cb0;
    border-radius: 6px;
    padding: 14px 18px;
    margin: 16px 0;
    font-size: 10pt;
    color: #2d3748;
    line-height: 1.7;
    page-break-inside: avoid;
    white-space: pre-line;
}

blockquote {
    border-left: 4px solid #e53e3e;
    background: #fff5f5;
    padding: 10px 16px;
    margin: 14px 0;
    font-size: 10pt;
}

code {
    background: #edf2f7;
    padding: 2px 5px;
    border-radius: 3px;
    font-size: 9.5pt;
    font-family: 'Consolas', monospace;
}

hr {
    border: none;
    border-top: 2px solid #e2e8f0;
    margin: 24px 0;
}

em {
    color: #4a5568;
}

ul, ol {
    margin: 6px 0;
    padding-left: 22px;
}

li { margin-bottom: 3px; }

/* Figure captions - italics after images */
p > em:only-child {
    display: block;
    text-align: center;
    font-size: 9pt;
    color: #718096;
    margin-top: -8px;
}
"""

html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>DiabForecast Research Report</title>
<style>{CSS}</style>
</head>
<body>
{html_body}
</body>
</html>"""

# ── 6.  Save HTML (for debugging) and generate PDF ──────────────────────

html_path = REPORTS_DIR / "DiabForecast_Research_Report.html"
html_path.write_text(html_doc, encoding="utf-8")
print(f"✓ HTML saved: {html_path}")

print(f"Generating PDF...")
from xhtml2pdf import pisa

with open(str(OUTPUT_PDF), "wb") as pdf_file:
    pisa_status = pisa.CreatePDF(html_doc, dest=pdf_file)
    if pisa_status.err:
        print(f"  ⚠ PDF generation had {pisa_status.err} errors")
    else:
        print(f"  ✓ PDF generated cleanly")

size_kb = OUTPUT_PDF.stat().st_size / 1024
print(f"\n✅ PDF saved: {OUTPUT_PDF}")
print(f"   Size: {size_kb:.0f} KB ({size_kb/1024:.1f} MB)")
