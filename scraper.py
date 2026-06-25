import requests
import tiktoken
import json
import time
from datetime import datetime, timezone
from bs4 import BeautifulSoup

# Initialize tokenizer once globally
ENCODING = tiktoken.get_encoding("cl100k_base")

# ==========================================
# SCRAPE TARGET CONFIGURATION
# ==========================================

# Full scrape: run twice per semester (start + midpoint)
# Covers all Hunter Financial Aid content domains from the proposal
FULL_SCRAPE_URLS = [
    "https://www.hunter.cuny.edu/students/financial-aid/",                            # Deadlines, announcements, office hours
    "https://www.hunter.cuny.edu/students/financial-aid/faq",                         # Pre-built Q&A pairs
    "https://www.hunter.cuny.edu/students/financial-aid/financial-aid-eligibility/",  # Eligibility criteria and requirements
    "https://www.hunter.cuny.edu/students/financial-aid/financial-aid-types/",        # Types of aid
    "https://www.hunter.cuny.edu/students/financial-aid/apply-for-financial-aid/",     # Application process and instructions
    "https://www.hunter.cuny.edu/students/financial-aid/office-of-financial-aid/"     # Office contact info, hours, and location
]

# Lightweight scrape: run monthly — deadlines change more frequently than other content
DEADLINE_SCRAPE_URLS = [
    "https://www.hunter.cuny.edu/students/financial-aid/",  # Deadlines table and announcements only
]

# ==========================================
# FUNCTION DEFINITIONS
# ==========================================

def scrape_hunter_page(url):
    """
    Fetches and cleans a Hunter College page.
    Returns (clean_text, page_title).
    """
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

    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')

    # Extract page title for metadata
    page_title = soup.title.string.strip() if soup.title else "Hunter College Financial Aid"

    # Remove non-content elements
    for element in soup(['script', 'style', 'header', 'footer', 'nav', 'aside']):
        element.decompose()

    raw_text = soup.get_text(separator=' ')
    clean_text = ' '.join(raw_text.split())

    return clean_text, page_title


def chunk_text(text, max_tokens=200, overlap=25):
    """
    Splits text into overlapping token chunks.
    200-token chunks chosen because financial aid content is short and discrete —
    smaller chunks produce more targeted retrieval than the conventional 500-token default.
    25-token overlap preserves context at chunk boundaries.
    """
    tokens = ENCODING.encode(text)
    chunks = []
    i = 0

    while i < len(tokens):
        chunk_tokens = tokens[i: i + max_tokens]
        decoded_chunk = ENCODING.decode(chunk_tokens)
        chunks.append(decoded_chunk)
        i += (max_tokens - overlap)

    return chunks


def run_scrape(urls, scrape_label="full"):
    """
    Runs a scrape job over a list of URLs.
    Returns a list of structured chunk documents ready for Supabase insertion.
    """
    all_structured_data = []
    global_chunk_id = 0
    scrape_timestamp = datetime.now(timezone.utc).isoformat()

    print(f"Starting HawkAI {scrape_label.upper()} Scrape — {scrape_timestamp}")
    print("-" * 50)

    for url in urls:
        print(f"Scraping: {url}")
        try:
            extracted_text, page_title = scrape_hunter_page(url)
            chunks = chunk_text(extracted_text, max_tokens=200, overlap=25)

            for chunk in chunks:
                document = {
                    "chunk_id": f"hawk_{scrape_label}_{global_chunk_id}",
                    "source_url": url,
                    "page_title": page_title,
                    "scraped_at": scrape_timestamp,
                    "scrape_type": scrape_label,  # Tracks which schedule produced this chunk
                    "text": chunk
                }
                all_structured_data.append(document)
                global_chunk_id += 1

            print(f"  -> Success! {len(chunks)} chunks created.")
            time.sleep(2)  # Polite delay between requests

        except Exception as e:
            print(f"  -> FAILED: {e}")

    return all_structured_data


# ==========================================
# BATCH EXECUTION
# ==========================================

if __name__ == "__main__":
    import sys

    # Pass "monthly" as a command-line arg to run the lightweight deadline scrape
    # Default (no args) runs the full semester scrape
    # Usage:
    #   python scraper.py          -> full scrape (run at semester start + midpoint)
    #   python scraper.py monthly  -> deadline scrape (run monthly)

    mode = sys.argv[1] if len(sys.argv) > 1 else "full"

    if mode == "monthly":
        data = run_scrape(DEADLINE_SCRAPE_URLS, scrape_label="monthly")
        output_filename = "campus_data_deadlines.json"
    else:
        data = run_scrape(FULL_SCRAPE_URLS, scrape_label="full")
        output_filename = "campus_data.json"

    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    print("-" * 50)
    print(f"Scrape complete! {len(data)} total chunks exported to {output_filename}.")
