from TikTokApi import TikTokApi
import json
import os
from datetime import datetime

HASHTAGS = {
    "decathlon": ["decathlon", "DecathlonFrance", "decathlonfr"],
    "intersport": ["intersport", "IntersportFrance"],
    "benchmark": ["decathlonvsintersport", "sportpascher"],
    "crise": ["decathlonfail", "decathlonpoubelle", "decathlonvelo"],
}

OUTPUT_DIR = "data/tiktok_scrapes"

def scrape_tiktok_category(api, category, hashtags, count=30):
    results = []
    
    for hashtag in hashtags:
        try:
            print(f"  Scraping #{hashtag}...")
            tag = api.hashtag.name(hashtag)
            videos = tag.videos(count=count)
            
            for video in videos:
                results.append({
                    "review_id": f"tt_{video.id}",
                    "platform": "TikTok",
                    "brand": category,
                    "post_type": "video",
                    "text": video.desc[:500] if video.desc else "",
                    "date": datetime.fromtimestamp(video.createTime).isoformat() if video.createTime else "",
                    "likes": video.diggCount,
                    "shares": video.shareCount,
                    "comments": video.commentCount,
                    "views": video.playCount,
                    "author": video.author.unique_id if video.author else "",
                    "author_followers": video.author.follower_count if video.author else 0,
                    "is_verified": video.author.verified if video.author else False,
                    "hashtags": [tag.name for tag in video.challenges] if video.challenges else [],
                })
            print(f"    ✓ Got {len(list(tag.videos(count=count)))} videos from #{hashtag}")
            
        except Exception as e:
            print(f"    ✗ Error on #{hashtag}: {e}")
            continue
    
    return results

def main():
    print("=" * 60)
    print("TikTok Scraper - Decathlon vs Intersport")
    print("=" * 60)
    
    api = TikTokApi()
    all_videos = []
    
    for category, hashtags in HASHTAGS.items():
        print(f"\n[{category.upper()}]")
        videos = scrape_tiktok_category(api, category, hashtags, 30)
        all_videos.extend(videos)
        print(f"  Total for {category}: {len(videos)} videos")
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{OUTPUT_DIR}/tiktok_{timestamp}.json"
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(all_videos, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'=' * 60}")
    print(f"Total videos collected: {len(all_videos)}")
    print(f"Saved to: {filename}")
    print(f"{'=' * 60}")
    
    return all_videos

if __name__ == "__main__":
    main()
