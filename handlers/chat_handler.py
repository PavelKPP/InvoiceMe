import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    CallbackContext,
    CallbackQueryHandler,
)
from datetime import datetime, timedelta
from services.business_service import Business
from services.invoice_service import Invoice
from services.pdf_service import PDFInvoiceItimized, PDFInvoiceHourly
from services.email_service import send_inovice_email
from services.database_service import store_business, store_invoice, update_user
from services.firestore_service import FirestoreService
from datetime import datetime

(
    MAIN_MENU,
    BUSINESS_NAME, BUSINESS_EMAIL, BUSINESS_ADDRESS, CURRENCY, PAYMENT_PROCESSOR,
    INVOICE_NUMBER, PAY_BY_DATE, CUSTOMER_NAME, CUSTOMER_ADDRESS, CUSTOMER_EMAIL,
    HOURS, ITEM_NAME, ITEM_QUANTITY, ITEM_PRICE, MORE_ITEMS
) = range(16)

async def start(update: Update, context: CallbackContext) -> int:
    """Start the conversation and show the main menu."""
    keyboard = [
        [InlineKeyboardButton("👤 My Account" , callback_data="account_info")],
        [InlineKeyboardButton("🏢 My Businesses", callback_data="business_info")],
        [InlineKeyboardButton("🧾 New Invoice", callback_data="create_invoice")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text("🌟 Welcome to InvoiceBot! 🌟\nHow can I help you today?", reply_markup=reply_markup)
    else:
        await update.callback_query.message.reply_text("🌟 Welcome to InvoiceBot! 🌟\nHow can I help you today?", reply_markup=reply_markup)
    
    return MAIN_MENU

async def main_menu_handler(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    
    if query.data == "create_invoice":
        context.user_data.clear()  # Clear any previous data
        
        # New: Ask if user wants existing or new business
        keyboard = [
            [InlineKeyboardButton("🔍 Use Existing Business" , callback_data="use_existing_business")],
            [InlineKeyboardButton("📝 Create new Business", callback_data="create_new_business")]
        ]
        
        await query.edit_message_text(
            "Would you like to use an existing business or create a new one?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return SELECT_BUSINESS_TYPE  # New state for this choice
    
    elif query.data == "account_info":
        # Keep your existing account info logic
        return await account_info_handler(update, context)
    
    elif query.data == "back_to_menu":
        # Return to main menu
        return await start(update, context)

    elif query.data == "business_info":
        return await business_info_handler(update, context)
        
    
    elif query.data == "back_to_menu":
        return await start(update, context)
    
    return MAIN_MENU


async def account_info_handler(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()

    user_id = str(query.from_user.id)


    user_exists = FirestoreService.if_user_exists(user_id)


    user_data = FirestoreService.get_user_details(user_id)

    if not user_exists:
        subscrtiption_end_date = (datetime.now() + timedelta(days=7)).strftime("%Y- %m-%d")

        user_data = {
            "user_id" : user_id,
            "subscription_types" : "Freemium (7 Day Trial)",
            "invoices_left": "unlimitted",
            "subscription" : subscrtiption_end_date
        }
        FirestoreService.create_or_update_user(user_id, user_data)

    message = (
        "👤 <b>Account Information</b>\n\n"
        f"🆔 User ID: <code>{user_data['user_id']}</code>\n"
        f"💰 Subscription Type: {user_data['subscription_types']}\n"
        f"Invoices Left: {user_data['invoices_left']}\n"
        f"📅 Subscription valid until: {user_data['subscription']}\n\n"
        f"📊 Invoices created: {len(FirestoreService.get_users_invoices(user_id))}"
    )

    await query.edit_message_text(
        text=message,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")]
        ])
    )
    return MAIN_MENU

async def business_info_handler(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()

    user_id = str(query.from_user.id)
    businesses = FirestoreService.get_user_businesses_for_buttons(user_id)

    if not businesses:
        await query.edit_message_text(
            "📭 You haven't created any businesses yet.\nWould you like to set one up now?",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📝 Create Business", callback_data="create_new_business_from_info")],
                [InlineKeyboardButton("🔙 Back", callback_data="back_to_menu")]
            ])
        )
        return BUSINESS_MENU
    
    keyboard = []
    for i in range(0, len(businesses), 2):
        row = businesses[i:i+2]
        keyboard.append([
            InlineKeyboardButton(biz["name"], callback_data=f"biz_{str(biz['id'])}")
            for biz in row
        ])

    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back_to_menu")])

    await query.edit_message_text(
        "📁 Your Businesses:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return BUSINESS_MENU

async def handle_create_from_info(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()

    user_id = str(query.from_user.id)
    period = FirestoreService.get_subscription_period(user_id)

    
    subscription_date = datetime.strptime(period, "%Y-%m-%d").date()
    today = datetime.now().date()

    if subscription_date < today:
        await query.message.reply_text(
        "⚠️ Your subscription has expired on {}. "
        "Please upgrade to continue using InvoiceBot.".format(period)
        )
        return ConversationHandler.END
    
    query = update.callback_query
    await query.answer()

    context.user_data.clear()

    await query.edit_message_text("Strating business creation...")

    await context.bot.send_message(     
        chat_id = query.message.chat_id,
        text = "🏢 Let's get your business set up!\nWhat should we call your business?",
        reply_markup = None
    )
    return BUSINESS_NAME

async def show_invoices_handler(update: Update, context: CallbackContext) -> int:
    """Show invoices for selected business"""
    query = update.callback_query
    await query.answer()
    
    business_id = query.data.replace("invoices_", "")
    invoices = FirestoreService.get_business_invoices(business_id)
    
    if not invoices:
        await query.edit_message_text(
            "No invoices found for this business!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data=f"biz_{business_id}")]
            ])
        )
        return BUSINESS_DETAILS
    
    text = "📋 Invoices:\n\n" + "\n".join(
        f"• {inv['invoice_number']} - {inv['created_at'].strftime('%Y-%m-%d')} - ${inv['total']}"
        for inv in invoices
    )
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data=f"biz_{business_id}")]
        ])
    )
    return BUSINESS_DETAILS

async def edit_business_handler(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()

    if query.data == "edit_name":
        await query.edit_message_text(
            "Enter the new business name:",
            reply_markup=None
        )
        return EDIT_BUSINESS_NAME
    
    elif query.data == "edit_email":
        await query.edit_message_text(
            "Enter the new business email:",
            reply_markup=None
        )
        return EDIT_BUSINESS_EMAIL
        
    elif query.data == "edit_address":
        await query.edit_message_text(
            "Enter the new business address:",
            reply_markup=None
        )
        return EDIT_BUSINESS_ADDRESS
        
    elif query.data == "edit_currency":
        await query.edit_message_text(
            "Enter the new currency:",
            reply_markup=None
        )
        return EDIT_BUSINESS_CURRENCY
        
    elif query.data == "edit_payment":
        await query.edit_message_text(
            "Enter the new payment processor:",
            reply_markup=None
        )
        return EDIT_BUSINESS_PAYMENT
    
    elif query.data == "edit_payment_details":
        await query.edit_message_text(
            "Enter new payment details information(Email, IBAN, Stripe Number)"
        )
        return EDIT_BUSINESS_PAYMENT_DETAILS
        
    elif query.data.startswith("biz_"):  # Back button
        return await handle_business_selection(update, context)
    

async def handle_business_selection(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()

    try:
        business_id = query.data.split("_")[1]
    except (IndexError, AttributeError):
        await query.edit_message_text(
            "Invalid business selection", 
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="business_info")]
            ])
        )
        return MAIN_MENU
    
    print(f"Fetching business with ID: {business_id}") 
    business = FirestoreService.get_business(business_id)

    if not business:
        await query.edit_message_text(
            "Business Not Found!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="business_info")]
            ])
        )
        return MAIN_MENU
    
    payment_details = business.get('payment_details', 'Not specified')
    
    #simple formatting for better output:
    text = (
        f"🏢 {business['name']}\n\n"
        f"📧 Email: {business['email']}\n"
        f"📍 Address: {business['address']}\n"
        f"💵 Currency: {business['currency']}\n"
        f"💳 Payment Processor: {business['payment_processor']}\n\n"
        f"💵 Payment Details: {payment_details}\n\n"
        f"Created: {business['created_at'].strftime('%Y-%m-%d')}"
    )

    keyboard = [
        [InlineKeyboardButton("View Invoices", callback_data=f"invoices_{business_id}")],
        [InlineKeyboardButton("Edit Business", callback_data=f"edit_business_{business_id}")],
        [InlineKeyboardButton("🔙 Back", callback_data="business_info")]
    ]

    await query.edit_message_text(
        text, 
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return BUSINESS_DETAILS


async def edit_business_options(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()

    try: 
        business_id = query.data.split("_")[-1]
    except(IndexError, AttributeError):
        await query.edit_message_text("Error: Business is not identified")
        return BUSINESS_DETAILS

    context.user_data["edit_business_id"] = business_id

    keyboard = [
        [InlineKeyboardButton("Edit Name", callback_data="edit_name")],
        [InlineKeyboardButton("Edit Email", callback_data="edit_email")],
        [InlineKeyboardButton("Edit Address", callback_data="edit_address")],
        [InlineKeyboardButton("Edit Currency", callback_data="edit_currency")],
        [InlineKeyboardButton("Edit Payment Processor", callback_data="edit_payment")],
        [InlineKeyboardButton("Edit Payment Details", callback_data="edit_payment_details")],
        [InlineKeyboardButton("🔙 Back", callback_data=f"biz_{business_id}")]
    ]

    await query.edit_message_text(
          "What would you like to edit?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return EDIT_BUSINESS    

async def select_business_type(update: Update, context: CallbackContext) -> int:
    """Handle new/existing business selection"""
    query = update.callback_query
    await query.answer()

    user_id = str(query.from_user.id)
    period = FirestoreService.get_subscription_period(user_id)

    print("PERIOD: ", period)
    
    subscription_date = datetime.strptime(period, "%Y-%m-%d").date()
    today = datetime.now().date()

    if subscription_date < today:
        await query.message.reply_text(
        "⚠️ Your subscription has expired on {}. "
        "Please upgrade to continue using InvoiceBot.".format(period)
        )
        return ConversationHandler.END
    
    query = update.callback_query
    
    if query.data == "create_new_business":
        # First edit the original message
        await query.edit_message_text("Starting business creation...")
        
        # Then send a new message with keyboard removal
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="🏢 Let's get your business set up!\nWhat should we call your business?",
            reply_markup=ReplyKeyboardRemove()  # <-- Now works correctly
        )
        return BUSINESS_NAME
    
    elif query.data == "use_existing_business":
        # Show existing businesses menu
        user_id = str(query.from_user.id)
        businesses = FirestoreService.get_user_businesses_for_buttons(user_id)
        print(f"Businesses retrieved: {[b['id'] for b in businesses]}")
        
        if not businesses:
            await query.edit_message_text(
                "You don't have any businesses yet. Please create one first.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📝 Create Business", callback_data="create_new_business_from_info")],
                    [InlineKeyboardButton("🔙 Back", callback_data="back_to_menu")]
                ])
            )
            return BUSINESS_MENU
        

        buttons = [
        [InlineKeyboardButton(biz["name"], callback_data=f"select_biz_{biz['id']}")]
        for biz in businesses
        ]

        print(f"Created buttons with data: {[b[0].callback_data for b in buttons]}")

        # Add back button
        buttons.append([InlineKeyboardButton("🔙 Back", callback_data="back_to_menu")])
        
        await query.edit_message_text(
            "Select a business to use for this invoice:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return SELECT_EXISTING_BUSINESS
    
    return MAIN_MENU

async def handle_existing_business_selection(update: Update, context: CallbackContext) -> int:
    """Store selected business and proceed to invoice creation"""
    query = update.callback_query
    await query.answer()
    
    try:
        business_id = query.data.split('_')[-1]
    except (IndexError, AttributeError) as e:
        print(f"Error parsing business ID: {e}")
        await query.edit_message_text(
            "⚠️ Error selecting business. Please try again.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="create_invoice")]
            ])
        )
        return MAIN_MENU
    
    business_data = FirestoreService.get_business(business_id)
    if not business_data:
        await query.edit_message_text(
            "Business not found!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="create_invoice")]
            ])
        )
        return MAIN_MENU
    
    # Convert the dictionary to a Business object before storing
    business = Business(
        name=business_data['name'],
        email=business_data['email'],
        address=business_data['address'],
        currency=business_data['currency'],
        payment_processor=business_data['payment_processor'],
        payment_details=business_data['payment_details']
    )
    
    # Store the Business object (not the raw dictionary)
    context.user_data["business"] = business
    
    await query.edit_message_text(
        f"✅ Using business: {business.name}\n"
        "Now enter the invoice number:",
        reply_markup=None
    )
    return INVOICE_NUMBER



(BUSINESS_MENU, BUSINESS_DETAILS, EDIT_BUSINESS) = range(16, 19)
(SELECT_BUSINESS_TYPE, SELECT_EXISTING_BUSINESS) = range(19, 21)






async def get_business_name(update: Update, context: CallbackContext) -> int:
    business_name = update.message.text.strip()
    user_id = str(update.effective_user.id)
    if not business_name or len(business_name) > 100:
        await update.message.reply_text(
            "❗ Please enter a valid business name (1-100 characters):"
        )
        return BUSINESS_NAME
    
    if FirestoreService.business_name_exists(user_id, business_name):
        await update.message.reply_text(
            "⚠️ You already have a business with this name.\n"
            "Please enter a different business name:"
        )
        return BUSINESS_NAME
    

    context.user_data['business_name'] = business_name
    await update.message.reply_text("📧 What's your business email address?")
    return BUSINESS_EMAIL

async def get_business_email(update: Update, context: CallbackContext) -> int:
    email = update.message.text.strip().lower()
    if not ("@" in email and "." in email.split("@")[1] and 5 <= len(email) <= 100):
        await update.message.reply_text(
            "❗ Please enter a valid email address (e.g., name@example.com):"
        )
        return BUSINESS_EMAIL
    

    context.user_data['business_email'] = email
    await update.message.reply_text("🏠 What's your business billing address?")
    return BUSINESS_ADDRESS

async def get_business_address(update: Update, context: CallbackContext) -> int:
    address = update.message.text.strip()
    if not address or len(address) > 200:
        await update.message.reply_text(
            "❗ Please enter a valid address (1-200 characters):"
        )
        return BUSINESS_ADDRESS


    context.user_data['business_address'] = address
    await update.message.reply_text("💵 What currency do you use? (e.g., USD, EUR, GBP)")
    return CURRENCY

async def get_currency(update: Update, context: CallbackContext) -> int:
    currency = update.message.text.strip().upper()
    if len(currency) != 3 or not currency.isalpha():
        await update.message.reply_text(
            "❗ Please enter a valid 3-letter currency code (e.g., USD, EUR):"
        )
        return CURRENCY

    context.user_data['currency'] = currency
    await update.message.reply_text("💳 Which payment processor do you use? (e.g., Stripe, PayPal)")
    return PAYMENT_PROCESSOR
  

async def get_payment_processor(update: Update, context: CallbackContext) -> int:
    processor = update.message.text.strip()
    if not processor or len(processor) > 50:
        await update.message.reply_text(
            "❗ Please enter a valid payment processor (1-50 characters):"
        )
        return PAYMENT_PROCESSOR

    context.user_data['payment_processor'] = processor
    await update.message.reply_text(
        "💳 Please enter payment details (IBAN, account number, or payment email):"
    )
    return PAYMENT_DETAILS

async def get_payment_details(update: Update, context: CallbackContext) -> int:
    payment_details = update.message.text.strip()
    if not payment_details:
        await update.message.reply_text("❗ Please enter valid payment details:")
        return PAYMENT_DETAILS
    
    context.user_data['payment_details'] = payment_details

    business = Business(
        name=context.user_data['business_name'],
        email=context.user_data['business_email'],
        address=context.user_data['business_address'],
        currency=context.user_data['currency'],
        payment_processor=context.user_data['payment_processor'],
        payment_details=payment_details 
    )
    context.user_data['business'] = business

    await update.message.reply_text(
        "✅ Business details saved!\n"
        "Now let's create your invoice.\n"
        "📄 What should be the invoice number/reference?"
    )
    return INVOICE_NUMBER


async def get_invoice_number(update: Update, context: CallbackContext) -> int:
    invoice_num = update.message.text.strip()
    if not invoice_num or len(invoice_num) > 20:
        await update.message.reply_text(
             "❗ Please enter a valid invoice number/reference (1-20 characters):"
        )
        return INVOICE_NUMBER

    context.user_data['invoice_number'] = invoice_num
    await update.message.reply_text("📅 When is payment due? (DD/MM/YYYY)")
    return PAY_BY_DATE

async def get_pay_by_date(update: Update, context: CallbackContext) -> int:
    date_str = update.message.text.strip()
    try:
        due_date = datetime.strptime(date_str, "%d/%m/%Y").date()
        if due_date < datetime.now().date():
            raise ValueError("Date in past")
    except ValueError:
        await update.message.reply_text(
            "❗ Please enter a valid future date in DD/MM/YYYY format:"
        )
        return PAY_BY_DATE


    context.user_data['pay_by_date'] = date_str
    await update.message.reply_text("👤 What's the customer's full name?")
    return CUSTOMER_NAME

async def get_customer_name(update: Update, context: CallbackContext) -> int:
    name = update.message.text.strip()
    if not name or len(name) > 100:
        await update.message.reply_text(
            "❗ Please enter a valid customer name (1-100 characters):"
        )
        return CUSTOMER_NAME


    context.user_data['customer_name'] = name
    await update.message.reply_text("🏠 What's the customer's address?")
    return CUSTOMER_ADDRESS

async def get_customer_address(update: Update, context: CallbackContext) -> int:
    context.user_data['customer_address'] = update.message.text
    await update.message.reply_text("📧 What's the customer's email address?")
    return CUSTOMER_EMAIL

async def get_customer_email(update: Update, context: CallbackContext) -> int:
    email = update.message.text.strip().lower()
    if not ("@" in email and "." in email.split("@")[1] and 5 <= len(email) <= 100):
        await update.message.reply_text(
            "❗ Please enter a valid customer email address (e.g., name@example.com):"
        )
        return CUSTOMER_EMAIL


    context.user_data['customer_email'] = email
    await update.message.reply_text("⏱️ How many hours worked? (Enter 0 if using itemized billing / Enter Total Hours if hourly billing)")
    return HOURS

async def get_hours(update: Update, context: CallbackContext) -> int:
    try:
        hours = float(update.message.text)
        if hours < 0:
            await update.message.reply_text("❗ Please enter a positive number or 0:")
            return HOURS
            
        context.user_data['hours'] = hours
        
        if hours >= 0:
            context.user_data['items'] = []
            await update.message.reply_text("🛒 Let's add items or service. What's the name of the first item/service?")
            return ITEM_NAME
            
    except ValueError:
        await update.message.reply_text("❗ Please enter a valid number:")
        return HOURS

async def get_item_name(update: Update, context: CallbackContext) -> int:
    context.user_data['current_item'] = {'name': update.message.text}
    await update.message.reply_text("🔢 How many units/hours?")
    return ITEM_QUANTITY

async def get_item_quantity(update: Update, context: CallbackContext) -> int:
    try:
        quantity = int(update.message.text)
        context.user_data['current_item']['quantity'] = quantity
    except ValueError:
        await update.message.reply_text("❗ Please enter a whole number:")
        return ITEM_QUANTITY
    
    await update.message.reply_text("💵 What's the price per unit?")
    return ITEM_PRICE

async def get_item_price(update: Update, context: CallbackContext) -> int:
    try:
        price = float(update.message.text)
        context.user_data['current_item']['price'] = price
    except ValueError:
        await update.message.reply_text("❗ Please enter a valid amount:")
        return ITEM_PRICE
    

    context.user_data['current_item']['total'] = (
        context.user_data['current_item']['quantity'] * 
        context.user_data['current_item']['price']
    )
    

    context.user_data['items'].append(context.user_data['current_item'])
    del context.user_data['current_item']
    
    keyboard = [[InlineKeyboardButton("Yes", callback_data="add_more_yes"),
                InlineKeyboardButton("No", callback_data="add_more_no")]]
    await update.message.reply_text(
        "🛒 Would you like to add another service/item to this invoice?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return MORE_ITEMS

async def handle_more_items(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    
    if query.data == "add_more_yes":
        await query.edit_message_text("Adding another item...")
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="🛒 What's the name of the next item/service?"
        )
        return ITEM_NAME
    else:
        await query.edit_message_text("Almost done here!")
        await context.bot.send_message(
            chat_id = query.message.chat_id,
            text = "What tax percentage should be applied? (Enter 0 if no tax)"
        )
        return TAX_PERCENT
    
async def get_tax_percent(update: Update, context: CallbackContext) -> int:
    try:
        tax_percent = float(update.message.text)
        if tax_percent < 0:
            await update.message.reply_text("❗ Please enter a positive number or 0:")
            return TAX_PERCENT
        
        context.user_data['tax_percent'] = tax_percent
        return await finalize_invoice(update, context)
    except ValueError:
        await update.message.reply_text("Please enter a valid tax percentage: ")
        return TAX_PERCENT

async def finalize_invoice(update: Update, context: CallbackContext) -> int:
    
    user_id = str(update.effective_user.id)
 

    if "business" not in context.user_data:
        # Create new Business object from individual fields
        business = Business(
            name=context.user_data['business_name'],
            email=context.user_data['business_email'],
            address=context.user_data['business_address'],
            currency=context.user_data['currency'],
            payment_processor=context.user_data['payment_processor'],
            payment_details=context.user_data['payment_details']
        )
    else:
        business = context.user_data["business"]
        print(business)
    
    if not business:
        await update.message.reply_text("Business information missing! Please start over.")
        return ConversationHandler.END
    

    

    tax_percent = context.user_data.get('tax_percent', 0)

    business_id = store_business(business)

    invoice = Invoice(
        business=business,
        invoice_number=context.user_data['invoice_number'],
        pay_by_date=context.user_data['pay_by_date'],
        customer_name=context.user_data['customer_name'],
        customer_address=context.user_data['customer_address'],
        customer_email=context.user_data['customer_email'],
        hours=context.user_data['hours'],
        tax_percent=tax_percent
    )

    # Add all items
    for item in context.user_data['items']:
        invoice.add_item(item['name'], item['price'], item['quantity'])

    invoice_id = store_invoice(invoice, business_id)

    update_user(user_id, business_id)
        

    print(invoice)
    print(type(invoice))
    
    hours_check = context.user_data['hours']
    if hours_check == 0:
        pdf_itemized = PDFInvoiceItimized(invoice)
        filename = f"invoice_{invoice.invoice_number}.pdf"
        pdf_itemized.generate_pdf(filename)
    else:
        pdf_hourlied = PDFInvoiceHourly(invoice)
        filename = f"invoice_{invoice.invoice_number}.pdf"
        pdf_hourlied.generate_pdf(filename)

    # Send to user
    with open(filename, "rb") as f:
        await context.bot.send_document(
            chat_id=update.effective_chat.id,
            document=f,
            filename=filename,
            caption=f"📄 Invoice #{invoice.invoice_number}"
        )



    # Send email
    send_inovice_email(
        user_email="invoiceme1488@gmail.com",
        customer_email=invoice.customer_email,
        business_email=invoice.business.email,
        pdf_filename=filename
    )
    
    # Clean up
    os.remove(filename)
    
    # Return to main menu
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="✅ Invoice created and sent!\nUse /start to create another invoice."
    )

    return ConversationHandler.END

(
    EDIT_BUSINESS_NAME, EDIT_BUSINESS_EMAIL, EDIT_BUSINESS_ADDRESS,
    EDIT_BUSINESS_CURRENCY, EDIT_BUSINESS_PAYMENT, TAX_PERCENT, PAYMENT_DETAILS, EDIT_BUSINESS_PAYMENT_DETAILS
 ) = range (21, 29)

async def edit_business_name(update: Update, context: CallbackContext) -> int:
    new_name = update.message.text.strip()
    business_id = context.user_data["edit_business_id"]
    
    # Add validation
    if not new_name or len(new_name) > 100:
        await update.message.reply_text("Invalid name! Please enter a name (1-100 chars):")
        return EDIT_BUSINESS_NAME
    
    # Update in Firestore
    FirestoreService.update_business_field(business_id, "name", new_name)
    
    await update.message.reply_text(
        f"✅ Business name updated to: {new_name}",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Back to Business", callback_data=f"biz_{business_id}")]
        ])
    )
    return BUSINESS_DETAILS

async def edit_business_email(update: Update, context: CallbackContext) -> int:
    new_email = update.message.text.strip()
    business_id = context.user_data["edit_business_id"]
    
    # Add email validation
    if "@" not in new_email:
        await update.message.reply_text("Invalid email! Please enter a valid email:")
        return EDIT_BUSINESS_EMAIL
    
    FirestoreService.update_business_field(business_id, "email", new_email)
    
    await update.message.reply_text(
        f"✅ Business email updated to: {new_email}",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Back to Business", callback_data=f"biz_{business_id}")]
        ])
    )
    return BUSINESS_DETAILS

async def edit_business_address(update: Update, context: CallbackContext) -> int:
    new_address = update.message.text.strip()
    business_id = context.user_data["edit_business_id"]

    if not new_address or len(new_address) > 200:
        await update.message.reply_text(
            "❗ Please enter a valid address (1-200 characters):"
        )
        return EDIT_BUSINESS_ADDRESS
    
    FirestoreService.update_business_field(business_id, "address", new_address)
    
    await update.message.reply_text(
        f"✅ Business address updated to: {new_address}",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Back to Business", callback_data=f"biz_{business_id}")]
        ])
    )
    return BUSINESS_DETAILS

async def edit_business_currency(update: Update, context: CallbackContext) -> int:
    new_currency = update.message.text.strip()
    business_id = context.user_data["edit_business_id"]

    if len(new_currency) != 3 or not new_currency.isalpha():
        await update.message.reply_text(
            "❗ Please enter a valid 3-letter currency code (e.g., USD, EUR):"
        )
        return EDIT_BUSINESS_CURRENCY

    FirestoreService.update_business_field(business_id, "currency", new_currency)

    await update.message.reply_text(
        f"✅ Business currency updated to: {new_currency}",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Back to Business", callback_data=f"biz_{business_id}")]
        ])
    )
    return BUSINESS_DETAILS

async def edit_business_payment_processor(update: Update, context: CallbackContext) -> int:
    new_processor = update.message.text.strip()
    business_id = context.user_data["edit_business_id"]

    if not new_processor or len(new_processor) > 50:
        await update.message.reply_text(
            "❗ Please enter a valid payment processor (1-50 characters):"
        )
        return EDIT_BUSINESS_PAYMENT
    
    FirestoreService.update_business_field(business_id, "payment_processor", new_processor)

    await update.message.reply_text(
        f"✅ Business payment processor updated to: {new_processor}",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Back to Business", callback_data=f"biz_{business_id}")]
        ])
    )
    return BUSINESS_DETAILS

async def edit_business_payment_details(update: Update, context: CallbackContext) -> int:
    new_details = update.message.text.strip()
    business_id = context.user_data["edit_business_id"]

    if not new_details or len(new_details) > 50:
        await update.message.reply_text(
            "❗ Please enter a valid payment processor (1-50 characters):"
        )
        return EDIT_BUSINESS_PAYMENT_DETAILS
    
    FirestoreService.update_business_field(business_id, "payment_details", new_details)

    await update.message.reply_text(
        f"✅ Business payment detauls updated to: {new_details}",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Back to Business", callback_data=f"biz_{business_id}")]
        ])
    )
    return BUSINESS_DETAILS



def setup_handlers(application: Application) -> None:
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MAIN_MENU: [CallbackQueryHandler(main_menu_handler)],
            BUSINESS_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_business_name)],
            BUSINESS_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_business_email)],
            BUSINESS_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_business_address)],
            CURRENCY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_currency)],
            PAYMENT_PROCESSOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_payment_processor)],
            PAYMENT_DETAILS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_payment_details)],
            INVOICE_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_invoice_number)],
            PAY_BY_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_pay_by_date)],
            CUSTOMER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_customer_name)],
            CUSTOMER_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_customer_address)],
            CUSTOMER_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_customer_email)],
            HOURS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_hours)],
            ITEM_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_item_name)],
            ITEM_QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_item_quantity)],
            ITEM_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_item_price)],
            MORE_ITEMS: [CallbackQueryHandler(handle_more_items)],
            BUSINESS_MENU: [
            CallbackQueryHandler(handle_business_selection, pattern="^biz_"),
            CallbackQueryHandler(handle_create_from_info, pattern="^create_new_business_from_info$"),
            CallbackQueryHandler(main_menu_handler, pattern="^back_to_menu$")
            ],
            BUSINESS_DETAILS: [
                CallbackQueryHandler(show_invoices_handler, pattern="^invoices_"),
                CallbackQueryHandler(edit_business_options, pattern="^edit_business_"),
                CallbackQueryHandler(business_info_handler, pattern="^business_info"),
                CallbackQueryHandler(handle_business_selection, pattern="^biz_")
            ],
                EDIT_BUSINESS: [
                CallbackQueryHandler(edit_business_handler)
            ],
            SELECT_BUSINESS_TYPE: [CallbackQueryHandler(select_business_type)], 
            SELECT_EXISTING_BUSINESS: [CallbackQueryHandler(handle_existing_business_selection, pattern="^select_biz_")],
            EDIT_BUSINESS_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_business_name)],
            EDIT_BUSINESS_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_business_email)],
            TAX_PERCENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_tax_percent)],
            EDIT_BUSINESS_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_business_address)],
            EDIT_BUSINESS_CURRENCY: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_business_currency)],
            EDIT_BUSINESS_PAYMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_business_payment_processor)],
            EDIT_BUSINESS_PAYMENT_DETAILS: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_business_payment_details)]

        },
        fallbacks=[CommandHandler("start", start)],
        allow_reentry=True
    )
    
    application.add_handler(conv_handler)