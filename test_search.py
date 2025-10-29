# test_search.py
# Purpose: Test vector search with real queries to verify the system works

import os
from dotenv import load_dotenv
from supabase import create_client
from embeddings import generate_embedding

load_dotenv()

# Initialize Supabase client
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_KEY')
)


def search_bills(query: str, top_k: int = 5, threshold: float = 0.5):
    """
    Search for relevant bill chunks using vector similarity
    
    Args:
        query: Natural language search query
        top_k: Number of results to return
        threshold: Minimum similarity score (0-1)
    
    Returns:
        List of matching chunks with metadata
    """
    
    print(f"\n{'='*80}")
    print(f"🔍 SEARCHING: '{query}'")
    print('='*80)
    
    # Step 1: Generate embedding for the query
    print("\n[1/2] Generating query embedding...")
    query_embedding = generate_embedding(query)
    
    if not query_embedding:
        print("❌ Failed to generate embedding")
        return []
    
    print(f"✅ Query embedded ({len(query_embedding)} dimensions)")
    
    # Step 2: Call the vector search function
    print(f"\n[2/2] Searching database (top {top_k} results)...")
    
    try:
        # Call the match_bill_chunks SQL function
        result = supabase.rpc(
            'match_bill_chunks',
            {
                'query_embedding': query_embedding,
                'match_threshold': threshold,
                'match_count': top_k
            }
        ).execute()
        
        # Get the matches
        matches = result.data
        
        if not matches:
            print("⚠️  No matches found (try lowering threshold or different query)")
            return []
        
        # Display results
        print(f"\n✅ Found {len(matches)} matches:\n")
        print("-"*80)
        
        for i, match in enumerate(matches, 1):
            print(f"\n{i}. Bill {match['bill_number']}: {match['bill_title'][:60]}...")
            print(f"   Similarity: {match['similarity']:.3f} (higher = better match)")
            print(f"   Chunk {match['chunk_index'] + 1}")
            print(f"   Preview: {match['chunk_text'][:150]}...")
        
        print("\n" + "-"*80)
        
        return matches
        
    except Exception as e:
        print(f"❌ Search failed: {str(e)}")
        return []


def test_multiple_queries():
    """
    Run multiple test queries to verify search quality
    """
    
    print("\n" + "🧪"*40)
    print("VECTOR SEARCH TESTING")
    print("🧪"*40)
    
    # Define test queries - use topics you know are in your bills
    test_queries = [
        # Generic queries
        "online streaming and broadcasting regulations",
        "COVID-19 pandemic support measures",
        "criminal law amendments",
        
        # Specific queries
        "what does bill C-2 say",
        "internet and social media content",
        
        # Abstract queries (test semantic understanding)
        "how does the government support citizens during emergencies",
    ]
    
    print(f"\nRunning {len(test_queries)} test queries...\n")
    
    # Run each query
    for query in test_queries:
        matches = search_bills(query, top_k=3, threshold=0.5)
        
        # Brief pause between queries
        input("\nPress Enter for next query...")
    
    print("\n" + "="*80)
    print("✅ All test queries complete!")
    print("="*80)


def interactive_search():
    """
    Interactive mode - type queries and see results
    """
    
    print("\n" + "💬"*40)
    print("INTERACTIVE SEARCH MODE")
    print("💬"*40)
    print("\nType your questions about Canadian bills")
    print("Type 'quit' to exit\n")
    
    while True:
        # Get user input
        query = input("\n🔍 Your question: ").strip()
        
        # Check for exit
        if query.lower() in ['quit', 'exit', 'q']:
            print("\n👋 Goodbye!")
            break
        
        # Skip empty queries
        if not query:
            continue
        
        # Search
        search_bills(query, top_k=3, threshold=0.5)


if __name__ == "__main__":
    import sys
    
    print("\n" + "🚀"*40)
    print("ExplainThisBill - Vector Search Tester")
    print("🚀"*40)
    
    # Check if user wants interactive mode
    if len(sys.argv) > 1 and sys.argv[1] == '--interactive':
        interactive_search()
    else:
        # Run automated tests
        print("\nRunning automated test queries...")
        print("(Use --interactive flag for interactive mode)")
        
        test_multiple_queries()
        
        print("\n\nWant to try your own queries?")
        print("Run: python test_search.py --interactive")