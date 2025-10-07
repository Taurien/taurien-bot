# C7 Restaurant Form Automation
# Automatically fills and submits the C7 restaurant order form
#
# Form URL: https://docs.google.com/forms/d/e/1FAIpQLSfdFpl_ODddg00ERQu5-j0q3Mn7VCa8ScxOxJ-N-TPWL8kS-Q/viewform
#
# Usage:
#   # Run in headless mode (no visible browser) - DEFAULT
#   python fill_form.py 1 2              # Menu 1, quantity 2
#   python fill_form.py 2 1              # Menu 2, quantity 1
#
#   # Run with visible browser (for debugging)
#   python fill_form.py 1 2 --show-browser
#
#   # As module import
#   from fill_form import fill_c7_form
#   fill_c7_form(menu_choice=1, menu_quantity=2, headless=True)

from playwright.sync_api import sync_playwright
import time
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def fill_c7_form(menu_choice, menu_quantity=1, headless=True, form_url=None):
    """
    Fill the C7 restaurant form with predefined data

    Args:
        menu_choice (int): 1 for Menu 1, 2 for Menu 2
        menu_quantity (int): Quantity for the selected menu (default: 1)
        headless (bool): Run browser in headless mode (default: True)
        form_url (str): Custom form URL to use. If None, uses default URL.

    Returns:
        bool: True if form was submitted successfully, False otherwise
    """

    # Form URL - use provided URL or default
    if form_url is None:
        form_url = "https://docs.google.com/forms/d/e/1FAIpQLSfdFpl_ODddg00ERQu5-j0q3Mn7VCa8ScxOxJ-N-TPWL8kS-Q/viewform"

    # Get WhatsApp number from environment variable
    whatsapp_number = os.getenv("WHATSAPP_NUMBER")
    utensils_choice = "NO"  # Always NO as specified

    try:
        with sync_playwright() as p:
            # Launch browser in headless mode by default
            browser = p.chromium.launch(headless=headless)
            page = browser.new_page()

            # Navigate to form
            print(f"Navigating to form: {form_url}")
            page.goto(form_url)

            # Wait for form to load
            page.wait_for_selector('input[type="text"]', timeout=10000)

            # Fill WhatsApp number (required field)
            print(f"Filling WhatsApp number: {whatsapp_number}")
            # Wait for the first text input (WhatsApp field)
            whatsapp_input = page.locator('input[type="text"]').first
            whatsapp_input.fill(whatsapp_number)

            # Fill menu choice based on parameter
            if menu_choice == 1:
                print(f"Selecting Menu 1 with quantity: {menu_quantity}")
                # Second text input is Menu 1
                menu1_input = page.locator('input[type="text"]').nth(1)
                menu1_input.fill(str(menu_quantity))
            elif menu_choice == 2:
                print(f"Selecting Menu 2 with quantity: {menu_quantity}")
                # Third text input is Menu 2
                menu2_input = page.locator('input[type="text"]').nth(2)
                menu2_input.fill(str(menu_quantity))
            else:
                print("Invalid menu choice. Must be 1 or 2")
                return False

            # Select utensils option (always NO)
            print(f"Selecting utensils: {utensils_choice}")
            # Wait for radio buttons to load and find NO option
            page.wait_for_selector('div[role="radiogroup"]', timeout=10000)
            no_radio = page.locator('div[role="radiogroup"] div[role="radio"]').nth(
                1
            )  # Second radio button is NO
            no_radio.click()

            # Wait a moment for the selection to register
            time.sleep(1)

            # Submit the form
            print("Submitting form...")
            submit_button = (
                page.locator('div[role="button"]').filter(has_text="Enviar").first
            )
            submit_button.click()

            # Wait for confirmation or success page
            time.sleep(3)

            print("Form submitted successfully!")
            browser.close()
            return True

    except Exception as e:
        print(f"Error filling form: {str(e)}")
        try:
            if "browser" in locals():
                browser.close()
        except:
            pass
        return False


def test_form_with_menu1():
    """Test the form filling function with Menu 1"""
    print("Testing form filling with Menu 1...")
    success = fill_c7_form(menu_choice=1, menu_quantity=1)

    if success:
        print("Form filled and submitted successfully!")
    else:
        print("Failed to fill form")


def test_form_with_menu2():
    """Test the form filling function with Menu 2"""
    print("Testing form filling with Menu 2...")
    success = fill_c7_form(menu_choice=2, menu_quantity=2)

    if success:
        print("Form filled and submitted successfully!")
    else:
        print("Failed to fill form")


def main():
    """Main function to run tests"""
    import sys

    # Check for show-browser flag
    show_browser = "--show-browser" in sys.argv
    if show_browser:
        sys.argv.remove("--show-browser")

    headless_mode = (
        not show_browser
    )  # Headless by default, unless --show-browser is specified

    if len(sys.argv) > 1:
        menu_choice = int(sys.argv[1])
        quantity = int(sys.argv[2]) if len(sys.argv) > 2 else 1

        print(f"Filling form with Menu {menu_choice}, quantity: {quantity}")
        print(f"Running in {'visible browser' if show_browser else 'headless'} mode...")
        success = fill_c7_form(
            menu_choice=menu_choice, menu_quantity=quantity, headless=headless_mode
        )

        if success:
            print("Form filled and submitted successfully!")
        else:
            print("Failed to fill form")
    else:
        # Default test with Menu 1
        print(f"Running in {'visible browser' if show_browser else 'headless'} mode...")
        success = fill_c7_form(menu_choice=1, menu_quantity=1, headless=headless_mode)

        if success:
            print("Form filled and submitted successfully!")
        else:
            print("Failed to fill form")


if __name__ == "__main__":
    main()
