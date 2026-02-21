"""
Video Understanding MCP Server (local stdio)
"""
import json
import re
import math
import httpx
from mcp.server.fastmcp import FastMCP
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import VideoUnavailable

DEFAULT_LANGUAGES = ["en", "en-US", "en-GB"]
MAX_TRANSCRIPT_CHARS = 100_000
OEMBED_URL = "https://www.youtube.com/oembed"
CHUNK_DURATION_SECONDS = 300

mcp = FastMCP("video-understanding")


def extract_video_id(url_or_id: str) -> str:
    url_or_id = url_or_id.strip()
    for pattern in [
        r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/v/|youtube\.com/shorts/)([a-zA-Z0-9_-]{11})",
        r"^([a-zA-Z0-9_-]{11})$",
    ]:
        m = re.search(pattern, url_or_id)
        if m:
            return m.group(1)
    raise ValueError(f"Could not extract YouTube video ID from: '{url_or_id}'")


def fmt(seconds: int) -> str:
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def fetch_metadata(video_id: str) -> dict:
    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(OEMBED_URL, params={
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "format": "json",
            })
            resp.raise_for_status()
            d = resp.json()
            return {
                "video_id": video_id,
                "title": d.get("title", "Unknown"),
                "author": d.get("author_name", "Unknown"),
                "channel_url": d.get("author_url", ""),
                "thumbnail": d.get("thumbnail_url", ""),
                "url": f"https://www.youtube.com/watch?v={video_id}",
            }
    except Exception as e:
        return {"video_id": video_id, "title": "Unknown", "author": "Unknown",
                "url": f"https://www.youtube.com/watch?v={video_id}", "error": str(e)}


def fetch_transcript(video_id: str, languages=None, translate_to=None):
    if languages is None:
        languages = DEFAULT_LANGUAGES
    ytt = YouTubeTranscriptApi()
    try:
        tl = ytt.list(video_id)
    except VideoUnavailable:
        raise ValueError(f"Video '{video_id}' is unavailable.")
    except Exception as e:
        raise ValueError(f"Cannot access transcripts: {e}")

    transcript = None
    for lang in languages:
        for t in tl:
            if t.language_code.startswith(lang) and not t.is_generated:
                transcript = t; break
        if transcript: break
    if not transcript:
        for lang in languages:
            for t in tl:
                if t.language_code.startswith(lang) and t.is_generated:
                    transcript = t; break
            if transcript: break
    if not transcript:
        for t in tl:
            transcript = t; break
    if not transcript:
        raise ValueError(f"No transcripts found for '{video_id}'.")

    if translate_to and translate_to != transcript.language_code:
        try:
            transcript = transcript.translate(translate_to)
        except Exception:
            pass

    fetched = transcript.fetch()
    segments = [{"text": s.text, "start": round(s.start, 2), "duration": round(s.duration, 2)} for s in fetched]
    full_text = " ".join(s["text"] for s in segments)
    if len(full_text) > MAX_TRANSCRIPT_CHARS:
        full_text = full_text[:MAX_TRANSCRIPT_CHARS] + "... [truncated]"
    duration = round(segments[-1]["start"] + segments[-1]["duration"]) if segments else 0
    return {
        "segments": segments,
        "full_text": full_text,
        "language": transcript.language_code,
        "is_generated": transcript.is_generated,
        "duration_seconds": duration,
        "duration": fmt(duration),
        "word_count": len(full_text.split()),
        "segment_count": len(segments),
    }


def build_chapters(segments, chunk_seconds=CHUNK_DURATION_SECONDS):
    if not segments:
        return []
    total = segments[-1]["start"] + segments[-1]["duration"]
    num = max(1, math.ceil(total / chunk_seconds))
    chapters = []
    idx = 0
    for i in range(num):
        start = i * chunk_seconds
        end = min((i + 1) * chunk_seconds, total)
        texts = []
        while idx < len(segments) and segments[idx]["start"] < end:
            texts.append(segments[idx]["text"]); idx += 1
        if texts:
            text = " ".join(texts)
            chapters.append({
                "chapter": i + 1,
                "time_range": f"{fmt(int(start))} - {fmt(int(end))}",
                "text": text,
                "word_count": len(text.split()),
            })
    return chapters


@mcp.tool()
def video_understand(url: str, languages: str = "en", chapter_minutes: int = 5) -> str:
    """Deeply understand a YouTube video: metadata, chaptered transcript, and statistics.

    This is the PRIMARY tool when a user shares a YouTube URL. Returns everything
    needed to analyze, summarize, or discuss the video.

    Args:
        url: YouTube URL or 11-character video ID.
        languages: Comma-separated language codes in priority order (default: 'en').
        chapter_minutes: Minutes per chapter for structuring the transcript (default: 5).
    """
    try:
        video_id = extract_video_id(url)
    except ValueError as e:
        return json.dumps({"error": str(e)})

    metadata = fetch_metadata(video_id)
    lang_list = [l.strip() for l in languages.split(",") if l.strip()]
    try:
        td = fetch_transcript(video_id, languages=lang_list)
    except ValueError as e:
        return json.dumps({"error": str(e), "metadata": metadata})

    chapters = build_chapters(td["segments"], chunk_seconds=max(60, min(chapter_minutes * 60, 1800)))
    return json.dumps({
        "metadata": metadata,
        "transcript_info": {
            "language": td["language"],
            "is_auto_generated": td["is_generated"],
            "duration": td["duration"],
            "duration_seconds": td["duration_seconds"],
            "word_count": td["word_count"],
            "total_chapters": len(chapters),
        },
        "chapters": chapters,
        "full_text": td["full_text"],
    }, ensure_ascii=False)


@mcp.tool()
def video_get_transcript(url: str, languages: str = "en", translate_to: str = "") -> str:
    """Get the full transcript of a YouTube video with timestamps.

    Args:
        url: YouTube URL or video ID.
        languages: Comma-separated language codes (default: 'en').
        translate_to: Language code to translate into, e.g. 'es'. Leave empty for original.
    """
    try:
        video_id = extract_video_id(url)
    except ValueError as e:
        return json.dumps({"error": str(e)})

    lang_list = [l.strip() for l in languages.split(",") if l.strip()]
    translate = translate_to.strip() or None
    try:
        td = fetch_transcript(video_id, languages=lang_list, translate_to=translate)
    except ValueError as e:
        return json.dumps({"error": str(e)})

    lines = [f"[{fmt(int(s['start']))}] {s['text']}" for s in td["segments"]]
    return json.dumps({
        "video_id": video_id,
        "language": td["language"],
        "is_auto_generated": td["is_generated"],
        "duration": td["duration"],
        "word_count": td["word_count"],
        "segment_count": td["segment_count"],
        "timestamped_transcript": "\n".join(lines),
        "full_text": td["full_text"],
    }, ensure_ascii=False)


@mcp.tool()
def video_get_metadata(url: str) -> str:
    """Get metadata for a YouTube video (title, author, thumbnail) without fetching the transcript.

    Args:
        url: YouTube URL or video ID.
    """
    try:
        video_id = extract_video_id(url)
    except ValueError as e:
        return json.dumps({"error": str(e)})
    return json.dumps(fetch_metadata(video_id), ensure_ascii=False)


@mcp.tool()
def video_search_transcript(url: str, query: str, languages: str = "en") -> str:
    """Search within a YouTube video's transcript for specific terms or phrases.

    Returns matching segments with surrounding context and timestamps.

    Args:
        url: YouTube URL or video ID.
        query: Term or phrase to find (case-insensitive).
        languages: Comma-separated language codes (default: 'en').
    """
    try:
        video_id = extract_video_id(url)
    except ValueError as e:
        return json.dumps({"error": str(e)})

    lang_list = [l.strip() for l in languages.split(",") if l.strip()]
    try:
        td = fetch_transcript(video_id, languages=lang_list)
    except ValueError as e:
        return json.dumps({"error": str(e)})

    query_lower = query.lower()
    results = []
    seen = set()
    for i, seg in enumerate(td["segments"]):
        if query_lower in seg["text"].lower():
            for j in range(max(0, i - 2), min(len(td["segments"]), i + 3)):
                if j not in seen:
                    seen.add(j)
                    results.append({
                        "text": td["segments"][j]["text"],
                        "timestamp": fmt(int(td["segments"][j]["start"])),
                        "seconds": round(td["segments"][j]["start"]),
                        "is_match": j == i,
                    })

    output = {"video_id": video_id, "query": query,
              "total_matches": sum(1 for r in results if r["is_match"]), "results": results}
    if not results:
        output["note"] = f"No matches found for '{query}'."
    return json.dumps(output, ensure_ascii=False)


if __name__ == "__main__":
    mcp.run()
