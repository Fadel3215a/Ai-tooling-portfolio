import os
import textwrap
import requests

OUTPUT_DIR = "research/youtube-transcripts"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# WARNING: Paste your Supadata API key here (dont ever share it)
SUPADATA_API_KEY = "sd_929f891eb41c700e86d7ed4e8f160283"

VIDEO_TARGETS = [
    {
        "speaker": "Chris Walker",
        "video_title": "Chris Walker on the CMO's Dilemma, Attribution, and Modern GTM Strategy",
        "video_url": "https://www.youtube.com/watch?v=xOoYQVqizmM", 
        "publish_date": "2024-02-14"
    },
    {
        "speaker": "Amanda Natividad",
        "video_title": "What Zero Click Marketing Actually Is",
        "video_url": "https://www.youtube.com/watch?v=J98cUdZl-JQ",
        "publish_date": "2024-05-01"
    },
    {
        "speaker": "Anthony Pierri",
        "video_title": "Why Clear Positioning Is the #1 Driver of B2B Business Growth",
        "video_url": "https://www.youtube.com/watch?v=I2dNW1cEo2o",
        "publish_date": "2024-04-20"
    },
    {
        "speaker": "Guillaume Moubeche",
        "video_title": "Building lemlist Into a Global Sales Powerhouse",
        "video_url": "https://www.youtube.com/watch?v=zJ-wPBVLR3w",
        "publish_date": "2024-01-30"
    }
]

def fetch_and_format_transcript(video_data):
    """
    Fetches the transcript via Supadata API and formats it into a Markdown file.
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
        
        if response.status_code != 200:
            print(f"❌ Error fetching {speaker}: {response.text}")
            return
            
        data = response.json()
        
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
        source_url: {video_url}
        extracted_via: supadata-api
        ---

        # Transcript Extraction
        
        {formatted_text}
        
        ## Research Annotation
        **Key Insight:** [Add your manual synthesis here after reading]
        """)
        
        video_id = video_url.split("v=")[1]
        filename = f"{speaker.lower().replace(' ', '_')}_{video_id}.md"
        filepath = os.path.join(OUTPUT_DIR, filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(markdown_content)
            
        print(f"✅ Saved: {filepath}")
        
    except Exception as e:
        print(f"❌ Error processing {speaker}: {str(e)}")

if __name__ == "__main__":
    if SUPADATA_API_KEY == "YOUR_SUPADATA_API_KEY_HERE":
        print("⚠️ Please insert your Supadata API key at the top of the script.")
    else:
        print("Starting Supadata YouTube Transcript Extraction...")
        for target in VIDEO_TARGETS:
            fetch_and_format_transcript(target)
        print("Extraction complete.")