import subprocess
import json
import os
from datetime import datetime

OUTPUT_DIR = "data/youtube_comments"

def get_video_comments(video_url, max_comments=50):
    cmd = f'yt-dlp --write-comments --skip-download --json "{video_url}"'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if not result.stdout:
        return []
    
    try:
        data = json.loads(result.stdout)
        comments = []
        
        if 'comments' in data:
            for comment in data['comments'][:max_comments]:
                comments.append({
                    "review_id": f"yt_comment_{comment.get('id', 'unknown')}",
                    "platform": "YouTube",
                    "brand": "decathlon",  # Will be updated
                    "post_type": "comment",
                    "text": comment.get('text', ''),
                    "author": comment.get('author', ''),
                    "likes": comment.get('like_count', 0),
                    "date": comment.get('timestamp', ''),
                    "video_url": video_url,
                })
        
        return comments
        
    except Exception as e:
        print(f"  Error parsing: {e}")
        return []

def main():
    print("=" * 60)
    print("YouTube Comments Scraper - Decathlon vs Intersport")
    print("=" * 60)
    
    video_urls = [
        "https://www.youtube.com/watch?v=XXXXXXXX",  # Add video IDs here
    ]
    
    all_comments = []
    
    for url in video_urls:
        print(f"\nFetching comments from: {url}")
        comments = get_video_comments(url)
        print(f"  Got {len(comments)} comments")
        all_comments.extend(comments)
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{OUTPUT_DIR}/comments_{timestamp}.json"
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(all_comments, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'=' * 60}")
    print(f"Total comments: {len(all_comments)}")
    print(f"Saved to: {filename}")

if __name__ == "__main__":
    main()
