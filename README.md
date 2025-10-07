# TaurienBot 🤖

My personal automation assistant that helps streamline daily tasks. Currently handles complete lunch ordering workflow automation with smart scheduling, menu scraping, and automated form submission. Built with Python, `python-telegram-bot`, and `playwright`.

## 🎯 Purpose

**This is the first automation in a planned series of personal productivity enhancements.**

TaurienBot provides complete end-to-end lunch ordering automation for C7 restaurant:

- **Smart Scheduling**: 3 days/week normally, 5 days/week during third week of each month
- **Automated Workflow**: Linktree checking → Menu scraping → Form submission
- **Interactive Interface**: Menu selection with images and prices
- **Zero Manual Work**: From reminder to order completion

## ✨ Features

### 🤖 Core Automation

- **Smart daily reminders** at 7:30 AM Colombian time
- **Intelligent scheduling** based on weekly patterns
- **Automatic menu availability checking**
- **Real-time menu scraping** with images and prices
- **One-click form submission** with predefined preferences

### 🎮 Interactive Interface

- **Y/N reminder buttons** for quick responses
- **Visual menu selection** with images and pricing
- **Status commands** to check scheduling
- **Dev/Production modes** for testing and deployment

### 🔧 Technical Features

- **Web scraping** of Linktree and Google Forms
- **Browser automation** using Playwright
- **Async/await architecture** for responsive interactions
- **Environment-based configuration**
- **Comprehensive error handling and logging**

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.8+
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- Your Telegram Chat ID

### 2. Installation

```bash
# Clone and navigate to project
cd "C7 automation"

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

Create a `.env` file:

```bash
# Telegram Bot Configuration
BOT_TOKEN=your_bot_token_here
TARGET_CHAT_ID=your_chat_id_here
WHATSAPP_NUMBER=your_whatsapp_number_here

# Development Configuration
DEV_MODE=True
DEV_REMINDER_MINUTES=2
TIMEZONE=America/Bogota
```

### 4. Install Browser Dependencies

```bash
# Install Playwright browsers (required for form automation)
playwright install
playwright install chromium
```

### 5. Run the Bot

```bash
# Development mode (immediate reminders every 2 minutes)
python3 main.py

# Production mode (smart scheduling at 7:30 AM)
# Set DEV_MODE=False in .env first
python3 main.py
```

## 🎮 Usage

### Commands

- `/start` - Activate smart daily order reminders
- `/stop` - Deactivate all reminders
- `/status` - Check current schedule and next reminder date

### Complete Workflow

**When bot starts (DEV_MODE=True):**

1. Sends immediate test reminder every 2 minutes
2. Full workflow testing with real menu scraping

**Smart Production Schedule:**

- **Normal weeks**: Monday, Tuesday, Wednesday
- **Third week of month**: Monday through Friday
- **Daily time**: 7:30 AM Colombian timezone

**Full Automation Flow:**

1. **Daily Check** - Bot checks if today requires reminder
2. **Menu Availability** - Scrapes Linktree for "Almuerzos del día" link
3. **Menu Options** - Extracts MENÚ 1 & MENÚ 2 with images and prices
4. **User Selection** - Interactive buttons for menu choice
5. **Form Submission** - Automated filling with predefined preferences
6. **Next Scheduling** - Intelligent scheduling for next valid day

**Response Actions:**

- **Y (Yes)**:

  - Checks menu availability
  - Displays menu options with images
  - Awaits menu selection (MENÚ 1 or MENÚ 2)
  - Automatically submits form with choice
  - Schedules next reminder

- **N (No)**:

  - Acknowledges response
  - Schedules next reminder based on weekly pattern

- **Menu Selection**:
  - Submits Google Form with selected menu
  - Uses predefined WhatsApp number
  - Sets utensils preference to "NO"
  - Confirms successful submission

## 📁 Project Structure

```
C7 automation/
├── main.py                          # Main bot application & orchestration
├── requirements.txt                 # Python dependencies
├── DEPLOYMENT.md                   # Deployment guide for various platforms
├── README.md                       # This documentation
├── .env                           # Environment variables (not in git)
├── .venv/                         # Virtual environment (not in git)
└── c7_actions/                    # Core automation package
    ├── __init__.py                # Package initialization
    ├── daily_menu_available.py    # Linktree scraper & availability checker
    ├── scrap_menu_options.py      # Google Form menu scraper
    └── fill_form.py               # Playwright form automation
```

### Module Descriptions

- **`main.py`** - Telegram bot orchestration, scheduling logic, and user interactions
- **`daily_menu_available.py`** - Scrapes Linktree to find and validate menu availability
- **`scrap_menu_options.py`** - Extracts menu options, prices, and images from Google Forms
- **`fill_form.py`** - Automates form submission using Playwright browser automation

## � Technical Details

### Dependencies

- **`python-telegram-bot[job-queue]`** - Telegram bot framework with scheduling
- **`playwright`** - Browser automation for form filling
- **`requests` + `beautifulsoup4`** - Web scraping for menu data
- **`pytz`** - Timezone handling for Colombian time
- **`python-dotenv`** - Environment variable management

### Architecture

- **Async/Await Design** - Non-blocking operations for responsive interactions
- **Modular Structure** - Separate modules for each automation task
- **Error Handling** - Comprehensive exception handling with user feedback
- **Thread Pool Execution** - Runs synchronous browser automation in async context
- **Smart Scheduling** - Calendar-aware scheduling with third-week detection

### Environment Variables

```bash
BOT_TOKEN=              # Telegram bot token from @BotFather
TARGET_CHAT_ID=         # Your Telegram chat ID
WHATSAPP_NUMBER=        # WhatsApp number for form submission
DEV_MODE=True/False     # Development mode toggle
DEV_REMINDER_MINUTES=2  # Minutes between dev reminders
TIMEZONE=America/Bogota # Timezone for scheduling
```

## �📝 License

This project is for personal automation use.
