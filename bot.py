# from telegram import Update
# from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler
# from handlers.chat_handler import conv_handler
# from config import TELEGRAM_BOT_TOKEN

# app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

# app.add_handler(conv_handler)


# if __name__ == "__main__":
#     print("Bot is running...")
#     app.run_polling()

from telegram.ext import Application, CallbackContext, ApplicationBuilder   
from telegram import Update 
from config import TELEGRAM_BOT_TOKEN
from handlers.chat_handler import setup_handlers
import logging  
import os
# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def post_init(application: Application) -> None:
    """Optional post-initialization actions"""
    await application.bot.set_my_commands([
        ("start", "Start the bot"),
        ("help", "Show help information")
    ])

# def main() -> None:
#     """Run the bot."""
#     # Create the Application
#     application = Application.builder() \
#         .token(TELEGRAM_BOT_TOKEN) \
#         .post_init(post_init) \
#         .build()

def main():
    # Get token from environment variable
    token = os.environ.get("TELEGRAM_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_TOKEN environment variable not set!")
    
    application = ApplicationBuilder() \
        .token(token) \
        .build()


    setup_handlers(application)

    # Add error handler
    application.add_error_handler(error_handler)

    logger.info("Bot is running...")
    application.run_polling()

async def error_handler(update: Update, context: CallbackContext) -> None:
    """Log errors and notify user"""
    logger.error("Exception while handling an update:", exc_info=context.error)
    
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "⚠️ An error occurred. Please try again or use /start to restart."
        )

if __name__ == "__main__":
    main()

