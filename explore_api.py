# explore_api.py
# Purpose: Explore the OpenParliament API to understand the structure of bill data

import requests
import json


def explore_openparliament():
    """
    Main function to explore what data is available from OpenParliament API.
    """
    
    # Base URL for the OpenParliament API - all endpoints start with this
    base_url = "https://api.openparliament.ca"
    
    print("=" * 80)
    print("EXPLORING OPENPARLIAMENT API")
    print("=" * 80 + "\n")
    
    # === STEP 1: Get list of recent bills ===
    print("STEP 1: Fetching recent bills from the API...")
    print("-" * 80)
    
    # Make a GET request to the /bills/ endpoint
    # IMPORTANT: Must add ?format=json to get JSON response
    response = requests.get(f"{base_url}/bills/?format=json")
    
    # Print the HTTP status code (200 = success, 404 = not found, etc.)
    print(f"Status Code: {response.status_code}")
    
    # Check if the request was successful
    if response.status_code != 200:
        print(f"❌ Error: API returned status {response.status_code}")
        return
    
    # Parse the JSON response into a Python dictionary
    bills_data = response.json()
    
    # The API returns data in an 'objects' array
    bills = bills_data.get('objects', [])
    
    # Print how many bills we found
    print(f"✅ Found {len(bills)} bills in this page\n")
    
    
    # === STEP 2: Examine the structure of the first bill ===
    print("STEP 2: Examining the structure of the first bill...")
    print("-" * 80)
    
    # Check if we got any bills back
    if bills:
        # Get the first bill from the list
        first_bill = bills[0]
        
        # Pretty-print the entire JSON structure with indentation
        print(json.dumps(first_bill, indent=2))
        print("\n")
        
        # === STEP 3: Extract key fields we care about ===
        print("STEP 3: Key fields we'll need for our database...")
        print("-" * 80)
        
        # Bill number (e.g., "C-11", "S-5")
        bill_number = first_bill.get('number', 'N/A')
        print(f"Bill Number: {bill_number}")
        
        # Bill name/title (usually in English and French)
        bill_name = first_bill.get('name', {})
        if isinstance(bill_name, dict):
            print(f"Title (EN): {bill_name.get('en', 'N/A')}")
            print(f"Title (FR): {bill_name.get('fr', 'N/A')}")
        else:
            print(f"Title: {bill_name}")
        
        # Session information (e.g., "44-1" for 44th Parliament, 1st Session)
        session = first_bill.get('session', 'N/A')
        print(f"Session: {session}")
        
        # URL to get more details about this specific bill
        bill_url = first_bill.get('url', 'N/A')
        print(f"Detail URL: {bill_url}")
        
        # Introduction date
        introduced = first_bill.get('introduced', 'N/A')
        print(f"Introduced: {introduced}")
        
        print("\n")
        
        
        # === STEP 4: Try to get full bill text ===
        print("STEP 4: Attempting to fetch full bill details...")
        print("-" * 80)
        
        # If the bill has a detail URL, try to fetch it
        if bill_url and bill_url != 'N/A':
            # The URL is a relative path, so prepend base_url and add format=json
            full_url = base_url + bill_url + "?format=json"
            
            print(f"Fetching: {full_url}")
            
            # Make another GET request to get detailed bill information
            detail_response = requests.get(full_url)
            
            # Check if successful
            if detail_response.status_code == 200:
                # Parse the detailed bill data
                bill_detail = detail_response.json()
                
                print("✅ Got bill details!")
                print("\nAvailable fields in bill detail:")
                for key in bill_detail.keys():
                    print(f"  - {key}")
                
                # Check for text fields
                if 'text' in bill_detail:
                    print("\n✅ 'text' field found!")
                    bill_text = bill_detail['text']
                    if isinstance(bill_text, dict):
                        en_text = bill_text.get('en', '')
                        print(f"Text preview (EN): {en_text[:200]}...")
                    else:
                        print(f"Text preview: {str(bill_text)[:200]}...")
                        
                # Check for summary
                if 'summary' in bill_detail:
                    print("\n✅ 'summary' field found!")
                    summary = bill_detail['summary']
                    if isinstance(summary, dict):
                        en_summary = summary.get('en', '')
                        print(f"Summary (EN): {en_summary[:200]}...")
                        
            else:
                print(f"❌ Failed to fetch bill details (status {detail_response.status_code})")
        
        print("\n")
    else:
        print("❌ No bills found in the response")
    
    
    # === STEP 5: Check pagination info ===
    print("STEP 5: Checking pagination information...")
    print("-" * 80)
    
    # OpenParliament API uses pagination
    pagination = bills_data.get('pagination', {})
    
    if pagination:
        print(f"Total count: {pagination.get('count', 'N/A')}")
        print(f"Next page: {pagination.get('next_url', 'None')}")
        print(f"Previous page: {pagination.get('previous_url', 'None')}")
    else:
        print("No pagination info available")
    
    print("\n" + "=" * 80)
    print("EXPLORATION COMPLETE!")
    print("=" * 80)


if __name__ == "__main__":
    explore_openparliament()