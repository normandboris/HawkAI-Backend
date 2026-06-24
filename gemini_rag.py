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
Hunter College Academics | Departments and Programs. The School of Arts and Sciences offers over 70 undergraduate programs. The Computer Science department (CSCI) offers a BA and an MA program, focusing on software engineering, data science, and artificial intelligence. The main department office is located on the 10th floor of the North Building. For academic advising in the School of Education, students must schedule an appointment through Navigate.
"""

test_question = "What degrees does the Computer Science department offer?"

print("Asking HawkAI (via Modern Free Gemini API)...")
answer = generate_campus_answer(test_question, simulated_retrieved_chunk)
print("-" * 40)
print(answer)