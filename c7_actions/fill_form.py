# C7 Restaurant Form Automation
# Automatically fills and submits the C7 restaurant order form
#
# Form URL: https://docs.google.com/forms/d/e/1FAIpQLSfdFpl_ODddg00ERQu5-j0q3Mn7VCa8ScxOxJ-N-TPWL8kS-Q/viewform
#
# Form Fields (as of Oct 14, 2025):
#   1. WhatsApp number (text input - required)
#   2. MENÚ 1 $20.000 (dropdown listbox - options: Elegir, 1, 2, 10)
#   3. MENÚ 2 $20.000 (dropdown listbox - options: Elegir, 1, 2, 10)
#   4. CUBIERTOS $1.000 (radio buttons - SI/NO - required)
#
# Usage:
#   # Run in headless mode (no visible browser) - DEFAULT
#   python fill_form.py 1 1              # Menu 1, quantity 1
#   python fill_form.py 2 2              # Menu 2, quantity 2
#
#   # Run with visible browser (for debugging)
#   python fill_form.py 1 2 --show-browser
#
#   # As module import
#   from fill_form import fill_c7_form
#   fill_c7_form(menu_choice=1, menu_quantity=1, headless=True)

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
            # Always set user-agent and slow_mo, use user-provided headless argument
            browser = p.chromium.launch(headless=headless, slow_mo=100)
            user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            page = browser.new_page(user_agent=user_agent)

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
            # Note: Menu fields are now dropdown/listbox elements instead of text inputs
            def click_menu_option(dropdown_locator, menu_quantity, menu_label):
                dropdown_locator.click()
                time.sleep(1)
                options = page.locator('div[role="option"]')
                found = False
                visible_options = []
                for i in range(options.count()):
                    option = options.nth(i)
                    if option.is_visible():
                        text = option.inner_text().strip()
                        visible_options.append(text)
                        if text == str(menu_quantity):
                            option.click()
                            found = True
                            break
                if not found:
                    print(
                        f"{menu_label} quantity option '{menu_quantity}' not found. Visible options: {visible_options}"
                    )
                    return False
                return True

            if menu_choice == 1:
                print(f"Selecting Menu 1 with quantity: {menu_quantity}")
                page.wait_for_selector('div[role="listbox"]', timeout=10000)
                menu1_dropdown = page.locator('div[role="listbox"]').first
                if not click_menu_option(menu1_dropdown, menu_quantity, "Menu 1"):
                    return False
            elif menu_choice == 2:
                print(f"Selecting Menu 2 with quantity: {menu_quantity}")
                page.wait_for_selector('div[role="listbox"]', timeout=10000)
                menu2_dropdown = page.locator('div[role="listbox"]').nth(1)
                if not click_menu_option(menu2_dropdown, menu_quantity, "Menu 2"):
                    return False
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
