"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

from src.recommender import load_songs, recommend_songs


def main() -> None:
    songs = load_songs("data/songs.csv")
    print(f"Loaded songs: {len(songs)}")

    # Taste profile: target values the recommender compares every song against.
    # Keys match the UserProfile fields in recommender.py.
    user_prefs = {
        "favorite_genre": "pop",    # +2.0 if the song's genre matches exactly
        "favorite_mood": "happy",   # +1.0 if the song's mood matches exactly
        "target_energy": 0.8,       # 0.0 (calm) to 1.0 (intense); closer = more points
        "likes_acoustic": False,    # False = prefers electronic/produced sound
    }

    recommendations = recommend_songs(user_prefs, songs, k=5)

    print()
    print("=" * 60)
    print(f" Top {len(recommendations)} for: {user_prefs['favorite_genre']} / "
          f"{user_prefs['favorite_mood']} / energy {user_prefs['target_energy']}")
    print("=" * 60)

    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        print(f"\n{rank}. {song['title']} by {song['artist']}")
        print(f"   Score: {score:.2f} / 4.50")
        for reason in explanation.split(", "):
            print(f"     - {reason}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
