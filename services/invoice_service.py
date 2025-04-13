from services.business_service import Business
from datetime import date


class Invoice:
    def __init__(self, business: Business, invoice_number, pay_by_date, 
                    customer_name, customer_address, customer_email,
                    hours, tax_percent):
        self.business = business
        self.invoice_number = invoice_number
        self.invoice_date = date.today().strftime("%d/%m/%Y")
        self.pay_by_date = pay_by_date
        self.customer_name = customer_name
        self.customer_address = customer_address
        self.customer_email = customer_email
        self.items_list = [] # Starting with an empty list
        self.hours = hours
        self.tax_percent = tax_percent

    def add_item(self, item_name, price, quantity):
        """Adds an item to the invoice"""
        total = price * quantity
        self.items_list.append({"item": item_name, "price": price, "quantity": quantity, "total": total})
        self.total = self.calculate_total()


    def calculate_total(self):
        sub_total = sum(item["total"] for item in self.items_list)
        taxed_total = ((self.tax_percent / 100) * sub_total) + sub_total
        return taxed_total

    def calculate_total_pdf(self):
        return sum(item["total"] for item in self.items_list)

    def invoice_to_dict(self):
        """For the db purposes"""
        return {
            "business": self.business.business_to_dict(),
            "invoice_number": self.invoice_number,
            "invoice_date": self.invoice_date,
            "pay_by_date": self.pay_by_date,
            "customer_name": self.customer_name,
            "customer_address": self.customer_address,
            "customer_email": self.customer_email,
            "tasks_cost": self.tasks_cost,
            "invoice_total": self.invoice_total,
            "hours": self.hours
        }
    
    def __str__(self):
        return (f"Invoice(invoice_number={self.invoice_number}, invoice_date={self.invoice_date}, "
            f"pay_by_date={self.pay_by_date}, customer_name={self.customer_name}, "
            f"customer_address={self.customer_address}, customer_email={self.customer_email}, "
            f"hours={self.hours}, items_list={self.items_list}), tax={self.tax_percent}%,")