from fastapi import FastAPI, Query
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai
import os
import re

app = FastAPI()

# Configure Gemini
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

def extract_video_id(url):
    # Regex to handle all types of YT links
    match = re.search(r"(?:v=|\/|be\/)([0-9A-Za-z_-]{11})", url)
    return match.group(1) if match else None

@app.get("/api/summarize")
def summarize(url: str = Query(..., description="YouTube URL")):
    video_id = extract_video_id(url)
    if not video_id:
        return {"error": "Invalid YouTube URL format."}

    try:
        # FIX: We use list_transcripts first, then fetch. 
        # This is more stable in recent versions of the library.
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        # This automatically finds the best available transcript (manual or auto-generated)
        transcript = transcript_list.find_transcript(['en']) 
        transcript_data = transcript.fetch()
        
        # Join the text pieces together
        full_text = " ".join([entry['text'] for entry in transcript_data])

        # Summarize with Gemini
        prompt = f"Summarize the following YouTube video transcript into clear study notes for a student. Use bullet points: {full_text}"
        response = model.generate_content(prompt)
        
        return {"summary": response.text}

    except Exception as e:
        error_str = str(e)
        # Better error messages for the user
        if "Subtitles are disabled" in error_str:
            return {"error": "Captions are disabled for this video."}
        elif "Cookies" in error_str or "blocked" in error_str.lower():
            return {"error": "YouTube is temporarily blocking the server. Try a different video."}
        return {"error": f"API Error: {error_str}"}
