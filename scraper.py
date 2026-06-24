import requests
import tiktoken
import json
from bs4 import BeautifulSoup

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

# Define your target
test_url = "https://www.hunter.cuny.edu/students/registration/academic-calendar/"
extracted_text = scrape_hunter_page(test_url)

print(f"Extracted {len(extracted_text)} characters.")
print("-" * 40)
print(extracted_text[:500]) # Preview the first 500 characters

with open('calendar_full_text.txt', 'w', encoding='utf-8') as f:
    f.write(extracted_text)

print("Saved the entire page to calendar_full_text.txt!")

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

# Execute Chunking
document_chunks = chunk_text(extracted_text, max_tokens=200, overlap=25)

print("\n--- CHUNKING RESULT ---")
print(f"Created {len(document_chunks)} discrete chunks.")
print("-" * 40)
print("Preview of Chunk 1:")
print(document_chunks[0])
print("-" * 40)
print("Preview of Chunk 2:")
print(document_chunks[1])

def export_to_json(chunks, source_url, output_filename="campus_data.json"):
    # Create a list of dictionaries (structured data)
    structured_data = []
    
    for index, chunk in enumerate(chunks):
        document = {
            "chunk_id": f"cal_{index}",
            "source_url": source_url,
            "text": chunk
        }
        structured_data.append(document)
        
    # Write to a JSON file
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(structured_data, f, indent=4, ensure_ascii=False)
        
    print(f"\nSuccessfully exported {len(chunks)} chunks to {output_filename}!")

# Execute Step 3
export_to_json(document_chunks, test_url)