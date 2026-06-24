import requests
import tiktoken
import json
from bs4 import BeautifulSoup

# ==========================================
# 1. FUNCTION DEFINITIONS (The Tools)
# ==========================================

def scrape_hunter_page(url):
    # Fetch the HTML content
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
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    # Parse with BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')

    # Remove scripts, styles, and common layout elements to clean the data
    for element in soup(['script', 'style', 'header', 'footer', 'nav', 'aside']):
        element.decompose()

    # Extract the remaining text
    raw_text = soup.get_text(separator=' ')
    
    # Clean up whitespace
    clean_text = ' '.join(raw_text.split())

    return clean_text

def chunk_text(text, max_tokens=200, overlap=25):
    # Initialize the tokenizer (cl100k_base is standard for modern LLMs)
    encoding = tiktoken.get_encoding("cl100k_base")
    
    # Encode the entire text into token integers
    tokens = encoding.encode(text)
    
    chunks = []
    i = 0
    
    # Iterate through tokens and create chunks with overlap
    while i < len(tokens):
        # Slice the token array to get our chunk
        chunk_tokens = tokens[i : i + max_tokens]
        
        # Decode back to a readable string
        chunk_text = encoding.decode(chunk_tokens)
        chunks.append(chunk_text)
        
        # Move forward by the chunk size minus the overlap
        i += (max_tokens - overlap)
        
    return chunks

# ==========================================
# 2. BATCH EXECUTION (The Action)
# ==========================================

# Define your master list of knowledge areas
target_urls = [
    "https://www.hunter.cuny.edu/students/registration/academic-calendar/",
    "https://hunter.cuny.edu/students/financial-aid/", 
    "https://www.hunter.cuny.edu/academics/departments-and-programs/"
]

all_structured_data = []
global_chunk_id = 0

print("Starting HawkAI Batch Scrape...")
print("-" * 40)

# Loop through every URL in our list
for url in target_urls:
    print(f"Scraping: {url}")
    try:
        # Extract and clean the text
        extracted_text = scrape_hunter_page(url)
        
        # Chop it into 200-token chunks with 25-token overlap
        chunks = chunk_text(extracted_text, max_tokens=200, overlap=25)
        
        # Format each chunk for the database
        for chunk in chunks:
            document = {
                "chunk_id": f"hawk_{global_chunk_id}",
                "source_url": url,
                "text": chunk
            }
            all_structured_data.append(document)
            global_chunk_id += 1
            
        print(f"  -> Success! Created {len(chunks)} chunks.")
    except Exception as e:
        print(f"  -> FAILED: {e}")

# Export everything into one master database file
output_filename = "campus_data.json"
with open(output_filename, 'w', encoding='utf-8') as f:
    json.dump(all_structured_data, f, indent=4, ensure_ascii=False)
    
print("-" * 40)
print(f"Batch complete! Exported {len(all_structured_data)} total chunks to {output_filename}.")