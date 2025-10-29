# fetch_bills.py
# Purpose: Fetch bills from OpenParliament API and scrape text from parl.ca
# This module handles all the data fetching - other modules will process the data

import requests
from bs4 import BeautifulSoup
import time
from typing import List, Dict, Optional


def fetch_bills_list(session: str = "44-1", limit: int = 5) -> List[Dict]:
    """
    Fetch a list of bills from OpenParliament API
    
    Args:
        session: Parliamentary session (e.g., "44-1" for 44th Parliament, 1st session)
        limit: Number of bills to fetch (default 5 for testing)
    
    Returns:
        List of bill dictionaries with basic metadata
    """
    
    # Base URL for OpenParliament API
    base_url = "https://api.openparliament.ca"
    
    # Construct the URL with session filter and format=json
    # The limit parameter controls how many bills we get per page
    url = f"{base_url}/bills/?format=json&session={session}&limit={limit}"
    
    # Print what we're doing (helpful for debugging)
    print(f"📥 Fetching up to {limit} bills from session {session}...")
    print(f"   URL: {url}")
    
    try:
        # Make the HTTP GET request
        response = requests.get(url)
        
        # Check if request was successful (status 200 = OK)
        if response.status_code != 200:
            print(f"❌ Error: API returned status {response.status_code}")
            return []
        
        # Parse JSON response
        data = response.json()
        
        # Extract the bills array from the response
        bills = data.get('objects', [])
        
        # Print how many we got
        print(f"✅ Retrieved {len(bills)} bills\n")
        
        # Return the list of bills
        return bills
        
    except Exception as e:
        # Catch any errors (network issues, JSON parsing, etc.)
        print(f"❌ Error fetching bills: {str(e)}")
        return []


def fetch_bill_details(bill_url: str) -> Optional[Dict]:
    """
    Fetch detailed information for a specific bill
    
    Args:
        bill_url: Relative URL from OpenParliament (e.g., "/bills/44-1/C-2/")
    
    Returns:
        Dictionary with detailed bill info, or None if failed
    """
    
    # Base URL for OpenParliament API
    base_url = "https://api.openparliament.ca"
    
    # Construct full URL with format=json
    full_url = base_url + bill_url + "?format=json"
    
    try:
        # Make the HTTP GET request
        response = requests.get(full_url)
        
        # Check if successful
        if response.status_code != 200:
            print(f"   ⚠️  Failed to fetch details (status {response.status_code})")
            return None
        
        # Parse and return JSON
        return response.json()
        
    except Exception as e:
        # Handle any errors
        print(f"   ⚠️  Error fetching details: {str(e)}")
        return None


def scrape_bill_text(text_url: str) -> Optional[str]:
    """
    Scrape the full bill text from parl.ca HTML page
    
    Args:
        text_url: URL to the bill text on parl.ca (from text_url field)
    
    Returns:
        Cleaned bill text as a string, or None if failed
    """
    
    try:
        # Make HTTP request to the parl.ca page
        response = requests.get(text_url)
        
        # Check if successful
        if response.status_code != 200:
            print(f"   ⚠️  Failed to fetch text (status {response.status_code})")
            return None
        
        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the main content area (where bill text lives)
        main_element = soup.find('main')
        
        # If we found the main element, extract text
        if main_element:
            # Get text from the element
            # separator=' ' adds spaces between elements
            # strip=True removes leading/trailing whitespace
            text = main_element.get_text(separator=' ', strip=True)
            
            # Basic cleaning: remove multiple spaces
            # Split by whitespace and rejoin with single spaces
            text = ' '.join(text.split())
            
            # Return the cleaned text
            return text
        else:
            # Couldn't find main element
            print(f"   ⚠️  Couldn't find main element in HTML")
            return None
            
    except Exception as e:
        # Handle any errors (network, parsing, etc.)
        print(f"   ⚠️  Error scraping text: {str(e)}")
        return None


def fetch_complete_bill_data(bill: Dict) -> Optional[Dict]:
    """
    Fetch complete data for a single bill (metadata + full text)
    
    Args:
        bill: Basic bill dict from the bills list
    
    Returns:
        Complete bill data dict, or None if critical data missing
    """
    
    # Extract bill number for logging
    bill_number = bill.get('number', 'UNKNOWN')
    
    # Print what we're processing
    print(f"📄 Processing Bill {bill_number}...", end=" ")
    
    # Step 1: Get detailed bill info
    bill_url = bill.get('url')
    if not bill_url:
        print("❌ No URL")
        return None
    
    # Fetch the detailed bill data
    bill_details = fetch_bill_details(bill_url)
    if not bill_details:
        print("❌ Failed to get details")
        return None
    
    # Step 2: Check if bill has text available
    text_url = bill_details.get('text_url')
    
    # Initialize full_text as empty
    full_text = ""
    
    # If text_url exists, try to scrape it
    if text_url:
        print(f"📥 Scraping text...")
        full_text = scrape_bill_text(text_url)
        
        # If scraping failed, we'll use title/short_title as fallback
        if not full_text:
            print("⚠️  Text scraping failed, using fallback")
    else:
        print("⚠️  No text_url available")
    
    # Step 3: Create fallback text if we don't have full text
    # This ensures we always have SOMETHING to embed and search
    if not full_text or len(full_text) < 100:
        # Use title and short_title as the "text"
        title = bill_details.get('name', {}).get('en', 'Untitled')
        short_title = bill_details.get('short_title', {})
        
        # Build a basic description
        fallback_text = f"{title}. "
        
        # Add short title if available
        if isinstance(short_title, dict):
            short_title_en = short_title.get('en', '')
            if short_title_en:
                fallback_text += f"Short title: {short_title_en}. "
        
        # Add any other available info
        status = bill_details.get('status', {})
        if isinstance(status, dict):
            status_en = status.get('en', '')
            if status_en:
                fallback_text += f"Status: {status_en}."
        
        full_text = fallback_text
        print("ℹ️  Using title as text")
    
    # Step 4: Build the complete bill data dictionary
    complete_data = {
        'bill_number': bill_number,
        'title': bill_details.get('name', {}).get('en', 'Untitled'),
        'short_title': bill_details.get('short_title', {}).get('en', ''),
        'summary': '',  # OpenParliament doesn't provide summaries
        'full_text': full_text,
        'status': bill_details.get('status', {}).get('en', 'Unknown'),
        'session': bill_details.get('session', ''),
        'introduced_date': bill_details.get('introduced'),
        'url': f"https://www.parl.ca/legisinfo/en/bill/{bill_details.get('session', '')}/{bill_number}",
        'text_url': text_url or '',
        'legisinfo_id': bill_details.get('legisinfo_id')
    }
    
    # Print success with text length
    print(f"✅ ({len(full_text)} chars)")
    
    # Return the complete data
    return complete_data


def fetch_bills(session: str = "44-1", max_bills: int = 5) -> List[Dict]:
    """
    Main function: Fetch multiple bills with complete data
    
    Args:
        session: Parliamentary session to fetch from
        max_bills: Maximum number of bills to fetch (for testing/scaling)
    
    Returns:
        List of complete bill data dictionaries
    """
    
    print("=" * 80)
    print(f"FETCHING BILLS FROM SESSION {session}")
    print(f"Max bills: {max_bills}")
    print("=" * 80 + "\n")
    
    # Step 1: Get list of bills
    bills_list = fetch_bills_list(session=session, limit=max_bills)
    
    # Check if we got any bills
    if not bills_list:
        print("❌ No bills retrieved")
        return []
    
    # Step 2: Process each bill to get complete data
    complete_bills = []
    
    # Loop through each bill
    for idx, bill in enumerate(bills_list, 1):
        # Print progress
        print(f"\n[{idx}/{len(bills_list)}] ", end="")
        
        # Fetch complete data for this bill
        complete_data = fetch_complete_bill_data(bill)
        
        # If successful, add to our list
        if complete_data:
            complete_bills.append(complete_data)
        
        # Be nice to the servers - wait 1 second between requests
        # This prevents overwhelming their servers
        if idx < len(bills_list):  # Don't wait after the last one
            time.sleep(1)
    
    # Print summary
    print("\n" + "=" * 80)
    print(f"✨ Successfully fetched {len(complete_bills)} bills with complete data")
    print("=" * 80 + "\n")
    
    # Return the list of complete bills
    return complete_bills


# Test code - runs when you execute this file directly
if __name__ == "__main__":
    # Test with just 3 bills to start
    print("🧪 TESTING: Fetching 3 bills\n")
    
    # Fetch 3 bills from session 44-1
    test_bills = fetch_bills(session="44-1", max_bills=3)
    
    # Print what we got
    print("\n📊 RESULTS:")
    print("-" * 80)
    for bill in test_bills:
        print(f"Bill {bill['bill_number']}: {bill['title'][:50]}...")
        print(f"  Text length: {len(bill['full_text'])} characters")
        print(f"  Status: {bill['status']}")
        print()