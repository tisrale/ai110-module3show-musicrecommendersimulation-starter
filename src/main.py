"""
Command line runner for the Music Recommender Simulation.

Run all profiles with the default ranking mode:
    python -m src.main

Switch ranking modes, or run a single profile:
    python -m src.main --mode mood-first
    python -m src.main --mode energy-focused --profile "Chill Lofi"

Spread the top 5 across artists and genres:
    python -m src.main --diverse

Output is a compact table plus a summary. For every reason on its own line:
    python -m src.main --detailed
"""

import argparse

from src.recommender import load_songs, recommend_songs, max_score, MODES

# Default ranking mode when --mode isn't given. Options: balanced, genre-first, mood-first, energy-focused
MODE = "balanced"


# Taste profiles: target values the recommender compares every song against.
# Keys match the UserProfile fields in recommender.py.
#   favorite_genre  -> +2.0 if the song's genre matches exactly
#   favorite_mood   -> +1.0 if the song's mood matches exactly
#   target_energy   -> 0.0 (calm) to 1.0 (intense); closer = more points
#   likes_acoustic  -> True = prefers acoustic sound, False = electronic/produced
# Optional extended preferences (only scored when present):
#   favorite_mood_tags -> +0.25 per shared tag, up to +0.75
#   preferred_decade   -> +0.5 same decade, +0.25 neighboring decade
#   preferred_language -> +0.5 if the song's language matches
#   prefers_popular    -> True rewards hits, False rewards hidden gems (up to +0.5)
#   allow_explicit     -> False subtracts 2.0 from explicit songs
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
    # Same taste plus detailed mood tags that describe what I love about these songs.
    "My Taste+ (Mood Tags)": {
        "favorite_genre": "ethio-jazz",
        "favorite_mood": "peaceful",
        "target_energy": 0.4,
        "likes_acoustic": True,
        "favorite_mood_tags": ["spiritual", "devotional", "nostalgic"],
    },
    # Hip-hop fan who doesn't want explicit lyrics: tests the explicit filter.
    "Clean Hip-Hop": {
        "favorite_genre": "hip-hop",
        "favorite_mood": "confident",
        "target_energy": 0.78,
        "likes_acoustic": False,
        "allow_explicit": False,
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


def fit(text: str, width: int) -> str:
    """Pad or cut text to exactly width characters, marking cuts with '..'."""
    return text.ljust(width) if len(text) <= width else text[:width - 2] + ".."


def short_reason(reason: str) -> str:
    """Shrink a reason for the table, e.g. 'energy similarity (+0.98)' -> 'energy +0.98'."""
    label, _, rest = reason.partition(" (")
    points = rest.split(":")[0].rstrip(")")
    words = label.split()
    if words[:2] == ["mood", "tags"]:
        name = "tags"
    elif words[-1] == "sound":
        name = "sound"
    elif words[0] == "near":
        name = "decade"
    elif words[-1] in ("release", "language"):
        name = words[-1].replace("release", "decade")
    else:
        name = words[0]
    return f"{name} {points}"


def print_table(name: str, user_prefs: dict, recommendations: list, mode: str) -> None:
    """Print one profile's top songs as a compact table: one row per song."""
    top = max_score(user_prefs, mode)
    print(f"\n{name}  ({user_prefs['favorite_genre']} / {user_prefs['favorite_mood']} / "
          f"energy {user_prefs['target_energy']})")
    print(f"  {'#':<2} {'Song':<28} {'Artist':<22} {'Score':<11} Why")
    print(f"  {'-' * 2} {'-' * 28} {'-' * 22} {'-' * 11} {'-' * 40}")
    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        why = ", ".join(short_reason(r) for r in explanation.split(", "))
        print(f"  {rank:<2} {fit(song['title'], 28)} {fit(song['artist'], 22)} "
              f"{f'{score:.2f}/{top:.2f}':<11} {why}")


def print_summary(results: list) -> None:
    """Print one row per profile: its #1 song, score, and how varied the top 5 is."""
    print("\nSUMMARY")
    print(f"  {'Profile':<28} {'#1 song':<28} {'Score':<6} {'Genres':<7} Artists")
    print(f"  {'-' * 28} {'-' * 28} {'-' * 6} {'-' * 7} {'-' * 7}")
    for name, recommendations in results:
        song, score, _ = recommendations[0]
        genres = len({s['genre'] for s, _, _ in recommendations})
        artists = len({s['artist'] for s, _, _ in recommendations})
        print(f"  {fit(name, 28)} {fit(song['title'], 28)} {score:<6.2f} {genres}/5     {artists}/5")


def print_recommendations(name: str, user_prefs: dict, songs: list, k: int = 5, mode: str = MODE,
                          diverse: bool = False, detailed: bool = True) -> list:
    """Rank songs for one profile, print them (detailed list or compact table), and return them."""
    recommendations = recommend_songs(user_prefs, songs, k=k, mode=mode, diverse=diverse)
    if not detailed:
        print_table(name, user_prefs, recommendations, mode)
        return recommendations

    print()
    print("=" * 60)
    print(f" {name}: top {len(recommendations)} for {user_prefs['favorite_genre']} / "
          f"{user_prefs['favorite_mood']} / energy {user_prefs['target_energy']}")
    print("=" * 60)

    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        print(f"\n{rank}. {song['title']} by {song['artist']}")
        print(f"   Score: {score:.2f} / {max_score(user_prefs, mode):.2f}")
        for reason in explanation.split(", "):
            print(f"     - {reason}")

    print("\n" + "=" * 60)
    return recommendations


def main() -> None:
    parser = argparse.ArgumentParser(description="Music recommender simulation")
    parser.add_argument("--mode", choices=MODES, default=MODE, help="ranking strategy")
    parser.add_argument("--profile", choices=list(PROFILES), help="run only this profile")
    parser.add_argument("--diverse", action="store_true",
                        help="penalize repeated artists and genres in the top 5")
    parser.add_argument("--detailed", action="store_true",
                        help="show every reason on its own line instead of the compact table")
    args = parser.parse_args()

    songs = load_songs("data/songs.csv")
    print(f"Loaded songs: {len(songs)}")
    print(f"Ranking mode: {args.mode}" + (" + diversity penalty" if args.diverse else ""))

    results = []
    for name, user_prefs in PROFILES.items():
        if args.profile is None or name == args.profile:
            recommendations = print_recommendations(name, user_prefs, songs, mode=args.mode,
                                                    diverse=args.diverse, detailed=args.detailed)
            results.append((name, recommendations))

    if not args.detailed and len(results) > 1:
        print_summary(results)


if __name__ == "__main__":
    main()
