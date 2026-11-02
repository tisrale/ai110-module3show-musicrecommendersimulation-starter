# AI Interactions Log

> **Stretch features only.** Only fill in the sections that apply to stretch features you attempted. If you did not attempt a stretch feature, leave its section blank or delete it. This file is not required for the core project.

---

## Agentic Workflow (SF8)

> Document your experience using an AI agent (e.g., Cursor Agent, Claude, Copilot) to make multi-step changes autonomously.

**What task did you give the agent?**

I used Claude Code (an AI agent in VS Code) to evaluate and improve my music recommender. The goal was to test it with many different users, try a logic experiment, find biases, replace the made-up songs with real music, and document everything in the README and model card. The agent edited files, ran the program, and checked its own results across many steps.

**Prompts used:**

- "Define at least three distinct user preference dictionaries (e.g., 'High-Energy Pop,' 'Chill Lofi,' 'Deep Intense Rock')."
- Asked it to suggest adversarial or edge-case profiles that could trick the scoring logic.
- "Could you replace the unreal ones with these new real music if possible?" (after giving it my own songs: Bob Marley, Gigi, Tewodros Tadesse, Alpha Blondy)
- "In src/recommender.py, change `score_song` so the genre match is worth +1.0 instead of +2.0, and energy similarity is worth up to +2.0 instead of +1.0. Keep mood and acoustic fit the same. Make the original values easy to restore. Then verify the math."
- "Attach recommender.py and songs.csv and identify potential filter bubbles or biases in the current scoring logic."
- "How do I know it did test 2,880 simulated users here for the grader?"

**What did the agent generate or change?**

- `src/main.py`: 10 user profiles (3 normal, my "My Taste (Gigi)" profile, and 6 edge cases), printed in one run.
- `data/songs.csv`: replaced the made-up songs with real songs and added my 5 picks.
- `src/recommender.py`: moved the weights into constants for the experiment, and finished the `Recommender` class using `score_song`.
- `src/bias_sweep.py`: a new script that simulates 2,880 users and counts how often each song is recommended.
- `README.md` and `model_card.md`: sample output for all profiles, the experiment results, limitations, and comparisons between profiles.
- It ran `python -m src.main` and `pytest` after each change to check the results.

**What did you verify or fix manually?**

- **Wrong artist.** It listed "Becher Yider" under Teddy Afro. I corrected it to Tewodros Tadesse.
- **Wrong genre.** It put all three Ethiopian songs under a made-up genre, "ethiopian." I asked if it had checked any sources, then found that all three are Ethio-Jazz, and had it use that.
- **Guessed numbers.** It estimated energy and other values for songs it had never heard. It told me it can't listen to music, even on YouTube. I told it Becher Yider is softer, and gave it a written description of Kahine, so it could turn real details into better numbers.
- **Missing evidence.** It quoted results from a test of 2,880 users, but the test wasn't saved anywhere. I asked how a grader could check it, so it saved the test as `src/bias_sweep.py`.
- **My own mistake.** During the experiment, I edited a comment line instead of the real weights, so nothing changed. The agent checked the file and showed me which lines to edit.
- I compared the results with my own taste. The system matched my top 3 exactly but missed my #4 and #5.

### Second task: extended song attributes

**What task did you give the agent?**

Add 5 new attributes to every song and make the scoring use them, without breaking the results I had already documented.

**Prompts used:**

- "Introduce 5 or more complex attributes to your dataset that are not currently present in the baseline data, such as Song Popularity (0-100), Release Decade, or Detailed Mood Tags."
- "Update both data/songs.csv and the scoring logic in src/recommender.py so scoring accounts for the new attributes."

**What did the agent generate or change?**

- `data/songs.csv`: 5 new columns for all 25 songs: `popularity` (0–100), `release_decade`, `mood_tags` (2–3 detailed tags like "devotional;mystical;yearning"), `language`, and `explicit`.
- `src/recommender.py`:
  - `load_songs` converts the new columns (numbers, a tag list, true/false).
  - `Song` and `UserProfile` got new optional fields.
  - `score_song` has new opt-in rules: shared mood tags (+0.25 each, up to +0.75), decade (+0.5, or +0.25 for a neighboring decade), language (+0.5), and popularity or "hidden gems" (up to +0.5).
  - A new `is_allowed` filter removes explicit songs when `allow_explicit=False`.
  - A new `max_score` function gives the right maximum for each profile.
- `src/main.py`: two new profiles, "My Taste+ (Mood Tags)" and "Clean Hip-Hop," and the score now shows the profile's real maximum instead of always "/ 4.50."
- `README.md` and `model_card.md`: regenerated output for all 12 profiles, and a description of the new attributes.

**What did you verify or fix manually?**

- **Old results stay the same.** The new rules only apply when a profile asks for them. The agent compared the new output with the old output: all 10 original profiles are identical, so my earlier documentation is still correct.
- **The explicit rule didn't work at first.** The agent first made explicit songs lose 2.0 points. But in testing, the "Clean Hip-Hop" user still got HUMBLE. (explicit) at #1, because it's the only hip-hop song and earns +3.0 for genre and mood. A user who says "no explicit songs" should never see one, so it was changed to a filter that removes them completely. Now that user gets no hip-hop at all, which shows how thin the catalog is.
- **Mood tags helped my taste, a little.** With spiritual / devotional / nostalgic tags, Take Me Home, Country Roads climbed from #12 to #6. Jerusalem stayed far down (#14).
- **I didn't let it fake a result.** The agent found that adding a 1980s decade preference would pull Jerusalem into my top 5. But I never said I prefer the 1980s, so we left it out instead of tuning the profile to get the answer I wanted.
- **Estimated data.** Popularity and most decades are estimates. My Ethiopian songs have the lowest popularity (20–30), so a "popular hits" preference would push them down even further. That's a bias to watch for.
- The tests pass, and the `Recommender` class gives the same results as `recommend_songs` for all 12 profiles.

---

## Design Pattern (SF10)

> Document how AI helped you choose or implement a design pattern.

**Which design pattern did you use?**

The **Strategy pattern**, in a simple "data" form. A strategy is a way of ranking songs. The recommender doesn't know which strategy it's using. It just gets handed one and uses it. I have four strategies: balanced, genre-first, mood-first, and energy-focused. You can switch between them with `--mode`, without changing any code.

**How did AI help you brainstorm or implement it?**

Prompts I used:

- "Build two or more different ranking strategies (e.g., 'Genre-First,' 'Mood-First,' or 'Energy-Focused') so a user can switch between modes in main.py."
- "Attach recommender.py and brainstorm a design pattern (like a simple 'Strategy' pattern) that keeps your code modular."

The AI compared four options:

| Option | Idea | Verdict |
|---|---|---|
| if/else per mode | `if mode == "genre-first": ...` inside `score_song` | Rejected: every new mode makes `score_song` longer and easier to break |
| **Strategy as data** | Each strategy is a table of weights; `score_song` takes the table | **Chosen**: my modes only differ in point values, so a table is enough |
| Strategy as classes | A `RankingStrategy` class with a subclass per mode | Not yet: more code than needed. Worth it if a mode ever needs its own logic, like a "diversity" mode that avoids repeating genres |
| Template Method | A base recommender with fixed steps and overridable hooks | Rejected: too heavy for 4 modes that only change numbers |

We picked the data version because it's the simplest thing that keeps the code modular. Adding a new mode is one new line in `STRATEGIES`, and nothing else changes. The AI also suggested making every mode add up to the same maximum (4.5), so scores can be compared across modes.

What I checked myself:

- **Balanced mode didn't change anything.** The new code gives exactly the same output as before for all 12 profiles, so my earlier results are still valid.
- **Both code paths agree.** The `Recommender` class and `recommend_songs` give the same top 5 for every mode and profile.
- **A typo is caught.** `--mode bogus` shows an error listing the 4 valid modes, instead of crashing or silently using the default.
- **A claim needed fixing.** The AI first wrote that the #1 song stays the same in every mode except Energetic Classical. When we checked all 12 profiles, Clean Hip-Hop was also an exception, so the README was corrected.

**How does the pattern appear in your final code?**

- **The strategies:** `STRATEGIES` in `src/recommender.py` (line 13) holds the weight table for each mode. `MODES` lists them, with "balanced" first.
- **Picking a strategy:** `get_weights(mode)` (line 20) returns the right table. "balanced" reads the original weight constants, and an unknown mode raises a clear error.
- **Using a strategy:** `score_song(user_prefs, song, weights)` (line 120) never checks which mode it's in. It just uses whatever weights it's given. `recommend_songs(..., mode=...)` (line 205), `max_score(..., mode)` (line 192), and `Recommender(songs, mode=...)` (line 83) pass the strategy along.
- **Switching modes:** `src/main.py` has a `MODE` default (line 17) and a `--mode` option (line 141).
