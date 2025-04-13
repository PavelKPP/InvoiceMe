from google.cloud import firestore
from google.oauth2 import service_account
import os
from typing import List, Dict, Optional
import uuid
from services.business_service import Business
import json
import base64

# Initialize Firestore
# current_dir = os.path.dirname(os.path.abspath(__file__))
# key_path = os.path.join(current_dir, "firebase-key.json")  # Your Firebase service account key
# key_path = "/home/pavlodev/Desktop/InvoiceMe/firebase-key.json"

# credentials = service_account.Credentials.from_service_account_file(key_path)
# db = firestore.Client(credentials=credentials)

def get_firestore_client():
    try:
        # Get credentials from environment variable
        firebase_config = json.loads(base64.b64decode(os.environ["FIREBASE_CRED"]))
        return firestore.Client.from_service_account_info(firebase_config)
    except Exception as e:
        print(f"🔥 Firestore initialization error: {e}")
        raise

db = get_firestore_client()



class FirestoreService:
    @staticmethod
    def generate_id() -> str:
        return str(uuid.uuid4())

    # User Operations
    @staticmethod
    def get_user(telegram_id: str) -> Optional[Dict]:
        doc_ref = db.collection("users").document(telegram_id)
        doc = doc_ref.get()
        return doc.to_dict() if doc.exists else None

    @staticmethod
    def create_or_update_user(telegram_id: str, business_id: str = None) -> None:
        user_ref = db.collection("users").document(telegram_id)
    
        if business_id:
            # Only add the business ID if it's not already associated
            user_ref.set({
                "telegram_id": telegram_id,
                "businesses_ids": firestore.ArrayUnion([business_id]),
                "updated_at": firestore.SERVER_TIMESTAMP
            }, merge=True)
        else:
            # Initialize user if doesn't exist
            user_ref.set({
                "telegram_id": telegram_id,
                "balance": 0.0,
                "subscription_end": "2024-12-31",
                "created_at": firestore.SERVER_TIMESTAMP
            }, merge=True)


    # Business Operations
    @staticmethod
    def create_business(business_data: Dict) -> str:
        business_id = FirestoreService.generate_id()
        db.collection("businesses").document(business_id).set(business_data)
        return business_id

    @staticmethod
    def get_business(business_id: str) -> Optional[Dict]:
        if not isinstance(business_id, str):
            print(f"Warning: Non-string business ID received: {business_id} ({type(business_id)})")
            return None
        
        try:
            doc_ref = db.collection("businesses").document(business_id)
            doc = doc_ref.get()
            if doc.exists:
                return {"id" : doc.id, **doc.to_dict()}
            return None
        except Exception as e:
            print(f"Error fetching business {business_id}: {str(e)}")
            return None

    

    # Invoice Operations
    @staticmethod
    def create_invoice(invoice_data: Dict) -> str:
        invoice_id = FirestoreService.generate_id()
        db.collection("invoices").document(invoice_id).set(invoice_data)
        return invoice_id

    @staticmethod
    def get_user_businesses(telegram_id: str) -> List[Dict]:
        user = FirestoreService.get_user(telegram_id)
        if not user or not user.get("businesses_ids"):
            return []
        
        businesses = []
        for business_id in user["businesses_ids"]:
            business = FirestoreService.get_business(business_id)
            if business:
                businesses.append({"id": business_id, **business})
        return businesses

    @staticmethod
    def get_business_invoices(business_id: str) -> List[Dict]:
        invoices_ref = db.collection("invoices").where("business_id", "==", business_id)
        return [{"id": doc.id, **doc.to_dict()} for doc in invoices_ref.stream()]
    
    @staticmethod
    def get_user_businesses_for_buttons(telegram_id: str) -> List[Dict]:
        businesses = FirestoreService.get_user_businesses(telegram_id)
        return [{"id": biz["id"], "name": biz["name"]} for biz in businesses]
    
    @staticmethod
    def get_user_details(telegram_id: str)  -> dict:
        user_ref = db.collection("users").where("telegram_id", "==", telegram_id).limit(1)
        docs = user_ref.stream()

        for doc in docs:
            user_data = doc.to_dict()
            return {
                "user_id": user_data.get("telegram_id"),
                "balance": user_data.get("balance", 0.0),
                "subscription": user_data.get("subscription_end", "2025-12-31")
            }
        return None
    
    def get_users_invoices(telegram_id: str) -> list:
        user = FirestoreService.get_user(telegram_id)
        if not user or not user.get("businesses_ids"):
            return []

        invoices = []
        for businesses_id in user["businesses_ids"]:
            invoices.extend(FirestoreService.get_business_invoices(businesses_id))

        return invoices
    
    @staticmethod
    def business_name_exists(user_id: str, business_name: str) -> bool:
        user = FirestoreService.get_user(user_id)
        if not user or not user.get("businesses_ids"):
            return False
        
        for business_id in user["businesses_ids"]:
            biz = FirestoreService.get_business(business_id)
            if biz and biz.get("name", "").lower() == business_name.lower():
                return True
        return False
    
    @staticmethod
    def update_business_field(business_id: str, field: str, value: str) -> None:
        db.collection("businesses").document(business_id).update({
            field: value,
            "updated_at": firestore.SERVER_TIMESTAMP
        })
    
    @staticmethod
    def find_existing_business(business: Business) -> Optional[dict]:
        query = db.collection("businesses") \
            .where("name", "==", business.name) \
            .where("email", "==", business.email) \
            .where("address", "==", business.address) \
            .where("currency", "==", business.currency) \
            .where("payment_processor", "==", business.payment_processor) \
            .where("payment_details", "==", business.payment_details ) \
            .limit(1)
    
        docs = query.stream()
    
        for doc in docs:
            return {"id": doc.id, **doc.to_dict()}
        return None
