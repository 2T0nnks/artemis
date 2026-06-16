from typing import List, Optional

CATEGORIES = [
    {"slug": "free",    "label": "Livre",   "emoji": "🔓"},
    {"slug": "book",    "label": "Livro",   "emoji": "📚"},
    {"slug": "manga",   "label": "Mangá",   "emoji": "📖"},
    {"slug": "movie",   "label": "Filme",   "emoji": "🎬"},
    {"slug": "music",   "label": "Música",  "emoji": "🎵"},
    {"slug": "course",  "label": "Curso",   "emoji": "🎓"},
    {"slug": "software","label": "Software","emoji": "💿"},
]

FORMATS_BY_CATEGORY = {
    "book":    ["pdf", "epub", "mobi", "djvu"],
    "manga":   ["cbz", "cbr", "pdf", "zip"],
    "movie":   ["mkv", "mp4", "avi", "1080p", "720p", "4k"],
    "music":   ["mp3", "flac", "wav", "ogg", "aac"],
    "course":  ["pdf", "mp4", "zip", "inurl:torrent"],
    "software":["exe", "zip", "iso", "dmg", "inurl:download", "inurl:release"],
    "free":    [],
}

PLACEHOLDERS = {
    "free":    'site:gov.br filetype:pdf  ou  inurl:login "admin"',
    "book":    "Ex: Clean Code, Harry Potter, O Senhor dos Anéis...",
    "manga":   "Ex: Naruto, One Piece, Berserk...",
    "movie":   "Ex: Inception, Interstellar, Parasita...",
    "music":   "Ex: Pink Floyd, Taylor Swift, Daft Punk...",
    "course":  "Ex: Python para iniciantes, Machine Learning...",
    "software":"Ex: Photoshop, Visual Studio Code, VLC...",
}

EXCLUDE_DEFAULTS = {
    "book":    ["amazon.com", "goodreads.com", "audible.com"],
    "manga":   ["amazon.com", "crunchyroll.com"],
    "movie":   ["imdb.com", "rottentomatoes.com"],
    "music":   ["spotify.com", "apple.com", "youtube.com"],
    "course":  ["udemy.com", "coursera.org", "linkedin.com"],
    "software":["microsoft.com", "apple.com"],
    "free":    [],
}


_INLINE_OPERATORS = {"inurl:", "intitle:", "intext:", "site:", "filetype:", "before:", "after:"}


def build_dork(
    category: str,
    title: str,
    formats: Optional[List[str]] = None,
    excludes: Optional[List[str]] = None,
    extra_operators: Optional[str] = None,
) -> str:
    title = title.strip()
    if not title:
        return ""

    if category == "free":
        base = title
        if extra_operators:
            base = base + " " + extra_operators.strip()
        return base

    if formats is None:
        formats = FORMATS_BY_CATEGORY.get(category, [])

    if excludes is None:
        excludes = EXCLUDE_DEFAULTS.get(category, [])

    parts = [f'intitle:"{title}"']

    if formats:
        inline = [f for f in formats if any(f.startswith(op) for op in _INLINE_OPERATORS)]
        ext_formats = [f for f in formats if f not in inline]

        if category in ("movie", "music"):
            res = [f for f in ext_formats if f in ("1080p", "720p", "4k")]
            ext_formats = [f for f in ext_formats if f not in res]
            ft_parts = [f"filetype:{f}" for f in ext_formats] + res + inline
        else:
            ft_parts = [f"filetype:{f}" for f in ext_formats] + inline

        if ft_parts:
            if len(ft_parts) == 1:
                parts.append(ft_parts[0])
            else:
                parts.append("(" + " OR ".join(ft_parts) + ")")

    for site in excludes:
        parts.append(f"-site:{site}")

    if extra_operators:
        parts.append(extra_operators.strip())

    return " ".join(parts)


def get_category(slug: str) -> Optional[dict]:
    return next((c for c in CATEGORIES if c["slug"] == slug), None)
