import os
import base64
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition
# from config import SENDGRID_API_KEY

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")

def send_inovice_email(user_email, customer_email, business_email, pdf_filename):

    if not SENDGRID_API_KEY:
        print("ERROR: No SendGrid API Key found!")  # Debug API key
        raise ValueError("Missing SendGrid API Key!")
    
    # Verify PDF exists
    if not os.path.exists(pdf_filename):
        print(f"ERROR: PDF file not found at {pdf_filename}")
        raise FileNotFoundError(f"PDF not found: {pdf_filename}")
    
    subject = "Your invoice is ready!"
    content = "Please find the attached invoice in PDF"

    with open(pdf_filename, "rb") as f:
        pdf_data = f.read()
        encoded_pdf = base64.b64encode(pdf_data).decode() 

    message = Mail(
        from_email="invoiceme1488@gmail.com",
        to_emails=[user_email, customer_email, business_email],
        subject=subject,
        plain_text_content=content
    )

    attachment = Attachment(
        file_content=FileContent(encoded_pdf),
        file_type = FileType("application/pdf"),
        file_name= FileName(os.path.basename(pdf_filename)),
        disposition=Disposition("attachment")
    )
    
    message.add_attachment(attachment)

    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        print(f"Email sent! Status Code: {response.status_code}")
    except Exception as e:
        print(f"Error sending email: {str(e)}")

