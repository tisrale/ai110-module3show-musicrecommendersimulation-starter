"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

from src.recommender import load_songs, recommend_songs


# Taste profiles: target values the recommender compares every song against.
# Keys match the UserProfile fields in recommender.py.
#   favorite_genre  -> +2.0 if the song's genre matches exactly
#   favorite_mood   -> +1.0 if the song's mood matches exactly
#   target_energy   -> 0.0 (calm) to 1.0 (intense); closer = more points
#   likes_acoustic  -> True = prefers acoustic sound, False = electronic/produced
PROFILES = {
    "High-Energy Pop": {
        "favorite_genre": "pop",
        "favorite_mood": "happy",
        "target_energy": 0.8,
        "likes_acoustic": False,
    },
    "Chill Lofi": {
        "favorite_genre": "lofi",
        "favorite_mood": "chill",
        "target_energy": 0.35,
        "likes_acoustic": True,
    },
    "Deep Intense Rock": {
        "favorite_genre": "rock",
        "favorite_mood": "intense",
        "target_energy": 0.9,
        "likes_acoustic": False,
    },
    # Personal taste: calm Ethio-Jazz like Gigi (Kahine, Abayi) and Tewodros Tadesse.
    "My Taste (Gigi)": {
        "favorite_genre": "ethio-jazz",
        "favorite_mood": "peaceful",
        "target_energy": 0.4,
        "likes_acoustic": True,
    },
    # --- Adversarial / edge-case profiles (System Evaluation) ---
    # Conflicting: sad mood but high energy. Does genre+mood override energy?
    "Edge: Sad but Hyped": {
        "favorite_genre": "folk",
        "favorite_mood": "sad",
        "target_energy": 0.9,
        "likes_acoustic": True,
    },
    # Genre that doesn't exist in the catalog: genre never matches.
    "Edge: Unknown Genre": {
        "favorite_genre": "k-pop",
        "favorite_mood": "happy",
        "target_energy": 0.8,
        "likes_acoustic": False,
    },
    # Spelling variant: catalog says "hip-hop", exact match fails.
    "Edge: Spelling Variant": {
        "favorite_genre": "hip hop",
        "favorite_mood": "confident",
        "target_energy": 0.78,
        "likes_acoustic": False,
    },
    # Energy outside 0-1: energy points go negative.
    "Edge: Energy Out of Range": {
        "favorite_genre": "classical",
        "favorite_mood": "peaceful",
        "target_energy": 1.5,
        "likes_acoustic": True,
    },
    # Contradiction: wants acoustic metal, but no acoustic metal exists.
    "Edge: Acoustic Metalhead": {
        "favorite_genre": "metal",
        "favorite_mood": "angry",
        "target_energy": 0.97,
        "likes_acoustic": True,
    },
    # Genre vs. everything else: classical fan who wants max energy.
    "Edge: Energetic Classical": {
        "favorite_genre": "classical",
        "favorite_mood": "energetic",
        "target_energy": 1.0,
        "likes_acoustic": False,
    },
}


def print_recommendations(name: str, user_prefs: dict, songs: list, k: int = 5) -> None:
    """Rank songs for one profile and print the top k with their reasons."""
    recommendations = recommend_songs(user_prefs, songs, k=k)

    print()
    print("=" * 60)
    print(f" {name}: top {len(recommendations)} for {user_prefs['favorite_genre']} / "
          f"{user_prefs['favorite_mood']} / energy {user_prefs['target_energy']}")
    print("=" * 60)

    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        print(f"\n{rank}. {song['title']} by {song['artist']}")
        print(f"   Score: {score:.2f} / 4.50")
        for reason in explanation.split(", "):
            print(f"     - {reason}")

    print("\n" + "=" * 60)


def main() -> None:
    songs = load_songs("data/songs.csv")
    print(f"Loaded songs: {len(songs)}")

    for name, user_prefs in PROFILES.items():
        print_recommendations(name, user_prefs, songs)


if __name__ == "__main__":
    main()
