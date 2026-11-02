# 🎵 Music Recommender Simulation

## Project Summary

**VibeJudge** is a small content-based music recommender that runs from the command line. You describe your taste (favorite genre, mood, energy level, and acoustic or electronic sound), and it scores all 25 songs in `data/songs.csv` and shows the top 5, each with the reasons it earned its points.

The catalog uses real songs, including five I actually listen to: Ethio-Jazz from Gigi and Tewodros Tadesse, plus reggae from Bob Marley and Alpha Blondy. I tested it with 12 profiles, including my own taste and six "trick" profiles designed to break the scoring.

Beyond the core scoring, it also has:

- **Extended attributes:** popularity, release decade, detailed mood tags, language, and an explicit-content filter.
- **Four ranking modes:** balanced, genre-first, mood-first, and energy-focused (`--mode`).
- **A diversity penalty** that limits repeated artists and genres in the top 5 (`--diverse`).
- **Readable table output**, with a summary of every profile.
- **A bias sweep** (`python -m src.bias_sweep`) that simulates 2,880 users to show which songs the scoring favors.

The biggest thing I learned: the recommender doesn't know music. It only knows the labels and numbers it's given. That's why it missed my own "chill" Ethiopian songs until I described them in its words.

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
| Can't Stop the Feeling! (pop/happy, 0.82) | +2.0 | +1.0 | +0.98 | +0.41 | **4.39** |
| Bad Romance (pop/intense, 0.93) | +2.0 | 0 | +0.87 | +0.47 | **3.35** |
| Electric Feel (indie pop/happy, 0.76) | 0 | +1.0 | +0.96 | +0.33 | **2.29** |

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

For example, the row `Can't Stop the Feeling!,pop,happy,0.82,…,0.18` is loaded as a dict and scored 2.0 + 1.0 + 0.98 + 0.41 = 4.39 for the pop/happy/0.8 profile. After all 25 songs are scored and sorted, it ranks #1.

### Expected Biases

- **Genre outweighs everything else.** A song that only matches the genre (2.0 plus energy and acoustic points) usually beats a song from another genre that matches the mood and has nearly perfect energy (2.5 at most). For a rock/happy user, *Mr. Brightside* (rock but intense) is expected to outrank *Can't Stop the Feeling!* (happy, right energy).
- **Exact labels miss close matches.** "indie pop" earns nothing for a pop fan, and "relaxed" earns nothing for someone who wants "chill," even though these are close in meaning.
- **The catalog is uneven.** Lofi, reggae, and Ethio-Jazz have 3 songs each, but most genres have only 1. A lofi fan gets several genre matches, while a metal or jazz fan gets one, and the rest of their top 5 is filled by energy alone.
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

The default output is a compact table for each profile (one row per song, with a short "Why" column), followed by a summary of every profile's #1 song and how many different genres and artists made its top 5:

```
My Taste (Gigi)  (ethio-jazz / peaceful / energy 0.4)
  #  Song                         Artist                 Score       Why
  -- ---------------------------- ---------------------- ----------- ----------------------------------------
  1  Kahine (My Priest)           Gigi                   4.38/4.50   genre +2.0, mood +1.0, energy +0.95, sound +0.42
  2  Becher Yider                 Tewodros Tadesse       3.33/4.50   genre +2.0, energy +0.98, sound +0.35
  3  Abayi                        Gigi                   3.25/4.50   genre +2.0, energy +0.95, sound +0.30
  4  Clair de Lune                Claude Debussy         2.30/4.50   mood +1.0, energy +0.82, sound +0.48
  5  Blue in Green                Miles Davis            1.42/4.50   energy +0.97, sound +0.45

SUMMARY
  Profile                      #1 song                      Score  Genres  Artists
  ---------------------------- ---------------------------- ------ ------- -------
  High-Energy Pop              Can't Stop the Feeling!      4.39   4/5     5/5
  Chill Lofi                   Snowman                      4.43   3/5     5/5
  ...
```

Options (they can be combined):

- `--detailed`: every reason on its own line (the format used in the Sample Recommendation Output below)
- `--profile "Chill Lofi"`: run one profile
- `--mode genre-first|mood-first|energy-focused`: switch ranking strategy (see Experiment 2)
- `--diverse`: limit repeated artists and genres (see Experiment 3)

### Running Tests

Run the starter tests with:

```bash
pytest
```

You can add more tests in `tests/test_recommender.py`.

---

## Sample Recommendation Output

Output of `python -m src.main --detailed` for every profile in `PROFILES` (src/main.py): three normal profiles, two personal profiles, one clean-lyrics profile, and six adversarial / edge-case profiles from the System Evaluation step. Songs are real tracks; their genre, mood, and audio-feature values are hand estimates, not official data.

### High-Energy Pop

```
============================================================
 High-Energy Pop: top 5 for pop / happy / energy 0.8
============================================================

1. Can't Stop the Feeling! by Justin Timberlake
   Score: 4.39 / 4.50
     - genre match (+2.0)
     - mood match (+1.0)
     - energy similarity (+0.98)
     - electronic sound (+0.41)

2. Bad Romance by Lady Gaga
   Score: 3.35 / 4.50
     - genre match (+2.0)
     - energy similarity (+0.87)
     - electronic sound (+0.47)

3. Electric Feel by MGMT
   Score: 2.29 / 4.50
     - mood match (+1.0)
     - energy similarity (+0.96)
     - electronic sound (+0.33)

4. HUMBLE. by Kendrick Lamar
   Score: 1.42 / 4.50
     - energy similarity (+0.98)
     - electronic sound (+0.44)

5. Mr. Brightside by The Killers
   Score: 1.34 / 4.50
     - energy similarity (+0.89)
     - electronic sound (+0.45)

============================================================
```

Can't Stop the Feeling! is the only song matching both genre and mood. Bad Romance (pop but intense) beats Electric Feel (happy indie pop), showing the genre-first weighting.

### Chill Lofi

```
============================================================
 Chill Lofi: top 5 for lofi / chill / energy 0.35
============================================================

1. Snowman by WYS
   Score: 4.43 / 4.50
     - genre match (+2.0)
     - mood match (+1.0)
     - energy similarity (+1.00)
     - acoustic sound (+0.43)

2. Affection by Jinsang
   Score: 4.29 / 4.50
     - genre match (+2.0)
     - mood match (+1.0)
     - energy similarity (+0.93)
     - acoustic sound (+0.35)

3. Aruarian Dance by Nujabes
   Score: 3.34 / 4.50
     - genre match (+2.0)
     - energy similarity (+0.95)
     - acoustic sound (+0.39)

4. Weightless by Marconi Union
   Score: 2.39 / 4.50
     - mood match (+1.0)
     - energy similarity (+0.93)
     - acoustic sound (+0.46)

5. Blue in Green by Miles Davis
   Score: 1.43 / 4.50
     - energy similarity (+0.98)
     - acoustic sound (+0.45)

============================================================
```

The only normal profile with a close race at the top: the catalog has three lofi songs, so #1-#3 all earn the genre bonus.

### Deep Intense Rock

```
============================================================
 Deep Intense Rock: top 5 for rock / intense / energy 0.9
============================================================

1. Mr. Brightside by The Killers
   Score: 4.44 / 4.50
     - genre match (+2.0)
     - mood match (+1.0)
     - energy similarity (+0.99)
     - electronic sound (+0.45)

2. Bad Romance by Lady Gaga
   Score: 2.44 / 4.50
     - mood match (+1.0)
     - energy similarity (+0.97)
     - electronic sound (+0.47)

3. Levels by Avicii
   Score: 1.44 / 4.50
     - energy similarity (+0.95)
     - electronic sound (+0.49)

4. Master of Puppets by Metallica
   Score: 1.42 / 4.50
     - energy similarity (+0.93)
     - electronic sound (+0.48)

5. Can't Stop the Feeling! by Justin Timberlake
   Score: 1.33 / 4.50
     - energy similarity (+0.92)
     - electronic sound (+0.41)

============================================================
```

Only one rock song exists, so #2-#5 drop by 2+ points and are ranked mostly on energy. EDM (Levels) edges out metal (Master of Puppets).

### My Taste (Gigi)

```
============================================================
 My Taste (Gigi): top 5 for ethio-jazz / peaceful / energy 0.4
============================================================

1. Kahine (My Priest) by Gigi
   Score: 4.38 / 4.50
     - genre match (+2.0)
     - mood match (+1.0)
     - energy similarity (+0.95)
     - acoustic sound (+0.42)

2. Becher Yider by Tewodros Tadesse
   Score: 3.33 / 4.50
     - genre match (+2.0)
     - energy similarity (+0.98)
     - acoustic sound (+0.35)

3. Abayi by Gigi
   Score: 3.25 / 4.50
     - genre match (+2.0)
     - energy similarity (+0.95)
     - acoustic sound (+0.30)

4. Clair de Lune by Claude Debussy
   Score: 2.30 / 4.50
     - mood match (+1.0)
     - energy similarity (+0.82)
     - acoustic sound (+0.48)

5. Blue in Green by Miles Davis
   Score: 1.42 / 4.50
     - energy similarity (+0.97)
     - acoustic sound (+0.45)

============================================================
```

Personal profile built around songs I actually listen to. All three Ethio-Jazz songs fill #1-#3, then the "peaceful" mood pulls in Clair de Lune. Under the Chill Lofi profile these same songs ranked #8 or lower, because they are not labeled "lofi" or "chill".

### My Taste+ (Mood Tags)

```
============================================================
 My Taste+ (Mood Tags): top 5 for ethio-jazz / peaceful / energy 0.4
============================================================

1. Kahine (My Priest) by Gigi
   Score: 4.62 / 5.25
     - genre match (+2.0)
     - mood match (+1.0)
     - energy similarity (+0.95)
     - acoustic sound (+0.42)
     - mood tags devotional (+0.25)

2. Abayi by Gigi
   Score: 3.50 / 5.25
     - genre match (+2.0)
     - energy similarity (+0.95)
     - acoustic sound (+0.30)
     - mood tags nostalgic (+0.25)

3. Becher Yider by Tewodros Tadesse
   Score: 3.33 / 5.25
     - genre match (+2.0)
     - energy similarity (+0.98)
     - acoustic sound (+0.35)

4. Clair de Lune by Claude Debussy
   Score: 2.30 / 5.25
     - mood match (+1.0)
     - energy similarity (+0.82)
     - acoustic sound (+0.48)

5. Aruarian Dance by Nujabes
   Score: 1.64 / 5.25
     - energy similarity (+1.00)
     - acoustic sound (+0.39)
     - mood tags nostalgic (+0.25)

============================================================
```

Same as My Taste, plus the mood tags spiritual / devotional / nostalgic (up to +0.75). Kahine gains for "devotional" and Abayi for "nostalgic", so Abayi passes Becher Yider. Take Me Home, Country Roads (tagged nostalgic) climbs from #12 to #6, just outside the top 5. Jerusalem stays far down.

### Clean Hip-Hop

```
============================================================
 Clean Hip-Hop: top 5 for hip-hop / confident / energy 0.78
============================================================

1. Can't Stop the Feeling! by Justin Timberlake
   Score: 1.37 / 4.50
     - energy similarity (+0.96)
     - electronic sound (+0.41)

2. Nightcall by Kavinsky
   Score: 1.36 / 4.50
     - energy similarity (+0.97)
     - electronic sound (+0.39)

3. Bad Romance by Lady Gaga
   Score: 1.32 / 4.50
     - energy similarity (+0.85)
     - electronic sound (+0.47)

4. Mr. Brightside by The Killers
   Score: 1.32 / 4.50
     - energy similarity (+0.87)
     - electronic sound (+0.45)

5. Levels by Avicii
   Score: 1.32 / 4.50
     - energy similarity (+0.83)
     - electronic sound (+0.49)

============================================================
```

allow_explicit=False removes explicit songs entirely. HUMBLE. is the only hip-hop song and it is explicit, so this user gets no hip-hop at all, only high-energy filler. A -2.0 penalty was tried first, but HUMBLE. still ranked #1.

### Edge: Sad but Hyped

```
============================================================
 Edge: Sad but Hyped: top 5 for folk / sad / energy 0.9
============================================================

1. Skinny Love by Bon Iver
   Score: 3.86 / 4.50
     - genre match (+2.0)
     - mood match (+1.0)
     - energy similarity (+0.40)
     - acoustic sound (+0.47)

2. Vivir Mi Vida by Marc Anthony
   Score: 1.26 / 4.50
     - energy similarity (+0.96)
     - acoustic sound (+0.30)

3. Mr. Brightside by The Killers
   Score: 1.04 / 4.50
     - energy similarity (+0.99)
     - acoustic sound (+0.05)

4. Electric Feel by MGMT
   Score: 1.03 / 4.50
     - energy similarity (+0.86)
     - acoustic sound (+0.17)

5. Take Me Home, Country Roads by John Denver
   Score: 1.02 / 4.50
     - energy similarity (+0.65)
     - acoustic sound (+0.37)

============================================================
```

Conflicting prefs: Skinny Love wins with energy 0.30 vs. a 0.9 target. Genre + mood (+3.0) outweighs the energy mismatch.

### Edge: Unknown Genre

```
============================================================
 Edge: Unknown Genre: top 5 for k-pop / happy / energy 0.8
============================================================

1. Can't Stop the Feeling! by Justin Timberlake
   Score: 2.39 / 4.50
     - mood match (+1.0)
     - energy similarity (+0.98)
     - electronic sound (+0.41)

2. Electric Feel by MGMT
   Score: 2.29 / 4.50
     - mood match (+1.0)
     - energy similarity (+0.96)
     - electronic sound (+0.33)

3. HUMBLE. by Kendrick Lamar
   Score: 1.42 / 4.50
     - energy similarity (+0.98)
     - electronic sound (+0.44)

4. Bad Romance by Lady Gaga
   Score: 1.34 / 4.50
     - energy similarity (+0.87)
     - electronic sound (+0.47)

5. Mr. Brightside by The Killers
   Score: 1.34 / 4.50
     - energy similarity (+0.89)
     - electronic sound (+0.45)

============================================================
```

"k-pop" never matches, with no warning. Results fall back to mood + energy.

### Edge: Spelling Variant

```
============================================================
 Edge: Spelling Variant: top 5 for hip hop / confident / energy 0.78
============================================================

1. HUMBLE. by Kendrick Lamar
   Score: 2.44 / 4.50
     - mood match (+1.0)
     - energy similarity (+1.00)
     - electronic sound (+0.44)

2. Can't Stop the Feeling! by Justin Timberlake
   Score: 1.37 / 4.50
     - energy similarity (+0.96)
     - electronic sound (+0.41)

3. Nightcall by Kavinsky
   Score: 1.36 / 4.50
     - energy similarity (+0.97)
     - electronic sound (+0.39)

4. Bad Romance by Lady Gaga
   Score: 1.32 / 4.50
     - energy similarity (+0.85)
     - electronic sound (+0.47)

5. Mr. Brightside by The Killers
   Score: 1.32 / 4.50
     - energy similarity (+0.87)
     - electronic sound (+0.45)

============================================================
```

"hip hop" does not match the catalog's "hip-hop"; HUMBLE. wins on mood alone, missing the +2.0 genre bonus.

### Edge: Energy Out of Range

```
============================================================
 Edge: Energy Out of Range: top 5 for classical / peaceful / energy 1.5
============================================================

1. Clair de Lune by Claude Debussy
   Score: 3.20 / 4.50
     - genre match (+2.0)
     - mood match (+1.0)
     - energy similarity (+-0.28)
     - acoustic sound (+0.48)

2. Kahine (My Priest) by Gigi
   Score: 1.28 / 4.50
     - mood match (+1.0)
     - energy similarity (+-0.15)
     - acoustic sound (+0.42)

3. Vivir Mi Vida by Marc Anthony
   Score: 0.66 / 4.50
     - energy similarity (+0.36)
     - acoustic sound (+0.30)

4. Master of Puppets by Metallica
   Score: 0.48 / 4.50
     - energy similarity (+0.47)
     - acoustic sound (+0.01)

5. Mr. Brightside by The Killers
   Score: 0.46 / 4.50
     - energy similarity (+0.41)
     - acoustic sound (+0.05)

============================================================
```

target_energy=1.5 is not validated: Clair de Lune gets a negative energy score (+-0.28), and Kahine reaches #2 on the "peaceful" mood alone.

### Edge: Acoustic Metalhead

```
============================================================
 Edge: Acoustic Metalhead: top 5 for metal / angry / energy 0.97
============================================================

1. Master of Puppets by Metallica
   Score: 4.01 / 4.50
     - genre match (+2.0)
     - mood match (+1.0)
     - energy similarity (+1.00)
     - acoustic sound (+0.01)

2. Vivir Mi Vida by Marc Anthony
   Score: 1.19 / 4.50
     - energy similarity (+0.89)
     - acoustic sound (+0.30)

3. Mr. Brightside by The Killers
   Score: 0.99 / 4.50
     - energy similarity (+0.94)
     - acoustic sound (+0.05)

4. Levels by Avicii
   Score: 0.99 / 4.50
     - energy similarity (+0.98)
     - acoustic sound (+0.01)

5. Bad Romance by Lady Gaga
   Score: 0.99 / 4.50
     - energy similarity (+0.96)
     - acoustic sound (+0.03)

============================================================
```

likes_acoustic=True barely matters: Master of Puppets earns only +0.01 for sound but still wins on genre + mood + energy.

### Edge: Energetic Classical

```
============================================================
 Edge: Energetic Classical: top 5 for classical / energetic / energy 1.0
============================================================

1. Levels by Avicii
   Score: 2.44 / 4.50
     - mood match (+1.0)
     - energy similarity (+0.95)
     - electronic sound (+0.49)

2. Clair de Lune by Claude Debussy
   Score: 2.23 / 4.50
     - genre match (+2.0)
     - energy similarity (+0.22)
     - electronic sound (+0.02)

3. Master of Puppets by Metallica
   Score: 1.46 / 4.50
     - energy similarity (+0.97)
     - electronic sound (+0.48)

4. Bad Romance by Lady Gaga
   Score: 1.41 / 4.50
     - energy similarity (+0.93)
     - electronic sound (+0.47)

5. Mr. Brightside by The Killers
   Score: 1.36 / 4.50
     - energy similarity (+0.91)
     - electronic sound (+0.45)

============================================================
```

The only profile where the genre match loses: EDM (Levels) beats the only classical song because mood + energy outweigh the genre bonus.

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or demo video link here -->

---

## Experiments You Tried

### Experiment 1: Weight shift (genre halved, energy doubled)

**Change:** in `src/recommender.py`, `GENRE_WEIGHT` went from 2.0 to 1.0 and `ENERGY_WEIGHT` from 1.0 to 2.0 (energy points = 2 × (1 − |diff|)). Mood (+1.0) and acoustic fit (up to +0.5) stayed the same.

**Math check:** the maximum is still 1.0 + 1.0 + 2.0 + 0.5 = 4.5, so the "/ 4.50" display stays correct. A song matching every rule scores exactly 4.50, and with energy targets between 0 and 1 the minimum is 0. Across all 10 profiles, real scores ranged from 0.02 to 4.43. One side effect: the out-of-range energy bug doubles (Clair de Lune gets −0.56 instead of −0.28 for `target_energy=1.5`).

**Top-5 changes (baseline → weight shift):**

| Profile | What changed |
|---|---|
| High-Energy Pop | Electric Feel (happy, indie pop) passes Bad Romance (intense, pop) for #2; Nightcall replaces Mr. Brightside at #5 |
| Chill Lofi | Weightless (ambient) passes Aruarian Dance (lofi) for #3; Kahine (My Priest) enters at #5 |
| Deep Intense Rock | No change |
| My Taste (Gigi) | Top 4 unchanged; Aruarian Dance replaces Blue in Green at #5 |
| Edge: Sad but Hyped | Skinny Love still #1 (genre + mood still outweigh a 0.6 energy gap); #4–5 become high-energy pop |
| Edge: Energetic Classical | Clair de Lune, the only classical song, drops out of the top 5 entirely |

**What I learned:**
- The **#1 song did not change for any profile**. Changes happened in positions 2–5, where songs compete on energy instead of labels.
- Halving genre makes the system follow **how a song feels** more than **what it is labeled**: a happy pop fan now gets the happy indie-pop song before the intense pop song, which matches intuition better.
- The trade-off: a genre fan's own genre can vanish when its energy doesn't fit (Energetic Classical lost its only classical song).
- Rankings are fairly stable in the top spot but sensitive lower down, so the weights mostly decide the "filler" songs.

**More accurate, or just different?** Mostly just different. I checked it against my own ranking for "My Taste (Gigi)" (Kahine, Becher Yider, Abayi, Jerusalem, Take Me Home, Country Roads). Both versions get the same 3 of my 5 songs in the top 5, and my #4 and #5 stay at ranks 16 and 12 either way, because neither song matches the genre, the mood, or the 0.4 energy target. The only real effect was a narrower lead: Abayi's margin over Clair de Lune shrank from 0.95 to 0.08. For High-Energy Pop the change looks more sensible (the happy song now beats the intense one), but that is a judgment call, not a measured improvement. Changing weights reshuffles songs that already fit the profile; it can't find songs my profile doesn't describe.

After recording these results, the weights were restored to the original recipe (genre 2.0, energy 1.0), which the Sample Recommendation Output above uses.

### Experiment 2: Ranking modes

You can now switch between four ranking strategies without editing code:

```
python -m src.main                                   # balanced (default)
python -m src.main --mode genre-first
python -m src.main --mode mood-first
python -m src.main --mode energy-focused --profile "Chill Lofi"
```

The rules are the same in every mode. Only the points change, and every mode tops out at 4.5, so scores are comparable:

| Mode | Genre | Mood | Energy | Sound | Idea |
|---|---|---|---|---|---|
| balanced | 2.0 | 1.0 | 1.0 | 0.5 | The original recipe |
| genre-first | 3.0 | 0.5 | 0.75 | 0.25 | "I only listen to my genre" |
| mood-first | 1.0 | 2.0 | 1.0 | 0.5 | "Match how I feel right now" |
| energy-focused | 1.0 | 0.5 | 2.5 | 0.5 | "Match the intensity, any style" |

**What changed:**

- **Energetic Classical shows the modes clearly.** Genre-first puts Clair de Lune (the only classical song) at #1. Balanced puts it at #2. Mood-first drops it to #5, and energy-focused removes it from the top 5.
- **My Taste (Gigi):** mood-first moves Clair de Lune (mood "peaceful") up to #2, above Becher Yider and Abayi, which don't match the mood. That doesn't match my own ranking, so mood-first is the wrong mode for me.
- **High-Energy Pop:** mood-first finally ranks Electric Feel (happy) above Bad Romance (intense).
- **Deep Intense Rock didn't change in any mode.** Its one rock song matches every rule, so the weights don't matter.
- The #1 song stayed the same in every mode for 10 of the 12 profiles. The exceptions are Energetic Classical, where the user's genre and mood point to different songs, and Clean Hip-Hop, which has no genre match at all, so energy-focused swaps in Nightcall.

### Experiment 3: Diversity penalty

Add `--diverse` to spread the top 5 across artists and genres. It works with any mode:

```
python -m src.main --diverse
python -m src.main --mode mood-first --diverse --profile "My Taste (Gigi)"
```

**How it works:** the top 5 is picked one song at a time. Each candidate loses 1.0 point for every already-picked song by the same artist, and 0.5 for every already-picked song in the same genre. There's also a hard cap of 2 songs per artist and 2 per genre. The penalty shows up in the reasons, like `diversity penalty (-0.50: repeat genre x1)`. It's off by default, so the Sample Recommendation Output above is unchanged.

**Why the hard cap:** the penalty alone didn't prevent repeats. Chill Lofi still got 3 lofi songs, because the third one was far enough ahead to absorb the penalty. With the cap, no top 5 has more than 2 songs from one genre or 1 from one artist, in any mode.

**What changed:**

| Profile | Normal top 5 | With `--diverse` |
|---|---|---|
| Chill Lofi | 3 lofi songs (Snowman, Affection, Aruarian Dance) | Aruarian Dance is replaced; Kahine (My Priest) enters at #5 |
| My Taste (Gigi) | Kahine, Becher Yider, Abayi (2 Gigi songs) | Abayi drops out (second Gigi song, third ethio-jazz song) |
| My Taste+ (Mood Tags) | Kahine, Abayi, Becher Yider, ... | Abayi drops out, and **Take Me Home, Country Roads enters at #5**, one of my own top-5 picks |
| Deep Intense Rock | 2 pop songs (Bad Romance, Can't Stop the Feeling!) | Can't Stop the Feeling! is replaced by HUMBLE. |

**The trade-off:** diversity helped my taste in one way and hurt it in another. It finally brought Country Roads into my list, but it also pushed out Abayi, which I ranked #3, just because Gigi already had a song. Diversity is good for discovery, but a user who really wants more of one artist would find it annoying. That's why it's a switch, not the default.

---

## Limitations and Risks

- **Tiny, uneven catalog.** There are only 25 songs. Lofi, reggae, and ethio-jazz have 3 songs each, but most genres have just 1. A rock or metal fan gets one real match, and the rest of their top 5 is filler.
- **Genre bubble.** The genre bonus (+2.0) outweighs everything else, and a profile holds only one genre and one mood. Listeners with broad tastes get missed. My own picks, Jerusalem (reggae) and Take Me Home, Country Roads (country), ranked #16 and #12 for my ethio-jazz profile.
- **Exact labels only.** "hip hop" doesn't match "hip-hop," and "indie pop" doesn't count for a pop fan. Users lose points with no warning.
- **Middle songs get favored.** Songs in the middle of the energy and acoustic scales fit "okay" for everyone. In a test of 2,880 simulated users, Adorn showed up in 36% of top-5 lists, while more distinctive songs like Kahine showed up in only 11%. (Run `python -m src.bias_sweep` to reproduce this.)
- **Extreme energy users are short-changed.** Someone who wants very calm (0.0) or very intense (1.0) music scores lower on average (0.42 and 0.58 energy points per song, vs. 0.79 for a target of 0.6), and the calmest song in the catalog is 0.22.
- **No understanding of the music itself.** It ignores lyrics, language, and culture. It can't tell a prayer-like song from a love song.
- **Estimated data.** Most numbers are hand estimates, not measurements. A wrong number can change a song's rank.
- **No input checks.** Energy above 1.0 gives a negative score. A missing mood or energy typed as text crashes the program.

**Risk:** if a system like this were used for real, it would keep showing people more of the same genre. It would also quietly under-serve listeners whose music isn't labeled the way the catalog expects.

The model card goes deeper on the biggest one, the genre bubble: [model_card.md](model_card.md), section 6.

---

## Reflection

Read and complete `model_card.md`:

[**Model Card**](model_card.md)

I learned that a recommender turns data into predictions by giving points. It compares each song's labels and numbers to what the user asked for, adds up the points, and calls the highest scores "recommendations." It doesn't know music. It only knows the genre and mood words and the numbers in the CSV. That's also where bias comes in. The choices about how many points each rule is worth, which songs are in the catalog, and how they're labeled decide who gets good results. Because genre is worth the most and each profile holds one genre, people with broad tastes get missed. My own reggae and country picks ranked #16 and #12. Songs in the middle of the scales show up for almost everyone, and music that doesn't fit the catalog's labels, like my Ethiopian songs under "chill," gets pushed down. None of this is on purpose, but it would still be unfair to real users. My full reflection is in the model card, section 9.



