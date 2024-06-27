import  os
from fpdf import FPDF

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Cotización', 0, 1, 'C')

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

def generar_pdf(cotizacion):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font('Arial', '', 12)
    cantidad = 0
    
    for item in cotizacion:
        pdf.cell(0, 10, f"Nombre: {item['nombre']}", 0, 1)
        pdf.cell(0, 10, f"Cantidad: {item['cantidad']}", 0, 1)
        pdf.cell(0, 10, f"Precio: {item['precio']}", 0, 1)
        pdf.ln(10)
        cantidad+= item['precio']
        
    pdf.cell(0, 10, f"Total: {cantidad}", 0, 1)
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(current_dir)
    
    pdf_file_path = os.path.join(project_dir, "resources", "cotizaciones", "Cotizacion.pdf")
    print("ruta: ", pdf_file_path)
    pdf.output(pdf_file_path)
    
    return pdf_file_path
    