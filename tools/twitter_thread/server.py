"""
Twitter/X Thread MCP Server
============================
Unroll, read, and search Twitter/X threads — no official API key required.

Uses twikit, which speaks Twitter's internal GraphQL API (same as the browser).
Requires a real Twitter/X account. Cookies are cached after first login.

Environment variables:
  TWITTER_USERNAME   Your Twitter/X username (without @)
  TWITTER_EMAIL      Your Twitter/X account email
  TWITTER_PASSWORD   Your Twitter/X password
"""

import json
import re
import os
from datetime import datetime
from mcp.server.fastmcp import FastMCP
from twikit import Client

COOKIES_PATH = os.path.expanduser("~/.local/share/twitter-mcp/cookies.json")
os.makedirs(os.path.dirname(COOKIES_PATH), exist_ok=True)

mcp = FastMCP("twitter-thread")
_client: Client | None = None


async def get_client() -> Client:
    global _client
    if _client is not None:
        return _client
    c = Client("en-US")
    if os.path.exists(COOKIES_PATH):
        c.load_cookies(COOKIES_PATH)
    else:
        username = os.environ.get("TWITTER_USERNAME")
        email = os.environ.get("TWITTER_EMAIL")
        password = os.environ.get("TWITTER_PASSWORD")
        if not username or not password:
            raise ValueError(
                "TWITTER_USERNAME and TWITTER_PASSWORD env vars are required on first run."
            )
        await c.login(auth_info_1=username, auth_info_2=email, password=password)
        c.save_cookies(COOKIES_PATH)
    _client = c
    return _client


def extract_tweet_id(url_or_id: str) -> str:
    url_or_id = url_or_id.strip()
    m = re.search(r"(?:twitter\.com|x\.com)/\w+/status/(\d+)", url_or_id)
    if m:
        return m.group(1)
    if re.match(r"^\d+$", url_or_id):
        return url_or_id
    raise ValueError(f"Cannot extract tweet ID from: '{url_or_id}'")


def parse_created_at(s: str):
    try:
        return datetime.strptime(s, "%a %b %d %H:%M:%S +0000 %Y")
    except Exception:
        return datetime.min


def tweet_to_dict(tweet) -> dict:
    return {
        "id": str(tweet.id),
        "text": tweet.text,
        "created_at": tweet.created_at,
        "url": f"https://x.com/{tweet.user.screen_name}/status/{tweet.id}",
        "author": tweet.user.screen_name,
        "author_name": tweet.user.name,
        "likes": tweet.favorite_count,
        "retweets": tweet.retweet_count,
        "replies": tweet.reply_count,
        "media": [
            m.media_url_https
            for m in (tweet.media or [])
            if hasattr(m, "media_url_https")
        ],
    }


@mcp.tool()
async def thread_unroll(url: str) -> str:
    """Unroll a complete Twitter/X thread from any tweet URL in that thread.

    Reconstructs the full thread by fetching all self-replies from the author,
    starting from the root tweet. Returns all tweets in chronological order,
    combined full text for easy LLM consumption, and engagement stats.

    Use this whenever a user shares a Twitter/X thread URL and wants it
    summarized, analyzed, or extracted.

    Args:
        url: Any tweet URL in the thread (e.g. https://x.com/user/status/12345...)
    """
    try:
        tweet_id = extract_tweet_id(url)
    except ValueError as e:
        return json.dumps({"error": str(e)})

    try:
        client = await get_client()
        tweet = await client.get_tweet_by_id(tweet_id)
    except Exception as e:
        return json.dumps({"error": f"Failed to fetch tweet: {e}"})

    author = tweet.user.screen_name
    conversation_id = tweet.conversation_id or tweet_id

    # Fetch all self-replies in this conversation via search
    thread_tweets = []
    seen = set()
    try:
        results = await client.search_tweet(
            f"conversation_id:{conversation_id} from:{author}", product="Latest"
        )
        for t in results:
            if str(t.id) not in seen:
                seen.add(str(t.id))
                thread_tweets.append(t)
        # Try to get next page
        try:
            more = await results.next()
            for t in more:
                if str(t.id) not in seen:
                    seen.add(str(t.id))
                    thread_tweets.append(t)
        except Exception:
            pass
    except Exception:
        pass

    # Always include the originally fetched tweet
    if str(tweet.id) not in seen:
        thread_tweets.append(tweet)

    # Sort chronologically
    thread_tweets.sort(key=lambda t: parse_created_at(t.created_at))

    tweets_data = [tweet_to_dict(t) for t in thread_tweets]
    full_text = "\n\n".join(
        f"[{i + 1}/{len(tweets_data)}] {t['text']}"
        for i, t in enumerate(tweets_data)
    )

    return json.dumps(
        {
            "author": author,
            "author_name": thread_tweets[0].user.name if thread_tweets else "",
            "thread_url": f"https://x.com/{author}/status/{conversation_id}",
            "tweet_count": len(tweets_data),
            "total_likes": sum(t["likes"] for t in tweets_data),
            "total_retweets": sum(t["retweets"] for t in tweets_data),
            "tweets": tweets_data,
            "full_text": full_text,
        },
        ensure_ascii=False,
    )


@mcp.tool()
async def tweet_get(url_or_id: str) -> str:
    """Get the full details of a single tweet by URL or ID.

    Args:
        url_or_id: Tweet URL (https://x.com/user/status/...) or numeric tweet ID.
    """
    try:
        tweet_id = extract_tweet_id(url_or_id)
    except ValueError as e:
        return json.dumps({"error": str(e)})
    try:
        client = await get_client()
        tweet = await client.get_tweet_by_id(tweet_id)
        return json.dumps(tweet_to_dict(tweet), ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def twitter_search(query: str, limit: int = 20) -> str:
    """Search Twitter/X for tweets matching a query.

    Supports Twitter search operators: from:user, to:user, since:2024-01-01,
    until:2024-12-31, min_faves:100, -filter:retweets, etc.

    Args:
        query: Search query string with optional operators.
        limit: Max number of results (default 20, max 100).
    """
    limit = min(max(1, limit), 100)
    try:
        client = await get_client()
        results = await client.search_tweet(query, product="Latest")
        tweets = []
        seen = set()
        for t in results:
            if str(t.id) not in seen and len(tweets) < limit:
                seen.add(str(t.id))
                tweets.append(tweet_to_dict(t))
        return json.dumps(
            {"query": query, "count": len(tweets), "tweets": tweets},
            ensure_ascii=False,
        )
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def twitter_get_timeline(limit: int = 20) -> str:
    """Get recent tweets from your Twitter/X home timeline.

    Args:
        limit: Number of tweets to return (default 20, max 50).
    """
    limit = min(max(1, limit), 50)
    try:
        client = await get_client()
        results = await client.get_timeline()
        tweets = []
        seen = set()
        for t in results:
            if str(t.id) not in seen and len(tweets) < limit:
                seen.add(str(t.id))
                tweets.append(tweet_to_dict(t))
        return json.dumps({"count": len(tweets), "tweets": tweets}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)})


if __name__ == "__main__":
    mcp.run()
