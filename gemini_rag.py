import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load environment variables from .env file
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("API key not found. Please check your .env file.")

client = genai.Client(api_key=api_key)

def generate_financial_aid_answer(user_question, retrieved_chunks):
    """
    Takes a student question and a list of retrieved chunks,
    and returns a grounded answer with source citation.
    """

    # Build context block using both page_title and source_url from your scraper
    context_block = ""
    for i, chunk in enumerate(retrieved_chunks):
        # Use .get() in case a chunk is missing the title
        title = chunk.get('page_title', 'Hunter College Financial Aid')
        url = chunk.get('source_url', 'Unknown URL')
        text = chunk.get('text', '')
        
        context_block += f"[Source {i+1}: {title} | {url}]\n{text}\n\n"

    system_instruction = """You are HawkAI, the official financial aid assistant for Hunter College students.
Your job is to answer student questions about Hunter College financial aid EXCLUSIVELY using the provided context.

RULES:
1. Only use information found in the provided context. Do not use outside knowledge.
2. If the answer is not in the context, respond EXACTLY with:
   "I could not find information about that in the Hunter College financial aid pages. Please contact the Financial Aid office directly or visit hunter.cuny.edu/students/financial-aid."
3. Always cite your source URL at the end of your answer in this format: (Source: [URL])
4. Be concise and direct. Students need quick answers.
5. Do not mention that you are reading from "context" or "retrieved data." Just answer."""

    user_message = f"""Context:
{context_block}

Student Question: {user_question}"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=user_message,
        config=types.GenerateContentConfig(
            temperature=0.0,        # Eliminates creative variance
            max_output_tokens=400,
            system_instruction=system_instruction
        )
    )

    return response.text


# --- Test the Implementation ---
if __name__ == "__main__":
    print("Loading real scraped data from campus_data.json...")
    
    try:
        # Load the file created by scraper.py
        with open('campus_data.json', 'r', encoding='utf-8') as f:
            all_chunks = json.load(f)
            
        # Simulate database search by just grabbing the first 3 chunks
        # (In the real app, Mahdi/Mohammed will use pgvector to find the *most relevant* chunks)
        simulated_retrieved_chunks = all_chunks[:3]
        
        print(f"Successfully loaded {len(all_chunks)} total chunks. Testing with top 3.\n")
        print("-" * 50)
        
        # Test 1: Question answerable from context (should cite source)
        test_q1 = "When is the priority deadline for filing the FAFSA application?"
        print("Test 1 — Answerable question:")
        print(f"Q: {test_q1}")
        print(f"A: {generate_financial_aid_answer(test_q1, simulated_retrieved_chunks)}")
        print("-" * 50)

        # Test 2: Ensure the hallucination guardrail still works
        test_q2 = "What will the FAFSA income limit be in 2026?"
        print("Test 2 — Unanswerable question (should refuse, not hallucinate):")
        print(f"Q: {test_q2}")
        print(f"A: {generate_financial_aid_answer(test_q2, simulated_retrieved_chunks)}")

    except FileNotFoundError:
        print("ERROR: campus_data.json not found! Please run `python scraper.py` first.")