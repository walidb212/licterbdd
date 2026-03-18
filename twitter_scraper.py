import snscrape.modules.twitter as sntwitter
import json
import os
from datetime import datetime

SEARCH_QUERIES = [
    "Decathlon lang:fr",
    "Intersport lang:fr",
    '"Decathlon vs Intersport" lang:fr',
    "Decathlon SAV lang:fr",
    "#Decathlon lang:fr",
]

OUTPUT_DIR = "data/twitter_scrapes"

def scrape_twitter(query, max_results=50):
    tweets = []
    
    print(f"  Searching: {query}")
    
    try:
        for i, tweet in enumerate(sntwitter.TwitterSearchScraper(query).get_items()):
            if i >= max_results:
                break
            
            tweets.append({
                "review_id": f"tw_{tweet.id}",
                "platform": "Twitter",
                "brand": "twitter",
                "post_type": "tweet",
                "text": tweet.content[:500],
                "date": tweet.date.isoformat() if tweet.date else "",
                "likes": tweet.likeCount,
                "retweets": tweet.retweetCount,
                "replies": tweet.replyCount,
                "views": tweet.viewCount if hasattr(tweet, 'viewCount') else 0,
                "author": tweet.user.username,
                "author_followers": tweet.user.followersCount,
                "author_verified": tweet.user.verified,
                "url": tweet.url,
                "hashtags": [tag for tag in tweet.entities.get('hashtags', [])],
                "query": query,
            })
        
        print(f"    Got {len(tweets)} tweets")
        
    except Exception as e:
        print(f"    Error: {e}")
    
    return tweets

def main():
    print("=" * 60)
    print("Twitter/X Scraper - snscrape")
    print("=" * 60)
    
    all_tweets = []
    
    for query in SEARCH_QUERIES:
        tweets = scrape_twitter(query, 50)
        all_tweets.extend(tweets)
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{OUTPUT_DIR}/twitter_{timestamp}.json"
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(all_tweets, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'=' * 60}")
    print(f"Total tweets: {len(all_tweets)}")
    print(f"Saved to: {filename}")
    print(f"{'=' * 60}")

if __name__ == "__main__":
    main()
