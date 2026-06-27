# Masquerade Murder Mystery — Moderator App

A Streamlit web app for running the Masquerade Murder Mystery game.

## Files

- `app.py` — the Streamlit app
- `assignments.json` — randomized name → letter mapping (do not open if you want to stay surprised!)
- `requirements.txt` — Python dependencies

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit Community Cloud

1. Push these three files (`app.py`, `assignments.json`, `requirements.txt`) to a GitHub repo.
2. Go to [share.streamlit.io](https://share.streamlit.io) and connect the repo.
3. Set the main file to `app.py`.

## Facilitator password

The facilitator view is gated by a password set in `app.py`:

```python
FACILITATOR_PASSWORD = "masquerade"
```

Change it if you want.

## Adding round media

Open `app.py` and edit the `ROUND_MEDIA` dictionary near the top.

For each round, add entries like:

```python
"Round 1": [
    {"label": "Round 1 Intro Video", "url": "https://www.dropbox.com/.../round1.mp4?raw=1", "type": "video"},
    {"label": "Round 1 Audio Clue", "url": "https://www.dropbox.com/.../clue.mp3?raw=1", "type": "audio"},
],
```

**Dropbox link tip:** To make a share link embeddable, replace `?dl=0` at the end with `?raw=1` (for videos/audio that Streamlit should stream).

Supported types: `video`, `audio`, `link`.

## How the game flows

1. **Players** — each player opens the app, selects "Players" in the sidebar, picks their name, and sees their character + secret letter.
2. **Facilitator (Setup)** — log into the facilitator view, stay on "Setup", and click **Reveal the Murderer**. A masquerade animation plays and reveals a random letter A–L. The player whose letter matches is the secret murderer.
3. **Facilitator (Rounds 1–4)** — switch to the appropriate round to play embedded videos/audio for the table.
