import markdown
from xhtml2pdf import pisa
import os

MD_PATH = os.path.join(os.path.dirname(__file__), "SYSTEM_REVIEWER.md")
PDF_PATH = os.path.join(os.path.dirname(__file__), "SYSTEM_REVIEWER.pdf")

with open(MD_PATH, encoding="utf-8") as f:
    md_text = f.read()

html_body = markdown.markdown(
    md_text,
    extensions=["tables", "fenced_code", "codehilite", "toc", "nl2br"],
)

full_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    @page {{
        size: A4;
        margin: 1.8cm 1.5cm;
        @frame footer {{
            -pdf-frame-content: footerContent;
            bottom: 0.3cm;
            margin-left: 1.5cm;
            margin-right: 1.5cm;
            height: 1cm;
        }}
    }}
    body {{
        font-family: Helvetica, Arial, sans-serif;
        font-size: 10pt;
        line-height: 1.5;
        color: #1a1a1a;
    }}
    h1 {{
        font-size: 20pt;
        color: #2c3e50;
        border-bottom: 3px solid #388087;
        padding-bottom: 6px;
        margin-top: 24px;
    }}
    h2 {{
        font-size: 15pt;
        color: #2c3e50;
        border-bottom: 1.5px solid #BADFE7;
        padding-bottom: 4px;
        margin-top: 20px;
    }}
    h3 {{
        font-size: 12pt;
        color: #34495e;
        margin-top: 16px;
    }}
    h4 {{
        font-size: 11pt;
        color: #34495e;
        margin-top: 12px;
    }}
    table {{
        border-collapse: collapse;
        width: 100%;
        margin: 10px 0;
        font-size: 9pt;
    }}
    th {{
        background-color: #388087;
        color: white;
        padding: 6px 8px;
        text-align: left;
        border: 1px solid #2c6e73;
    }}
    td {{
        padding: 5px 8px;
        border: 1px solid #ccc;
        vertical-align: top;
    }}
    tr:nth-child(even) td {{
        background-color: #f6f6f2;
    }}
    code {{
        background-color: #f0f0f0;
        padding: 1px 4px;
        border-radius: 3px;
        font-family: Courier, monospace;
        font-size: 9pt;
    }}
    pre {{
        background-color: #2c3e50;
        color: #ecf0f1;
        padding: 10px 12px;
        border-radius: 4px;
        font-size: 8.5pt;
        line-height: 1.4;
        white-space: pre-wrap;
        word-wrap: break-word;
        font-family: Courier, monospace;
        margin: 8px 0;
    }}
    pre code {{
        background-color: transparent;
        color: #ecf0f1;
        padding: 0;
    }}
    blockquote {{
        border-left: 3px solid #388087;
        margin: 8px 0;
        padding: 6px 12px;
        background-color: #f6f6f2;
        color: #555;
        font-size: 9.5pt;
    }}
    hr {{
        border: none;
        border-top: 1px solid #ddd;
        margin: 16px 0;
    }}
    strong {{
        color: #2c3e50;
    }}
    a {{
        color: #388087;
        text-decoration: none;
    }}
    ul, ol {{
        margin: 4px 0 4px 20px;
        padding: 0;
    }}
    li {{
        margin-bottom: 3px;
    }}
    p {{
        margin: 6px 0;
    }}
</style>
</head>
<body>
{html_body}
<div id="footerContent">
    <p style="text-align:center; font-size:8pt; color:#888;">
        Go-onCARE System &mdash; Defense Reviewer
    </p>
</div>
</body>
</html>"""

with open(PDF_PATH, "wb") as pdf_file:
    status = pisa.CreatePDF(full_html, dest=pdf_file)

if status.err:
    print(f"ERROR: PDF conversion failed with {status.err} error(s)")
else:
    size_kb = os.path.getsize(PDF_PATH) / 1024
    print(f"SUCCESS: Created {PDF_PATH} ({size_kb:.0f} KB)")
