from dotenv import load_dotenv
import os
import openai
import re
import time
import sqlite3
from setup import connect_db
from models.audio_translation import translate_audio 

# Load environment variables from .env file
load_dotenv()

# Set OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

db_name = 'automated_interviews.db'
def connect_db():
    return sqlite3.connect(db_name)

def get_chatgpt_response(prompt):
    """
    Sends a prompt to the OpenAI API to get a response using the latest library version.
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.7
        )
        return response.choices[0].message['content']
    except Exception as e:
        print(f"Error with ChatGPT API call: {e}")
        return None
    
def save_similarity_results(answer_id, response_data, response_time):
    """
    Inserts similarity analysis results into the similarity_results table.
    """
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO similarity_results (
            answer_id,
            relevance_score, clarity_score, depth_score, keywords_coverage_score,
            confidence_score, experience_score, response_time, extracted_keywords,
            matching_keywords, useful_information, key_strengths, areas_for_improvement
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        answer_id,
        response_data.get("relevance_score"),
        response_data.get("clarity_score"),
        response_data.get("depth_score"),
        response_data.get("keywords_coverage_score"),
        response_data.get("confidence_score"),
        response_data.get("experience_score"),
        response_time,
        response_data.get("extracted_keywords"),
        response_data.get("matching_keywords"),
        response_data.get("useful_information"),
        response_data.get("key_strengths"),
        response_data.get("areas_for_improvement")
    ))
    conn.commit()
    conn.close()
    print(f"Similarity results saved for answer_id {answer_id}")

# Get ChatGPT response function
def get_chatgpt_response(prompt, model="gpt-3.5-turbo"):
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=500
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        print(f"Error with ChatGPT API call: {e}")
        return None

# Assess similarity function with question type-based prompts
def assess_similarity_with_chatgpt(answer_id, question, keywords, audio_path, question_type, template_answer=None):
    # Translate the audio to text first
    translation = translate_audio(audio_path)

    # Define different prompts based on question type
    if question_type == "role-based":
        prompt = (
            f"You are an AI assistant evaluating a candidate's answer based on a question related to the role they're applying for. (Position specific)\n\n"
            f"Question: {question}\n"
            f"Template Answer: {template_answer}\n"
            f"Answer: {translation}\n"
            f"Important keywords to consider: {', '.join(keywords)}.\n\n"
            "Evaluate the candidate's answer by comparing it to the template answer and the provided keywords.\n"
            "Give higher scores to answers with matching or has similar meanings to the provided keywords, and align or similar to the template answer.\n"
            "Use the following structure for your response: (Scores must be from 0 to 1)\n\n"
            "**Scoring Matrix**:\n"
            "- Relevance: [Score]\n"
            "- Clarity: [Score]\n"
            "- Depth of Information: [Score]\n"
            "- Keywords Coverage: [Score]\n\n"
            "**Extracted Information**:\n"
            "- Extracted Keywords:\n"
            "- Matching Keywords:\n"
            "- Alignment with Template Answer:\n"
            "- Key strengths:\n"
            "- Areas for improvement:\n\n"
        )
    else:  # Assume "personal" question type
        prompt = (
            f"You are an AI assistant evaluating a candidate's answer based on a personal interview question.\n\n"
            f"Question: {question}\n"
            f"Answer: {translation}\n\n"
            "Evaluate the candidate's answer based on relevance between the question and answer, confidence in the answer, experience level, depth of detail, and clarity.\n"
            "Extract the main mentioned keywords in the answer (e.g: names, organizations, tools)"
            "Use the following structure for your response: (Scores must be from 0 to 1)\n\n"
            "**Scoring Matrix**:\n"
            "- Relevance: [Score]\n"
            "- Clarity: [Score]\n"
            "- Depth of Information: [Score]\n"
            "- Extracted Keywords:\n"
            "**Extracted Information**:\n"
            "- Key strengths:\n"
        )

    # Send prompt to ChatGPT and retrieve response
    start_time = time.time()
    chatgpt_response = get_chatgpt_response(prompt)
    end_time = time.time()
    response_time = end_time - start_time

    if chatgpt_response:
        # Parse the response for scores and keywords
        relevance_score = re.search(r"Relevance: ([0-9]*\.?[0-9]+)", chatgpt_response)
        clarity_score = re.search(r"Clarity: ([0-9]*\.?[0-9]+)", chatgpt_response)
        depth_score = re.search(r"Depth of Information: ([0-9]*\.?[0-9]+)", chatgpt_response)
        keywords_coverage_score = re.search(r"Keywords Coverage: ([0-9]*\.?[0-9]+)", chatgpt_response)
        
        # More fields specific to each question type
        confidence_score = re.search(r"Confidence: ([0-9]*\.?[0-9]+)", chatgpt_response) if question_type == "personal" else None
        experience_score = re.search(r"Experience: ([0-9]*\.?[0-9]+)", chatgpt_response) if question_type == "personal" else None

        # Prepare result dictionary for storage
        results = {
            "relevance_score": float(relevance_score.group(1)) if relevance_score else None,
            "clarity_score": float(clarity_score.group(1)) if clarity_score else None,
            "depth_score": float(depth_score.group(1)) if depth_score else None,
            "keywords_coverage_score": float(keywords_coverage_score.group(1)) if keywords_coverage_score else None,
            "confidence_score": float(confidence_score.group(1)) if confidence_score else None,
            "experience_score": float(experience_score.group(1)) if experience_score else None,
            "extracted_keywords": ", ".join(re.findall(r"Extracted Keywords: (.*)", chatgpt_response)),
            "matching_keywords": ", ".join(re.findall(r"Matching Keywords: (.*)", chatgpt_response)),
            "useful_information": re.search(r"Does the answer provide enough useful information\? (Yes|No)", chatgpt_response).group(1) if re.search(r"Does the answer provide enough useful information\? (Yes|No)", chatgpt_response) else None,
            "key_strengths": re.search(r"Key strengths: (.*)", chatgpt_response).group(1).strip() if re.search(r"Key strengths: (.*)", chatgpt_response) else None,
            "areas_for_improvement": re.search(r"Areas for improvement: (.*)", chatgpt_response).group(1).strip() if re.search(r"Areas for improvement: (.*)", chatgpt_response) else None
        }

        # Insert results into the database
        save_similarity_results(answer_id, results, response_time)

    return None