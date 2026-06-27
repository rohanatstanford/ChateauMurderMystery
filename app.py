"""
Masquerade Murder Mystery - Game Moderator App
Streamlit web app with a player view and facilitator view.
"""

import json
import random
import string
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

# =============================================================================
# CONFIG: FILL IN YOUR DROPBOX LINKS BELOW
# -----------------------------------------------------------------------------
# For each round, add entries describing the media to embed.
# Each entry is a dict with keys: label, url, type
#   - type "video"  -> embedded as a video player (use .mp4 / .mov links)
#   - type "audio"  -> embedded as an audio player (use .mp3 / .wav links)
#   - type "link"   -> rendered as a clickable link (use for PDFs, etc.)
#
# To get an embeddable Dropbox link:
#   Take the share URL ending in `?dl=0` and replace `dl=0` with `raw=1`.
#   Example: https://www.dropbox.com/scl/fi/abc/round1.mp4?rlkey=xyz&raw=1
# =============================================================================
ROUND_MEDIA = {
    "Round 1": [
        # {"label": "Round 1 Video", "url": "https://www.dropbox.com/.../round1.mp4?raw=1", "type": "video"},
        # {"label": "Round 1 Audio Clue", "url": "https://www.dropbox.com/.../round1_clue.mp3?raw=1", "type": "audio"},
    ],
    "Round 2": [
        # {"label": "Round 2 Video", "url": "...", "type": "video"},
    ],
    "Round 3": [
        # {"label": "Round 3 Video", "url": "...", "type": "video"},
    ],
    "Round 4": [
        # {"label": "Round 4 Final Reveal", "url": "...", "type": "video"},
    ],
}

# Shared Dropbox folder (shown on facilitator page for reference)
DROPBOX_FOLDER_URL = (
    "https://www.dropbox.com/scl/fo/6eehtwnqlgbmm2gkj8nit/"
    "ABpyscCHh5AqiwOH73qagBs?rlkey=sgdb5jrpnd6q4ivnppdhkpma5&dl=0"
)

FACILITATOR_PASSWORD = "masquerade"

PLAYERS_ROLES = {
    "Chandani": "Countess",
    "Jermaine": "Turtle",
    "Rohan": "Hare",
    "Stephanie": "Dove",
    "Bindi": "Bluebird",
    "Kellen": "Dragon",
    "Cullen": "Stallion",
    "Ivy": "Unicorn",
    "Bharat": "Stag",
    "Nisha": "Phoenix",
    "Chintan": "Lion",
    "Kira": "Black Swan",
}

LETTERS = list(string.ascii_uppercase[:12])  # A..L


# -----------------------------------------------------------------------------
# Data loaders
# -----------------------------------------------------------------------------
@st.cache_data
def load_assignments() -> dict:
    """Load the persisted name -> letter assignments from assignments.json."""
    p = Path(__file__).parent / "assignments.json"
    with open(p) as f:
        return json.load(f)


# -----------------------------------------------------------------------------
# Page config + theme
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Masquerade Murder Mystery",
    page_icon="🎭",
    layout="centered",
)

st.markdown(
    """
    <style>
    .stApp {
        background: radial-gradient(ellipse at top, #1a1208 0%, #0a0a0a 70%);
        color: #f5d76e;
    }
    h1, h2, h3, h4 {
        color: #d4af37 !important;
        font-family: 'Georgia', 'Times New Roman', serif;
        letter-spacing: 1px;
    }
    .stMarkdown, p, label, .stRadio label, .stSelectbox label, .stTextInput label {
        color: #f5d76e !important;
    }
    .stButton>button {
        background: linear-gradient(135deg, #d4af37 0%, #b8941f 100%);
        color: #0a0a0a;
        font-weight: bold;
        border: 1px solid #d4af37;
        padding: 0.6em 1.4em;
        font-family: 'Georgia', serif;
        letter-spacing: 1px;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #f5d76e 0%, #d4af37 100%);
        color: #000;
    }
    .stTabs [data-baseweb="tab-list"] button {
        color: #d4af37;
    }
    section[data-testid="stSidebar"] {
        background: #0a0a0a;
        border-right: 1px solid #4a3a14;
    }
    .player-card {
        background: linear-gradient(135deg, #1a1208 0%, #2a1f0c 100%);
        border: 1px solid #d4af37;
        border-radius: 12px;
        padding: 24px;
        margin-top: 16px;
        box-shadow: 0 4px 20px rgba(212,175,55,0.2);
    }
    .player-card .letter {
        font-size: 72px;
        color: #f5d76e;
        text-align: center;
        font-family: 'Georgia', serif;
        letter-spacing: 4px;
        text-shadow: 0 0 20px rgba(245,215,110,0.6);
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# -----------------------------------------------------------------------------
# Reveal animation
# -----------------------------------------------------------------------------
def reveal_html(letter: str) -> str:
    """Black-and-gold masquerade reveal animation that ends on the given letter."""
    return f"""
<!DOCTYPE html>
<html>
<head>
<style>
  body {{ margin: 0; }}
  .stage {{
    position: relative;
    width: 100%;
    height: 540px;
    background: radial-gradient(circle at center, #2a1f0c 0%, #0a0a0a 60%, #000 100%);
    overflow: hidden;
    border: 2px solid #d4af37;
    border-radius: 12px;
    font-family: Georgia, 'Times New Roman', serif;
  }}
  .ring {{
    position: absolute;
    top: 50%; left: 50%;
    width: 320px; height: 320px;
    margin: -160px 0 0 -160px;
    border: 2px solid #d4af37;
    border-radius: 50%;
    opacity: 0;
    animation: ringExpand 2.4s ease-out forwards;
  }}
  .ring.r2 {{ animation-delay: 0.3s; border-color: #f5d76e; }}
  .ring.r3 {{ animation-delay: 0.6s; border-color: #b8941f; }}

  .mask-wrap {{
    position: absolute;
    top: 50%; left: 50%;
    width: 260px; height: 200px;
    margin: -110px 0 0 -130px;
    animation: maskSpin 2.6s cubic-bezier(.2,.7,.2,1) forwards,
               maskFade 0.6s ease-in 2.4s forwards;
    transform-origin: center;
  }}

  .letter {{
    position: absolute;
    top: 50%; left: 50%;
    transform: translate(-50%, -50%) scale(0);
    font-size: 220px;
    color: #f5d76e;
    text-shadow:
      0 0 18px rgba(245,215,110,0.9),
      0 0 36px rgba(212,175,55,0.7),
      0 0 80px rgba(184,148,31,0.6);
    opacity: 0;
    letter-spacing: 4px;
    animation: letterIn 1.0s cubic-bezier(.2,.9,.2,1.2) 2.8s forwards;
  }}

  .subtitle {{
    position: absolute;
    bottom: 32px; left: 0; right: 0;
    text-align: center;
    color: #d4af37;
    font-size: 18px;
    letter-spacing: 6px;
    text-transform: uppercase;
    opacity: 0;
    animation: fadeIn 0.8s ease 3.4s forwards;
  }}

  .sparkle {{
    position: absolute;
    width: 4px; height: 4px;
    background: #f5d76e;
    border-radius: 50%;
    box-shadow: 0 0 8px #f5d76e, 0 0 16px #d4af37;
    opacity: 0;
    animation: sparkleFloat 3s ease-in-out infinite;
  }}

  @keyframes maskSpin {{
    0%   {{ transform: rotate(0deg) scale(0.3); opacity: 0; }}
    30%  {{ opacity: 1; }}
    100% {{ transform: rotate(900deg) scale(1.2); opacity: 1; }}
  }}
  @keyframes maskFade {{
    to {{ opacity: 0; transform: rotate(900deg) scale(1.6); }}
  }}
  @keyframes ringExpand {{
    0%   {{ transform: scale(0.1); opacity: 0; }}
    50%  {{ opacity: 0.8; }}
    100% {{ transform: scale(1.8); opacity: 0; }}
  }}
  @keyframes letterIn {{
    0%   {{ transform: translate(-50%, -50%) scale(0) rotate(-20deg); opacity: 0; }}
    60%  {{ transform: translate(-50%, -50%) scale(1.15) rotate(2deg); opacity: 1; }}
    100% {{ transform: translate(-50%, -50%) scale(1) rotate(0deg); opacity: 1; }}
  }}
  @keyframes fadeIn {{
    to {{ opacity: 1; }}
  }}
  @keyframes sparkleFloat {{
    0%, 100% {{ opacity: 0; transform: translateY(0) scale(0.5); }}
    50%      {{ opacity: 1; transform: translateY(-30px) scale(1.2); }}
  }}
</style>
</head>
<body>
  <div class="stage">
    <div class="ring r1"></div>
    <div class="ring r2"></div>
    <div class="ring r3"></div>

    <!-- floating sparkles -->
    <div class="sparkle" style="top:20%; left:15%; animation-delay:0.2s;"></div>
    <div class="sparkle" style="top:30%; left:80%; animation-delay:0.7s;"></div>
    <div class="sparkle" style="top:65%; left:10%; animation-delay:1.1s;"></div>
    <div class="sparkle" style="top:75%; left:78%; animation-delay:1.6s;"></div>
    <div class="sparkle" style="top:18%; left:60%; animation-delay:2.0s;"></div>
    <div class="sparkle" style="top:80%; left:45%; animation-delay:2.4s;"></div>
    <div class="sparkle" style="top:40%; left:30%; animation-delay:2.8s;"></div>
    <div class="sparkle" style="top:55%; left:88%; animation-delay:3.2s;"></div>

    <div class="mask-wrap">
      <!-- Stylized masquerade mask -->
      <svg viewBox="0 0 260 200" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <linearGradient id="g" x1="0" x2="0" y1="0" y2="1">
            <stop offset="0%" stop-color="#f5d76e"/>
            <stop offset="50%" stop-color="#d4af37"/>
            <stop offset="100%" stop-color="#8a6a14"/>
          </linearGradient>
        </defs>
        <!-- Left side -->
        <path d="M130,100
                 C 110,40 30,40 20,100
                 C 15,140 60,160 90,150
                 C 110,144 125,128 130,110
                 Z"
              fill="url(#g)" stroke="#f5d76e" stroke-width="2"/>
        <!-- Right side -->
        <path d="M130,100
                 C 150,40 230,40 240,100
                 C 245,140 200,160 170,150
                 C 150,144 135,128 130,110
                 Z"
              fill="url(#g)" stroke="#f5d76e" stroke-width="2"/>
        <!-- Eye holes -->
        <ellipse cx="70" cy="100" rx="22" ry="14" fill="#000"/>
        <ellipse cx="190" cy="100" rx="22" ry="14" fill="#000"/>
        <!-- Top flourish -->
        <path d="M130,60 Q140,30 160,40 Q150,55 130,60 Z" fill="#f5d76e"/>
        <path d="M130,60 Q120,30 100,40 Q110,55 130,60 Z" fill="#f5d76e"/>
        <!-- Decorative dots -->
        <circle cx="40" cy="90" r="2" fill="#f5d76e"/>
        <circle cx="50" cy="120" r="2" fill="#f5d76e"/>
        <circle cx="210" cy="120" r="2" fill="#f5d76e"/>
        <circle cx="220" cy="90" r="2" fill="#f5d76e"/>
      </svg>
    </div>

    <div class="letter">{letter}</div>
    <div class="subtitle">&#10086; The Murderer &#10086;</div>
  </div>
</body>
</html>
"""


# -----------------------------------------------------------------------------
# Sidebar navigation
# -----------------------------------------------------------------------------
st.sidebar.markdown("## 🎭 Masquerade")
section = st.sidebar.radio("View", ["Players", "Facilitator"])
st.sidebar.markdown("---")
st.sidebar.caption("Players: see your character & secret letter.")
st.sidebar.caption("Facilitator: control rounds, reveal the murderer.")


# -----------------------------------------------------------------------------
# PLAYER VIEW
# -----------------------------------------------------------------------------
if section == "Players":
    st.title("🎭 Masquerade Murder Mystery")
    st.markdown("### Player Assignment")
    st.write(
        "Select your name from the list (or type it) to reveal your character "
        "and your secret letter."
    )

    mode = st.radio(
        "How would you like to find your name?",
        ["Select from list", "Type my name"],
        horizontal=True,
    )

    if mode == "Select from list":
        name = st.selectbox(
            "Your name",
            [""] + sorted(PLAYERS_ROLES.keys()),
            format_func=lambda x: "— choose your name —" if x == "" else x,
        )
    else:
        typed = st.text_input("Type your name (exact spelling):")
        name = ""
        if typed:
            # Case-insensitive match
            for n in PLAYERS_ROLES:
                if n.lower() == typed.strip().lower():
                    name = n
                    break
            if not name:
                st.error("Name not found. Check spelling or use the dropdown.")

    if name:
        assignments = load_assignments()
        role = PLAYERS_ROLES[name]
        letter = assignments[name]
        st.markdown(
            f"""
            <div class="player-card">
                <h3 style="margin-top:0;">Welcome, {name}</h3>
                <p style="font-size:18px; margin-bottom:4px;"><b>Your character:</b> {role}</p>
                <p style="font-size:14px; color:#b8941f; margin-top:0;">Your secret letter</p>
                <div class="letter">{letter}</div>
                <p style="text-align:center; font-size:13px; color:#b8941f; letter-spacing:2px;">
                    KEEP THIS SECRET
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption(
            "If your letter is called during Setup, you are the murderer. "
            "Do not reveal your identity!"
        )


# -----------------------------------------------------------------------------
# FACILITATOR VIEW
# -----------------------------------------------------------------------------
else:
    st.title("🎭 Facilitator Console")

    # Password gate using session state so it persists across reruns
    if "facilitator_ok" not in st.session_state:
        st.session_state.facilitator_ok = False

    if not st.session_state.facilitator_ok:
        pw = st.text_input("Facilitator password", type="password")
        if st.button("Enter"):
            if pw == FACILITATOR_PASSWORD:
                st.session_state.facilitator_ok = True
                st.rerun()
            else:
                st.error("Incorrect password.")
        st.stop()

    # Game stage selector
    stage = st.radio(
        "Game stage",
        ["Setup", "Round 1", "Round 2", "Round 3", "Round 4"],
        horizontal=True,
    )

    st.markdown("---")

    # Persist the chosen murderer letter across reruns
    if "murderer_letter" not in st.session_state:
        st.session_state.murderer_letter = None

    if stage == "Setup":
        st.subheader("Setup — Select the Murderer")
        st.write(
            "Click below to randomly choose the secret letter. The player "
            "whose letter matches is the murderer for this game."
        )

        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("🎭 Reveal the Murderer"):
                st.session_state.murderer_letter = random.choice(LETTERS)
        with col2:
            if st.session_state.murderer_letter is not None:
                if st.button("🔄 Reset"):
                    st.session_state.murderer_letter = None
                    st.rerun()

        if st.session_state.murderer_letter is not None:
            components.html(
                reveal_html(st.session_state.murderer_letter),
                height=580,
            )
            st.success(
                f"The murderer's letter is **{st.session_state.murderer_letter}**. "
                "Only the player holding that letter knows who they are."
            )

    else:
        st.subheader(stage)
        items = ROUND_MEDIA.get(stage, [])

        if not items:
            st.info(
                f"No media configured for **{stage}** yet.\n\n"
                "Edit `ROUND_MEDIA` at the top of `app.py` to add Dropbox links."
            )
            st.markdown(f"[📁 Open shared Dropbox folder]({DROPBOX_FOLDER_URL})")
        else:
            for item in items:
                st.markdown(f"**{item['label']}**")
                kind = item.get("type", "link")
                try:
                    if kind == "video":
                        st.video(item["url"])
                    elif kind == "audio":
                        st.audio(item["url"])
                    else:
                        st.markdown(f"[Open {item['label']}]({item['url']})")
                except Exception as e:
                    st.error(f"Could not load media: {e}")
                    st.markdown(f"[Direct link]({item['url']})")
                st.markdown("---")

            st.markdown(f"[📁 Open shared Dropbox folder]({DROPBOX_FOLDER_URL})")

    st.markdown("---")
    if st.button("Log out"):
        st.session_state.facilitator_ok = False
        st.session_state.murderer_letter = None
        st.rerun()
