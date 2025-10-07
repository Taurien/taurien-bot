import requests
from bs4 import BeautifulSoup
import re
from typing import Dict, List, Optional


def scrape_menu_options(form_url: str) -> Dict[str, any]:
    """
    Scrape the Google Form to extract MENÚ 1 and MENÚ 2 options with their image URLs.

    Args:
        form_url: The Google Form URL to scrape

    Returns:
        Dict containing:
        - 'success': bool - whether scraping was successful
        - 'menus': dict - containing menu_1 and menu_2 data
        - 'error': str - error message if any
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        response = requests.get(form_url, headers=headers, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")

        # Find MENÚ 1 and MENÚ 2 sections
        menu_data = {"menu_1": None, "menu_2": None}

        # Look for elements containing "MENÚ 1" and "MENÚ 2" text
        menu_1_elements = soup.find_all(string=re.compile(r"MENÚ\s*1", re.IGNORECASE))
        menu_2_elements = soup.find_all(string=re.compile(r"MENÚ\s*2", re.IGNORECASE))

        # Process MENÚ 1
        for text_elem in menu_1_elements:
            parent_element = text_elem.parent
            if parent_element:
                full_text = parent_element.get_text(strip=True)
                menu_info = extract_menu_info(parent_element, full_text, "MENÚ 1", soup)
                if menu_info:
                    menu_data["menu_1"] = menu_info
                    break

        # Process MENÚ 2
        for text_elem in menu_2_elements:
            parent_element = text_elem.parent
            if parent_element:
                full_text = parent_element.get_text(strip=True)
                menu_info = extract_menu_info(parent_element, full_text, "MENÚ 2", soup)
                if menu_info:
                    menu_data["menu_2"] = menu_info
                    break

        # Check if we found both menus
        if menu_data["menu_1"] and menu_data["menu_2"]:
            return {"success": True, "menus": menu_data, "error": None}
        else:
            missing = []
            if not menu_data["menu_1"]:
                missing.append("MENÚ 1")
            if not menu_data["menu_2"]:
                missing.append("MENÚ 2")

            return {
                "success": False,
                "menus": menu_data,
                "error": f"Could not find: {', '.join(missing)}",
            }

    except requests.RequestException as e:
        return {"success": False, "menus": None, "error": f"Network error: {str(e)}"}
    except Exception as e:
        return {"success": False, "menus": None, "error": f"Unexpected error: {str(e)}"}


def extract_menu_info(
    heading_element, heading_text: str, menu_name: str, soup: BeautifulSoup
) -> Optional[Dict[str, str]]:
    """
    Extract menu information including price and image URL from a heading element.

    Args:
        heading_element: BeautifulSoup element of the heading
        heading_text: Text content of the heading
        menu_name: Name of the menu (for identification)
        soup: BeautifulSoup object for broader searches

    Returns:
        Dict containing menu info or None if not found
    """
    try:
        # Extract price from heading text (looking for full price like $20.000)
        price_match = re.search(r"\$(\d+[,\.\d]*)", heading_text)
        price = price_match.group(1) if price_match else None

        # Find the image by looking for the container that has both the menu text and the image
        image_url = None

        # Strategy: Find all img tags and check if any parent contains our menu text
        all_imgs = soup.find_all("img")

        for img in all_imgs:
            # Get the img src
            img_src = get_image_src(img)
            if not img_src:
                continue

            # Check if this image is in a container that also contains our menu text
            # Look at various parent levels
            current_parent = img.parent
            for _ in range(5):  # Check up to 5 levels up
                if current_parent:
                    parent_text = current_parent.get_text()
                    if (
                        menu_name.replace("Ú", "U") in parent_text
                        or menu_name in parent_text
                    ):
                        # Found the image in the same container as the menu text
                        image_url = img_src
                        break
                    current_parent = current_parent.parent
                else:
                    break

            if image_url:
                break

        # Alternative strategy: Look specifically for images in list items
        if not image_url:
            listitem = heading_element.find_parent(["li", "div"])
            if listitem:
                img_tag = listitem.find("img")
                if img_tag:
                    image_url = get_image_src(img_tag)

        return {
            "name": menu_name,
            "full_text": heading_text,
            "price": price,
            "image_url": image_url,
        }

    except Exception as e:
        print(f"Error extracting info for {menu_name}: {str(e)}")
        return None


def get_image_src(img_tag) -> Optional[str]:
    """
    Extract the image source URL from an img tag, handling various attributes.

    Args:
        img_tag: BeautifulSoup img element

    Returns:
        Image URL string or None
    """
    # Try different common image source attributes
    for attr in ["src", "data-src", "data-lazy-src"]:
        if img_tag.get(attr):
            return img_tag.get(attr)
    return None
