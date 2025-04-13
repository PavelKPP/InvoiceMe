from services.firestore_service import FirestoreService
from services.business_service import Business
from services.invoice_service import Invoice
from typing import List, Dict
from google.cloud import firestore

def store_business(business: Business) -> str:

    existing_business = FirestoreService.find_existing_business(business)

    if existing_business:
        print(f"Business already exists with ID: {existing_business['id']}")
        return existing_business['id']

    business_data = {
        "name": business.name,
        "email": business.email,
        "address": business.address,
        "currency": business.currency,
        "payment_processor": business.payment_processor,
        "payment_details": business.payment_details,
        "created_at": firestore.SERVER_TIMESTAMP
    }
    return FirestoreService.create_business(business_data)

def store_invoice(invoice: Invoice, business_id: str) -> str:
    
    invoice_data = {
        "business_id": business_id,
        "invoice_number": invoice.invoice_number,
        "pay_by_date": invoice.pay_by_date,
        "customer_name": invoice.customer_name,
        "customer_address": invoice.customer_address,
        "customer_email": invoice.customer_email,
        "hours": invoice.hours,
        "items": invoice.items_list,
        "tax":invoice.tax_percent,
        "total": invoice.calculate_total(),
        "created_at": firestore.SERVER_TIMESTAMP
    }
    return FirestoreService.create_invoice(invoice_data)

def update_user(telegram_id: str, business_id: str) -> None:
    FirestoreService.create_or_update_user(telegram_id, business_id)

def get_user_businesses(telegram_id: str) -> List[Dict]:
    return FirestoreService.get_user_businesses(telegram_id)

def get_business_invoices(business_id: str) -> List[Dict]:
    return FirestoreService.get_business_invoices(business_id)