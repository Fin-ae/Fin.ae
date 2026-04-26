import os
import re
from urllib.parse import quote_plus, unquote

from dotenv import load_dotenv

load_dotenv()


def _encode_mongo_url(url: str) -> str:
    scheme_match = re.match(r'^(mongodb(?:\+srv)?://)', url)
    if not scheme_match:
        return url
    scheme = scheme_match.group(1)
    rest = url[len(scheme):]
    at_idx = rest.rfind('@')
    if at_idx == -1:
        return url
    userinfo, hostinfo = rest[:at_idx], rest[at_idx + 1:]
    colon_idx = userinfo.find(':')
    if colon_idx == -1:
        return url
    user, password = userinfo[:colon_idx], userinfo[colon_idx + 1:]
    return f"{scheme}{quote_plus(unquote(user))}:{quote_plus(unquote(password))}@{hostinfo}"


GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "").strip()
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile").strip()
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

NEWS_API_KEY = os.environ.get("NEWS_API_KEY", "").strip()
NEWS_API_URL = "https://eventregistry.org/api/v1/article/getArticles"
NEWS_CACHE_TTL = 1800  # 30 minutes

_raw_mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
MONGO_URL = _encode_mongo_url(_raw_mongo_url)

_scheme_match = re.match(r'^(mongodb(?:\+srv)?://)', MONGO_URL)
if _scheme_match:
    _rest = MONGO_URL[len(_scheme_match.group(1)):]
    _at = _rest.rfind('@')
    _colon = _rest.find(':')
    _user = _rest[:_colon] if _colon != -1 else '?'
    _host = _rest[_at + 1:] if _at != -1 else '?'
    print(f"[DEBUG] MONGO_URL parsed — user={_user!r} host={_host!r} raw_len={len(_raw_mongo_url)}", flush=True)

DB_NAME = os.environ.get("DB_NAME", "finae")
JWT_SECRET = os.environ.get("JWT_SECRET", "finae-dev-secret-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_DAYS = 7
