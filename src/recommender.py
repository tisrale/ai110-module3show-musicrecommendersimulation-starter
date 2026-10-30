import csv
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

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

class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        # TODO: Implement recommendation logic
        return self.songs[:k]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        # TODO: Implement explanation logic
        return "Explanation placeholder"

def load_songs(csv_path: str) -> List[Dict]:
    """Read songs.csv into a list of dicts, converting id to int and audio features to float."""
    print(f"Loading songs from {csv_path}...")
    float_fields = ("energy", "tempo_bpm", "valence", "danceability", "acousticness")

    songs = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            # csv gives every value as a string; convert numbers so we can do math on them
            row["id"] = int(row["id"])
            for field in float_fields:
                row[field] = float(row[field])
            songs.append(row)
    return songs

def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """Score one song against the user's prefs and return (score, reasons) for every rule that earned points."""
    score = 0.0
    reasons = []

    if song["genre"].strip().lower() == user_prefs["favorite_genre"].strip().lower():
        score += 2.0
        reasons.append("genre match (+2.0)")

    if song["mood"].strip().lower() == user_prefs["favorite_mood"].strip().lower():
        score += 1.0
        reasons.append("mood match (+1.0)")

    # Closer energy earns more: identical = +1.0, opposite ends of the scale = 0.0
    energy_points = 1.0 - abs(song["energy"] - user_prefs["target_energy"])
    score += energy_points
    reasons.append(f"energy similarity (+{energy_points:.2f})")

    if user_prefs.get("likes_acoustic", False):
        acoustic_points = 0.5 * song["acousticness"]
        reasons.append(f"acoustic sound (+{acoustic_points:.2f})")
    else:
        acoustic_points = 0.5 * (1.0 - song["acousticness"])
        reasons.append(f"electronic sound (+{acoustic_points:.2f})")
    score += acoustic_points

    return score, reasons

def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, str]]:
    """Score every song, sort by score (ties to lower id), and return the top k as (song, score, explanation)."""
    # Judge every song, then rank: highest score first, ties go to the lower id
    judged = ((song, *score_song(user_prefs, song)) for song in songs)
    ranked = sorted(judged, key=lambda item: (-item[1], item[0]["id"]))
    return [(song, score, ", ".join(reasons)) for song, score, reasons in ranked[:k]]
