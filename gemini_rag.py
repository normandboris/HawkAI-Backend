import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load the environment variables from the .env file
load_dotenv()

# Securely fetch the key
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("API Key not found. Please check your .env file.")

# Initialize the modern GenAI client
client = genai.Client(api_key=api_key)

def generate_campus_answer(user_question, retrieved_context):
    """
    Takes a user query and a retrieved context block, and returns a grounded answer.
    """
    
    # We use the modern Gemini 2.5 Flash model
    model_name = "gemini-2.5-flash"
    
    system_instruction = """
    You are HawkAI, the official digital assistant for Hunter College students.
    Your singular job is to answer student questions based EXCLUSIVELY on the provided campus data context.
    
    RULES:
    1. Do not use outside knowledge. If the answer is not contained in the context, output EXACTLY: "I'm sorry, I cannot find the answer to that in the current campus database."
    2. Be concise, direct, and helpful.
    3. Do not mention that you are reading from "context" or "retrieved data." Just give the answer.
    """

    # Format the prompt with our data
    user_message = f"""
    Context Data:
    {retrieved_context}
    
    Student Question: {user_question}
    """

    # Call the modern API with strict factual settings
    response = client.models.generate_content(
        model=model_name,
        contents=user_message,
        config=types.GenerateContentConfig(
            temperature=0.0, # CRITICAL: Mathematically eliminates creative variance
            max_output_tokens=300,
            system_instruction=system_instruction
        )
    )

    return response.text

# --- Test the Implementation ---
simulated_retrieved_chunk = """
8/5 Wednesday Withdrawal (W) period ends 8/19 Wednesday Last day of 5-Weeks classes Grade rosters available to faculty 8/21 Thursday Deadline to submit final grade rosters Upcoming Fall 2026 The Academic Calendar is subject to change at any time by official action of the University. 4/7 Tuesday Fall 2026 shopping cart opens in Schedule Builder 4/20 Monday Priority registration begins 4/21 Tuesday Continuing Doctoral and Graduate registration begins
"""

test_question = "When does the Fall 2026 shopping cart open?"

print("Asking HawkAI (via Modern Free Gemini API)...")
answer = generate_campus_answer(test_question, simulated_retrieved_chunk)
print("-" * 40)
print(answer)