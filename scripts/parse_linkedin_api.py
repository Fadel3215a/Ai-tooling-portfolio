import os
import json
import textwrap

# Directories
OUTPUT_DIR = "research/linkedin-posts"
INPUT_JSON_PATH = "raw_linkedin_data.json"

# Whitelist of experts we are researching
WHITELISTED_AUTHORS = [
    "Chris Walker", "Amanda Natividad", "Anthony Pierri", "Guillaume Moubeche",
    "Dave Gerhardt", "Peep Laja", "Richard van der Blom", "Elena Verna",
    "Lashay Lewis", "Todd Clouser"
]

os.makedirs(OUTPUT_DIR, exist_ok=True)

def parse_linkedin_data():
    """
    Reads the Apify JSON export and converts each post 
    into a structured markdown file, filtering by whitelisted authors.
    """
    if not os.path.exists(INPUT_JSON_PATH):
        print(f"❌ Could not find '{INPUT_JSON_PATH}'.")
        return
        
    with open(INPUT_JSON_PATH, "r", encoding="utf-8") as f:
        try:
            posts = json.load(f)
        except json.JSONDecodeError:
            print("❌ Error: Invalid JSON file.")
            return

    print(f"Found {len(posts)} total posts. Filtering for 10 experts...")
    
    count = 0
    for i, post in enumerate(posts):
        author_data = post.get("author", {})
        author = author_data.get("name", "Unknown Author")
        
        # Only process if author is in our whitelisted set
        if author not in WHITELISTED_AUTHORS:
            continue
            
        content = post.get("content", "No content extracted.")
        engagement = post.get("engagement", {})
        likes = engagement.get("likes", 0) if engagement else 0
        comments = engagement.get("comments", 0) if engagement else 0
        url = post.get("linkedinUrl", "No URL")
        posted_at = post.get("postedAt", {}).get("date", "Unknown Date")
        
        # Generate a safe filename
        safe_author = author.lower().replace(" ", "_")
        filename = f"{safe_author}_post_{i+1}.md"
        filepath = os.path.join(OUTPUT_DIR, filename)

        markdown_content = textwrap.dedent(f"""\
        ---
        author: {author}
        date_extracted: {posted_at}
        metrics: 
          likes: {likes}
          comments: {comments}
        source_url: {url}
        ---

        # Post Content

        {content}

        ## Research Annotation
        **Pattern Identified:** [Analyze hook, structure, or methodology here]
        """)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(markdown_content)
            
        print(f"✅ Generated: {filename}")
        count += 1
            
    print(f"Finished. Generated {count} expert posts.")

if __name__ == "__main__":
    parse_linkedin_data()