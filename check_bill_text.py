# check_bill_text.py
# Purpose: Check what format the bill text is in (via text_url)

import requests
import json


def check_bill_text():
    """
    Fetch a bill's text_url to see what format it's in
    """
    
    base_url = "https://api.openparliament.ca"
    
    print("=" * 80)
    print("CHECKING BILL TEXT FORMAT")
    print("=" * 80 + "\n")
    
    # First, get a bill that has text
    print("Step 1: Fetching a recent bill...")
    bills_response = requests.get(f"{base_url}/bills/?format=json&session=44-1")
    bills = bills_response.json().get('objects', [])
    
    if not bills:
        print("❌ No bills found")
        return
    
    # Get first bill details
    first_bill = bills[0]
    bill_number = first_bill['number']
    detail_url = base_url + first_bill['url'] + "?format=json"
    
    print(f"Selected: Bill {bill_number}")
    print(f"Fetching: {detail_url}\n")
    
    detail_response = requests.get(detail_url)
    bill_detail = detail_response.json()
    
    # Check if text_url exists
    text_url = bill_detail.get('text_url')
    
    if not text_url:
        print("❌ No text_url found for this bill")
        print("Let's try a few more bills...\n")
        
        # Try the first 5 bills
        for bill in bills[:5]:
            detail_url = base_url + bill['url'] + "?format=json"
            detail_resp = requests.get(detail_url)
            detail = detail_resp.json()
            
            if detail.get('text_url'):
                text_url = detail.get('text_url')
                bill_number = bill['number']
                print(f"✅ Found text_url in Bill {bill_number}")
                break
    
    if not text_url:
        print("❌ None of the recent bills have text_url")
        print("\nThis might mean:")
        print("1. Bills don't have full text in OpenParliament")
        print("2. We need to use LEGISinfo or parl.ca as alternative source")
        return
    
    # Fetch the text
    print(f"\nStep 2: Fetching bill text from text_url...")
    print(f"URL: {text_url}")
    
    # Add format=json if it's an API endpoint
    if text_url.startswith('/'):
        text_url = base_url + text_url + "?format=json"
    
    print(f"Full URL: {text_url}\n")
    
    text_response = requests.get(text_url)
    
    print(f"Status Code: {text_response.status_code}")
    print(f"Content-Type: {text_response.headers.get('Content-Type')}")
    
    # Check if it's JSON
    if 'application/json' in text_response.headers.get('Content-Type', ''):
        print("\n✅ Response is JSON")
        text_data = text_response.json()
        
        print("\nJSON structure:")
        print(json.dumps(text_data, indent=2)[:1000] + "...")
        
    else:
        print("\n⚠️ Response is not JSON (might be HTML or plain text)")
        print("\nFirst 500 characters:")
        print(text_response.text[:500])
    
    print("\n" + "=" * 80)
    print("CHECK COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    check_bill_text()