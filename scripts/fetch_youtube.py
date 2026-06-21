import os
import textwrap
import requests
import time

OUTPUT_DIR = "research/youtube-transcripts"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# WARNING: Paste your Supadata API key here (dont ever share it publicly)
SUPADATA_API_KEY = "sd_929f891eb41c700e86d7ed4e8f160283"

VIDEO_TARGETS = [
    # Existing (already committed)
    {"speaker": "Chris Walker", "video_title": "The CMO's Dilemma", "video_url": "https://www.youtube.com/watch?v=xOoYQVqizmM", "publish_date": "2024-02-14"},
    {"speaker": "Amanda Natividad", "video_title": "What Zero Click Marketing Is", "video_url": "https://www.youtube.com/watch?v=J98cUdZl-JQ", "publish_date": "2024-05-01"},
    {"speaker": "Anthony Pierri", "video_title": "Clear Positioning", "video_url": "https://www.youtube.com/watch?v=I2dNW1cEo2o", "publish_date": "2024-04-20"},
    {"speaker": "Guillaume Moubeche", "video_title": "Building lemlist", "video_url": "https://www.youtube.com/watch?v=zJ-wPBVLR3w", "publish_date": "2024-01-30"},
    # Corrected video urls (adding the rest)
    {"speaker": "Dave Gerhardt", "video_title": "B2B Communities", "video_url": "https://www.youtube.com/watch?v=obXLy-AU5m4", "publish_date": "2024-03-15"},
    {"speaker": "Peep Laja", "video_title": "How to Win Beyond Product", "video_url": "https://www.youtube.com/watch?v=UddBHQ0PuTg", "publish_date": "2024-04-10"},
    {"speaker": "Richard van der Blom", "video_title": "Cracking the LinkedIn Algorithm", "video_url": "https://www.youtube.com/watch?v=QVhwM6LS2p0", "publish_date": "2024-03-01"},
    {"speaker": "Elena Verna", "video_title": "The new AI growth playbook", "video_url": "https://www.youtube.com/watch?v=6qAB6aUMIeA", "publish_date": "2026-06-01"},
    {"speaker": "Lashay Lewis", "video_title": "BOFU Content System", "video_url": "https://www.youtube.com/watch?v=BA87rM-wIoc", "publish_date": "2024-03-20"},
    {"speaker": "Todd Clouser", "video_title": "Growth Marketing Camp", "video_url": "https://www.youtube.com/watch?v=q64rmr9wSyM", "publish_date": "2023-10-31"}
]

def fetch_and_format_transcript(video_data):
    """
    Fetches the transcript via Supadata API and formats it into a Markdown file.
    Handles asynchronous queue polling for large files.
    """
    speaker = video_data["speaker"]
    video_url = video_data["video_url"]
    
    print(f"Fetching transcript for {speaker} via Supadata...")
    
    endpoint = f"https://api.supadata.ai/v1/transcript?url={video_url}"
    headers = {
        "x-api-key": SUPADATA_API_KEY
    }
    
    try:
        response = requests.get(endpoint, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            # Check if this is an async job or immediate result
            if "jobId" in data:
                 print(f"[{speaker}] Job queued. Waiting for Supadata async processing...")
                 # Wait and poll for result
                 return poll_for_transcript(speaker, video_data, data["jobId"])
            
            # If immediate content returned, process it directly
            if "content" in data:
                 process_transcript_data(speaker, video_data, data)
                 return
                 
            # Fallback error for missing expected keys
            print(f"❌ Error fetching {speaker}: Unexpected response format: {data}")
            return
            
        else:
            print(f"❌ Error fetching {speaker}: Status Code {response.status_code} - {response.text}")
            return
        
    except Exception as e:
        print(f"❌ Error processing {speaker}: {str(e)}")

def poll_for_transcript(speaker, video_data, job_id):
    """
    Polls the Supadata batch API for the result of an asynchronous extraction job.
    """
    # Note: Using youtube batch get_batch_results endpoint based on docs
    endpoint = f"https://api.supadata.ai/v1/youtube/batch/results?jobId={job_id}"
    headers = {
        "x-api-key": SUPADATA_API_KEY
    }
    
    max_retries = 10
    retry_delay = 5
    
    for attempt in range(max_retries):
        print(f"[{speaker}] Polling job {job_id}... (Attempt {attempt+1}/{max_retries})")
        
        try:
             response = requests.get(endpoint, headers=headers)
             if response.status_code == 200:
                 data = response.json()
                 
                 # The batch response structure might contain the result directly or a status
                 # Note: The exact schema depends on the supadata batch API docs.
                 # Adjusting to a likely structure:
                 status = data.get("status", "").lower()
                 
                 if status == "completed":
                      # Assuming results are in a 'results' array or similar
                      results = data.get("results", [])
                      if results and "content" in results[0]:
                          process_transcript_data(speaker, video_data, results[0])
                          return
                      elif "content" in data:
                           process_transcript_data(speaker, video_data, data)
                           return
                      else:
                           print(f"❌ Error fetching {speaker}: Completed but missing content.")
                           return
                 elif status == "failed":
                      print(f"❌ Error fetching {speaker}: Job failed. {data}")
                      return
                 else:
                      # Still processing
                      time.sleep(retry_delay)
             else:
                 print(f"❌ Error polling {speaker}: Status Code {response.status_code} - {response.text}")
                 return
        except Exception as e:
             print(f"❌ Error polling {speaker}: {str(e)}")
             return
             
    print(f"❌ Error fetching {speaker}: Polling timeout.")

def process_transcript_data(speaker, video_data, data):
    """
    Takes successful JSON payload, formats timestamps, and writes to Markdown.
    """
    formatted_text = ""
    for entry in data.get("content", []):
        # Supadata returns offset in milliseconds, convert to MM:SS
        total_seconds = int(entry.get("offset", 0) / 1000)
        minutes, seconds = divmod(total_seconds, 60)
        timestamp = f"[{minutes:02d}:{seconds:02d}]"
        
        # Clean up text and append
        text = entry.get("text", "").strip()
        if text:
            formatted_text += f"{timestamp} {text}\n"
        
    markdown_content = textwrap.dedent(f"""\
    ---
    speaker: {speaker}
    video_title: {video_data['video_title']}
    publish_date: {video_data['publish_date']}
    source_url: {video_data['video_url']}
    extracted_via: supadata-api
    ---

    # Transcript Extraction
    
    {formatted_text}
    
    ## Research Annotation
    **Key Insight:** [Add your manual synthesis here after reading]
    """)
    
    video_id = video_data['video_url'].split("v=")[1]
    filename = f"{speaker.lower().replace(' ', '_')}_{video_id}.md"
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(markdown_content)
        
    print(f"✅ Saved: {filepath}")

if __name__ == "__main__":
    if SUPADATA_API_KEY == "ADD YOUR SUPADATA API KEY AT THE TOP":
        print("⚠️ Please insert your Supadata API key at the top of the script.")
    else:
        print("Starting Supadata YouTube Transcript Extraction...")
        for target in VIDEO_TARGETS:
            fetch_and_format_transcript(target)
        print("Extraction complete.")