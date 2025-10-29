# ExplainThisBill - Canadian Legislation Explainer

AI-powered tool to explain Canadian federal bills in plain English.

## Setup

### 1. Clone the repository
```bash
git clone <your-repo-url>
cd ExplainThisBill
```

### 2. Create virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Create `.env` file
Create a `.env` file in the project root with:
```
OPENAI_API_KEY=your_openai_key_here
SUPABASE_URL=your_supabase_url_here
SUPABASE_SERVICE_KEY=your_supabase_service_key_here
```

### 5. Ingest bills (one-time setup)
```bash
python ingest_bills.py
```

## Usage

### Test vector search
```bash
python test_search.py
```

### Add more bills
Edit `MAX_BILLS` in `ingest_bills.py`, then run it again.

## Project Structure

- `fetch_bills.py` - Fetch bills from OpenParliament API
- `chunking.py` - Split bill text into chunks
- `embeddings.py` - Generate OpenAI embeddings
- `supabase_client.py` - Database operations
- `ingest_bills.py` - Main ingestion pipeline
- `test_search.py` - Test vector search

## Tech Stack

- Python 3.13
- Supabase (PostgreSQL + pgvector)
- OpenAI embeddings API
- OpenParliament API