# test_weasyprint.py
from weasyprint import HTML

html_content = "<h1>Test PDF</h1><p>This is a test.</p>"
HTML(string=html_content).write_pdf("test.pdf")
print("PDF generated successfully!")