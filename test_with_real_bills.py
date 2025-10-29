# test_integration.py
# Purpose: Test fetch_bills.py + chunking.py together with real data

from fetch_bills import fetch_bills
from chunking import chunk_bill, count_tokens


def test_with_real_bills():
    """
    Fetch real bills and chunk them to see real-world performance
    """
    
    print("=" * 80)
    print("INTEGRATION TEST: Real Bills + Chunking")
    print("=" * 80 + "\n")
    
    # Fetch 3 real bills
    print("Step 1: Fetching real bills...")
    bills = fetch_bills(session="44-1", max_bills=3)
    
    if not bills:
        print("❌ No bills fetched")
        return
    
    print(f"\n{'=' * 80}")
    print("Step 2: Chunking each bill...")
    print("=" * 80 + "\n")
    
    # Process each bill
    for bill in bills:
        print(f"📄 Bill {bill['bill_number']}: {bill['title'][:50]}...")
        print("-" * 80)
        
        # Show original text stats
        full_text = bill['full_text']
        total_tokens = count_tokens(full_text)
        print(f"  Original text:")
        print(f"    - Characters: {len(full_text):,}")
        print(f"    - Tokens: {total_tokens:,}")
        
        # Chunk it
        chunks = chunk_bill(bill, max_tokens=500, overlap_tokens=50)
        print(f"\n  Chunked into: {len(chunks)} chunks")
        
        # Show first chunk
        if chunks:
            first = chunks[0]
            chunk_tokens = count_tokens(first['chunk_text'])
            print(f"\n  First chunk preview:")
            print(f"    - Tokens: {chunk_tokens}")
            print(f"    - Text: {first['chunk_text'][:150]}...")
        
        print("\n")
    
    print("=" * 80)
    print("✅ Integration test complete!")
    print("=" * 80)


if __name__ == "__main__":
    test_with_real_bills()