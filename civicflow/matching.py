"""Lightweight lexical similarity for possibly related reports (a triage hint, not a verdict)."""
import unicodedata

# small set of generic words removed before comparison
GENERIC = {
    "near", "opposite", "beside", "behind", "next", "to", "the", "a", "an", "in", "at", "of", "on", "and",
    "road", "rd", "street", "st", "main", "area", "no", "number", "is", "are", "by", "from", "with",
}

LOCATION_STRONG = 0.55
LOCATION_VERY_STRONG = 0.82
DESC_WITH_STRONG = 0.16
DESC_WITH_VERY_STRONG = 0.10


def tokens(text: str) -> set:
    """Unicode-aware tokens: letters, combining marks (Telugu/Devanagari vowel signs) and digits."""
    out, cur = [], []
    for ch in text.casefold():
        if unicodedata.category(ch)[0] in "LMN":
            cur.append(ch)
        elif cur:
            out.append("".join(cur))
            cur = []
    if cur:
        out.append("".join(cur))
    return {t for t in out if t not in GENERIC}


def jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def compare(loc_a, desc_a, loc_b, desc_b):
    loc = jaccard(tokens(loc_a), tokens(loc_b))
    desc = jaccard(tokens(desc_a), tokens(desc_b))
    related = (loc >= LOCATION_STRONG and desc >= DESC_WITH_STRONG) or (
        loc >= LOCATION_VERY_STRONG and desc >= DESC_WITH_VERY_STRONG
    )
    return related, loc, desc


def find_cluster(conn, category: str, is_demo: int, location: str, description: str):
    """Return the cluster_id of the best matching earlier report, or None.
    Only same category and same demo/non-demo partition are considered."""
    rows = conn.execute(
        "SELECT cluster_id, location, description FROM complaints WHERE category = ? AND is_demo = ?",
        (category, is_demo),
    ).fetchall()
    best, best_score = None, -1.0
    for r in rows:
        related, loc, desc = compare(location, description, r["location"], r["description"])
        if related and loc + desc > best_score:
            best, best_score = r["cluster_id"], loc + desc
    return best
