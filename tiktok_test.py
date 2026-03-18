from TikTokApi import TikTokApi
import asyncio
import json

async def test_tiktok():
    print("Testing TikTokApi with #decathlon (5 videos)...")
    
    api = TikTokApi()
    
    try:
        print("Creating sessions...")
        await api.create_sessions(num_sessions=1, sleep_after=True)
        print("Sessions created!")
        
        hashtag = api.hashtag("decathlon")
        videos = []
        
        async for video in hashtag.videos(count=5):
            data = {
                "id": video.id,
                "desc": video.desc[:200] if video.desc else "",
                "diggCount": video.diggCount,
                "commentCount": video.commentCount,
                "shareCount": video.shareCount,
                "playCount": video.playCount,
                "author": video.author.unique_id if video.author else "",
            }
            videos.append(data)
            print(f"  OK: {data['desc'][:80]}...")
        
        print(f"\nSUCCESS: Got {len(videos)} videos")
        
        import os
        os.makedirs("data", exist_ok=True)
        with open("data/tiktok_test.json", "w") as f:
            json.dump(videos, f, indent=2)
        
        return True
        
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    asyncio.run(test_tiktok())

if __name__ == "__main__":
    main()
