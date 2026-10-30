# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name  

Give your model a short, descriptive name.  
Example: **VibeFinder 1.0**  

---

## 2. Intended Use  

Describe what your recommender is designed to do and who it is for. 

Prompts:  

- What kind of recommendations does it generate  
- What assumptions does it make about the user  
- Is this for real users or classroom exploration  

---

## 3. How the Model Works  

Think of the recommender as a judge at a talent show. Each song comes up on stage one at a time, the judge gives it points based on how well it fits your taste, and at the end the songs with the most points are your recommendations.

**What the judge knows about you.** You tell it four things: your favorite genre (like pop), the mood you want (like happy), how energetic you want the music to be on a scale from calm to intense, and whether you prefer acoustic or electronic sound.

**What the judge looks at in each song.** Every song in the catalog has a genre label, a mood label, an energy level, and a measure of how acoustic it sounds. The catalog also lists tempo, danceability, and how positive a song feels, but the judge ignores those for now. Tempo and danceability rise and fall almost exactly with energy in this catalog, so counting them too would reward energy three times over.

**How points are given.**

- **Right genre: 2 points.** This counts the most, because people usually describe their taste by genre first.
- **Right mood: 1 point.** Mood matters, but a song in your genre with a slightly different mood is usually a smaller miss than a song in the wrong genre.
- **Energy: up to 1 point.** The closer a song's energy is to what you asked for, the more points it gets. A perfect match earns the full point. The judge rewards being *close*, not being *high*: if you want calm music, a calm song beats a loud one.
- **Sound: up to half a point.** If you like acoustic music, more acoustic songs earn more. If you prefer electronic, the reverse. This is kept small so it mostly settles close calls.

A perfect song would score 4.5 points.

**Turning scores into recommendations.** Once every song has a score, the judge lines them up from highest to lowest and hands you the top five. If two songs tie, the one listed earlier in the catalog goes first. Each recommendation comes with its reasons, such as "genre match" and "energy similarity", so you can see exactly why it was picked.

**Changes from the starter.** The starter came with empty placeholder functions, so I wrote the loading, scoring, and ranking steps. I also added the acoustic-versus-electronic preference to the sample user in `main.py` (the starter's sample only had genre, mood, and energy), made matching ignore capital letters and extra spaces, and added a clear tie-breaking rule and a list of reasons for every recommendation.

---

## 4. Data  

Describe the dataset the model uses.  

Prompts:  

- How many songs are in the catalog  
- What genres or moods are represented  
- Did you add or remove data  
- Are there parts of musical taste missing in the dataset  

---

## 5. Strengths  

Where does your system seem to work well  

Prompts:  

- User types for which it gives reasonable results  
- Any patterns you think your scoring captures correctly  
- Cases where the recommendations matched your intuition  

---

## 6. Limitations and Bias 

Where the system struggles or behaves unfairly. 

Prompts:  

- Features it does not consider  
- Genres or moods that are underrepresented  
- Cases where the system overfits to one preference  
- Ways the scoring might unintentionally favor some users  

---

## 7. Evaluation  

How you checked whether the recommender behaved as expected. 

Prompts:  

- Which user profiles you tested  
- What you looked for in the recommendations  
- What surprised you  
- Any simple tests or comparisons you ran  

No need for numeric metrics unless you created some.

---

## 8. Future Work  

Ideas for how you would improve the model next.  

Prompts:  

- Additional features or preferences  
- Better ways to explain recommendations  
- Improving diversity among the top results  
- Handling more complex user tastes  

---

## 9. Personal Reflection  

A few sentences about your experience.  

Prompts:  

- What you learned about recommender systems  
- Something unexpected or interesting you discovered  
- How this changed the way you think about music recommendation apps  
