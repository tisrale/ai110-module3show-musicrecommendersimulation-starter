# 🎵 Music Recommender Simulation

## Project Summary

In this project you will build and explain a small music recommender system.

Your goal is to:

- Represent songs and a user "taste profile" as data
- Design a scoring rule that turns that data into recommendations
- Evaluate what your system gets right and wrong
- Reflect on how this mirrors real world AI recommenders

Replace this paragraph with your own summary of what your version does.

---

## How The System Works

Real-world platforms like Spotify and YouTube predict what you'll love next by combining two approaches. **Collaborative filtering** looks at other users' behavior ("people who play A also play B"), using signals like likes, skips, saves, playlists, and watch or listen time. **Content-based filtering** looks at the song itself: genre, mood, tempo, energy, and other audio features. Big platforms blend both, then use a separate ranking step to turn scores into a varied, ordered list. My simulation is a small **content-based** recommender: it has no listening history from other users, so it compares each song's attributes to one user's taste profile. It prioritizes **genre first, then mood, then how close the song's energy is to what the user wants**, with a smaller adjustment for acoustic vs. electronic sound. It rewards songs that are *close* to the user's preferences, not songs that simply have higher or lower values.

### Features used

**`Song`** (from `data/songs.csv`)

| Feature | Type | Used for scoring? |
|---|---|---|
| `id`, `title`, `artist` | identifiers | No (display and tie-breaking only) |
| `genre` | category | Yes: exact match with favorite genre |
| `mood` | category | Yes: exact match with favorite mood |
| `energy` | 0–1 | Yes: closeness to target energy |
| `acousticness` | 0–1 | Yes: fit with acoustic preference |
| `valence` | 0–1 | Not in v1 (planned experiment) |
| `tempo_bpm`, `danceability` | number, 0–1 | No: they move almost in lockstep with energy in this dataset, so they would double-count it |

**`UserProfile`**

| Feature | Type | Meaning |
|---|---|---|
| `favorite_genre` | text | The genre the user likes most (e.g. `pop`) |
| `favorite_mood` | text | The vibe the user wants (e.g. `happy`) |
| `target_energy` | 0–1 | How intense the user wants the music to be |
| `likes_acoustic` | True/False | Prefers acoustic (True) or electronic (False) sound |

### Algorithm Recipe (final)

**Scoring rule: judging one song**

| Rule | Points | How it is computed |
|---|---|---|
| Genre match | **+2.0** | `song.genre == favorite_genre` (case-insensitive, trimmed) |
| Mood match | **+1.0** | `song.mood == favorite_mood` (case-insensitive, trimmed) |
| Energy similarity | **0.0 – 1.0** | `1 − |song.energy − target_energy|` |
| Acoustic fit | **0.0 – 0.5** | `0.5 × acousticness` if `likes_acoustic`, else `0.5 × (1 − acousticness)` |

```
score = 2.0 × [genre matches]
      + 1.0 × [mood matches]
      + 1.0 × (1 − |song.energy − target_energy|)
      + 0.5 × (acousticness if likes_acoustic else 1 − acousticness)
```

The maximum score is 4.5. Genre is weighted highest because people usually describe their taste by genre first, and a wrong genre feels like a worse miss than a wrong mood. Mood is worth half of genre but still more than any single energy difference, so it acts as the second filter. Energy uses *closeness*, not size, so a calm-music fan is not pushed toward loud songs. Acoustic fit is kept small so it mostly breaks near-ties.

Why not weight genre and mood equally? In testing against `songs.csv`, equal weights (1.5 / 1.5) produced near-ties: for a rock/happy profile, the top two songs differed by only 0.01, which left the ranking up to tiny energy differences. The 2.0 / 1.0 split gives clearer, easier-to-explain rankings.

**Worked example** — profile `pop / happy / energy 0.8 / likes_acoustic False`:

| Song | Genre | Mood | Energy | Acoustic | Total |
|---|---|---|---|---|---|
| Sunrise City (pop/happy, 0.82) | +2.0 | +1.0 | +0.98 | +0.41 | **4.39** |
| Gym Hero (pop/intense, 0.93) | +2.0 | 0 | +0.87 | +0.47 | **3.35** |
| Rooftop Lights (indie pop/happy, 0.76) | 0 | +1.0 | +0.96 | +0.33 | **2.29** |

**Ranking rule: turning scores into a list**

1. Score every song in the catalog.
2. Sort by score, highest first; break ties by lower song `id`.
3. Return the top *k* (default 5), each with a short "because…" explanation built from the rules that earned points.

### Data Flow Plan

```
INPUT    user prefs (main.py)  +  data/songs.csv ──load_songs──▶ list of song dicts
PROCESS  for each song: score_song(user_prefs, song) ──▶ (score, reasons)
OUTPUT   sort by score (tie → lower id) ──▶ top k ──▶ [(song, score, explanation), ...]
```

For example, the row `Sunrise City,pop,happy,0.82,…,0.18` is loaded as a dict and scored 2.0 + 1.0 + 0.98 + 0.41 = 4.39 for the pop/happy/0.8 profile. After all 20 songs are scored and sorted, it ranks #1.

### Expected Biases

- **Genre outweighs everything else.** A song that only matches the genre (2.0 plus energy and acoustic points) usually beats a song from another genre that matches the mood and has nearly perfect energy (2.5 at most). For a rock/happy user, *Storm Runner* (rock but intense) is expected to outrank *Sunrise City* (happy, right energy).
- **Exact labels miss close matches.** "indie pop" earns nothing for a pop fan, and "relaxed" earns nothing for someone who wants "chill," even though these are close in meaning.
- **The catalog is uneven.** Lofi has 3 songs, but most genres have only 1. A lofi fan gets several genre matches, while a metal or jazz fan gets one, and the rest of their top 5 is filled by energy alone.
- **Energy stands in for sound.** Tempo and danceability are left out because they track energy, and valence is not scored. Two songs with the same energy can feel very different, and the system can't tell them apart.
- **Acoustic taste is yes or no.** Users who like a mix of acoustic and electronic songs can't express that, so the acoustic points push them toward one extreme.
- **The labels are subjective.** Genre and mood tags were assigned by hand, so the recommendations inherit whatever judgment calls the dataset author made.

---

## Getting Started

### Setup

1. Create a virtual environment (optional but recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Mac or Linux
   .venv\Scripts\activate         # Windows

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
python -m src.main
```

### Running Tests

Run the starter tests with:

```bash
pytest
```

You can add more tests in `tests/test_recommender.py`.

---

## Sample Recommendation Output

Output of `python -m src.main` for the default profile (`favorite_genre="pop"`, `favorite_mood="happy"`, `target_energy=0.8`, `likes_acoustic=False`):

```
Loading songs from data/songs.csv...
Loaded songs: 20

============================================================
 Top 5 for: pop / happy / energy 0.8
============================================================

1. Sunrise City by Neon Echo
   Score: 4.39 / 4.50
     - genre match (+2.0)
     - mood match (+1.0)
     - energy similarity (+0.98)
     - electronic sound (+0.41)

2. Gym Hero by Max Pulse
   Score: 3.35 / 4.50
     - genre match (+2.0)
     - energy similarity (+0.87)
     - electronic sound (+0.47)

3. Rooftop Lights by Indigo Parade
   Score: 2.29 / 4.50
     - mood match (+1.0)
     - energy similarity (+0.96)
     - electronic sound (+0.33)

4. Concrete Crown by Mic Atlas
   Score: 1.42 / 4.50
     - energy similarity (+0.98)
     - electronic sound (+0.44)

5. Storm Runner by Voltline
   Score: 1.34 / 4.50
     - energy similarity (+0.89)
     - electronic sound (+0.45)

============================================================
```

Sunrise City is the only song that matches both genre and mood, so it ranks first. Gym Hero (pop but intense) beats Rooftop Lights (happy indie pop), which shows the genre-first weighting predicted under Expected Biases. Songs #4 and #5 match neither label and are ranked only on energy and sound.

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or demo video link here -->

---

## Experiments You Tried

Use this section to document the experiments you ran. For example:

- What happened when you changed the weight on genre from 2.0 to 0.5
- What happened when you added tempo or valence to the score
- How did your system behave for different types of users

---

## Limitations and Risks

Summarize some limitations of your recommender.

Examples:

- It only works on a tiny catalog
- It does not understand lyrics or language
- It might over favor one genre or mood

You will go deeper on this in your model card.

---

## Reflection

Read and complete `model_card.md`:

[**Model Card**](model_card.md)

Write 1 to 2 paragraphs here about what you learned:

- about how recommenders turn data into predictions
- about where bias or unfairness could show up in systems like this



