# embeddings.py
# Purpose: Generate vector embeddings for text chunks using OpenAI API
# Embeddings are numerical representations of text that capture semantic meaning
# This allows us to do "similarity search" - find chunks related to a query

import os
from openai import OpenAI
from typing import List, Dict
from dotenv import load_dotenv
import time

# Load environment variables from .env file
load_dotenv()

# Initialize OpenAI client with API key from environment
# Make sure you have OPENAI_API_KEY in your .env file
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))


def generate_embedding(text: str, model: str = "text-embedding-3-small") -> List[float]:
    """
    Generate an embedding vector for a single piece of text
    
    Args:
        text: The text to embed
        model: OpenAI embedding model to use (text-embedding-3-small is cost-effective)
    
    Returns:
        List of floats representing the embedding (1536 dimensions)
    """
    
    try:
        # Call OpenAI API to generate embedding
        response = client.embeddings.create(
            model=model,
            input=text
        )
        
        # Extract the embedding vector from response
        # response.data is a list, we want the first (and only) item
        embedding = response.data[0].embedding
        
        # Return the embedding as a list of floats
        return embedding
        
    except Exception as e:
        # Handle any errors (API failures, rate limits, etc.)
        print(f"❌ Error generating embedding: {str(e)}")
        # Return None to indicate failure
        return None


def generate_embeddings_batch(texts: List[str], model: str = "text-embedding-3-small") -> List[List[float]]:
    """
    Generate embeddings for multiple texts in a single API call (more efficient)
    
    OpenAI allows up to 2048 inputs in one batch call, which is much faster
    and more cost-effective than individual calls
    
    Args:
        texts: List of text strings to embed
        model: OpenAI embedding model to use
    
    Returns:
        List of embedding vectors (each is a list of floats)
    """
    
    # Handle empty input
    if not texts:
        return []
    
    try:
        # Call OpenAI API with multiple inputs
        # The API will process all texts and return embeddings in the same order
        response = client.embeddings.create(
            model=model,
            input=texts  # Pass the entire list
        )
        
        # Extract embeddings from response
        # response.data is a list of embedding objects
        embeddings = [item.embedding for item in response.data]
        
        # Return list of embeddings
        return embeddings
        
    except Exception as e:
        # Handle errors
        print(f"❌ Error generating batch embeddings: {str(e)}")
        # Return empty list on failure
        return []


def embed_chunks(chunk_records: List[Dict], batch_size: int = 100) -> List[Dict]:
    """
    Generate embeddings for a list of chunk records
    Processes in batches for efficiency and rate limit management
    
    Args:
        chunk_records: List of chunk dictionaries from chunking.py
        batch_size: How many chunks to embed per API call (max 2048, but 100 is safer)
    
    Returns:
        List of chunk records with 'embedding' field added
    """
    
    # Count total chunks
    total_chunks = len(chunk_records)
    
    # Handle empty input
    if total_chunks == 0:
        return []
    
    print(f"🧮 Generating embeddings for {total_chunks} chunks...")
    
    # List to store chunks with embeddings
    embedded_chunks = []
    
    # Process in batches
    for i in range(0, total_chunks, batch_size):
        # Calculate batch boundaries
        batch_start = i
        batch_end = min(i + batch_size, total_chunks)
        
        # Get the batch of chunks
        batch = chunk_records[batch_start:batch_end]
        
        # Extract just the text from each chunk
        texts = [chunk['chunk_text'] for chunk in batch]
        
        # Print progress
        print(f"  Processing chunks {batch_start + 1}-{batch_end} of {total_chunks}...")
        
        # Generate embeddings for this batch
        embeddings = generate_embeddings_batch(texts)
        
        # Check if embedding generation succeeded
        if not embeddings or len(embeddings) != len(batch):
            print(f"  ⚠️  Warning: Embedding batch failed or incomplete")
            continue
        
        # Add embeddings to chunk records
        for chunk, embedding in zip(batch, embeddings):
            # Create a copy of the chunk dict
            chunk_with_embedding = chunk.copy()
            # Add the embedding
            chunk_with_embedding['embedding'] = embedding
            # Add to results
            embedded_chunks.append(chunk_with_embedding)
        
        # Rate limiting: wait a bit between batches to avoid hitting API limits
        # OpenAI has rate limits, so we're being polite
        if batch_end < total_chunks:
            time.sleep(0.5)  # Wait 500ms between batches
    
    print(f"✅ Generated {len(embedded_chunks)} embeddings")
    
    # Return chunks with embeddings
    return embedded_chunks


def embed_bill_chunks(bill_data: Dict, chunk_records: List[Dict]) -> List[Dict]:
    """
    Convenience function: Generate embeddings for all chunks of a single bill
    
    Args:
        bill_data: The complete bill data dictionary
        chunk_records: List of chunk dictionaries for this bill
    
    Returns:
        List of chunk records with embeddings added
    """
    
    # Get bill number for logging
    bill_number = bill_data.get('bill_number', 'Unknown')
    
    print(f"\n📄 Embedding chunks for Bill {bill_number}...")
    
    # Generate embeddings
    embedded_chunks = embed_chunks(chunk_records)
    
    # Return the chunks with embeddings
    return embedded_chunks


# Test code
if __name__ == "__main__":
    print("🧪 TESTING EMBEDDINGS MODULE\n")
    print("=" * 80)
    
    # Check if API key is set
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ ERROR: OPENAI_API_KEY not found in environment")
        print("Please create a .env file with:")
        print("OPENAI_API_KEY=sk-...")
        exit(1)
    
    # Test 1: Single embedding
    print("\nTest 1: Single Text Embedding")
    print("-" * 80)
    
    test_text = "This is a test of the OpenAI embedding API."
    print(f"Text: '{test_text}'")
    
    embedding = generate_embedding(test_text)
    
    if embedding:
        print(f"✅ Embedding generated!")
        print(f"   Dimensions: {len(embedding)}")
        print(f"   First 5 values: {embedding[:5]}")
    else:
        print("❌ Embedding generation failed")
    
    # Test 2: Batch embeddings
    print("\n\nTest 2: Batch Embedding")
    print("-" * 80)
    
    test_texts = [
        "Bill C-11 is about online streaming.",
        "Bill C-18 deals with news media compensation.",
        "Bill C-27 focuses on privacy legislation."
    ]
    
    print(f"Embedding {len(test_texts)} texts in batch...")
    
    embeddings = generate_embeddings_batch(test_texts)
    
    if embeddings:
        print(f"✅ Batch embeddings generated!")
        print(f"   Count: {len(embeddings)}")
        print(f"   Each has {len(embeddings[0])} dimensions")
    else:
        print("❌ Batch embedding failed")
    
    # Test 3: Embed chunk records
    print("\n\nTest 3: Embedding Chunk Records")
    print("-" * 80)
    
    # Create fake chunk records
    fake_chunks = [
        {
            'chunk_text': 'Section 1: Introduction to the Act.',
            'chunk_index': 0,
            'bill_number': 'C-999',
            'bill_title': 'Test Bill'
        },
        {
            'chunk_text': 'Section 2: Definitions and scope.',
            'chunk_index': 1,
            'bill_number': 'C-999',
            'bill_title': 'Test Bill'
        },
        {
            'chunk_text': 'Section 3: Implementation requirements.',
            'chunk_index': 2,
            'bill_number': 'C-999',
            'bill_title': 'Test Bill'
        }
    ]
    
    embedded_chunks = embed_chunks(fake_chunks)
    
    if embedded_chunks:
        print(f"\n✅ Successfully embedded {len(embedded_chunks)} chunks")
        
        # Show first chunk with embedding
        first = embedded_chunks[0]
        print(f"\nFirst chunk:")
        print(f"  Text: {first['chunk_text']}")
        print(f"  Has embedding: {'embedding' in first}")
        if 'embedding' in first:
            print(f"  Embedding dimensions: {len(first['embedding'])}")
    else:
        print("❌ Chunk embedding failed")
    
    print("\n" + "=" * 80)
    print("✅ All tests complete!")
