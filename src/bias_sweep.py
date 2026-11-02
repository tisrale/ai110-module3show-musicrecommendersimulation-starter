"""
Bias sweep: simulate many users and count how often each song reaches a top 5.

Every combination of genre x mood x energy level x acoustic preference is one
simulated user. Songs that show up far more often than others reveal what the
scoring favors.

Run with: python -m src.bias_sweep
"""

from collections import Counter

from src.recommender import load_songs, recommend_songs

ENERGY_LEVELS = [0.1, 0.3, 0.5, 0.7, 0.9]


def main() -> None:
    songs = load_songs("data/songs.csv")
    genres = sorted({song["genre"] for song in songs})
    moods = sorted({song["mood"] for song in songs})

    counts = Counter()
    users = 0
    for genre in genres:
        for mood in moods:
            for energy in ENERGY_LEVELS:
                for likes_acoustic in (True, False):
                    user_prefs = {
                        "favorite_genre": genre,
                        "favorite_mood": mood,
                        "target_energy": energy,
                        "likes_acoustic": likes_acoustic,
                    }
                    for song, _, _ in recommend_songs(user_prefs, songs, k=5):
                        counts[song["title"]] += 1
                    users += 1

    print(f"Simulated users: {len(genres)} genres x {len(moods)} moods x "
          f"{len(ENERGY_LEVELS)} energy levels x 2 acoustic = {users}")
    print("\nShare of users whose top 5 includes each song:\n")
    for song in songs:
        counts.setdefault(song["title"], 0)
    for title, count in counts.most_common():
        print(f"  {count / users * 100:5.1f}%  {title}")

    print("\nAverage energy points per song, by the user's target energy:\n")
    for target in [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]:
        average = sum(1.0 - abs(song["energy"] - target) for song in songs) / len(songs)
        print(f"  target {target:.1f}: {average:.2f}")


if __name__ == "__main__":
    main()
