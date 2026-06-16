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
    "movie":   ["mkv", "mp4", "avi", "1080p", "720p"],
    "music":   ["mp3", "flac", "wav", "ogg"],
    "course":  ["pdf", "mp4", "zip"],
    "software":["exe", "zip", "iso", "dmg"],
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


def build_dork(
    category: str,
    title: str,
    formats: Optional[List[str]] = None,
    excludes: Optional[List[str]] = None,
) -> str:
    title = title.strip()
    if not title:
        return ""

    if category == "free":
        return title

    if formats is None:
        formats = FORMATS_BY_CATEGORY.get(category, [])

    if excludes is None:
        excludes = EXCLUDE_DEFAULTS.get(category, [])

    parts = [f'intitle:"{title}"']

    if formats:
        if category in ("movie", "music") and any(f in ("1080p", "720p") for f in formats):
            ext_formats = [f for f in formats if f not in ("1080p", "720p")]
            res_formats = [f for f in formats if f in ("1080p", "720p")]
            ft_parts = [f"filetype:{f}" for f in ext_formats] + res_formats
        else:
            ft_parts = [f"filetype:{f}" for f in formats]

        if ft_parts:
            if len(ft_parts) == 1:
                parts.append(ft_parts[0])
            else:
                parts.append("(" + " OR ".join(ft_parts) + ")")

    for site in excludes:
        parts.append(f"-site:{site}")

    return " ".join(parts)


def get_category(slug: str) -> Optional[dict]:
    return next((c for c in CATEGORIES if c["slug"] == slug), None)
