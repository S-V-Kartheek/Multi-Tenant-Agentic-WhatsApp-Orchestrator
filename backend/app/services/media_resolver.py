"""
services/media_resolver.py — Tenant media library resolver.

Maps customer query terms to tenant-specific media asset URLs.
Used by the LangGraph dispatcher node when the LLM decides to send
an image or document based on customer intent.
"""
import logging

logger = logging.getLogger(__name__)


def resolve_media_url(
    media_library: dict[str, str],
    query_term: str,
) -> str | None:
    """
    Find the best-matching media URL for a query term in the tenant's library.

    Matching strategy (in order of priority):
    1. Exact match on key
    2. Partial match — query_term appears in any key
    3. Partial match — any key appears in query_term

    Args:
        media_library: Tenant's dict of {term: url} from MongoDB
        query_term: The term the LLM extracted (e.g. "catalog", "sofa image")

    Returns:
        The media URL string, or None if no match found.
    """
    if not media_library or not query_term:
        return None

    query_lower = query_term.lower().strip()

    # 1. Exact match
    if query_lower in media_library:
        logger.debug(f"✅ Exact media match: {query_lower}")
        return media_library[query_lower]

    # 2. Query term contains a known key
    for key, url in media_library.items():
        if key.lower() in query_lower:
            logger.debug(f"✅ Partial media match (key in query): {key}")
            return url

    # 3. A known key contains the query term
    for key, url in media_library.items():
        if query_lower in key.lower():
            logger.debug(f"✅ Partial media match (query in key): {key}")
            return url

    logger.warning(f"⚠️  No media match found for query: '{query_term}'")
    return None


def get_filename_from_url(url: str, default: str = "document.pdf") -> str:
    """Extract a clean filename from a URL for document messages."""
    try:
        path = url.split("?")[0]   # Remove query params
        return path.split("/")[-1] or default
    except Exception:
        return default
