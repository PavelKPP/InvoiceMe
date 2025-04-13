import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")