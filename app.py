# AI helped generate this code

import csv
from pathlib import Path

import chromadb
import gradio as gr
from sentence_transformers import SentenceTransformer


# Load the embedding model from the starter example.
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# Open the database folder next to app.py.
project_folder = Path(__file__).resolve().parent
client = chromadb.PersistentClient(path=str(project_folder / "chromadb"))
collection = client.get_or_create_collection("episode_transcript")


def build_database():
    """Read the transcript, chunk the dialogue, and save the embeddings."""
    csv_path = Path.home() / "Downloads" / "transcript.csv"

    with csv_path.open(encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))

    # Group dialogue by the 30-second window in which each line starts.
    windows = {}
    for row in sorted(rows, key=lambda row: int(row["start"])):
        text = row["text"].strip()
        if not text or "Transcribed by TurboScribe" in text:
            continue

        window = int(row["start"]) // 30_000
        windows.setdefault(window, []).append(row)

    ids = []
    texts = []
    timestamps = []

    for window, lines in windows.items():
        ids.append(str(window))
        texts.append(" ".join(line["text"].strip() for line in lines))
        timestamps.append({
            "start": int(lines[0]["start"]),
            "end": max(int(line["end"]) for line in lines),
        })

    embeddings = model.encode(texts)
    collection.upsert(
        ids=ids,
        documents=texts,
        embeddings=embeddings.tolist(),
        metadatas=timestamps,
    )
    print(f"Saved {collection.count()} passages to chromadb/")


def format_timestamp(milliseconds):
    minutes, seconds = divmod(milliseconds // 1_000, 60)
    return f"{minutes}:{seconds:02d}"


def semantic_search(query):
    query = query.strip()
    if not query:
        return "Enter a description of the scene you want to find."

    query_embedding = model.encode([query])
    results = collection.query(
        query_embeddings=query_embedding.tolist(),
        n_results=min(3, collection.count()),
        include=["documents", "metadatas"],
    )

    matches = []
    for text, times in zip(results["documents"][0], results["metadatas"][0]):
        start = format_timestamp(times["start"])
        end = format_timestamp(times["end"])
        matches.append(f"{start}–{end}\n{text}")

    return "\n\n".join(matches)


if __name__ == "__main__":
    if collection.count() == 0:
        build_database()

    demo = gr.Interface(
        fn=semantic_search,
        inputs=gr.Textbox(label="Describe a scene"),
        outputs=gr.Textbox(label="Top matches", lines=12),
        title="Austin & Ally Scene Finder",
        description="Describe a moment from the episode to find matching dialogue and timestamps.",
    )
    demo.launch()