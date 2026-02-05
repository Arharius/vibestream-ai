from fpdf import FPDF
import os

class VibePDF(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 16)
        self.set_text_color(192, 132, 252)
        self.cell(0, 10, 'VibeStream AI PRO Report', 0, 1, 'C')
        self.ln(5)

def create_pdf(content, filename, save_dir, thumb_path=None):
    pdf = VibePDF()
    # Используем Helvetica для простоты или ArialUnicode если есть файл
    pdf.add_page()
    if thumb_path and os.path.exists(thumb_path):
        pdf.image(thumb_path, x=10, y=25, w=190)
        pdf.set_y(135)
    
    pdf.set_font('Helvetica', '', 12)
    pdf.set_text_color(31, 41, 55)
    pdf.multi_cell(0, 8, txt=content.encode('latin-1', 'replace').decode('latin-1'))
    
    path = os.path.join(save_dir, filename)
    pdf.output(path)
    return path