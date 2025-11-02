import os
import time
from datetime import datetime

from dotenv import load_dotenv
from openai import OpenAI
from supabase import create_client, Client

# Initialize clients
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not all([SUPABASE_URL, SUPABASE_KEY, OPENAI_API_KEY]):
    print("ERROR: Missing required environment variables!")
    print("Required: SUPABASE_URL, SUPABASE_SERVICE_KEY, OPENAI_API_KEY")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

def generate_summary_for_bill(bill_id: str, bill_number: str, bill_title: str) -> str:
    """Generate a summary for a specific bill using OpenAI."""
    
    # Get chunks for this bill
    chunks_response = supabase.table("bill_chunks")\
        .select("chunk_text")\
        .eq("bill_id", bill_id)\
        .order("chunk_index")\
        .limit(10)\
        .execute()
    
    if not chunks_response.data:
        print(f"  ⚠️  No chunks found for {bill_number}")
        return None
    
    # Build context from chunks
    context = "\n\n---\n\n".join([
        f"Source {i+1} ({bill_number} - {bill_title}):\n{chunk['chunk_text']}"
        for i, chunk in enumerate(chunks_response.data)
    ])
    
    # System prompt (matches your edge function)
    system_prompt = """You are Alex, a friendly Canadian legislative assistant for ExplainThisBill.com. Your purpose is to help everyday Canadians understand bills in plain language. Your audience is the general public, not lawyers or policy experts. You have access to a database of bills from Session 45-1 (2025). You are conversational, helpful, and honest."""
    
    user_prompt = f"""<instructions>
Answer in 2-3 sentences maximum using plain language. Cite the bill number (e.g., "Bill {bill_number}").
</instructions>

<context>
{context}
</context>

<user_question>Explain Bill {bill_number}</user_question>"""
    
    # Call OpenAI API
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",  # Cheaper and faster for summaries
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        max_tokens=500,
        temperature=0.7
    )
    
    summary = response.choices[0].message.content
    return summary

def main():
    print("=" * 60)
    print("Bill Summary Generation Script (OpenAI)")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Get all bills
    print("Fetching bills from database...")
    bills_response = supabase.table("bills")\
        .select("id, bill_number, title, session")\
        .eq("session", "45-1")\
        .order("bill_number")\
        .execute()
    
    bills = bills_response.data
    total_bills = len(bills)
    print(f"Found {total_bills} bills\n")
    
    # Check which bills already have summaries
    existing_summaries = supabase.table("bill_summaries")\
        .select("bill_id")\
        .execute()
    
    existing_bill_ids = {s['bill_id'] for s in existing_summaries.data}
    already_done = len(existing_bill_ids)
    
    bills_to_process = [b for b in bills if b['id'] not in existing_bill_ids]
    to_generate = len(bills_to_process)
    
    print(f"Status: {already_done} already completed, {to_generate} to generate\n")
    
    if to_generate == 0:
        print("✓ All bills already have summaries!")
        return
    
    # Estimate time and cost (gpt-4o-mini is much cheaper)
    estimated_minutes = (to_generate * 2) / 60  # ~2 seconds per bill
    estimated_cost = to_generate * 0.005  # ~$0.005 per summary with gpt-4o-mini
    
    print(f"Estimated time: {estimated_minutes:.1f} minutes")
    print(f"Estimated cost: ${estimated_cost:.2f} (using gpt-4o-mini)")
    print("\n" + "=" * 60 + "\n")
    
    # Confirm before proceeding
    confirm = input(f"Generate summaries for {to_generate} bills? (yes/no): ")
    if confirm.lower() != 'yes':
        print("Cancelled.")
        return
    
    print("\nGenerating summaries...\n")
    
    # Generate summaries
    success_count = 0
    error_count = 0
    
    for i, bill in enumerate(bills_to_process, 1):
        bill_number = bill['bill_number']
        print(f"[{i}/{to_generate}] {bill_number}...", end=" ", flush=True)
        
        try:
            summary = generate_summary_for_bill(
                bill['id'],
                bill['bill_number'],
                bill['title']
            )
            
            if summary:
                # Insert into bill_summaries table
                supabase.table("bill_summaries").insert({
                    "bill_id": bill['id'],
                    "summary": summary
                }).execute()
                
                print(f"✓ ({len(summary)} chars)")
                success_count += 1
            else:
                print("✗ No chunks")
                error_count += 1
            
            # Rate limiting
            time.sleep(1)
            
        except Exception as e:
            print(f"✗ Error: {str(e)[:50]}")
            error_count += 1
            time.sleep(3)
            continue
    
    # Summary
    print("\n" + "=" * 60)
    print(f"Complete! Success: {success_count}, Errors: {error_count}")
    print(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

if __name__ == "__main__":
    main()
