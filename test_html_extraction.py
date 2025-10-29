# test_html_parse.py
# Purpose: Try to extract bill text from parl.ca HTML

import requests
from bs4 import BeautifulSoup


def test_html_extraction():
    """
    Test if we can extract bill text from parl.ca HTML pages
    """
    
    # Use the Bill C-2 URL we found
    url = "https://www.parl.ca/DocumentViewer/en/11512864"
    
    print("=" * 80)
    print("TESTING HTML TEXT EXTRACTION")
    print("=" * 80 + "\n")
    
    print(f"Fetching: {url}\n")
    
    response = requests.get(url)
    
    if response.status_code != 200:
        print(f"❌ Failed to fetch (status {response.status_code})")
        return
    
    # Parse HTML with BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Try to find the bill text
    # Common patterns in parliamentary HTML:
    # - <div class="BillContent">
    # - <div id="DocumentContent">
    # - <article>
    
    print("Searching for bill text in HTML...\n")
    
    # Try different selectors
    selectors_to_try = [
        ('div', {'class': 'BillContent'}),
        ('div', {'id': 'DocumentContent'}),
        ('article', {}),
        ('div', {'class': 'document-viewer'}),
        ('main', {}),
    ]
    
    found_text = False
    
    for tag, attrs in selectors_to_try:
        element = soup.find(tag, attrs) if attrs else soup.find(tag)
        
        if element:
            text = element.get_text(strip=True)
            if len(text) > 200:  # Only count if substantial text
                print(f"✅ Found text in <{tag}> {attrs}")
                print(f"Text length: {len(text)} characters")
                print(f"\nFirst 500 characters:")
                print("-" * 80)
                print(text[:500])
                print("-" * 80)
                found_text = True
                break
    
    if not found_text:
        print("⚠️ Couldn't find bill text with common selectors")
        print("\nLet's see what's in the page:")
        print("-" * 80)
        # Get all text
        all_text = soup.get_text()
        print(f"Total page text length: {len(all_text)} characters")
        print("\nFirst 1000 characters of page:")
        print(all_text[:1000])
        print("-" * 80)
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    test_html_extraction()