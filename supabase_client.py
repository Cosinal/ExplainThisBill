# supabase_client.py
# Purpose: Handle all interactions with Supabase database
# This module provides functions to insert bills and chunks into the database

import os
from supabase import create_client, Client
from dotenv import load_dotenv
from typing import Dict, List, Optional

# Load environment variables from .env file
load_dotenv()

# Initialize Supabase client
# Using service role key for full database access (bypasses RLS)
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_KEY')

# Create the client - this is used for all database operations
supabase: Client = create_client(supabase_url, supabase_key)


def bill_exists(bill_number: str) -> bool:
    """
    Check if a bill already exists in the database
    
    This prevents duplicate insertions and allows incremental updates
    
    Args:
        bill_number: The bill number to check (e.g., "C-11")
    
    Returns:
        True if bill exists, False otherwise
    """
    
    try:
        # Query the bills table for this bill number
        # .select('id') only retrieves the id field (efficient)
        # .eq('bill_number', bill_number) filters for exact match
        result = supabase.table('bills').select('id').eq('bill_number', bill_number).execute()
        
        # If data is returned, bill exists
        return len(result.data) > 0
        
    except Exception as e:
        # Handle any database errors
        print(f"   ⚠️  Error checking if bill exists: {str(e)}")
        # Return False to be safe (will attempt insert)
        return False


def insert_bill(bill_data: Dict) -> Optional[str]:
    """
    Insert a new bill into the bills table
    
    Args:
        bill_data: Dictionary with bill information
    
    Returns:
        The bill's UUID (id) if successful, None if failed
    """
    
    try:
        # Prepare the data for insertion
        # Only include fields that exist in the database schema
        insert_data = {
            'bill_number': bill_data.get('bill_number'),
            'title': bill_data.get('title'),
            'summary': bill_data.get('summary', ''),
            'full_text': bill_data.get('full_text'),
            'status': bill_data.get('status'),
            'session': bill_data.get('session'),
            'introduced_date': bill_data.get('introduced_date'),
            'url': bill_data.get('url'),
            'short_title': bill_data.get('short_title'),
            'status_code': bill_data.get('status_code'),
            'status_description': bill_data.get('status_description'),
            'home_chamber': bill_data.get('home_chamber'),
            'legisinfo_url': bill_data.get('legisinfo_url'),
            'text_url': bill_data.get('text_url'),
            'private_member_bill': bill_data.get('private_member_bill'),
            'law_date': bill_data.get('law_date'),
            'sponsor_name': bill_data.get('sponsor_name'),
            'sponsor_party': bill_data.get('sponsor_party'),
            'sponsor_riding': bill_data.get('sponsor_riding'),
            'sponsor_province': bill_data.get('sponsor_province'),
            'is_ceremonial': bill_data.get('is_ceremonial', False)
        }
        
        # Insert into bills table
        # .execute() performs the operation
        result = supabase.table('bills').insert(insert_data).execute()
        
        # Extract the bill ID from the result
        # result.data is a list with one item (the inserted record)
        bill_id = result.data[0]['id']
        
        # Return the bill's UUID
        return bill_id
        
    except Exception as e:
        # Handle insertion errors (duplicates, constraint violations, etc.)
        print(f"   ❌ Error inserting bill: {str(e)}")
        return None


def insert_bill_chunks(bill_id: str, chunks_data: List[Dict]) -> bool:
    """
    Insert multiple bill chunks into the bill_chunks table
    
    Args:
        bill_id: UUID of the parent bill
        chunks_data: List of chunk dictionaries with text and embeddings
    
    Returns:
        True if successful, False if failed
    """
    
    # Prepare chunk records for insertion
    insert_records = []

    for chunk in chunks_data:
        record = {
            'bill_id': bill_id,
            'chunk_text': chunk.get('chunk_text'),
            'chunk_index': chunk.get('chunk_index'),
            'embedding': chunk.get('embedding'),
            'clause_reference': None
        }

        insert_records.append(record)

    try:
        supabase.table('bill_chunks').insert(insert_records).execute()
        return True
    except Exception as e:
        print(f"   ❌ Error inserting chunks: {str(e)}")
        return False


def reset_bill_data() -> bool:
    """
    Remove all bills and chunks before a fresh ingestion run.

    Returns:
        True when both deletes succeed, False otherwise.
    """

    try:
        # Delete children first to avoid foreign key violations if CASCADE is disabled
        supabase.table('bill_chunks').delete().neq(
            'id', '00000000-0000-0000-0000-000000000000'
        ).execute()
        supabase.table('bills').delete().neq(
            'id', '00000000-0000-0000-0000-000000000000'
        ).execute()
        return True
    except Exception as e:
        print(f"   ❌ Error resetting bill data: {str(e)}")
        return False


def delete_bill(bill_number: str) -> bool:
    """
    Delete a bill and all its chunks from the database
    
    Uses CASCADE delete - when bill is deleted, chunks are auto-deleted
    because of the foreign key constraint with ON DELETE CASCADE
    
    Args:
        bill_number: The bill number to delete
    
    Returns:
        True if successful, False if failed
    """
    
    try:
        # Delete from bills table
        # Chunks will be automatically deleted due to CASCADE
        supabase.table('bills').delete().eq('bill_number', bill_number).execute()
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error deleting bill: {str(e)}")
        return False


def get_bill_by_number(bill_number: str) -> Optional[Dict]:
    """
    Retrieve a bill by its bill number
    
    Args:
        bill_number: The bill number to look up
    
    Returns:
        Bill dictionary if found, None otherwise
    """
    
    try:
        # Query bills table
        result = supabase.table('bills').select('*').eq('bill_number', bill_number).execute()
        
        # Check if found
        if result.data:
            return result.data[0]
        else:
            return None
            
    except Exception as e:
        print(f"   ❌ Error retrieving bill: {str(e)}")
        return None


def get_all_bills() -> List[Dict]:
    """
    Retrieve all bills from the database
    
    Returns:
        List of bill dictionaries
    """
    
    try:
        # Query all bills, ordered by bill_number
        result = supabase.table('bills').select('*').order('bill_number').execute()
        
        return result.data
        
    except Exception as e:
        print(f"   ❌ Error retrieving bills: {str(e)}")
        return []


def get_bill_chunks(bill_id: str) -> List[Dict]:
    """
    Retrieve all chunks for a specific bill
    
    Args:
        bill_id: UUID of the bill
    
    Returns:
        List of chunk dictionaries
    """
    
    try:
        # Query bill_chunks table for this bill
        result = supabase.table('bill_chunks').select('*').eq('bill_id', bill_id).order('chunk_index').execute()
        
        return result.data
        
    except Exception as e:
        print(f"   ❌ Error retrieving chunks: {str(e)}")
        return []


def count_bills() -> int:
    """
    Count total bills in the database
    
    Returns:
        Number of bills
    """
    
    try:
        # Count bills
        result = supabase.table('bills').select('id', count='exact').execute()
        
        # Return count
        return result.count
        
    except Exception as e:
        print(f"   ❌ Error counting bills: {str(e)}")
        return 0


def count_chunks() -> int:
    """
    Count total chunks in the database
    
    Returns:
        Number of chunks
    """
    
    try:
        # Count chunks
        result = supabase.table('bill_chunks').select('id', count='exact').execute()
        
        return result.count
        
    except Exception as e:
        print(f"   ❌ Error counting chunks: {str(e)}")
        return 0


# Test code
if __name__ == "__main__":
    print("🧪 TESTING SUPABASE CLIENT\n")
    print("=" * 80)
    
    # Check if credentials are set
    if not supabase_url or not supabase_key:
        print("❌ ERROR: Supabase credentials not found in .env")
        exit(1)
    
    print("✅ Supabase client initialized")
    print(f"   URL: {supabase_url}")
    print()
    
    # Test 1: Check if connection works
    print("Test 1: Database Connection")
    print("-" * 80)
    
    try:
        # Try to count bills (simple query to test connection)
        bill_count = count_bills()
        chunk_count = count_chunks()
        
        print(f"✅ Connection successful!")
        print(f"   Current bills in database: {bill_count}")
        print(f"   Current chunks in database: {chunk_count}")
        
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        exit(1)
    
    # Test 2: Insert a test bill
    print("\n\nTest 2: Insert Test Bill")
    print("-" * 80)
    
    test_bill_number = "TEST-999"
    
    # Check if test bill already exists
    if bill_exists(test_bill_number):
        print(f"Test bill {test_bill_number} already exists, deleting it first...")
        delete_bill(test_bill_number)
    
    # Create test bill data
    test_bill = {
        'bill_number': test_bill_number,
        'title': 'Test Bill for Supabase Client',
        'summary': 'This is a test bill',
        'full_text': 'An Act to test the Supabase client functionality.',
        'status': 'Testing',
        'session': '99-9',
        'introduced_date': '2025-01-01',
        'url': 'https://example.com/test'
    }
    
    print(f"Inserting test bill {test_bill_number}...")
    bill_id = insert_bill(test_bill)
    
    if bill_id:
        print(f"✅ Bill inserted successfully!")
        print(f"   Bill ID: {bill_id}")
    else:
        print("❌ Bill insertion failed")
        exit(1)
    
    # Test 3: Insert test chunks
    print("\n\nTest 3: Insert Test Chunks")
    print("-" * 80)
    
    # Create test chunks with fake embeddings
    # Real embeddings are 1536 dimensions, but for testing we'll use smaller ones
    test_chunks = [
        {
            'chunk_text': 'Section 1: This is the first section.',
            'chunk_index': 0,
            'embedding': [0.1] * 1536  # Fake embedding
        },
        {
            'chunk_text': 'Section 2: This is the second section.',
            'chunk_index': 1,
            'embedding': [0.2] * 1536  # Fake embedding
        }
    ]
    
    print(f"Inserting {len(test_chunks)} test chunks...")
    success = insert_bill_chunks(bill_id, test_chunks)
    
    if success:
        print("✅ Chunks inserted successfully!")
    else:
        print("❌ Chunk insertion failed")
    
    # Test 4: Retrieve the data
    print("\n\nTest 4: Retrieve Data")
    print("-" * 80)
    
    # Retrieve the bill we just inserted
    retrieved_bill = get_bill_by_number(test_bill_number)
    
    if retrieved_bill:
        print(f"✅ Retrieved bill {test_bill_number}")
        print(f"   Title: {retrieved_bill['title']}")
        
        # Retrieve its chunks
        chunks = get_bill_chunks(retrieved_bill['id'])
        print(f"   Chunks: {len(chunks)}")
        
    else:
        print("❌ Could not retrieve bill")
    
    # Test 5: Cleanup
    print("\n\nTest 5: Cleanup")
    print("-" * 80)
    
    print(f"Deleting test bill {test_bill_number}...")
    if delete_bill(test_bill_number):
        print("✅ Test bill deleted")
    else:
        print("❌ Deletion failed")
    
    # Final counts
    print("\n\nFinal Database State:")
    print("-" * 80)
    print(f"Bills: {count_bills()}")
    print(f"Chunks: {count_chunks()}")
    
    print("\n" + "=" * 80)
    print("✅ All tests complete!")
