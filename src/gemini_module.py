# gemini_module.py
import google.generativeai as genai
import os
from dotenv import load_dotenv
load_dotenv()

genai.configure(api_key=os.environ["API_KEY"])

def generate_text(prompt):

    model = genai.GenerativeModel('gemini-2.0-flash')

    response = model.generate_content(prompt)
    return response.text

def summarize_transcript(transcript):
    prompt = f"""
        You are an expert summarizer. 
        Please provide a short summary of the following call transcript between a student and a counsellor. 
        Focus on the key topics discussed, the main concerns raised by the student, and any advice or actions suggested by the counsellor.
        Answer in 3-5 sentences.

        Transcript:
        {transcript}
        """
    return generate_text(prompt)

def analyze_sentiment(transcript):
    prompt = f"""
        You are an expert in sentiment analysis. 
        Analyze the following call transcript and describe the overall emotional tone of the student's responses. 
        Identify the key emotions (e.g., frustration, sadness, hope) and any noticeable changes in sentiment throughout the conversation.
        Answer in 3-5 sentences.

        Transcript:
        {transcript}
        """
    return generate_text(prompt)

def suggest_counsellor_response(transcript):
    prompt = f"""
        You are an experienced counsellor and communication coach. 
        Review the following call transcript between a student and a counsellor. 
        Based on the conversation, suggest additional or alternative responses that the counsellor could have used to provide better guidance to the student. 
        Answer in 3-5 points, one sentence each.

        Transcript:
        {transcript}
        """
    return generate_text(prompt)
