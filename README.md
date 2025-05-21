Telegram Messanger Bot "InvoiceMe":

[ Idea of the Bot]

Designed and built fully functionall bot for messanger Telegram. Which is collecting business information from user, saves it to the database for future use of selected business and then collects information for the invoice. 
Based on collected information from users input it validates the data and generates PDF file of the invoice. Besides creating invoice it automatically sends it to the user mail and contractor mail.

[ Stack ]: 

Python, Firebase API, Sendgrid API, Telegram API, Kubernetes.

[ Functionallity]: 

1. Main menu navigation
2. Collect and store business information.
3. Edit business information through menu navigation.
4. Automatically collect and store user information
5. Collect and store invoice information.
6. Generate PDF file of the invoice.
7. Send PDF file of the invoice to the user via Telegram.
8. Send the pdf file over user and contractor email.

[ Project Structure ]:

InvoiceBot/
├── handlers/ # Telegram bot conversation handlers
│ ├── init.py
│ └── chat_handler.py # Main chat logic
│
├── services/ # Backend service layers
│ ├── init.py
│ ├── business_service.py # Business model
│ ├── database_service.py # Database operations
│ ├── email_service.py # Email sending operations
│ ├── firestore_service.py # Firestore interactions
│ ├── invoice_service.py # Invoice model
│ └── pdf_service.py # PDF creation service
│
├── venv/ # Python virtual environment
│
├── .dockerignore # Docker ignore rules
├── .gitignore # Git ignore rules
├── bot.py # Main bot entry point
├── config.py # Configuration settings
├── Dockerfile # Containerization
└── requirements.txt # Python dependencies
