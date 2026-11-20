# AI helped generate this slide

---
title: Austin and Ally Scene Finder
sdk: gradio
sdk_version: 6.32.0
app_file: app.py
---

# Austin & Ally Scene Finder

AIPI 510 · Week 13 Semantic Search Activity

The app searches the dialogue in the *Austin & Ally* episode “Duets and Destiny.” Describe a moment in your own words, and the app returns the three closest transcript passages with their start and end timestamps.

## Repository structure

| Path | Purpose |
|---|---|
| `app.py` | Builds the search database from the source CSV when the collection is empty, then runs the Gradio app. |
| `requirements.txt` | Lists the Python dependencies and their versions. |
| `chromadb/` | Contains the saved Chroma database, including `chroma.sqlite3` and any generated index files. |
| `README.md` | Documents the dataset, build process, and Hugging Face configuration. |

## Run the app with the saved database

Use Python 3.12. In the repository folder, run:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:7860` or the local URL printed in the terminal. The first run downloads the embedding model and requires an internet connection.

The repository includes the populated `chromadb/` directory, which is sufficient to run the search. The source CSV is needed only to rebuild the database.

## Source data

The input is a TurboScribe CSV transcript of Disney Channel’s *Austin & Ally* episode “Duets and Destiny,” posted under the title “Austin & Ally FULL Episode ‘Duets and Destiny’ | The Big Reunion.” The source CSV contains 516 entries and uses these columns:

| Column | Meaning |
|---|---|
| `start` | Start time of the transcript segment in milliseconds |
| `end` | End time of the transcript segment in milliseconds |
| `text` | Transcribed dialogue |

The timestamps refer to this specific upload. Rebuilding the same 49 passages requires the original CSV export. A new transcription of the episode may segment or timestamp the dialogue differently.

## Rebuild the database from the CSV

1. Save the original CSV as `~/Downloads/transcript.csv`.
2. Stop the app with `Ctrl+C` if it is running.
3. In a separate local checkout, rename the existing `chromadb/` directory to `chromadb-backup/` so the app starts with an empty collection.
4. Run `python app.py`. With the original CSV, the terminal should print `Saved 49 passages to chromadb/`. The app will then start.

### How the database is built

1. Sort the transcript rows by start time. Strip surrounding whitespace and skip blank text and the TurboScribe notice.
2. Assign each row to a 30-second window using `start // 30_000`. Join the dialogue within each window in chronological order. A segment that crosses a window boundary stays with the window where it starts.
3. Use the window number as the passage ID. Store the first segment’s start time and the latest end time as metadata.
4. Embed each passage with `sentence-transformers/all-MiniLM-L6-v2`. Save the text, embedding, and timestamps in the `episode_transcript` collection with Chroma’s `PersistentClient`.

## Verify the search

1. Search for `two people are excited to see each other again`. Check whether the opening reunion appears among the three results and whether its timestamp takes you to the matching dialogue.
2. Submit a blank query. The app should ask you to enter a description.
3. Stop and restart the app. Repeat the first search to verify that the app can reopen the saved database.

For each nonblank query, the app uses the same embedding model as the database build and asks Chroma for the three closest passages. The app searches the spoken dialogue, so moments that are conveyed only through visuals may be harder to find.