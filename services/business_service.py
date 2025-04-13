class Business:
    def __init__(self, name, email, address, currency, payment_processor, payment_details):
        self.name = name[0] if isinstance(name, tuple) else name
        self.email = email[0] if isinstance(email, tuple) else email
        self.address = address[0] if isinstance(address, tuple) else address
        self.currency = currency[0] if isinstance(currency, tuple) else currency
        self.payment_processor = payment_processor[0] if isinstance(payment_processor, tuple) else payment_processor
        self.payment_details = payment_details[0] if isinstance(payment_details, tuple) else payment_details

    def business_to_dict(self):
        """Convert  obj to dict (For db storage)"""
        return {
            "name": self.name,
            "email": self.email,
            "address": self.address,
            "currency": self.currency,
            "payment_processor": self.payment_processor,
            "payment_details": self.payment_details
        }

    def __str__(self):
        return (f"Business(name={self.name}, email={self.email}, address={self.address}, "
                f"currency={self.currency}, payment_processor={self.payment_processor}, payment_details = {self.payment_details})")
