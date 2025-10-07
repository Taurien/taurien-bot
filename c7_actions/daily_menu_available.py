import requests
from bs4 import BeautifulSoup
import re
from typing import Optional, Dict


def check_daily_menu_available() -> Dict[str, any]:
    """
    Check if daily menu is available by scraping the Linktree page.

    Returns:
        Dict containing:
        - 'available': bool - whether the menu link was found
        - 'url': str - the Google Form URL if found
        - 'error': str - error message if any
    """
    try:
        # Target URL
        url = "https://linktr.ee/cocina.siete"

        # Headers to mimic a real browser request
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        # Make the request
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        # Parse the HTML
        soup = BeautifulSoup(response.content, "html.parser")

        # Search for the "Almuerzos del día" link
        menu_link = find_daily_menu_link(soup)

        if menu_link:
            # Check if the form is actually accepting requests
            form_status = check_form_availability(menu_link)

            if form_status["accepting_requests"]:
                return {"available": True, "url": menu_link, "error": None}
            else:
                return {
                    "available": False,
                    "url": menu_link,
                    "error": "No more almuerzos available - " + form_status["message"],
                }
        else:
            return {
                "available": False,
                "url": None,
                "error": "Daily menu link not found on the page",
            }

    except requests.RequestException as e:
        return {"available": False, "url": None, "error": f"Network error: {str(e)}"}
    except Exception as e:
        return {"available": False, "url": None, "error": f"Unexpected error: {str(e)}"}


def find_daily_menu_link(soup: BeautifulSoup) -> Optional[str]:
    """
    Find the "Almuerzos del día" link in the parsed HTML.

    Args:
        soup: BeautifulSoup object of the parsed HTML

    Returns:
        The Google Form URL if found, None otherwise
    """
    # Look for links containing "Almuerzos del día" text
    # Based on the HTML structure in your comments

    # Method 1: Look for the specific text in any link
    links = soup.find_all("a", href=True)
    for link in links:
        text = link.get_text(strip=True)
        if "almuerzos del día" in text.lower():
            href = link.get("href")
            if "docs.google.com/forms" in href:
                return href

    # Method 2: Look for the specific data-testid structure
    link_containers = soup.find_all("div", {"data-testid": "Link"})
    for container in link_containers:
        # Find the text content
        text_div = container.find(
            "div", text=re.compile(r"Almuerzos del día", re.IGNORECASE)
        )
        if text_div:
            # Find the associated link
            link = container.find("a", href=True)
            if link:
                href = link.get("href")
                if "docs.google.com/forms" in href:
                    return href

    # Method 3: More flexible search
    # Look for any element containing the target text
    elements = soup.find_all(text=re.compile(r"Almuerzos del día", re.IGNORECASE))
    for element in elements:
        # Find the nearest parent link
        parent = element.parent
        while parent:
            if parent.name == "a" and parent.get("href"):
                href = parent.get("href")
                if "docs.google.com/forms" in href:
                    return href
            parent = parent.parent

    return None


def check_form_availability(form_url: str) -> Dict[str, any]:
    """
    Check if the Google Form is actually accepting requests or if it's sold out.

    Args:
        form_url: The Google Form URL to check

    Returns:
        Dict containing:
        - 'accepting_requests': bool - whether the form is accepting new submissions
        - 'message': str - status message
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        response = requests.get(
            form_url, headers=headers, timeout=10, allow_redirects=True
        )
        response.raise_for_status()

        # Check if URL was redirected to closedform
        if "/closedform" in response.url:
            return {
                "accepting_requests": False,
                "message": "Form redirected to closedform (sold out)",
            }

        # Parse the form content to check for sold out messages
        soup = BeautifulSoup(response.content, "html.parser")

        # Look for common sold out indicators in Spanish
        sold_out_phrases = [
            # "agotado",
            "agotados",
            "se han agotado",
            "no hay",
            "sin disponibilidad",
            "sold out",
        ]

        page_text = soup.get_text().lower()

        for phrase in sold_out_phrases:
            if phrase in page_text:
                return {
                    "accepting_requests": False,
                    "message": f"Form shows sold out content: '{phrase}' found",
                }

        # If no sold out indicators found, assume it's accepting requests
        return {
            "accepting_requests": True,
            "message": "Form appears to be accepting requests",
        }

    except Exception as e:
        # If we can't check the form, assume it might still be available
        return {
            "accepting_requests": True,
            "message": f"Could not verify form status: {str(e)}",
        }


def main():
    """Main function to test the daily menu checker."""
    print("Checking if daily menu is available...")
    result = check_daily_menu_available()

    if result["available"]:
        print(f"Daily menu is available!")
        print(f"Form URL: {result['url']}")
    else:
        if "no more almuerzos" in str(result["error"]).lower():
            print(f"No more almuerzos available today!")
        else:
            print(f"Daily menu not available")

        if result["error"]:
            print(f"Details: {result['error']}")

        if result["url"]:
            print(f"Form URL: {result['url']}")


if __name__ == "__main__":
    main()
