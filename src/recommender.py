import csv
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict, field

# Scoring weights (original recipe). Weight-shift experiment in README: GENRE_WEIGHT = 1.0, ENERGY_WEIGHT = 2.0.
GENRE_WEIGHT = 2.0
MOOD_WEIGHT = 1.0
ENERGY_WEIGHT = 1.0
ACOUSTIC_WEIGHT = 0.5

# Ranking strategies: same rules, different point values. Every mode tops out at 4.5,
# so scores stay comparable across modes. "balanced" is the original recipe above.
STRATEGIES = {
    "genre-first":    {"genre": 3.0, "mood": 0.5, "energy": 0.75, "acoustic": 0.25},
    "mood-first":     {"genre": 1.0, "mood": 2.0, "energy": 1.0,  "acoustic": 0.5},
    "energy-focused": {"genre": 1.0, "mood": 0.5, "energy": 2.5,  "acoustic": 0.5},
}
MODES = ["balanced", *STRATEGIES]

def get_weights(mode: str = "balanced") -> Dict[str, float]:
    """Return the base-rule weights for a ranking mode ("balanced" reads the constants above)."""
    if mode == "balanced":
        return {"genre": GENRE_WEIGHT, "mood": MOOD_WEIGHT, "energy": ENERGY_WEIGHT, "acoustic": ACOUSTIC_WEIGHT}
    if mode not in STRATEGIES:
        raise ValueError(f"Unknown mode {mode!r}. Choose from: {', '.join(MODES)}")
    return STRATEGIES[mode]

# Extended-attribute rules. Each one only applies when the user sets that preference,
# so profiles without them score exactly as before (max 4.5).
TAG_WEIGHT = 0.25          # per shared mood tag
TAG_MAX = 0.75             # cap, so tags can't outweigh the main mood match
DECADE_WEIGHT = 0.5        # exact decade; half for a neighboring decade
LANGUAGE_WEIGHT = 0.5
POPULARITY_WEIGHT = 0.5    # scaled by popularity (or by obscurity for "hidden gems")
# allow_explicit=False is a hard filter, not a penalty: a -2.0 penalty still let the
# only hip-hop song (explicit) rank #1 for a "clean" hip-hop fan.

# Diversity penalty (opt-in): subtracted for each already-picked song that shares the
# artist or genre, so the top 5 doesn't fill up with one artist or one genre.
ARTIST_PENALTY = 1.0
GENRE_PENALTY = 0.5
# Hard caps: the penalty alone still let 3 lofi songs into Chill Lofi's top 5, because
# the third one was far enough ahead to absorb it.
MAX_PER_ARTIST = 2
MAX_PER_GENRE = 2

@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float
    # Extended attributes (defaults keep older code and tests working)
    popularity: int = 0                 # 0-100, hand-estimated
    release_decade: int = 0             # e.g. 1980 for the 1980s
    mood_tags: List[str] = field(default_factory=list)  # detailed moods, e.g. ["devotional", "mystical"]
    language: str = ""                  # "english", "amharic", "instrumental", ...
    explicit: bool = False

@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool
    # Optional extended preferences (None = no preference, rule is skipped)
    favorite_mood_tags: Optional[List[str]] = None
    preferred_decade: Optional[int] = None
    preferred_language: Optional[str] = None
    prefers_popular: Optional[bool] = None   # True = hits, False = hidden gems
    allow_explicit: bool = True

class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song], mode: str = "balanced", diverse: bool = False):
        self.songs = songs
        self.mode = mode
        self.diverse = diverse

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        """Rank songs with the same recipe as recommend_songs (ties to lower id) and return the top k."""
        by_id = {song.id: song for song in self.songs}
        results = recommend_songs(asdict(user), [asdict(song) for song in self.songs],
                                  k=k, mode=self.mode, diverse=self.diverse)
        return [by_id[song["id"]] for song, _, _ in results]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        """Return the song's score and the reasons behind it, e.g. 'Score 4.39: genre match (+2.0), ...'."""
        score, reasons = score_song(asdict(user), asdict(song), get_weights(self.mode))
        return f"Score {score:.2f}: " + ", ".join(reasons)

def load_songs(csv_path: str) -> List[Dict]:
    """Read songs.csv into a list of dicts, converting numbers, splitting mood tags, and parsing explicit."""
    print(f"Loading songs from {csv_path}...")
    float_fields = ("energy", "tempo_bpm", "valence", "danceability", "acousticness")
    int_fields = ("id", "popularity", "release_decade")

    songs = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            # csv gives every value as a string; convert numbers so we can do math on them
            for name in int_fields:
                row[name] = int(row[name])
            for name in float_fields:
                row[name] = float(row[name])
            # "devotional;mystical;yearning" -> ["devotional", "mystical", "yearning"]
            row["mood_tags"] = [tag.strip() for tag in row["mood_tags"].split(";") if tag.strip()]
            row["explicit"] = row["explicit"].strip().lower() == "true"
            songs.append(row)
    return songs

def score_song(user_prefs: Dict, song: Dict, weights: Optional[Dict[str, float]] = None) -> Tuple[float, List[str]]:
    """Score one song against the user's prefs and return (score, reasons) for every rule that earned points.

    weights picks the ranking mode (see get_weights); None means "balanced".
    """
    w = weights or get_weights("balanced")
    score = 0.0
    reasons = []

    if song["genre"].strip().lower() == user_prefs["favorite_genre"].strip().lower():
        score += w["genre"]
        reasons.append(f"genre match (+{w['genre']:.1f})")

    if song["mood"].strip().lower() == user_prefs["favorite_mood"].strip().lower():
        score += w["mood"]
        reasons.append(f"mood match (+{w['mood']:.1f})")

    # Closer energy earns more: identical = full energy weight, opposite ends of the scale = 0.0
    energy_points = w["energy"] * (1.0 - abs(song["energy"] - user_prefs["target_energy"]))
    score += energy_points
    reasons.append(f"energy similarity (+{energy_points:.2f})")

    if user_prefs.get("likes_acoustic", False):
        acoustic_points = w["acoustic"] * song["acousticness"]
        reasons.append(f"acoustic sound (+{acoustic_points:.2f})")
    else:
        acoustic_points = w["acoustic"] * (1.0 - song["acousticness"])
        reasons.append(f"electronic sound (+{acoustic_points:.2f})")
    score += acoustic_points

    # --- Extended attributes: each rule runs only if the user set that preference ---

    wanted_tags = {tag.strip().lower() for tag in user_prefs.get("favorite_mood_tags") or []}
    if wanted_tags:
        shared = sorted(wanted_tags & {tag.lower() for tag in song.get("mood_tags", [])})
        if shared:
            tag_points = min(TAG_WEIGHT * len(shared), TAG_MAX)
            score += tag_points
            reasons.append(f"mood tags {'/'.join(shared)} (+{tag_points:.2f})")

    decade = user_prefs.get("preferred_decade")
    if decade is not None:
        gap = abs(song.get("release_decade", 0) - decade)
        if gap == 0:
            score += DECADE_WEIGHT
            reasons.append(f"{decade}s release (+{DECADE_WEIGHT:.2f})")
        elif gap == 10:
            score += DECADE_WEIGHT / 2
            reasons.append(f"near the {decade}s (+{DECADE_WEIGHT / 2:.2f})")

    language = user_prefs.get("preferred_language")
    if language and song.get("language", "").lower() == language.strip().lower():
        score += LANGUAGE_WEIGHT
        reasons.append(f"{song['language']} language (+{LANGUAGE_WEIGHT:.2f})")

    prefers_popular = user_prefs.get("prefers_popular")
    if prefers_popular is not None:
        popularity = song.get("popularity", 0) / 100
        if prefers_popular:
            popularity_points = POPULARITY_WEIGHT * popularity
            reasons.append(f"popular hit (+{popularity_points:.2f})")
        else:
            popularity_points = POPULARITY_WEIGHT * (1.0 - popularity)
            reasons.append(f"hidden gem (+{popularity_points:.2f})")
        score += popularity_points

    return score, reasons

def is_allowed(user_prefs: Dict, song: Dict) -> bool:
    """False when the user doesn't want explicit songs and this one is explicit."""
    return user_prefs.get("allow_explicit", True) or not song.get("explicit", False)

def max_score(user_prefs: Dict, mode: str = "balanced") -> float:
    """Highest score any song could earn for these prefs (4.5 base plus each extended rule the user turned on)."""
    total = sum(get_weights(mode).values())
    if user_prefs.get("favorite_mood_tags"):
        total += min(TAG_WEIGHT * len(user_prefs["favorite_mood_tags"]), TAG_MAX)
    if user_prefs.get("preferred_decade") is not None:
        total += DECADE_WEIGHT
    if user_prefs.get("preferred_language"):
        total += LANGUAGE_WEIGHT
    if user_prefs.get("prefers_popular") is not None:
        total += POPULARITY_WEIGHT
    return total

def diversify(ranked: List[Tuple[Dict, float, List[str]]], k: int) -> List[Tuple[Dict, float, List[str]]]:
    """Pick the top k one at a time, penalizing songs that repeat an artist or genre already picked.

    Each pick costs every remaining song ARTIST_PENALTY per already-picked song by the same
    artist and GENRE_PENALTY per already-picked song in the same genre. Songs that would go
    past MAX_PER_ARTIST or MAX_PER_GENRE are skipped, unless nothing else is left.
    """
    picked: List[Tuple[Dict, float, List[str]]] = []
    pool = list(ranked)
    while pool and len(picked) < k:
        def counts(song: Dict) -> Tuple[int, int]:
            return (sum(p[0]["artist"] == song["artist"] for p in picked),
                    sum(p[0]["genre"] == song["genre"] for p in picked))
        eligible = [item for item in pool
                    if counts(item[0])[0] < MAX_PER_ARTIST and counts(item[0])[1] < MAX_PER_GENRE]
        best = None
        for song, score, reasons in eligible or pool:
            same_artist, same_genre = counts(song)
            penalty = ARTIST_PENALTY * same_artist + GENRE_PENALTY * same_genre
            # Highest adjusted score wins; ties go to the lower id
            if best is None or (score - penalty, -song["id"]) > (best[1], -best[0]["id"]):
                notes = []
                if same_artist:
                    notes.append(f"repeat artist x{same_artist}")
                if same_genre:
                    notes.append(f"repeat genre x{same_genre}")
                # " + " not ", ": explanations are joined with ", " and split on it again for display
                extra = [f"diversity penalty (-{penalty:.2f}: {' + '.join(notes)})"] if penalty else []
                best = (song, score - penalty, reasons + extra)
        picked.append(best)
        pool = [item for item in pool if item[0]["id"] != best[0]["id"]]
    return picked

def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5, mode: str = "balanced",
                    diverse: bool = False) -> List[Tuple[Dict, float, str]]:
    """Score every song with the chosen ranking mode, sort by score (ties to lower id), and return the top k.

    diverse=True re-ranks with a penalty for repeated artists and genres (see diversify).
    """
    weights = get_weights(mode)
    # Judge every song, then rank: highest score first, ties go to the lower id
    judged = ((song, *score_song(user_prefs, song, weights)) for song in songs if is_allowed(user_prefs, song))
    ranked = sorted(judged, key=lambda item: (-item[1], item[0]["id"]))
    top = diversify(ranked, k) if diverse else ranked[:k]
    return [(song, score, ", ".join(reasons)) for song, score, reasons in top]
