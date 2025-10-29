# chunking.py
# Purpose: Split long bill text into smaller chunks for embedding
# We need chunks because:
# 1. OpenAI embeddings work best on smaller text segments
# 2. Vector search retrieves specific relevant sections, not entire bills
# 3. Makes the RAG system more precise

import tiktoken
from typing import List


def count_tokens(text: str, model: str = "cl100k_base") -> int:
    """
    Count how many tokens are in a text string
    
    Args:
        text: The text to count tokens for
        model: The tokenizer model to use (cl100k_base is for GPT-3.5/GPT-4)
    
    Returns:
        Number of tokens
    """
    
    # Get the tokenizer encoding for the specified model
    # cl100k_base is the encoding used by GPT-3.5-turbo, GPT-4, and text-embedding models
    encoding = tiktoken.get_encoding(model)
    
    # Encode the text into tokens and count them
    tokens = encoding.encode(text)
    
    # Return the count
    return len(tokens)


def chunk_text(text: str, max_tokens: int = 500, overlap_tokens: int = 50) -> List[str]:
    """
    Split text into overlapping chunks of a maximum token size
    
    Why overlap? If a sentence is split across chunks, the overlap ensures
    we don't lose context at chunk boundaries.
    
    Args:
        text: The full text to chunk
        max_tokens: Maximum tokens per chunk (default 500)
        overlap_tokens: Number of tokens to overlap between chunks (default 50)
    
    Returns:
        List of text chunks
    """
    
    # Get the tokenizer
    encoding = tiktoken.get_encoding("cl100k_base")
    
    # Encode the entire text into tokens
    # This converts the string into a list of integers (token IDs)
    tokens = encoding.encode(text)
    
    # Calculate total number of tokens
    total_tokens = len(tokens)
    
    # If text is shorter than max_tokens, no chunking needed
    if total_tokens <= max_tokens:
        # Return the original text as a single-item list
        return [text]
    
    # Initialize list to store chunks
    chunks = []
    
    # Start at the beginning
    start = 0
    
    # Loop through the tokens, creating chunks
    while start < total_tokens:
        # Calculate end position: start + max_tokens
        end = start + max_tokens
        
        # Make sure we don't go past the end of the tokens
        if end > total_tokens:
            end = total_tokens
        
        # Extract the chunk of tokens
        chunk_tokens = tokens[start:end]
        
        # Decode tokens back into text
        text_chunk = encoding.decode(chunk_tokens)
        
        # Add to our list of chunks
        chunks.append(text_chunk)
        
        # Move the start position forward
        # We subtract overlap_tokens so chunks overlap
        # This ensures continuity at chunk boundaries
        start += (max_tokens - overlap_tokens)
        
        # Safety check: if we're very close to the end, just include it
        # This prevents tiny final chunks
        if start + overlap_tokens >= total_tokens:
            break
    
    # Return all the chunks
    return chunks


def chunk_bill(bill_data: dict, max_tokens: int = 500, overlap_tokens: int = 50) -> List[dict]:
    """
    Chunk a complete bill's text and create chunk records ready for database
    
    Args:
        bill_data: Dictionary with bill info including 'full_text'
        max_tokens: Maximum tokens per chunk
        overlap_tokens: Overlap between chunks
    
    Returns:
        List of chunk dictionaries with metadata
    """
    
    # Extract the full text from bill data
    full_text = bill_data.get('full_text', '')
    
    # If no text, return empty list
    if not full_text:
        return []
    
    # Count tokens before chunking (for logging)
    total_tokens = count_tokens(full_text)
    
    # Chunk the text
    text_chunks = chunk_text(full_text, max_tokens, overlap_tokens)
    
    # Create structured chunk records with metadata
    chunk_records = []
    
    # Loop through each chunk with its index
    for idx, text_chunk in enumerate(text_chunks):
        # Create a dictionary for this chunk
        chunk_record = {
            'chunk_text': text_chunk,
            'chunk_index': idx,  # Position in the sequence
            'bill_number': bill_data.get('bill_number'),
            'bill_title': bill_data.get('title'),
            'total_chunks': len(text_chunks)  # How many chunks this bill has
        }
        
        # Add to list
        chunk_records.append(chunk_record)
    
    # Return all chunk records
    return chunk_records


# Test code
if __name__ == "__main__":
    print("🧪 TESTING CHUNKING MODULE\n")
    print("=" * 80)
    
    # Test 1: Token counting
    print("\nTest 1: Token Counting")
    print("-" * 80)
    
    # Short text
    short_text = "This is a short test."
    token_count = count_tokens(short_text)
    print(f"Text: '{short_text}'")
    print(f"Tokens: {token_count}")
    
    # Long text
    long_text = "This is a test. " * 100  # Repeat 100 times
    token_count = count_tokens(long_text)
    print(f"\nLong text (100 repetitions)")
    print(f"Tokens: {token_count}")
    
    # Test 2: Text chunking
    print("\n\nTest 2: Text Chunking")
    print("-" * 80)
    
    # Create a medium-length text
    test_text = ("Section 1: This is the first section. " * 20 + 
                 "Section 2: This is the second section. " * 20 +
                 "Section 3: This is the third section. " * 20)
    
    # Count tokens
    total = count_tokens(test_text)
    print(f"Test text tokens: {total}")
    
    # Chunk with max 100 tokens, 20 overlap
    chunks = chunk_text(test_text, max_tokens=100, overlap_tokens=20)
    
    print(f"Created {len(chunks)} chunks\n")
    
    # Show first few chunks
    for i, chunk in enumerate(chunks[:3]):  # Show first 3
        tokens = count_tokens(chunk)
        print(f"Chunk {i}:")
        print(f"  Tokens: {tokens}")
        print(f"  Text preview: {chunk[:80]}...")
        print()
    
    # Test 3: Bill chunking
    print("\nTest 3: Bill Chunking")
    print("-" * 80)
    
    # Create a fake bill for testing
    fake_bill = {
        'bill_number': 'C-999',
        'title': 'Test Bill for Chunking',
        'full_text': "An Act to test chunking functionality. " * 200  # Long text
    }
    
    # Chunk it
    chunk_records = chunk_bill(fake_bill, max_tokens=500, overlap_tokens=50)
    
    print(f"Bill C-999 chunked into {len(chunk_records)} chunks\n")
    
    # Show first chunk details
    if chunk_records:
        first_chunk = chunk_records[0]
        print("First chunk:")
        print(f"  Bill Number: {first_chunk['bill_number']}")
        print(f"  Chunk Index: {first_chunk['chunk_index']}")
        print(f"  Total Chunks: {first_chunk['total_chunks']}")
        print(f"  Text length: {len(first_chunk['chunk_text'])} chars")
        print(f"  Text tokens: {count_tokens(first_chunk['chunk_text'])}")
    
    print("\n" + "=" * 80)
    print("✅ All tests complete!")