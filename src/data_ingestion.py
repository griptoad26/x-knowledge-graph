"""
Data ingestion module for X (Twitter) exports.
Handles loading and parsing JSON exports from X archives.

X Export Structure (2024 format):
├── your_twitter_archive/
│   ├── data/
│   │   ├── tweet.js        ← Your tweets (singular!)
│   │   ├── like.js         ← Your likes
│   │   ├── reply.js        ← Your replies
│   │   └── retweet.js      ← Your retweets
│   └── manifest.js
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import pandas as pd


def load_x_export(export_path: Path) -> Dict[str, List[Dict]]:
    """
    Load all data from X export directory.
    
    Supports multiple X export formats:
    1. New format (2024): data/tweet.js, data/like.js, data/reply.js, data/retweet.js
    2. Old format: tweets.js, like.js (may include replies/retweets)
    3. Multi-part: tweets/tweets.part0.js
    
    Returns:
        Dict with keys: "tweets", "likes", "retweets"
    """
    export_path = Path(export_path)
    data = {
        "tweets": [],
        "likes": [],
        "retweets": [],
        "replies": []
    }
    
    # Log what we're looking for
    print(f"🔍 Searching for X export files in: {export_path}")
    
    # Method 1: Try new format (data/tweet.js, data/like.js, etc.)
    data_loaded = _load_new_format(export_path, data)
    
    # Method 2: If new format didn't work, try old format
    if not data_loaded:
        print("📋 Trying old format (tweets.js, like.js)...")
        _load_old_format(export_path, data)
    
    # Log results
    print(f"✅ Loaded: {len(data['tweets'])} tweets, {len(data['likes'])} likes, {len(data['retweets'])} retweets")
    
    return data


def _load_new_format(export_path: Path, data: Dict) -> bool:
    """Load X export using new format: data/tweet.js, data/like.js, etc."""
    
    data_dir = export_path / "data"
    if not data_dir.exists():
        print(f"⚠️ No 'data/' subdirectory found in {export_path}")
        return False
    
    print(f"📁 Found 'data/' directory: {data_dir}")
    
    files_found = {}
    
    # Check for tweet.js (your posts)
    tweet_file = data_dir / "tweet.js"
    if tweet_file.exists():
        print(f"✅ Found: {tweet_file}")
        tweets = _parse_x_tweet_file(tweet_file)
        if tweets:
            # Separate original tweets from replies
            original_tweets = []
            replies = []
            for t in tweets:
                if t.get("in_reply_to_status_id"):
                    replies.append(t)
                else:
                    original_tweets.append(t)
            
            data["tweets"] = original_tweets
            data["replies"] = replies
            files_found["tweet.js"] = len(tweets)
    
    # Check for like.js
    like_file = data_dir / "like.js"
    if like_file.exists():
        print(f"✅ Found: {like_file}")
        likes = _parse_x_like_file(like_file)
        if likes:
            data["likes"] = likes
            files_found["like.js"] = len(likes)
    
    # Check for retweet.js
    retweet_file = data_dir / "retweet.js"
    if retweet_file.exists():
        print(f"✅ Found: {retweet_file}")
        retweets = _parse_x_tweet_file(retweet_file)  # Same format as tweet.js
        if retweets:
            data["retweets"] = retweets
            files_found["retweet.js"] = len(retweets)
    
    # Check for reply.js (some exports have this separate)
    reply_file = data_dir / "reply.js"
    if reply_file.exists():
        print(f"✅ Found: {reply_file}")
        replies = _parse_x_tweet_file(reply_file)
        if replies:
            data["replies"].extend(replies)
            files_found["reply.js"] = len(replies)
    
    if files_found:
        print(f"📊 New format files loaded: {files_found}")
        return True
    
    print("⚠️ No files found in data/ directory")
    return False


def _load_old_format(export_path: Path, data: Dict) -> bool:
    """Load X export using old format: tweets.js, like.js"""
    
    # Check for tweets.js or tweet.js in root
    tweet_files = [
        export_path / "tweets.js",
        export_path / "tweet.js",
        export_path / "tweets.json"
    ]
    
    for tweet_file in tweet_files:
        if tweet_file.exists():
            print(f"✅ Found old format: {tweet_file}")
            tweets = _parse_x_tweet_file(tweet_file)
            if tweets:
                data["tweets"] = tweets
                return True
    
    # Check for like.js or likes.js
    like_files = [
        export_path / "like.js",
        export_path / "likes.js",
        export_path / "likes.json"
    ]
    
    for like_file in like_files:
        if like_file.exists():
            print(f"✅ Found old format: {like_file}")
            likes = _parse_x_like_file(like_file)
            if likes:
                data["likes"] = likes
    
    return False


def _parse_x_tweet_file(filepath: Path) -> List[Dict]:
    """
    Parse tweet.js or retweet.js file.
    
    X format:
    window.YTD.tweet = [
      {"tweet": { "id": "123", "full_text": "Hello", ... }},
      {"tweet": { "id": "456", "full_text": "World", ... }}
    ];
    
    Or direct JSON:
    [
      {"tweet": { "id": "123", ... }},
      ...
    ]
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remove JavaScript wrapper if present
        if content.startswith('window.YTD'):
            # Handle window.YTD.tweet = [...];
            # Handle window.YTD.tweets.part0 = [...];
            content = re.sub(r'^window\.YTD\.\w+\s*=\s*', '', content)
        
        # Remove trailing semicolons
        content = content.rstrip(';')
        
        # Parse JSON
        parsed = json.loads(content)
        
        # Handle different structures
        tweets = []
        
        if isinstance(parsed, list):
            for item in parsed:
                if isinstance(item, dict):
                    if "tweet" in item:
                        # Format: [{"tweet": {...}}, ...]
                        tweet_data = item["tweet"]
                        tweet_data["_raw"] = item  # Keep original
                        tweets.append(tweet_data)
                    else:
                        # Format: [{...}, {...}] - direct tweet objects
                        tweets.append(item)
        
        elif isinstance(parsed, dict):
            if "tweet" in parsed:
                # Format: {"tweet": {...}}
                tweets.append(parsed["tweet"])
        
        print(f"📄 Parsed {len(tweets)} tweets from {filepath.name}")
        return tweets
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON error in {filepath.name}: {e}")
        print(f"   First 300 chars: {content[:300]}")
        return []
    except Exception as e:
        print(f"❌ Error reading {filepath.name}: {e}")
        return []


def _parse_x_like_file(filepath: Path) -> List[Dict]:
    """
    Parse like.js file.
    
    X format:
    window.YTD.like = [
      {"like": { "tweet": { "id": "123", "full_text": "Hello", ... }}},
      ...
    ];
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remove JavaScript wrapper if present
        if content.startswith('window.YTD'):
            content = re.sub(r'^window\.YTD\.\w+\s*=\s*', '', content)
        
        content = content.rstrip(';')
        
        parsed = json.loads(content)
        
        likes = []
        
        if isinstance(parsed, list):
            for item in parsed:
                if isinstance(item, dict):
                    if "like" in item and "tweet" in item["like"]:
                        # Format: [{"like": {"tweet": {...}}}, ...]
                        likes.append(item["like"]["tweet"])
                    elif "tweet" in item:
                        # Format: [{"tweet": {...}}, ...]
                        likes.append(item["tweet"])
                    else:
                        # Direct format
                        likes.append(item)
        
        print(f"📄 Parsed {len(likes)} likes from {filepath.name}")
        return likes
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON error in {filepath.name}: {e}")
        print(f"   First 300 chars: {content[:300]}")
        return []
    except Exception as e:
        print(f"❌ Error reading {filepath.name}: {e}")
        return []


def load_grok_export(export_path: Path) -> Optional[List[Dict]]:
    """Load Grok conversation exports if available"""
    export_path = Path(export_path)
    
    # Common Grok export file names
    grok_files = [
        "grok.js",
        "grok.json", 
        "conversations.js",
        "grok_conversations.js",
        "data/grok.js",
        "data/conversations.js"
    ]
    
    for filename in grok_files:
        filepath = export_path / filename
        if filepath.exists():
            print(f"✅ Found Grok export: {filepath}")
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Remove JS wrapper if present
                content = re.sub(r'^window\.YTD\.\w+\s*=\s*', '', content)
                content = content.rstrip(';')
                
                data = json.loads(content)
                if isinstance(data, list):
                    print(f"📄 Loaded {len(data)} Grok conversations")
                    return data
            except Exception as e:
                print(f"❌ Error reading Grok file: {e}")
    
    print("⚠️ No Grok export found")
    return None


def _find_file(directory: Path, filenames: List[str]) -> Optional[Path]:
    """Find a file in directory, checking multiple possible names and locations"""
    directory = Path(directory)
    
    # Check root directory
    for filename in filenames:
        path = directory / filename
        if path.exists():
            return path
    
    # Check subdirectories
    for subdir in directory.iterdir():
        if subdir.is_dir():
            for filename in filenames:
                path = subdir / filename
                if path.exists():
                    return path
    
    # Check data subdirectory
    data_dir = directory / "data"
    if data_dir.exists():
        for filename in filenames:
            path = data_dir / filename
            if path.exists():
                return path
    
    return None


def normalize_text(text: str) -> str:
    """Clean and normalize tweet text"""
    if not text:
        return ""
    
    # Remove URLs
    text = re.sub(r'http\S+|www\.\S+', '', text)
    # Remove mentions
    text = re.sub(r'@\w+', '', text)
    # Remove hashtag symbols
    text = re.sub(r'#', '', text)
    # Remove extra whitespace
    text = ' '.join(text.split())
    # Remove emojis
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"
        u"\U0001F300-\U0001F5FF"
        u"\U0001F680-\U0001F6FF"
        u"\U0001F1E0-\U0001F1FF"
        "]+", flags=re.UNICODE)
    text = emoji_pattern.sub('', text)
    
    return text.strip()


def extract_timestamps(df: pd.DataFrame) -> pd.DataFrame:
    """Convert created_at to datetime - handles X export formats"""
    if 'created_at' in df.columns:
        # Try multiple date formats X uses
        formats = [
            "%a %b %d %H:%M:%S %z %Y",    # "Wed Jan 02 12:00:00 +0000 2024"
            "%Y-%m-%dT%H:%M:%S.%fZ",      # ISO format
            "%Y-%m-%dT%H:%M:%SZ",         # ISO format without microseconds
            "%Y-%m-%d %H:%M:%S",          # SQL format
        ]
        
        for fmt in formats:
            parsed = pd.to_datetime(df['created_at'], format=fmt, errors='coerce')
            # Check how many successfully parsed
            valid_count = parsed.notna().sum()
            if valid_count > df['created_at'].notna().sum() * 0.5:  # >50% success
                df['created_at'] = parsed
                break
        else:
            # Fallback to infer
            df['created_at'] = pd.to_datetime(df['created_at'], infer_datetime_format=True, errors='coerce')
    return df
