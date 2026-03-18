import subprocess
import json
import os
from datetime import datetime

SEARCH_QUERIES = [
    ("decathlon", "Decathlon avis", 15),
    ("decathlon", "Decathlon test", 10),
    ("intersport", "Intersport avis", 10),
    ("benchmark", "Decathlon vs Intersport", 10),
    ("cx", "Decathlon SAV retour", 10),
]

OUTPUT_DIR = "data/youtube_scrapes"
OUTPUT_COMMENTS_DIR = "data/youtube_comments"

def search_youtube(query, max_results=10):
    cmd = f'yt-dlp --quiet --print "%(id)s|%(title)s|%(upload_date)s|%(view_count)s|%(channel)s" "ytsearch{max_results}:{query}"'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip().split('\n') if result.stdout else []

def get_video_comments(video_url, max_comments=30):
    cmd = f'yt-dlp --write-comments --skip-download --json "{video_url}" 2>nul'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if not result.stdout:
        return []
    
    try:
        data = json.loads(result.stdout)
        comments = []
        
        if 'comments' in data:
            for comment in data['comments'][:max_comments]:
                comments.append({
                    "review_id": f"yt_comment_{comment.get('id', 'unknown')[:20]}",
                    "platform": "YouTube",
                    "brand": "youtube",
                    "post_type": "comment",
                    "text": comment.get('text', ''),
                    "author": comment.get('author', ''),
                    "likes": comment.get('like_count', 0),
                    "date": comment.get('timestamp', ''),
                    "video_url": video_url,
                })
        
        return comments
        
    except Exception as e:
        return []

def main():
    print("=" * 60)
    print("YouTube Scraper v2 - With Comments")
    print("=" * 60)
    
    all_videos = []
    all_comments = []
    
    for category, query, max_results in SEARCH_QUERIES:
        print(f"\n[{category}] Searching: {query}...")
        
        try:
            results = search_youtube(query, max_results)
            count = 0
            
            for line in results:
                if '|' in line:
                    parts = line.split('|')
                    if len(parts) >= 5:
                        video_id = parts[0]
                        url = f"https://youtube.com/watch?v={video_id}"
                        
                        video = {
                            "review_id": f"yt_{video_id}",
                            "platform": "YouTube",
                            "brand": category,
                            "post_type": "video",
                            "video_id": video_id,
                            "title": parts[1],
                            "date": parts[2],
                            "views": parts[3],
                            "channel": parts[4],
                            "url": url,
                        }
                        all_videos.append(video)
                        count += 1
                        
                        # Get comments for top videos
                        if count <= 3:
                            print(f"  Fetching comments from: {parts[1][:40]}...")
                            comments = get_video_comments(url)
                            all_comments.extend(comments)
                            print(f"    Got {len(comments)} comments")
                        
        except Exception as e:
            print(f"  Error: {e}")
    
    # Save videos
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    video_file = f"{OUTPUT_DIR}/youtube_{timestamp}.json"
    
    with open(video_file, "w", encoding="utf-8") as f:
        json.dump(all_videos, f, ensure_ascii=False, indent=2)
    
    # Save comments
    os.makedirs(OUTPUT_COMMENTS_DIR, exist_ok=True)
    comment_file = f"{OUTPUT_COMMENTS_DIR}/comments_{timestamp}.json"
    
    with open(comment_file, "w", encoding="utf-8") as f:
        json.dump(all_comments, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'=' * 60}")
    print(f"Total videos: {len(all_videos)}")
    print(f"Total comments: {len(all_comments)}")
    print(f"Videos saved: {video_file}")
    print(f"Comments saved: {comment_file}")
    print(f"{'=' * 60}")

if __name__ == "__main__":
    main()
