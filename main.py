from datetime import time, datetime, timedelta
import pytz
from telegram.ext import ContextTypes, Application, CommandHandler, CallbackQueryHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
import logging
import os
from dotenv import load_dotenv
import sys
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Import from the c7 actions package
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from c7_actions.daily_menu_available import check_daily_menu_available
from c7_actions.scrap_menu_options import scrape_menu_options
from c7_actions.fill_form import fill_c7_form

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load configuration from environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
TARGET_CHAT_ID = os.getenv("TARGET_CHAT_ID")
Y_CALLBACK_DATA = "ORDER_Y"
N_CALLBACK_DATA = "ORDER_N"
MENU_1_CALLBACK_DATA = "MENU_1"
MENU_2_CALLBACK_DATA = "MENU_2"
TIMEZONE = os.getenv("TIMEZONE", "America/Bogota")  # Default fallback
DAILY_TIME = time(hour=7, minute=45, tzinfo=pytz.timezone(TIMEZONE))

# Development Mode Configuration from environment
DEV_MODE = os.getenv("DEV_MODE", "True").lower() == "true"  # Convert string to boolean
DEV_REMINDER_MINUTES = int(os.getenv("DEV_REMINDER_MINUTES", "2"))  # Convert to int

# Validate required environment variables
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required")
if not TARGET_CHAT_ID:
    raise ValueError("TARGET_CHAT_ID environment variable is required")

# Global application instance
application = None


def should_send_reminder_today(target_date=None):
    """
    Determine if a reminder should be sent based on the weekly schedule:
    - 3 days per week (Monday, Tuesday, Wednesday) normally
    - 5 days per week (Monday through Friday) during the third week of each month

    Args:
        target_date: datetime object to check (defaults to today in Colombian timezone)

    Returns:
        bool: True if reminder should be sent, False otherwise
    """
    if target_date is None:
        colombia_tz = pytz.timezone(TIMEZONE)
        target_date = datetime.now(colombia_tz)

    # Get the day of the week (0=Monday, 1=Tuesday, ..., 6=Sunday)
    weekday = target_date.weekday()

    # Calculate which week of the month this is
    # Get the first day of the month
    first_day = target_date.replace(day=1)
    # Calculate how many days into the month we are
    days_into_month = target_date.day
    # Calculate which week (1-based) - account for partial first week
    week_of_month = ((days_into_month - 1 + first_day.weekday()) // 7) + 1

    # Check if it's the third week of the month
    is_third_week = week_of_month == 3

    if is_third_week:
        # Third week: Monday through Friday (weekdays 0-4)
        return weekday <= 4  # Monday(0) to Friday(4)
    else:
        # Normal weeks: Monday, Tuesday, Wednesday (weekdays 0-2)
        return weekday <= 2  # Monday(0) to Wednesday(2)


def get_next_reminder_date(current_date=None):
    """
    Calculate the next date when a reminder should be sent.

    Args:
        current_date: datetime object to start from (defaults to now in Colombian timezone)

    Returns:
        datetime: Next date when reminder should be sent
    """
    if current_date is None:
        colombia_tz = pytz.timezone(TIMEZONE)
        current_date = datetime.now(colombia_tz)

    # Start checking from tomorrow
    check_date = current_date + timedelta(days=1)

    # Look ahead up to 7 days to find the next valid reminder day
    for _ in range(7):
        if should_send_reminder_today(check_date):
            return check_date.replace(hour=7, minute=30, second=0, microsecond=0)
        check_date += timedelta(days=1)

    # Fallback - should never happen, but return next Monday just in case
    days_ahead = (0 - check_date.weekday()) % 7  # Monday is 0
    if days_ahead == 0:
        days_ahead = 7
    return (check_date + timedelta(days=days_ahead)).replace(
        hour=7, minute=30, second=0, microsecond=0
    )


def get_next_reminder_message():
    """Generate a message about when the next reminder will be sent."""
    if DEV_MODE:
        return f"DEV MODE: I'll ask you again in {DEV_REMINDER_MINUTES} minutes."
    else:
        next_date = get_next_reminder_date()
        return f"I'll ask you again on {next_date.strftime('%A, %B %d at %I:%M %p')}."


async def daily_order_reminder(context: ContextTypes.DEFAULT_TYPE):
    """Send the daily order reminder message at 7 AM Colombian time."""
    try:
        # Check if today should have a reminder based on the schedule
        if not should_send_reminder_today():
            logger.info("Skipping reminder - not scheduled for today")
            return

        # Define the two inline buttons
        keyboard = [
            [
                InlineKeyboardButton("Y", callback_data=Y_CALLBACK_DATA),
                InlineKeyboardButton("N", callback_data=N_CALLBACK_DATA),
            ]
        ]
        # Create the inline keyboard markup
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Send the daily reminder message
        await context.bot.send_message(
            chat_id=TARGET_CHAT_ID,
            text="Do you want to order today?",
            reply_markup=reply_markup,
        )
        logger.info(f"Daily reminder sent to chat ID: {TARGET_CHAT_ID}")

    except Exception as e:
        logger.error(f"Error sending daily reminder: {e}")


# async def send_oki_message(context: ContextTypes.DEFAULT_TYPE):
#     """Send the 'OKi' confirmation message."""
#     try:
#         await context.bot.send_message(chat_id=TARGET_CHAT_ID, text="OKi")
#         logger.info("OKi message sent successfully")
#     except Exception as e:
#         logger.error(f"Error sending OKi message: {e}")


async def send_menu_options(
    context: ContextTypes.DEFAULT_TYPE, chat_id: str, menus: dict
):
    """Send the menu options with images and selection buttons."""
    try:
        await context.bot.send_message(
            chat_id=chat_id, text="Here are today's menu options:"
        )

        # Send Menu 1
        menu1 = menus.get("menu_1")
        if menu1:
            caption1 = f"MENÚ 1 - ${menu1.get('price', 'N/A')}"
            if menu1.get("image_url"):
                await context.bot.send_photo(
                    chat_id=chat_id, photo=menu1["image_url"], caption=caption1
                )
            else:
                await context.bot.send_message(
                    chat_id=chat_id, text=f"{caption1}\n(Image not available)"
                )

        # Send Menu 2
        menu2 = menus.get("menu_2")
        if menu2:
            caption2 = f"MENÚ 2 - ${menu2.get('price', 'N/A')}"
            if menu2.get("image_url"):
                await context.bot.send_photo(
                    chat_id=chat_id, photo=menu2["image_url"], caption=caption2
                )
            else:
                await context.bot.send_message(
                    chat_id=chat_id, text=f"{caption2}\n(Image not available)"
                )

        # Send selection buttons
        keyboard = [
            [
                InlineKeyboardButton("MENÚ 1", callback_data=MENU_1_CALLBACK_DATA),
                InlineKeyboardButton("MENÚ 2", callback_data=MENU_2_CALLBACK_DATA),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await context.bot.send_message(
            chat_id=chat_id,
            text="Which menu would you like to order?",
            reply_markup=reply_markup,
        )

        logger.info(f"Menu options sent to chat ID: {chat_id}")

    except Exception as e:
        logger.error(f"Error sending menu options: {e}")
        await context.bot.send_message(
            chat_id=chat_id,
            text="Sorry, there was an error displaying the menu options.",
        )


def schedule_next_reminder(context: ContextTypes.DEFAULT_TYPE, chat_id: str):
    """Schedule the next reminder based on the weekly schedule (or in X minutes for dev mode)."""
    # Cancel any existing daily reminder jobs to avoid duplicates
    current_jobs = context.job_queue.get_jobs_by_name(f"daily_order_reminder_{chat_id}")
    for job in current_jobs:
        job.schedule_removal()

    if DEV_MODE:
        # DEV MODE: Schedule reminder in X minutes
        context.job_queue.run_once(
            daily_order_reminder,
            DEV_REMINDER_MINUTES * 60,  # Convert minutes to seconds
            chat_id=chat_id,
            name=f"daily_order_reminder_{chat_id}",
        )
        logger.info(
            f"DEV MODE: Next reminder scheduled in {DEV_REMINDER_MINUTES} minutes"
        )
    else:
        # PRODUCTION MODE: Schedule daily reminders (will check schedule internally)
        # Use run_daily to check every day, but the reminder function will decide if it should send
        context.job_queue.run_daily(
            daily_order_reminder,
            DAILY_TIME,
            chat_id=chat_id,
            name=f"daily_order_reminder_{chat_id}",
        )

        # Calculate and log the next actual reminder date
        next_reminder_date = get_next_reminder_date()
        colombia_tz = pytz.timezone(TIMEZONE)
        current_date = datetime.now(colombia_tz)

        # Check if it's a third week
        days_into_month = current_date.day
        first_day = current_date.replace(day=1)
        week_of_month = ((days_into_month - 1 + first_day.weekday()) // 7) + 1
        is_third_week = week_of_month == 3

        schedule_info = (
            "5 days/week (Mon-Fri)" if is_third_week else "3 days/week (Mon-Wed)"
        )

        logger.info(
            f"PRODUCTION MODE: Daily job scheduled at 7:30 AM Colombian time "
            f"({schedule_info}). Next reminder: {next_reminder_date.strftime('%A, %B %d at %I:%M %p')}"
        )


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the button click logic (Y or N)."""
    query = update.callback_query
    await query.answer()  # Acknowledge the button press

    chat_id = str(query.message.chat_id)
    data = query.data

    # Remove the buttons from the original message
    await query.edit_message_reply_markup(reply_markup=None)

    if data == Y_CALLBACK_DATA:
        # User wants to order - scrape menu and show options
        await context.bot.send_message(
            chat_id=chat_id, text="Great! Let me check today's menu options..."
        )

        # Check if daily menu is available
        availability_result = check_daily_menu_available()

        if not availability_result["available"]:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"Sorry, daily menu is not available today.\n"
                f"Reason: {availability_result.get('error', 'Unknown error')}",
            )
            # Schedule next reminder
            await context.bot.send_message(
                chat_id=chat_id,
                text=get_next_reminder_message(),
            )
            schedule_next_reminder(context, chat_id)
            return

        # Scrape menu options
        scrape_result = scrape_menu_options(availability_result["url"])

        if not scrape_result["success"]:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"Sorry, couldn't load the menu options.\n"
                f"Error: {scrape_result.get('error', 'Unknown error')}",
            )
            schedule_next_reminder(context, chat_id)
            return

        # Send menu options with images
        await send_menu_options(context, chat_id, scrape_result["menus"])

        # Store the scraped URL in context for later use in form submission
        context.user_data["form_url"] = (
            availability_result["url"] if not DEV_MODE else None
        )

    elif data == N_CALLBACK_DATA:
        # User doesn't want to order - schedule based on mode
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"No problem! {get_next_reminder_message()}",
        )
        schedule_next_reminder(context, chat_id)

    elif data == MENU_1_CALLBACK_DATA:
        # User selected Menu 1
        await context.bot.send_message(
            chat_id=chat_id,
            text="Perfect! You've chosen MENÚ 1. Submitting your order...",
        )

        # Fill and submit the form for Menu 1 using thread executor
        try:
            # Get the appropriate form URL based on DEV_MODE
            form_url = context.user_data.get("form_url") if not DEV_MODE else None

            # Run the synchronous form filling function in a thread
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as executor:
                success = await loop.run_in_executor(
                    executor,
                    lambda: fill_c7_form(
                        menu_choice=1, menu_quantity=1, headless=True, form_url=form_url
                    ),
                )

            if success:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="Your order has been submitted successfully!",
                )
                logger.info("Menu 1 order submitted successfully")
            else:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="Sorry, there was an error submitting your order. Please try ordering manually.",
                )
                logger.error("Form submission returned False for Menu 1")
        except Exception as e:
            logger.error(f"Error filling form for Menu 1: {e}")
            await context.bot.send_message(
                chat_id=chat_id,
                text="Sorry, there was an error submitting your order. Please try ordering manually.",
            )

        # Schedule next reminder
        await context.bot.send_message(
            chat_id=chat_id,
            text=get_next_reminder_message(),
        )
        schedule_next_reminder(context, chat_id)

    elif data == MENU_2_CALLBACK_DATA:
        # User selected Menu 2
        await context.bot.send_message(
            chat_id=chat_id,
            text="Perfect! You've chosen MENÚ 2. Submitting your order...",
        )

        # Fill and submit the form for Menu 2 using thread executor
        try:
            # Get the appropriate form URL based on DEV_MODE
            form_url = context.user_data.get("form_url") if not DEV_MODE else None

            # Run the synchronous form filling function in a thread
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as executor:
                success = await loop.run_in_executor(
                    executor,
                    lambda: fill_c7_form(
                        menu_choice=2, menu_quantity=1, headless=True, form_url=form_url
                    ),
                )

            if success:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="Your order has been submitted successfully!",
                )
                logger.info("Menu 2 order submitted successfully")
            else:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="Sorry, there was an error submitting your order. Please try ordering manually.",
                )
                logger.error("Form submission returned False for Menu 2")
        except Exception as e:
            logger.error(f"Error filling form for Menu 2: {e}")
            await context.bot.send_message(
                chat_id=chat_id,
                text="Sorry, there was an error submitting your order. Please try ordering manually.",
            )

        # Schedule next reminder
        await context.bot.send_message(
            chat_id=chat_id,
            text=get_next_reminder_message(),
        )
        schedule_next_reminder(context, chat_id)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Initialize the daily order reminder system."""
    chat_id = str(update.effective_chat.id)

    # Cancel any existing jobs for this chat
    current_jobs = context.job_queue.get_jobs_by_name(f"daily_order_reminder_{chat_id}")
    for job in current_jobs:
        job.schedule_removal()

    # Schedule the daily reminder based on mode
    if not DEV_MODE:
        context.job_queue.run_daily(
            daily_order_reminder,
            DAILY_TIME,
            chat_id=chat_id,
            name=f"daily_order_reminder_{chat_id}",
        )

    # Send immediate confirmation and today's reminder
    if DEV_MODE:
        await update.message.reply_text(
            f"DEV MODE: Order reminder (executes immediately)\n"
            f"Reminders every {DEV_REMINDER_MINUTES} minutes for testing.\n\n"
            "Here's your order question:"
        )
    else:
        # Get current week info for user message
        colombia_tz = pytz.timezone(TIMEZONE)
        current_date = datetime.now(colombia_tz)
        days_into_month = current_date.day
        first_day = current_date.replace(day=1)
        week_of_month = ((days_into_month - 1 + first_day.weekday()) // 7) + 1
        is_third_week = week_of_month == 3

        schedule_text = (
            "5 days per week (Monday-Friday)"
            if is_third_week
            else "3 days per week (Monday-Wednesday)"
        )

        next_reminder_date = get_next_reminder_date()

        await update.message.reply_text(
            f"Daily order reminder activated!\n\n"
            f"Schedule:\n"
            f"• Normal weeks: 3 days (Mon-Wed)\n"
            f"• Third week of month: 5 days (Mon-Fri)\n\n"
            f"Current: {schedule_text}\n"
            f"Next reminder: {next_reminder_date.strftime('%A, %B %d at %I:%M %p')}\n\n"
            "Let me check if I should ask you today:"
        )

    # Send today's reminder immediately
    await daily_order_reminder(context)


# def main():
#     """Start the bot, register handlers, and set up the job queue."""

#     application = Application.builder().token(BOT_TOKEN).build()

#     # 1. Register a dedicated handler for the /start command
#     # Assuming you have a function called 'start_command' to handle user input
#     application.add_handler(CommandHandler("start", start_command))

#     # 2. Get the JobQueue (will work after the installation fix)
#     job_queue = application.job_queue

#     # 3. Schedule the 'start_command' function to run once after 60 seconds
#     #    It's okay to call start_command here, but ideally you'd have a separate job function.
#     job_queue.run_once(start_command, 60)

#     print("Bot is starting polling and scheduled 'start_command' to run in 60 seconds.")
#     application.run_polling(poll_interval=3)


# if __name__ == "__main__":
#     main()
#     pass  # Uncomment the lines above to run the bot


async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Stop the daily order reminders."""
    chat_id = str(update.effective_chat.id)

    # Cancel all existing jobs for this chat
    current_jobs = context.job_queue.get_jobs_by_name(f"daily_order_reminder_{chat_id}")
    removed_count = 0
    for job in current_jobs:
        job.schedule_removal()
        removed_count += 1

    if removed_count > 0:
        await update.message.reply_text(
            "Daily order reminders have been stopped.\n"
            "Use /start to activate them again."
        )
    else:
        await update.message.reply_text(
            "No active daily reminders found.\n"
            "Use /start to activate daily reminders."
        )


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check the status of daily reminders."""
    chat_id = str(update.effective_chat.id)

    current_jobs = context.job_queue.get_jobs_by_name(f"daily_order_reminder_{chat_id}")

    if current_jobs:
        colombia_tz = pytz.timezone(TIMEZONE)
        current_date = datetime.now(colombia_tz)

        # Get current week info
        days_into_month = current_date.day
        first_day = current_date.replace(day=1)
        week_of_month = ((days_into_month - 1 + first_day.weekday()) // 7) + 1
        is_third_week = week_of_month == 3

        current_schedule = (
            "5 days/week (Mon-Fri)" if is_third_week else "3 days/week (Mon-Wed)"
        )

        # Get next reminder date
        next_reminder_date = get_next_reminder_date()

        # Check if today should have a reminder
        today_has_reminder = should_send_reminder_today()
        today_text = "Yes" if today_has_reminder else "No"

        await update.message.reply_text(
            f"Daily order reminders are ACTIVE\n\n"
            f"Current Schedule: {current_schedule}\n"
            f"Reminder today ({current_date.strftime('%A')}): {today_text}\n"
            f"Next reminder: {next_reminder_date.strftime('%A, %B %d at %I:%M %p')}\n\n"
            f"Weekly Schedule:\n"
            f"• Normal weeks: Mon, Tue, Wed\n"
            f"• Third week: Mon, Tue, Wed, Thu, Fri\n\n"
            f"Use /stop to deactivate reminders."
        )
    else:
        await update.message.reply_text(
            "Daily order reminders are INACTIVE\n\n"
            "Use /start to activate daily reminders."
        )


async def dev_mode_immediate_reminder(context: ContextTypes.DEFAULT_TYPE):
    """DEV MODE: Send immediate order reminder when bot starts."""

    # Send immediate reminder for development
    try:
        await context.bot.send_message(
            chat_id=TARGET_CHAT_ID,
            text="DEV MODE: Bot started! Sending immediate order reminder...",
        )

        # Define the two inline buttons
        keyboard = [
            [
                InlineKeyboardButton("Y", callback_data=Y_CALLBACK_DATA),
                InlineKeyboardButton("N", callback_data=N_CALLBACK_DATA),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await context.bot.send_message(
            chat_id=TARGET_CHAT_ID,
            text="Do you want to order today?",
            reply_markup=reply_markup,
        )
        logger.info("DEV MODE: Immediate reminder sent")

    except Exception as e:
        logger.error(f"DEV MODE: Error sending immediate reminder: {e}")


def main():
    """Start the bot, register handlers, and set up the job queue."""
    global application

    mode_text = "DEV MODE" if DEV_MODE else "PRODUCTION MODE"
    logger.info(f"Starting Daily Order Reminder Bot... ({mode_text})")

    # Build the application with better timeout settings
    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .get_updates_read_timeout(10)
        .get_updates_write_timeout(10)
        .get_updates_connect_timeout(10)
        .build()
    )

    # Register command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("stop", stop_command))
    application.add_handler(CommandHandler("status", status_command))

    # Register callback query handler for button presses
    application.add_handler(CallbackQueryHandler(button_callback))

    logger.info("Bot is ready! Available commands:")
    if DEV_MODE:
        logger.info(
            f"/start - Activate order reminders (DEV: immediate + every {DEV_REMINDER_MINUTES} min)"
        )
    else:
        logger.info(
            "/start - Activate smart scheduling (3 days/week, 5 days during 3rd week)"
        )
    logger.info("/stop - Deactivate order reminders")
    logger.info("/status - Check current schedule and next reminder")

    # Schedule immediate reminder if in dev mode
    if DEV_MODE:
        application.job_queue.run_once(dev_mode_immediate_reminder, 3)
    else:
        # Production mode: Schedule daily reminder automatically on startup
        logger.info(
            f"PRODUCTION MODE: Scheduling daily reminder at {DAILY_TIME.strftime('%I:%M %p')}"
        )
        application.job_queue.run_daily(
            daily_order_reminder,
            DAILY_TIME,
            chat_id=TARGET_CHAT_ID,
            name=f"daily_order_reminder_{TARGET_CHAT_ID}",
        )

    # Use polling for both dev and production modes (local deployment)
    logger.info(f"{mode_text}: Using polling")
    try:
        logger.info("Starting polling...")
        # Start polling with improved settings
        application.run_polling(poll_interval=3, drop_pending_updates=True)
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        raise


if __name__ == "__main__":
    main()
