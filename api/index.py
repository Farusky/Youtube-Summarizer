from fastapi import FastAPI, Query
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai
import os
import re

app = FastAPI()

# Configure Gemini (We will set the API_KEY in Vercel settings later)
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

def extract_video_id(url):
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url)
    return match.group(1) if match else None

@app.get("/api/summarize")
def summarize(url: str = Query(..., description="YouTube URL")):
    video_id = extract_video_id(url)
    if not video_id:
        return {"error": "Invalid YouTube URL"}

    try:
        # 1. Get Transcript
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        transcript_text = " ".join([i['text'] for i in transcript_list])

        # 2. Summarize with Gemini
        prompt = f"Summarize this YouTube transcript into key bullet points for a student: {transcript_text}"
        response = model.generate_content(prompt)
        
        return {"summary": response.text}
    except Exception as e:
        return {"error": str(e)}