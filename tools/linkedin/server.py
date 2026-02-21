"""
LinkedIn MCP Server
====================
Post, read, and search LinkedIn — combining the official API (for writing)
with the unofficial Voyager API (for reading, since LinkedIn's read scopes
are closed to new developers as of 2026).

POSTING  → Official LinkedIn API (safe, ToS-compliant)
READING  → Unofficial linkedin-api Voyager library (ToS risk, use your own account)

Environment variables:
  For posting (official API):
    LINKEDIN_ACCESS_TOKEN   OAuth access token with w_member_social scope
    LINKEDIN_PERSON_URN     Your URN, e.g. urn:li:person:ABC123
                            Run linkedin_get_my_urn() to retrieve it.

  For reading (unofficial):
    LINKEDIN_EMAIL          Your LinkedIn login email
    LINKEDIN_PASSWORD       Your LinkedIn login password

  Getting an access token:
    1. Create an app at https://developer.linkedin.com
    2. Add the "Share on LinkedIn" product (self-service approved)
    3. Add OAuth redirect URI: https://localhost
    4. Run this in your browser (replace CLIENT_ID):
       https://www.linkedin.com/oauth/v2/authorization?response_type=code
         &client_id=CLIENT_ID&redirect_uri=https://localhost
         &scope=w_member_social%20openid%20profile%20email
    5. Exchange the code for a token using your client_id + client_secret.
"""

import json
import os
import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("linkedin")

LINKEDIN_API = "https://api.linkedin.com/v2"

_li_client = None


def _get_unofficial_client():
    """Return a cached unofficial linkedin-api client."""
    global _li_client
    if _li_client is not None:
        return _li_client
    try:
        from linkedin_api import Linkedin
    except ImportError:
        raise RuntimeError("linkedin-api not installed. Run: pip install linkedin-api")
    email = os.environ.get("LINKEDIN_EMAIL")
    password = os.environ.get("LINKEDIN_PASSWORD")
    if not email or not password:
        raise ValueError(
            "LINKEDIN_EMAIL and LINKEDIN_PASSWORD env vars required for read tools."
        )
    _li_client = Linkedin(email, password)
    return _li_client


# ─── WRITE TOOLS (Official API) ──────────────────────────────────────────────

@mcp.tool()
def linkedin_post(
    text: str,
    url: str = "",
    url_title: str = "",
    url_description: str = "",
) -> str:
    """Post content to your LinkedIn profile (official API, ToS-compliant).

    Requires LINKEDIN_ACCESS_TOKEN and LINKEDIN_PERSON_URN env vars.
    If you don't have your URN yet, call linkedin_get_my_urn() first.

    Args:
        text: The post body text (supports line breaks).
        url: Optional URL to attach as a link preview.
        url_title: Title for the link preview (defaults to the URL).
        url_description: Short description for the link preview.
    """
    token = os.environ.get("LINKEDIN_ACCESS_TOKEN")
    person_urn = os.environ.get("LINKEDIN_PERSON_URN")
    if not token:
        return json.dumps({"error": "LINKEDIN_ACCESS_TOKEN env var not set."})
    if not person_urn:
        return json.dumps({
            "error": "LINKEDIN_PERSON_URN not set. Call linkedin_get_my_urn() to get it."
        })

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
    }
    body: dict = {
        "author": person_urn,
        "commentary": text,
        "visibility": "PUBLIC",
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": [],
        },
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False,
    }
    if url:
        body["content"] = {
            "article": {
                "source": url,
                "title": url_title or url,
                "description": url_description,
            }
        }

    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(f"{LINKEDIN_API}/posts", headers=headers, json=body)
            if resp.status_code in (200, 201):
                post_id = resp.headers.get("x-restli-id", "unknown")
                return json.dumps({
                    "success": True,
                    "post_id": post_id,
                    "message": "Post published to LinkedIn successfully.",
                })
            return json.dumps({"error": f"HTTP {resp.status_code}", "detail": resp.text})
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def linkedin_get_my_urn() -> str:
    """Retrieve your LinkedIn Person URN via the official API.

    Call this once to get your URN, then set it as LINKEDIN_PERSON_URN.
    Requires LINKEDIN_ACCESS_TOKEN with openid + profile scope.
    """
    token = os.environ.get("LINKEDIN_ACCESS_TOKEN")
    if not token:
        return json.dumps({"error": "LINKEDIN_ACCESS_TOKEN env var not set."})
    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(
                "https://api.linkedin.com/v2/userinfo",
                headers={"Authorization": f"Bearer {token}"},
            )
            resp.raise_for_status()
            data = resp.json()
            sub = data.get("sub")
            urn = f"urn:li:person:{sub}" if sub else None
            return json.dumps({
                "person_urn": urn,
                "name": data.get("name"),
                "email": data.get("email"),
                "hint": f"Set this in your env: LINKEDIN_PERSON_URN={urn}",
            })
    except Exception as e:
        return json.dumps({"error": str(e)})


# ─── READ TOOLS (Unofficial Voyager API) ─────────────────────────────────────

@mcp.tool()
def linkedin_get_profile(username: str) -> str:
    """Get a LinkedIn profile by public username/slug.

    Returns name, headline, summary, experience, education, and skills.
    NOTE: Uses unofficial Voyager API. Requires LINKEDIN_EMAIL + LINKEDIN_PASSWORD.

    Args:
        username: Public profile slug (e.g. 'satya-nadella', not a full URL).
                  From https://linkedin.com/in/USERNAME
    """
    try:
        api = _get_unofficial_client()
        p = api.get_profile(username)
        return json.dumps({
            "name": f"{p.get('firstName', '')} {p.get('lastName', '')}".strip(),
            "headline": p.get("headline", ""),
            "summary": p.get("summary", ""),
            "location": p.get("geoLocationName", ""),
            "industry": p.get("industryName", ""),
            "followers": p.get("followersCount", 0),
            "connections": p.get("connectionsCount", 0),
            "profile_url": f"https://www.linkedin.com/in/{username}/",
            "experience": [
                {
                    "title": e.get("title", ""),
                    "company": e.get("companyName", ""),
                    "description": (e.get("description") or "")[:300],
                    "starts": e.get("timePeriod", {}).get("startDate", {}),
                    "ends": e.get("timePeriod", {}).get("endDate", {}),
                }
                for e in p.get("experience", [])[:6]
            ],
            "education": [
                {
                    "school": e.get("schoolName", ""),
                    "degree": e.get("degreeName", ""),
                    "field": e.get("fieldOfStudy", ""),
                }
                for e in p.get("education", [])
            ],
            "skills": [s.get("name", "") for s in p.get("skills", [])[:20]],
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def linkedin_get_profile_posts(username: str, limit: int = 10) -> str:
    """Get recent posts from a LinkedIn profile.

    NOTE: Uses unofficial Voyager API. Requires LINKEDIN_EMAIL + LINKEDIN_PASSWORD.

    Args:
        username: Public profile slug (e.g. 'satya-nadella').
        limit: Number of posts to return (default 10, max 50).
    """
    limit = min(max(1, limit), 50)
    try:
        api = _get_unofficial_client()
        posts = api.get_profile_posts(public_id=username, post_count=limit)
        results = []
        for post in posts:
            commentary = post.get("commentary") or {}
            text = commentary.get("text", "") if isinstance(commentary, dict) else str(commentary)
            social = post.get("socialDetail", {}).get("totalSocialActivityCounts", {})
            results.append({
                "text": text,
                "likes": social.get("numLikes", 0),
                "comments": social.get("numComments", 0),
                "reposts": social.get("numShares", 0),
            })
        return json.dumps(
            {"username": username, "count": len(results), "posts": results},
            ensure_ascii=False,
        )
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def linkedin_get_feed(limit: int = 10) -> str:
    """Get posts from your LinkedIn home feed.

    NOTE: Uses unofficial Voyager API. Requires LINKEDIN_EMAIL + LINKEDIN_PASSWORD.
    Official LinkedIn read scopes are closed to new developers as of 2026.

    Args:
        limit: Number of posts to return (default 10, max 50).
    """
    limit = min(max(1, limit), 50)
    try:
        api = _get_unofficial_client()
        posts = api.get_feed_posts(limit=limit)
        results = []
        for post in posts:
            actor = post.get("actor", {})
            name_obj = actor.get("name", {})
            name = name_obj.get("text", "Unknown") if isinstance(name_obj, dict) else str(name_obj)
            commentary = post.get("commentary") or {}
            text = commentary.get("text", "") if isinstance(commentary, dict) else str(commentary)
            social = post.get("socialDetail", {}).get("totalSocialActivityCounts", {})
            results.append({
                "author": name,
                "text": text,
                "likes": social.get("numLikes", 0),
                "comments": social.get("numComments", 0),
            })
        return json.dumps({"count": len(results), "posts": results}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def linkedin_search_people(query: str, limit: int = 10) -> str:
    """Search for people on LinkedIn by name, title, company, or keywords.

    NOTE: Uses unofficial Voyager API. Requires LINKEDIN_EMAIL + LINKEDIN_PASSWORD.

    Args:
        query: Search query (e.g. 'AI researcher Google', 'CTO fintech NYC').
        limit: Max results to return (default 10, max 25).
    """
    limit = min(max(1, limit), 25)
    try:
        api = _get_unofficial_client()
        results = api.search_people(keywords=query, limit=limit)
        people = []
        for p in results:
            people.append({
                "name": p.get("name", ""),
                "headline": p.get("headline", ""),
                "location": p.get("location", ""),
                "profile_url": f"https://www.linkedin.com/in/{p.get('public_id', '')}/",
                "public_id": p.get("public_id", ""),
            })
        return json.dumps(
            {"query": query, "count": len(people), "results": people},
            ensure_ascii=False,
        )
    except Exception as e:
        return json.dumps({"error": str(e)})


if __name__ == "__main__":
    mcp.run()
