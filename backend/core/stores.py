"""Process-local in-memory stores. Not persisted across restarts."""

news_store: list = []
conversations_store: dict = {}
profiles_store: dict = {}
open_chats_store: dict = {}

_news_cache: dict = {"articles": [], "fetched_at": None}


def get_news_cache() -> dict:
    return _news_cache


def set_news_cache(articles: list, fetched_at: float) -> None:
    global _news_cache
    _news_cache = {"articles": articles, "fetched_at": fetched_at}
