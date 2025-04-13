from fpdf import FPDF
from services.invoice_service import Invoice

class PDFInvoiceItimized(FPDF):
    def __init__(self, invoice: Invoice):
        super().__init__()
        self.invoice = invoice
        self.final_tax: float = invoice.tax_percent / 100

    def header(self):
        """Creates the invoice header with title, logo, and invoice details."""
        self.set_font("Arial", "B", 24)
        self.cell(190, 15, "INVOICE", ln=True, align="C")
        self.ln(5)

        # Insert logo (if available)
        # self.image("logo.png", 160, 10, 30)  # Uncomment and provide a logo file

        # Invoice metadata (invoice number, date, due date)
        self.set_font("Arial", "B", 12)
        self.set_fill_color(173, 216, 230)  # Light blue background

        self.cell(63, 8, f"INVOICE NO.: {self.invoice.invoice_number}", 1, 0, "C", fill=True)
        self.cell(63, 8, f"INVOICE DATE: {self.invoice.invoice_date}", 1, 0, "C", fill=True)
        self.cell(64, 8, f"PAY BY: {self.invoice.pay_by_date}", 1, 1, "C", fill=True)
        self.ln(5)


    def company_details(self):
        """Add business and customer details with Business Name first."""
        self.set_font("Arial", "B", 12)
        self.cell(100, 6, "NAME OF COMPANY", ln=True)

        business_name = ", ".join(self.invoice.business.name) if isinstance(self.invoice.business.name, tuple) else self.invoice.business.name

        self.set_font("Arial", "", 11)
        self.cell(100, 6, business_name, ln=True)

        self.set_font("Arial", "", 11)

    
        business_address = ", ".join(self.invoice.business.address) if isinstance(self.invoice.business.address, tuple) else self.invoice.business.address
        business_email = ", ".join(self.invoice.business.email) if isinstance(self.invoice.business.email, tuple) else self.invoice.business.email

        self.cell(100, 6, business_address, ln=True)
        self.cell(100, 6, business_email, ln=True)
        self.ln(5)

        self.set_font("Arial", "B", 12)
        self.cell(100, 6, "BILL TO:", ln=True)
        self.set_font("Arial", "", 11)

    
        customer_address = ", ".join(self.invoice.customer_address) if isinstance(self.invoice.customer_address, tuple) else self.invoice.customer_address
        customer_email = ", ".join(self.invoice.customer_email) if isinstance(self.invoice.customer_email, tuple) else self.invoice.customer_email

        self.cell(100, 6, self.invoice.customer_name, ln=True)
        self.cell(100, 6, customer_address, ln=True)
        self.cell(100, 6, customer_email, ln=True)
        self.ln(10)



    def invoice_table(self):
        """Create invoice table for items."""
        self.set_font("Arial", "B", 12)
        self.set_fill_color(173, 216, 230)  # Light blue background

        # Table Headers
        self.cell(80, 8, "DESCRIPTION OF PRODUCT/SERVICE", 1, 0, "C", fill=True)
        self.cell(30, 8, "UNIT PRICE", 1, 0, "C", fill=True)
        self.cell(30, 8, "QTY", 1, 0, "C", fill=True)
        self.cell(30, 8, "TOTAL", 1, 1, "C", fill=True)

        # Table Items
        self.set_font("Arial", "", 11)
        for item in self.invoice.items_list:
            self.cell(80, 8, item["item"], 1)
            self.cell(30, 8, f"${item['price']:.2f}", 1, 0, "C")
            self.cell(30, 8, str(item["quantity"]), 1, 0, "C")
            self.cell(30, 8, f"${item['total']:.2f}", 1, 1, "C")

        self.ln(5)

    def totals_section(self):
        """Add subtotal, tax, and final total (No Discounts)."""
        subtotal = self.invoice.calculate_total_pdf()
        tax = subtotal * self.final_tax 
        amount_due = subtotal + tax  # No discount applied

        self.set_font("Arial", "B", 12)
        self.cell(140, 8, "", 0)  # Empty space before the total section
        self.cell(30, 8, "SUBTOTAL:", 1, 0, "C", fill=True)
        self.cell(30, 8, f"${subtotal:.2f}", 1, 1, "C")

        self.cell(140, 8, "", 0)
        self.cell(30, 8, f"TAX:{self.invoice.tax_percent}%", 1, 0, "C", fill=True)
        self.cell(30, 8, f"${tax:.2f}", 1, 1, "C")

        self.cell(140, 8, "", 0)
        self.cell(30, 8, "AMOUNT DUE:", 1, 0, "C", fill=True)
        self.cell(30, 8, f"${amount_due:.2f}", 1, 1, "C")

        self.ln(10)

    def payment_methods(self):
        """Add payment method details."""
        self.set_font("Arial", "B", 12)
        self.cell(100, 6, "PAYMENT METHODS", ln=True)
        self.set_font("Arial", "", 11)
        self.cell(100, 6, f"COMPANY NAME: {self.invoice.business.name}", ln=True)
        self.cell(100, 6, f"{self.invoice.business.payment_processor}: {self.invoice.business.payment_details}", ln=True)
        self.ln(10)

    def thank_you_message(self):
        """Add a 'Thank You' message at the bottom."""
        self.set_font("Arial", "B", 14)
        self.cell(190, 10, "THANK YOU", ln=True, align="C")

    def generate_pdf(self, filename="invoice.pdf"):
        """Generate the invoice PDF."""
        self.add_page()
        self.company_details()
        self.invoice_table()
        self.totals_section()
        self.payment_methods()
        self.thank_you_message()
        self.output(filename)

        return filename



class PDFInvoiceHourly(FPDF):
    def __init__(self, invoice: Invoice):
        super().__init__()
        self.invoice = invoice
        self.final_tax: float = invoice.tax_percent / 100

    def header(self):
        """Creates the invoice header with title, logo, and invoice details."""
        self.set_font("Arial", "B", 24)
        self.cell(190, 15, "INVOICE", ln=True, align="C")
        self.ln(5)

        # Insert logo (if available)
        # self.image("logo.png", 160, 10, 30)  # Uncomment and provide a logo file

        # Invoice metadata (invoice number, date, due date)
        self.set_font("Arial", "B", 12)
        self.set_fill_color(173, 216, 230)  # Light blue background

        self.cell(63, 8, f"INVOICE NO.: {self.invoice.invoice_number}", 1, 0, "C", fill=True)
        self.cell(63, 8, f"INVOICE DATE: {self.invoice.invoice_date}", 1, 0, "C", fill=True)
        self.cell(64, 8, f"PAY BY: {self.invoice.pay_by_date}", 1, 1, "C", fill=True)
        self.ln(5)


    def company_details(self):
        """Add business and customer details with Business Name first."""
        self.set_font("Arial", "B", 12)
        self.cell(100, 6, "NAME OF COMPANY", ln=True)

        business_name = ", ".join(self.invoice.business.name) if isinstance(self.invoice.business.name, tuple) else self.invoice.business.name

        self.set_font("Arial", "", 11)
        self.cell(100, 6, business_name, ln=True)

        self.set_font("Arial", "", 11)

    
        business_address = ", ".join(self.invoice.business.address) if isinstance(self.invoice.business.address, tuple) else self.invoice.business.address
        business_email = ", ".join(self.invoice.business.email) if isinstance(self.invoice.business.email, tuple) else self.invoice.business.email

        self.cell(100, 6, business_address, ln=True)
        self.cell(100, 6, business_email, ln=True)
        self.ln(5)

        self.set_font("Arial", "B", 12)
        self.cell(100, 6, "BILL TO:", ln=True)
        self.set_font("Arial", "", 11)

    
        customer_address = ", ".join(self.invoice.customer_address) if isinstance(self.invoice.customer_address, tuple) else self.invoice.customer_address
        customer_email = ", ".join(self.invoice.customer_email) if isinstance(self.invoice.customer_email, tuple) else self.invoice.customer_email

        self.cell(100, 6, self.invoice.customer_name, ln=True)
        self.cell(100, 6, customer_address, ln=True)
        self.cell(100, 6, customer_email, ln=True)
        self.ln(10)



    def invoice_table(self):
        """Create invoice table for items."""
        self.set_font("Arial", "B", 12)
        self.set_fill_color(173, 216, 230)  # Light blue background

        # Table Headers
        self.cell(80, 8, "DESCRIPTION OF PRODUCT/SERVICE", 1, 0, "C", fill=True)
        self.cell(30, 8, "UNIT PRICE", 1, 0, "C", fill=True)
        self.cell(30, 8, "HOURS", 1, 0, "C", fill=True)
        self.cell(30, 8, "TOTAL", 1, 1, "C", fill=True)

        # Table Items
        self.set_font("Arial", "", 11)
        for item in self.invoice.items_list:
            self.cell(80, 8, item["item"], 1)
            self.cell(30, 8, f"${item['price']:.2f}", 1, 0, "C")
            self.cell(30, 8, str(item["quantity"]), 1, 0, "C")
            self.cell(30, 8, f"${item['total']:.2f}", 1, 1, "C")

        self.ln(5)

    def totals_section(self):
        """Add subtotal, tax, and final total (No Discounts)."""
        subtotal = self.invoice.calculate_total_pdf()
        tax = subtotal * self.final_tax  
        amount_due = subtotal + tax  # No discount applied

        self.set_font("Arial", "B", 12)
        self.cell(140, 8, "", 0)  # Empty space before the total section
        self.cell(30, 8, "SUBTOTAL:", 1, 0, "C", fill=True)
        self.cell(30, 8, f"${subtotal:.2f}", 1, 1, "C")

        self.cell(140, 8, "", 0)
        self.cell(30, 8, f"TAX: 10%:{self.invoice.tax_percent}%", 1, 0, "C", fill=True)
        self.cell(30, 8, f"${tax:.2f}", 1, 1, "C")

        self.cell(140, 8, "", 0)
        self.cell(30, 8, "AMOUNT DUE:", 1, 0, "C", fill=True)
        self.cell(30, 8, f"${amount_due:.2f}", 1, 1, "C")

        self.ln(10)

    def payment_methods(self):
        """Add payment method details."""
        self.set_font("Arial", "B", 12)
        self.cell(100, 6, "PAYMENT METHODS", ln=True)
        self.set_font("Arial", "", 11)
        self.cell(100, 6, f"COMPANY NAME: {self.invoice.business.name}", ln=True)
        self.cell(100, 6, f"{self.invoice.business.payment_processor}: {self.invoice.business.payment_details}", ln=True)
        self.ln(10)

    def thank_you_message(self):
        """Add a 'Thank You' message at the bottom."""
        self.set_font("Arial", "B", 14)
        self.cell(190, 10, "THANK YOU", ln=True, align="C")

    def generate_pdf(self, filename="invoice.pdf"):
        """Generate the invoice PDF."""
        self.add_page()
        self.company_details()
        self.invoice_table()
        self.totals_section()
        self.payment_methods()
        self.thank_you_message()
        self.output(filename)

        return filename
