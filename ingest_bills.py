# ingest_bills.py
# Purpose: Orchestrate the complete bill ingestion pipeline
# This is the main script that ties everything together:
# Fetch → Chunk → Embed → Save to Database

import time
from typing import List, Dict

# Import our custom modules
from fetch_bills import fetch_bills
from chunking import chunk_bill, count_tokens
from embeddings import embed_chunks
from supabase_client import (
    bill_exists,
    insert_bill,
    insert_bill_chunks,
    count_bills,
    count_chunks
)


def process_single_bill(bill_data: Dict) -> bool:
    """
    Process one complete bill through the entire pipeline
    
    Pipeline steps:
    1. Check if bill already exists (skip if so)
    2. Chunk the bill text
    3. Generate embeddings for chunks
    4. Insert bill into database
    5. Insert chunks with embeddings
    
    Args:
        bill_data: Complete bill dictionary from fetch_bills()
    
    Returns:
        True if successful, False if failed
    """
    
    # Extract bill number for logging
    bill_number = bill_data.get('bill_number', 'UNKNOWN')
    
    print(f"\n{'='*80}")
    print(f"Processing Bill {bill_number}")
    print('='*80)
    
    # Step 1: Check if bill already exists
    print(f"\n[1/5] Checking if bill exists...")
    if bill_exists(bill_number):
        print(f"   ⏭️  Bill {bill_number} already in database, skipping")
        return False  # Not an error, just skip
    
    print(f"   ✅ Bill {bill_number} is new")
    
    # Step 2: Chunk the bill text
    print(f"\n[2/5] Chunking bill text...")
    
    # Get text length for logging
    full_text = bill_data.get('full_text', '')
    text_length = len(full_text)
    token_count = count_tokens(full_text)
    
    print(f"   Text: {text_length:,} characters, {token_count:,} tokens")
    
    # Create chunks
    chunk_records = chunk_bill(bill_data, max_tokens=500, overlap_tokens=50)
    
    # Check if chunking succeeded
    if not chunk_records:
        print(f"   ❌ No chunks created (text too short or empty)")
        return False
    
    print(f"   ✅ Created {len(chunk_records)} chunks")
    
    # Step 3: Generate embeddings
    print(f"\n[3/5] Generating embeddings...")
    
    # Embed all chunks
    embedded_chunks = embed_chunks(chunk_records, batch_size=100)
    
    # Check if embedding succeeded
    if not embedded_chunks or len(embedded_chunks) != len(chunk_records):
        print(f"   ❌ Embedding failed or incomplete")
        return False
    
    print(f"   ✅ Embedded {len(embedded_chunks)} chunks")
    
    # Step 4: Insert bill into database
    print(f"\n[4/5] Inserting bill into database...")
    
    bill_id = insert_bill(bill_data)
    
    # Check if bill insertion succeeded
    if not bill_id:
        print(f"   ❌ Failed to insert bill")
        return False
    
    print(f"   ✅ Bill inserted (ID: {bill_id[:8]}...)")
    
    # Step 5: Insert chunks with embeddings
    print(f"\n[5/5] Inserting chunks into database...")
    
    success = insert_bill_chunks(bill_id, embedded_chunks)
    
    # Check if chunk insertion succeeded
    if not success:
        print(f"   ❌ Failed to insert chunks")
        # Note: Bill is already inserted, but without chunks
        # You might want to delete the bill here to keep data consistent
        return False
    
    print(f"   ✅ Inserted {len(embedded_chunks)} chunks")
    
    # Success!
    print(f"\n{'='*80}")
    print(f"✅ Successfully processed Bill {bill_number}")
    print(f"{'='*80}")
    
    return True


def ingest_bills_batch(session: str = "44-1", max_bills: int = 5, delay_seconds: int = 2) -> Dict:
    """
    Main function: Ingest multiple bills from a parliamentary session
    
    Args:
        session: Parliamentary session to fetch from (e.g., "44-1")
        max_bills: Maximum number of bills to process
        delay_seconds: Seconds to wait between bills (be nice to APIs)
    
    Returns:
        Dictionary with statistics about the ingestion
    """
    
    print("\n" + "="*80)
    print("BILL INGESTION PIPELINE")
    print("="*80)
    print(f"Session: {session}")
    print(f"Max bills: {max_bills}")
    print(f"Delay between bills: {delay_seconds}s")
    print("="*80 + "\n")
    
    # Track statistics
    stats = {
        'attempted': 0,
        'successful': 0,
        'failed': 0,
        'skipped': 0,
        'total_chunks': 0
    }
    
    # Step 1: Fetch bills from OpenParliament
    print("STEP 1: FETCHING BILLS")
    print("-"*80)
    
    bills = fetch_bills(session=session, max_bills=max_bills)
    
    # Check if we got any bills
    if not bills:
        print("\n❌ No bills fetched. Aborting.")
        return stats
    
    print(f"\n✅ Fetched {len(bills)} bills to process\n")
    
    # Step 2: Process each bill
    print("\nSTEP 2: PROCESSING BILLS")
    print("-"*80)
    
    for idx, bill in enumerate(bills, 1):
        # Update attempted count
        stats['attempted'] += 1
        
        print(f"\n{'#'*80}")
        print(f"BILL {idx} of {len(bills)}")
        print(f"{'#'*80}")
        
        # Process this bill
        success = process_single_bill(bill)
        
        # Update statistics
        if success:
            stats['successful'] += 1
            # Count chunks added (estimate based on text length)
            text_length = len(bill.get('full_text', ''))
            estimated_chunks = max(1, text_length // 2500)  # Rough estimate
            stats['total_chunks'] += estimated_chunks
        elif bill_exists(bill.get('bill_number', '')):
            stats['skipped'] += 1
        else:
            stats['failed'] += 1
        
        # Wait between bills to be nice to APIs and databases
        if idx < len(bills):  # Don't wait after the last one
            print(f"\n⏳ Waiting {delay_seconds}s before next bill...")
            time.sleep(delay_seconds)
    
    # Step 3: Print final summary
    print("\n\n" + "="*80)
    print("INGESTION COMPLETE")
    print("="*80)
    
    # Get current database state
    total_bills = count_bills()
    total_chunks = count_chunks()
    
    print(f"\nProcessing Summary:")
    print(f"  Attempted:  {stats['attempted']}")
    print(f"  Successful: {stats['successful']} ✅")
    print(f"  Skipped:    {stats['skipped']} ⏭️")
    print(f"  Failed:     {stats['failed']} ❌")
    
    print(f"\nDatabase State:")
    print(f"  Total bills:  {total_bills}")
    print(f"  Total chunks: {total_chunks}")
    
    print("\n" + "="*80)
    
    # Return statistics
    return stats


def ingest_incremental(session: str = "44-1", max_new_bills: int = 10) -> Dict:
    """
    Incrementally add new bills without re-processing existing ones
    
    This is useful for updating your database with new bills as they're introduced
    
    Args:
        session: Parliamentary session
        max_new_bills: Maximum NEW bills to add (will skip existing)
    
    Returns:
        Statistics dictionary
    """
    
    print("\n" + "="*80)
    print("INCREMENTAL BILL INGESTION")
    print("="*80)
    
    # Get current count
    current_count = count_bills()
    print(f"Current bills in database: {current_count}")
    
    # Fetch more bills than we need (to account for existing ones)
    fetch_count = min(max_new_bills * 3, 100)  # Fetch 3x what we need, max 100
    
    print(f"Fetching up to {fetch_count} bills (will skip existing ones)")
    print("="*80 + "\n")
    
    # Use the main ingestion function
    stats = ingest_bills_batch(session=session, max_bills=fetch_count, delay_seconds=2)
    
    return stats


# Main execution
if __name__ == "__main__":
    print("\n" + "🚀"*40)
    print("ExplainThisBill - Bill Ingestion Pipeline")
    print("🚀"*40 + "\n")
    
    # Configuration
    # Start small for testing, then scale up
    SESSION = "44-1"  # 44th Parliament, 1st session (current as of 2025)
    MAX_BILLS = 5     # Start with 5 for testing
    
    print("Configuration:")
    print(f"  Session: {SESSION}")
    print(f"  Max bills: {MAX_BILLS}")
    print()
    
    # Confirmation prompt
    response = input(f"Ready to ingest up to {MAX_BILLS} bills from session {SESSION}? (yes/no): ")
    
    if response.lower() not in ['yes', 'y']:
        print("\n❌ Ingestion cancelled")
        exit(0)
    
    print("\n✅ Starting ingestion...\n")
    
    # Run the ingestion
    start_time = time.time()
    
    stats = ingest_bills_batch(
        session=SESSION,
        max_bills=MAX_BILLS,
        delay_seconds=2
    )
    
    end_time = time.time()
    duration = end_time - start_time
    
    # Final summary
    print("\n" + "="*80)
    print("FINAL SUMMARY")
    print("="*80)
    print(f"Total time: {duration:.1f} seconds ({duration/60:.1f} minutes)")
    print(f"Successfully processed: {stats['successful']} bills")
    print(f"Average time per bill: {duration/max(1, stats['successful']):.1f} seconds")
    print("\n🎉 Ingestion complete! Your database is ready.")
    print("="*80 + "\n")
    
    # Next steps
    print("Next Steps:")
    print("1. Check your Supabase dashboard to see the bills")
    print("2. Test vector search with test_search.py (if you have it)")
    print("3. Build your Lovable frontend!")
    print("4. To add more bills, run this script again with higher MAX_BILLS")
    print()