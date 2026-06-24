import requests
import tiktoken
import json
import time
from datetime import datetime
from bs4 import BeautifulSoup

# Initialize tokenizer once globally (Fix #3)
ENCODING = tiktoken.get_encoding("cl100k_base")

# ==========================================
# 1. FUNCTION DEFINITIONS
# ==========================================

def scrape_hunter_page(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1'
    }
    
    # Add 10-second timeout (Fix #2)
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()

    # Parse with BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')

    # Extract the page title for metadata (Suggestion #2)
    page_title = soup.title.string.strip() if soup.title else "Hunter College Page"

    # Remove scripts, styles, and common layout elements to clean the data
    for element in soup(['script', 'style', 'header', 'footer', 'nav', 'aside']):
        element.decompose()

    # Extract the remaining text
    raw_text = soup.get_text(separator=' ')
    clean_text = ' '.join(raw_text.split())

    return clean_text, page_title

def chunk_text(text, max_tokens=200, overlap=25):
    tokens = ENCODING.encode(text)
    chunks = []
    i = 0
    
    while i < len(tokens):
        chunk_tokens = tokens[i : i + max_tokens]
        
        # Rename to avoid shadowing the function name (Fix #1)
        decoded_chunk = ENCODING.decode(chunk_tokens)
        chunks.append(decoded_chunk)
        
        i += (max_tokens - overlap)
        
    return chunks

# ==========================================
# 2. BATCH EXECUTION
# ==========================================

# Wrap in main guard (Fix #4)
if __name__ == "__main__":
    
    target_urls = [
        "https://www.hunter.cuny.edu/students/registration/academic-calendar/",
        "https://www.hunter.cuny.edu/students/financial-aid/", # Standardized URL
        "https://www.hunter.cuny.edu/academics/departments-and-programs/"
    ]

    all_structured_data = []
    global_chunk_id = 0
    
    # Generate an ISO timestamp for the database (Suggestion #2)
    scrape_timestamp = datetime.utcnow().isoformat()

    print("Starting HawkAI Batch Scrape (Production Version)...")
    print("-" * 40)

    for url in target_urls:
        print(f"Scraping: {url}")
        try:
            # Unpack the new tuple return value
            extracted_text, page_title = scrape_hunter_page(url)
            
            chunks = chunk_text(extracted_text, max_tokens=200, overlap=25)
            
            for chunk in chunks:
                document = {
                    "chunk_id": f"hawk_{global_chunk_id}",
                    "source_url": url,
                    "page_title": page_title,
                    "scraped_at": scrape_timestamp,
                    "text": chunk
                }
                all_structured_data.append(document)
                global_chunk_id += 1
                
            print(f"  -> Success! Created {len(chunks)} chunks.")
            
            # Polite delay between requests (Suggestion #1)
            time.sleep(2)
            
        except Exception as e:
            print(f"  -> FAILED: {e}")

    # Export
    output_filename = "campus_data.json"
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(all_structured_data, f, indent=4, ensure_ascii=False)
        
    print("-" * 40)
    print(f"Batch complete! Exported {len(all_structured_data)} total chunks to {output_filename}.")