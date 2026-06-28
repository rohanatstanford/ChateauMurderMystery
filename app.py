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
# =============================================================================
ROUND_MEDIA = {
    "Round 1": [
        {"label": "Round 1 Audio Clue", "url": "https://www.dropbox.com/scl/fo/6eehtwnqlgbmm2gkj8nit/ALC0yB9IAeIUOI8IM0HayMg/Detective%20Audio%20Files/Masquerade%20Round%201.mp3?rlkey=sgdb5jrpnd6q4ivnppdhkpma5&e=1&raw=1", "type": "audio"},
    ],
    "Round 2": [
        {"label": "Round 2 Audio Clue", "url": "https://www.dropbox.com/scl/fo/6eehtwnqlgbmm2gkj8nit/APvCW0u3jrwNHaehOwYRKnk/Detective%20Audio%20Files/Masquerade%20Round%202.mp3?rlkey=sgdb5jrpnd6q4ivnppdhkpma5&e=1&raw=1", "type": "audio"},
    ],
    "Round 3": [
        {"label": "Round 3 Audio Clue", "url": "https://www.dropbox.com/scl/fo/6eehtwnqlgbmm2gkj8nit/AJnyG9ebrcbx4KPZhCbrYXc/Detective%20Audio%20Files/Masquerade%20Round%203.mp3?rlkey=sgdb5jrpnd6q4ivnppdhkpma5&e=1&raw=1", "type": "audio"},
    ],
    "Round 4": [
        {"label": "Round 4 Audio Clue", "url": "https://www.dropbox.com/scl/fo/6eehtwnqlgbmm2gkj8nit/ANlg-cmO1jRUt4ZcdZfJEPA/Detective%20Audio%20Files/Masquerade%20Round%204.mp3?rlkey=sgdb5jrpnd6q4ivnppdhkpma5&e=1&raw=1", "type": "audio"},
    ],
}

# Closing audio (moved from Round 4 Final).
CLOSING_AUDIO = {
    "label": "Closing Audio Clue",
    "url": "https://www.dropbox.com/scl/fo/6eehtwnqlgbmm2gkj8nit/AC3yFFFTubPe3QPMm_5Xhc8/Detective%20Audio%20Files/Masquerade%20Round%204%20Final.mp3?rlkey=sgdb5jrpnd6q4ivnppdhkpma5&e=1&raw=1",
    "type": "audio",
}

DROPBOX_FOLDER_URL = (
    "https://www.dropbox.com/scl/fo/6eehtwnqlgbmm2gkj8nit/"
    "ABpyscCHh5AqiwOH73qagBs?rlkey=sgdb5jrpnd6q4ivnppdhkpma5&dl=0"
)

FACILITATOR_PASSWORD = "masquerade"

PLAYERS_ROLES = {
    "Chandani":  "Countess",
    "Jermaine":  "Turtle",
    "Rohan":     "Hare",
    "Stephanie": "Dove",
    "Bindi":     "Bluebird",
    "Kellen":    "Dragon",
    "Cullen":    "Stallion",
    "Ivy":       "Unicorn",
    "Bharat":    "Stag",
    "Nisha":     "Phoenix",
    "Chintan":   "Lion",
    "Kira":      "Black Swan",
}
PLAYER_NAMES = list(PLAYERS_ROLES.keys())
LETTERS = list(string.ascii_uppercase[:12])

ROUND_STAGES = ["Setup", "Round 1", "Round 2", "Round 3", "Round 4", "Closing"]


# -----------------------------------------------------------------------------
# Data loaders
# -----------------------------------------------------------------------------
@st.cache_data
def load_assignments() -> dict:
    """name -> letter"""
    p = Path(__file__).parent / "assignments.json"
    with open(p) as f:
        return json.load(f)


@st.cache_data
def load_groups() -> dict:
    """group_name -> [player_names]"""
    p = Path(__file__).parent / "groups.json"
    with open(p) as f:
        return json.load(f)


def letter_to_name(letter: str):
    assignments = load_assignments()
    for n, l in assignments.items():
        if l == letter:
            return n
    return None


# -----------------------------------------------------------------------------
# Page config + session state defaults
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Masquerade Murder Mystery",
    page_icon="🎭",
    layout="wide",
    initial_sidebar_state="expanded",
)

_defaults = {
    "facilitator_ok": False,
    "murderer_letter": None,
    "murderer_name": None,
    "reveal_active": False,
    "music_on": True,
    # Per-round random first-asker + answer checklist
    "round2_asker": None,
    "round3_asker": None,
    "round4_asker": None,
    "round2_answered": {n: False for n in PLAYER_NAMES},
    "round3_answered": {n: False for n in PLAYER_NAMES},
    "round4_answered": {n: False for n in PLAYER_NAMES},
    # Closing flow state machine: "audio" -> "accusations" -> "statements" -> "reveal"
    "closing_step": "audio",
    "accusation_order": None,    # list of player names, shuffled
    "accusation_index": 0,
    "accusations": {},           # accuser -> accused
    "final_order": None,         # innocents shuffled + murderer last
    "final_index": 0,
    "results_revealed": False,
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# -----------------------------------------------------------------------------
# Global CSS theme
# -----------------------------------------------------------------------------
def inject_global_css(is_facilitator: bool, hide_chrome: bool):
    """Inject the page CSS. hide_chrome=True nukes sidebar/header for cinematic full-screen."""
    chrome_css = ""
    if hide_chrome:
        chrome_css = """
        section[data-testid="stSidebar"] { display: none !important; }
        header[data-testid="stHeader"] { display: none !important; }
        .stApp > header { display: none !important; }
        div[data-testid="stToolbar"] { display: none !important; }
        .main .block-container { padding-top: 0 !important; padding-left: 1rem !important; padding-right: 1rem !important; max-width: 100% !important; }
        """

    if is_facilitator:
        container_css = """
        .main .block-container {
            max-width: 100% !important;
            padding-left: 4rem !important;
            padding-right: 4rem !important;
            padding-top: 2rem !important;
        }
        """
    else:
        container_css = """
        .main .block-container {
            max-width: 760px !important;
            padding-top: 3rem !important;
        }
        """

    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;800&family=Cormorant+Garamond:ital,wght@0,400;0,600;1,400&display=swap');

        .stApp {{
            background:
              radial-gradient(ellipse at 20% 10%, #2a1f0c 0%, transparent 50%),
              radial-gradient(ellipse at 80% 90%, #1a0f04 0%, transparent 50%),
              linear-gradient(135deg, #0a0703 0%, #0a0a0a 100%);
            color: #f5d76e;
            font-family: 'Cormorant Garamond', Georgia, serif;
        }}
        h1, h2, h3, h4, h5 {{
            color: #d4af37 !important;
            font-family: 'Cinzel', Georgia, serif !important;
            letter-spacing: 2px;
            text-shadow: 0 0 20px rgba(212,175,55,0.3);
        }}
        h1 {{ font-size: 3rem !important; }}
        h2 {{ font-size: 2.2rem !important; }}
        p, label, .stMarkdown, .stRadio label, .stSelectbox label, .stTextInput label, .stCaption {{
            color: #f5d76e !important;
            font-size: 1.05rem;
        }}
        .stButton>button {{
            background: linear-gradient(135deg, #d4af37 0%, #b8941f 100%);
            color: #0a0a0a;
            font-weight: 700;
            border: 1px solid #f5d76e;
            padding: 0.7em 1.6em;
            font-family: 'Cinzel', Georgia, serif;
            letter-spacing: 2px;
            text-transform: uppercase;
            font-size: 0.95rem;
            box-shadow: 0 4px 14px rgba(212,175,55,0.3);
            transition: all .25s ease;
        }}
        .stButton>button:hover {{
            background: linear-gradient(135deg, #f5d76e 0%, #d4af37 100%);
            color: #000;
            transform: translateY(-1px);
            box-shadow: 0 6px 22px rgba(245,215,110,0.5);
        }}
        .stTabs [data-baseweb="tab-list"] button {{ color: #d4af37; }}
        section[data-testid="stSidebar"] {{
            background: linear-gradient(180deg, #0a0703 0%, #1a1208 100%);
            border-right: 1px solid #4a3a14;
        }}
        section[data-testid="stSidebar"] * {{ color: #d4af37; }}

        /* Radio (stage selector) */
        .stRadio > div {{
            gap: 14px;
            justify-content: center;
            flex-wrap: wrap;
        }}
        .stRadio > div > label {{
            background: rgba(26,18,8,0.6);
            border: 1px solid #4a3a14;
            border-radius: 8px;
            padding: 10px 18px;
            transition: all .2s ease;
        }}
        .stRadio > div > label:hover {{
            border-color: #d4af37;
            background: rgba(42,31,12,0.8);
        }}
        .stRadio > div > label:has(input:checked) {{
            border-color: #f5d76e;
            background: linear-gradient(135deg, rgba(212,175,55,0.2), rgba(245,215,110,0.1));
            box-shadow: 0 0 20px rgba(245,215,110,0.3);
        }}

        /* Expander styling */
        .streamlit-expanderHeader, [data-testid="stExpander"] summary {{
            background: linear-gradient(135deg, #1a1208 0%, #221706 100%) !important;
            border: 1px solid #4a3a14 !important;
            border-left: 4px solid #d4af37 !important;
            border-radius: 8px !important;
            color: #f5d76e !important;
            font-family: 'Cinzel', serif !important;
            letter-spacing: 2px !important;
        }}
        [data-testid="stExpander"] {{
            border: 1px solid #4a3a14;
            border-radius: 8px;
            background: rgba(10,7,3,0.4);
        }}

        /* Checkbox styling */
        .stCheckbox label {{ color: #f5d76e !important; font-size: 1.1rem !important; }}
        .stCheckbox label[data-checked="true"] p,
        .stCheckbox label:has(input:checked) p {{
            color: #8a6a14 !important; text-decoration: line-through;
        }}

        /* Player card */
        .player-card {{
            background: linear-gradient(135deg, #1a1208 0%, #2a1f0c 100%);
            border: 2px solid #d4af37;
            border-radius: 16px;
            padding: 32px;
            margin-top: 20px;
            box-shadow: 0 8px 32px rgba(212,175,55,0.25), inset 0 1px 0 rgba(245,215,110,0.2);
        }}
        .player-card .letter {{
            font-size: 96px;
            color: #f5d76e;
            text-align: center;
            font-family: 'Cinzel', Georgia, serif;
            letter-spacing: 6px;
            text-shadow: 0 0 30px rgba(245,215,110,0.7), 0 0 60px rgba(212,175,55,0.4);
            margin: 12px 0;
        }}

        /* Facilitator hero header */
        .facilitator-hero {{
            text-align: center;
            padding: 20px 0 30px;
            border-bottom: 1px solid #4a3a14;
            margin-bottom: 32px;
        }}
        .facilitator-hero .title {{
            font-family: 'Cinzel', Georgia, serif;
            font-size: 3.4rem;
            font-weight: 800;
            color: #f5d76e;
            letter-spacing: 8px;
            text-shadow: 0 0 30px rgba(245,215,110,0.5);
            margin: 0;
        }}
        .facilitator-hero .subtitle {{
            font-family: 'Cormorant Garamond', serif;
            font-style: italic;
            font-size: 1.3rem;
            color: #d4af37;
            letter-spacing: 4px;
            margin-top: 6px;
        }}
        .facilitator-hero .ornament {{
            color: #d4af37;
            font-size: 1.5rem;
            margin: 8px 0;
            letter-spacing: 8px;
        }}

        /* Round media card */
        .media-card {{
            background: linear-gradient(135deg, #1a1208 0%, #221706 100%);
            border: 1px solid #4a3a14;
            border-left: 4px solid #d4af37;
            border-radius: 8px;
            padding: 24px 28px;
            margin-bottom: 24px;
            box-shadow: 0 6px 24px rgba(0,0,0,0.5);
        }}
        .media-card .media-title {{
            font-family: 'Cinzel', serif;
            font-size: 1.4rem;
            color: #f5d76e;
            letter-spacing: 3px;
            margin-bottom: 14px;
            text-transform: uppercase;
        }}

        /* Group card (Round 1) */
        .group-card {{
            background: linear-gradient(135deg, #1a1208 0%, #2a1f0c 100%);
            border: 2px solid #d4af37;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 16px;
            box-shadow: 0 4px 18px rgba(212,175,55,0.2);
            text-align: center;
        }}
        .group-card h4 {{
            margin: 0 0 12px 0;
            font-size: 1.5rem !important;
            color: #f5d76e !important;
        }}
        .group-card .name {{
            display: block;
            font-family: 'Cormorant Garamond', serif;
            font-size: 1.3rem;
            color: #f5d76e;
            padding: 6px 0;
            border-bottom: 1px solid rgba(212,175,55,0.2);
        }}
        .group-card .name:last-child {{ border-bottom: none; }}

        /* Big asker reveal */
        .asker-reveal {{
            text-align: center;
            padding: 30px;
            margin: 20px 0;
            background: linear-gradient(135deg, #1a1208 0%, #2a1f0c 100%);
            border: 2px solid #d4af37;
            border-radius: 16px;
            box-shadow: 0 8px 32px rgba(212,175,55,0.3);
        }}
        .asker-reveal .label {{
            color: #d4af37;
            letter-spacing: 6px;
            font-size: 14px;
            text-transform: uppercase;
        }}
        .asker-reveal .name {{
            font-family: 'Cinzel', serif;
            font-size: 4rem;
            color: #f5d76e;
            text-shadow: 0 0 24px rgba(245,215,110,0.6);
            letter-spacing: 4px;
            margin: 8px 0;
        }}

        /* Audio/video sizing */
        audio, video {{ width: 100% !important; }}
        audio {{
            filter: sepia(0.5) saturate(1.4) hue-rotate(-10deg);
            height: 54px;
        }}
        video {{
            max-height: 70vh;
            border: 2px solid #4a3a14;
            border-radius: 8px;
        }}

        /* Closing flow */
        .closing-stage {{
            text-align: center;
            padding: 40px 20px;
        }}
        .closing-stage .stage-title {{
            font-family: 'Cinzel', serif;
            font-size: 4rem;
            color: #f5d76e;
            letter-spacing: 8px;
            text-shadow: 0 0 24px rgba(245,215,110,0.5);
            text-transform: uppercase;
            margin: 0;
        }}
        .closing-stage .stage-sub {{
            font-family: 'Cormorant Garamond', serif;
            font-style: italic;
            font-size: 1.5rem;
            color: #d4af37;
            letter-spacing: 4px;
            margin: 8px 0 32px;
        }}
        .closing-stage .big-name {{
            font-family: 'Cinzel', serif;
            font-size: 5rem;
            color: #f5d76e;
            letter-spacing: 6px;
            text-shadow: 0 0 28px rgba(245,215,110,0.7);
            margin: 20px 0;
        }}
        .closing-stage .progress-pill {{
            display: inline-block;
            background: rgba(212,175,55,0.1);
            border: 1px solid #4a3a14;
            border-radius: 999px;
            padding: 6px 22px;
            color: #d4af37;
            letter-spacing: 4px;
            font-size: 0.95rem;
            margin-bottom: 24px;
        }}
        .closing-stage .prompt-card {{
            background: linear-gradient(135deg, #1a1208 0%, #2a1f0c 100%);
            border: 2px solid #d4af37;
            border-radius: 16px;
            padding: 32px;
            max-width: 720px;
            margin: 0 auto 32px;
            box-shadow: 0 8px 32px rgba(212,175,55,0.25);
        }}
        .closing-stage .innocent-banner {{
            font-family: 'Cinzel', serif;
            color: #f5d76e;
            letter-spacing: 8px;
            font-size: 1.4rem;
        }}
        .closing-stage .guilty-banner {{
            font-family: 'Cinzel', serif;
            color: #ff6b6b;
            letter-spacing: 8px;
            font-size: 1.6rem;
            text-shadow: 0 0 24px rgba(255,107,107,0.5);
        }}

        .results-row {{
            display: flex; justify-content: space-between; align-items: center;
            background: rgba(26,18,8,0.6); border-left: 4px solid #4a3a14;
            border-radius: 6px; padding: 10px 18px; margin: 6px 0;
            font-family: 'Cormorant Garamond', serif; font-size: 1.15rem;
            color: #f5d76e;
        }}
        .results-row.correct {{ border-left-color: #4ade80; background: rgba(74,222,128,0.08); }}
        .results-row.wrong   {{ border-left-color: #ef4444; background: rgba(239,68,68,0.05); color: #b8941f;}}
        .results-row .verdict {{ font-family: 'Cinzel', serif; letter-spacing: 3px; font-size: 0.9rem; }}

        .inspector-crown {{
            text-align: center; padding: 32px;
            background: radial-gradient(circle, rgba(212,175,55,0.25), transparent 70%);
            border: 2px solid #f5d76e; border-radius: 20px;
            margin: 32px auto; max-width: 720px;
        }}
        .inspector-crown .label {{
            color: #d4af37; letter-spacing: 8px; font-size: 1rem; text-transform: uppercase;
        }}
        .inspector-crown .name {{
            font-family: 'Cinzel', serif; font-size: 3.4rem; color: #f5d76e;
            text-shadow: 0 0 30px rgba(245,215,110,0.7);
            letter-spacing: 5px; margin: 12px 0;
        }}

        {container_css}
        {chrome_css}
        </style>
        """,
        unsafe_allow_html=True,
    )


# -----------------------------------------------------------------------------
# Background music (Tone.js procedural ambient)
# -----------------------------------------------------------------------------
def background_music_html(enabled: bool) -> str:
    enabled_js = "true" if enabled else "false"
    return f"""
<!DOCTYPE html>
<html><head>
<style>
  body {{ margin: 0; background: transparent; font-family: Georgia, serif; }}
  .music-bar {{
    display: flex; align-items: center; justify-content: space-between;
    background: linear-gradient(135deg, rgba(26,18,8,0.9), rgba(42,31,12,0.9));
    border: 1px solid #4a3a14; border-radius: 8px;
    padding: 10px 16px; color: #d4af37; font-size: 13px;
    letter-spacing: 2px; text-transform: uppercase;
  }}
  .music-bar .label {{ display: flex; align-items: center; gap: 10px; }}
  .music-bar .eq {{ display:inline-flex; gap:3px; align-items:flex-end; height: 14px; }}
  .music-bar .eq span {{
    width: 3px; background: #d4af37; display: inline-block;
    animation: eq 1.1s ease-in-out infinite;
  }}
  .music-bar .eq span:nth-child(1) {{ animation-delay: 0s; height: 6px; }}
  .music-bar .eq span:nth-child(2) {{ animation-delay: .25s; height: 12px; }}
  .music-bar .eq span:nth-child(3) {{ animation-delay: .5s; height: 8px; }}
  .music-bar .eq span:nth-child(4) {{ animation-delay: .75s; height: 14px; }}
  @keyframes eq {{ 0%,100% {{ transform: scaleY(0.4); }} 50% {{ transform: scaleY(1); }} }}
  .music-bar.paused .eq span {{ animation-play-state: paused; opacity: 0.3; }}
  .music-bar button {{
    background: linear-gradient(135deg, #d4af37, #b8941f);
    color: #0a0a0a; border: none; padding: 6px 14px;
    font-family: Georgia, serif; font-weight: bold;
    letter-spacing: 2px; cursor: pointer; border-radius: 4px; font-size: 12px;
  }}
  .music-bar button:hover {{ background: #f5d76e; }}
  .hint {{ color: #8a6a14; font-size: 11px; margin-left: 8px; font-style: italic; text-transform: none; letter-spacing: 1px; }}
</style>
</head>
<body>
<div class="music-bar" id="bar">
  <div class="label">
    <span class="eq"><span></span><span></span><span></span><span></span></span>
    <span>Masquerade Theme</span>
    <span class="hint" id="hint">click anywhere to begin</span>
  </div>
  <button id="toggle">Pause</button>
</div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/tone/14.8.49/Tone.js"></script>
<script>
(function() {{
  const enabled = {enabled_js};
  const bar = document.getElementById('bar');
  const btn = document.getElementById('toggle');
  const hint = document.getElementById('hint');
  let started = false;
  let muted = !enabled;
  try {{
    const saved = sessionStorage.getItem('masq_music_muted');
    if (saved !== null) muted = saved === '1';
  }} catch (e) {{}}

  let reverb, harp, pad, bell, loop;
  function buildAudio() {{
    Tone.Destination.volume.value = -8;
    reverb = new Tone.Reverb({{ decay: 9, wet: 0.55 }}).toDestination();
    const delay = new Tone.FeedbackDelay({{ delayTime: '4n.', feedback: 0.3, wet: 0.2 }}).connect(reverb);
    harp = new Tone.PluckSynth({{ attackNoise: 0.6, dampening: 2600, resonance: 0.9 }}).connect(delay);
    harp.volume.value = -8;
    pad = new Tone.PolySynth(Tone.AMSynth, {{
      harmonicity: 1.5,
      oscillator: {{ type: 'triangle' }},
      envelope: {{ attack: 1.2, decay: 1, sustain: 0.6, release: 4 }},
      modulation: {{ type: 'sine' }},
      modulationEnvelope: {{ attack: 2, decay: 0, sustain: 1, release: 4 }}
    }}).connect(reverb);
    pad.volume.value = -22;
    bell = new Tone.MetalSynth({{
      frequency: 80,
      envelope: {{ attack: 0.001, decay: 3, release: 2 }},
      harmonicity: 3.1, modulationIndex: 16, resonance: 800, octaves: 1.5
    }}).connect(reverb);
    bell.volume.value = -30;
    const progression = [
      {{ pad: ['D3','F3','A3'],   arp: ['D4','F4','A4','F4'] }},
      {{ pad: ['Bb2','D3','F3'],  arp: ['Bb3','D4','F4','D4'] }},
      {{ pad: ['G2','Bb2','D3'],  arp: ['G3','Bb3','D4','Bb3'] }},
      {{ pad: ['A2','C#3','E3','G3'], arp: ['A3','C#4','E4','C#4'] }},
    ];
    let beat = 0;
    loop = new Tone.Loop((time) => {{
      const chordIdx = Math.floor(beat / 4) % progression.length;
      const step = beat % 4;
      const ch = progression[chordIdx];
      harp.triggerAttackRelease(ch.arp[step], '2n', time);
      if (step === 0) pad.triggerAttackRelease(ch.pad, '1m', time);
      if (beat % 16 === 0) bell.triggerAttackRelease('C2', '2n', time + 0.05);
      beat++;
    }}, '2n').start(0);
    Tone.Transport.bpm.value = 56;
  }}

  async function startAudio() {{
    if (started) return;
    try {{
      await Tone.start();
      buildAudio();
      Tone.Transport.start();
      started = true;
      hint.style.display = 'none';
      updateUI();
    }} catch (e) {{
      hint.textContent = 'audio blocked';
    }}
  }}
  function setMuted(m) {{
    muted = m;
    try {{ sessionStorage.setItem('masq_music_muted', m ? '1' : '0'); }} catch (e) {{}}
    if (started) Tone.Destination.mute = m;
    updateUI();
  }}
  function updateUI() {{
    btn.textContent = muted ? 'Play' : 'Pause';
    bar.classList.toggle('paused', muted);
  }}
  btn.addEventListener('click', async () => {{
    if (!started) {{ await startAudio(); setMuted(false); }}
    else setMuted(!muted);
  }});
  function tryAutoStart() {{ if (!muted && !started) startAudio(); }}
  document.addEventListener('click', tryAutoStart, {{ once: true }});
  try {{
    window.parent.document.addEventListener('click', tryAutoStart, {{ once: true }});
  }} catch (e) {{}}
  window.addEventListener('load', () => {{ if (!muted) tryAutoStart(); }});
  updateUI();

  // Duck when other audio/video plays
  function checkOtherMedia() {{
    if (!started) return;
    try {{
      const parentDoc = window.parent.document;
      const els = parentDoc.querySelectorAll('audio, video');
      let othersPlaying = false;
      els.forEach(el => {{
        if (!el.paused && !el.ended && el.currentTime > 0 && !el.muted) othersPlaying = true;
      }});
      Tone.Destination.volume.value = othersPlaying ? -60 : -8;
    }} catch (e) {{}}
  }}
  setInterval(checkOtherMedia, 700);
}})();
</script>
</body></html>
"""


# -----------------------------------------------------------------------------
# Thunderclap (Web Audio API, fires in sync with letter reveal)
# -----------------------------------------------------------------------------
THUNDER_HTML = """
<!DOCTYPE html><html><head></head><body>
<script>
(async function() {
  const Ctx = window.AudioContext || window.webkitAudioContext;
  if (!Ctx) return;
  const ctx = new Ctx();
  if (ctx.state === 'suspended') { try { await ctx.resume(); } catch (e) {} }

  function noiseBuf(duration, decay) {
    const sr = ctx.sampleRate;
    const len = Math.max(1, Math.floor(sr * duration));
    const buf = ctx.createBuffer(1, len, sr);
    const d = buf.getChannelData(0);
    for (let i = 0; i < len; i++) {
      d[i] = (Math.random() * 2 - 1) * Math.exp(-i / (sr * decay));
    }
    return buf;
  }

  function playCrack(when, vol) {
    const src = ctx.createBufferSource();
    src.buffer = noiseBuf(0.35, 0.06);
    const filt = ctx.createBiquadFilter();
    filt.type = 'lowpass';
    filt.frequency.setValueAtTime(9000, when);
    filt.frequency.exponentialRampToValueAtTime(700, when + 0.35);
    const g = ctx.createGain();
    g.gain.value = vol;
    src.connect(filt).connect(g).connect(ctx.destination);
    src.start(when);
    src.stop(when + 0.45);
  }

  function playRumble(when, dur, vol) {
    const src = ctx.createBufferSource();
    src.buffer = noiseBuf(dur, dur / 3.5);
    const filt = ctx.createBiquadFilter();
    filt.type = 'lowpass';
    filt.frequency.value = 220;
    const shelf = ctx.createBiquadFilter();
    shelf.type = 'lowshelf';
    shelf.frequency.value = 100;
    shelf.gain.value = 14;
    const g = ctx.createGain();
    g.gain.setValueAtTime(vol, when);
    g.gain.exponentialRampToValueAtTime(0.0001, when + dur);
    src.connect(filt).connect(shelf).connect(g).connect(ctx.destination);
    src.start(when);
    src.stop(when + dur + 0.1);
  }

  // Fire in sync with the letter reveal (animation has ~3.0s delay before letter appears)
  const t0 = ctx.currentTime + 3.0;
  playCrack(t0, 0.95);
  playRumble(t0 + 0.05, 5.2, 0.7);
  // a second smaller crack for drama
  playCrack(t0 + 0.55, 0.5);
  playRumble(t0 + 0.6, 3.0, 0.35);
})();
</script>
</body></html>
"""


# -----------------------------------------------------------------------------
# Victorious fanfare (Tone.js)
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# Tragic music + thunderclap (Web Audio + Tone.js)
# -----------------------------------------------------------------------------
# Played when nobody correctly accused the murderer. Opens with a thunderclap,
# then a slow descending D-minor lament on violin/pad with heavy reverb.
TRAGIC_HTML = """
<!DOCTYPE html><html><head></head><body>
<script src="https://cdnjs.cloudflare.com/ajax/libs/tone/14.8.49/Tone.js"></script>
<script>
(async function() {
  // --- Thunderclap (raw Web Audio) ---
  const Ctx = window.AudioContext || window.webkitAudioContext;
  if (Ctx) {
    const ctx = new Ctx();
    if (ctx.state === 'suspended') { try { await ctx.resume(); } catch (e) {} }
    function noiseBuf(dur, decay) {
      const sr = ctx.sampleRate;
      const len = Math.max(1, Math.floor(sr * dur));
      const buf = ctx.createBuffer(1, len, sr);
      const d = buf.getChannelData(0);
      for (let i = 0; i < len; i++) {
        d[i] = (Math.random() * 2 - 1) * Math.exp(-i / (sr * decay));
      }
      return buf;
    }
    function crack(when, vol) {
      const src = ctx.createBufferSource();
      src.buffer = noiseBuf(0.4, 0.07);
      const filt = ctx.createBiquadFilter();
      filt.type = 'lowpass';
      filt.frequency.setValueAtTime(9500, when);
      filt.frequency.exponentialRampToValueAtTime(500, when + 0.45);
      const g = ctx.createGain();
      g.gain.value = vol;
      src.connect(filt).connect(g).connect(ctx.destination);
      src.start(when); src.stop(when + 0.5);
    }
    function rumble(when, dur, vol) {
      const src = ctx.createBufferSource();
      src.buffer = noiseBuf(dur, dur / 3.5);
      const f1 = ctx.createBiquadFilter();
      f1.type = 'lowpass'; f1.frequency.value = 200;
      const f2 = ctx.createBiquadFilter();
      f2.type = 'lowshelf'; f2.frequency.value = 100; f2.gain.value = 16;
      const g = ctx.createGain();
      g.gain.setValueAtTime(vol, when);
      g.gain.exponentialRampToValueAtTime(0.0001, when + dur);
      src.connect(f1).connect(f2).connect(g).connect(ctx.destination);
      src.start(when); src.stop(when + dur + 0.1);
    }
    const t0 = ctx.currentTime + 0.15;
    crack(t0, 1.0);
    rumble(t0 + 0.05, 6.5, 0.85);
    crack(t0 + 0.65, 0.55);
    rumble(t0 + 0.7, 3.5, 0.45);
  }

  // --- Lament (Tone.js) ---
  try { await Tone.start(); } catch (e) {}
  Tone.Destination.volume.value = -6;
  const reverb = new Tone.Reverb({ decay: 9, wet: 0.7 }).toDestination();
  const delay = new Tone.FeedbackDelay({ delayTime: '4n', feedback: 0.35, wet: 0.25 }).connect(reverb);

  // Sustained somber pad
  const pad = new Tone.PolySynth(Tone.AMSynth, {
    harmonicity: 1.2,
    oscillator: { type: 'triangle' },
    envelope: { attack: 1.8, decay: 1, sustain: 0.65, release: 5 },
    modulation: { type: 'sine' },
    modulationEnvelope: { attack: 2.5, decay: 0, sustain: 1, release: 5 }
  }).connect(reverb);
  pad.volume.value = -10;

  // Lead "violin" voice
  const violin = new Tone.MonoSynth({
    oscillator: { type: 'sawtooth' },
    envelope: { attack: 0.6, decay: 0.4, sustain: 0.7, release: 2.5 },
    filter: { Q: 2, frequency: 1400, type: 'lowpass' },
    filterEnvelope: { attack: 0.2, decay: 0.5, sustain: 0.5, release: 2, baseFrequency: 400, octaves: 2.2 }
  }).connect(delay);
  violin.volume.value = -14;

  // Low cello drone for gravitas
  const cello = new Tone.Synth({
    oscillator: { type: 'triangle' },
    envelope: { attack: 1.0, decay: 0.5, sustain: 0.9, release: 4 }
  }).connect(reverb);
  cello.volume.value = -18;

  const now = Tone.now() + 1.6;  // start after the thunderclap

  // Slow descending lament in D minor: A4 — F4 — D4 — C#4 — A3
  // (sospirosa, like Lacrimosa)
  violin.triggerAttackRelease('A4',  '2n',   now + 0.0);
  violin.triggerAttackRelease('G4',  '4n',   now + 1.4);
  violin.triggerAttackRelease('F4',  '2n.',  now + 2.0);
  violin.triggerAttackRelease('E4',  '4n',   now + 3.8);
  violin.triggerAttackRelease('D4',  '2n',   now + 4.4);
  violin.triggerAttackRelease('C#4', '4n.',  now + 5.8);
  violin.triggerAttackRelease('D4',  '1n',   now + 7.0);

  // Pad chords underneath: Dm -> Bb -> Gm -> A7 -> Dm
  pad.triggerAttackRelease(['D3', 'F3', 'A3'],         '1m', now);
  pad.triggerAttackRelease(['Bb2','D3', 'F3'],         '2n', now + 2.5);
  pad.triggerAttackRelease(['G2', 'Bb2','D3'],         '2n', now + 4.0);
  pad.triggerAttackRelease(['A2', 'C#3','E3'],         '2n', now + 5.5);
  pad.triggerAttackRelease(['D3', 'F3', 'A3', 'D4'],   '1m', now + 7.0);

  // Cello drone
  cello.triggerAttackRelease('D2', '2m', now);
  cello.triggerAttackRelease('A1', '1m', now + 5.5);
})();
</script>
</body></html>
"""


# -----------------------------------------------------------------------------
# ESC-to-close handler
# -----------------------------------------------------------------------------
# Listens for the Escape key on as many DOM contexts as possible and clicks
# any visible button whose text matches one of our close-button labels.
# Used on both the fullscreen Reveal overlay and the fullscreen Closing page.
ESC_CLOSE_HTML = """
<!DOCTYPE html><html><head></head><body>
<script>
(function() {
  const TARGETS = ['Close Reveal', 'Exit Closing'];
  function clickClose() {
    const docs = [];
    try { docs.push(window.parent.document); } catch (e) {}
    try { docs.push(window.top.document); } catch (e) {}
    docs.push(document);
    for (const d of docs) {
      let buttons = [];
      try { buttons = d.querySelectorAll('button'); } catch (e) { continue; }
      for (const b of buttons) {
        const t = (b.textContent || '').trim();
        for (const needle of TARGETS) {
          if (t.indexOf(needle) !== -1) { b.click(); return true; }
        }
      }
    }
    return false;
  }
  function isInteractive(el) {
    if (!el) return false;
    const tag = (el.tagName || '').toLowerCase();
    if (tag === 'input' || tag === 'textarea' || tag === 'select') return true;
    const role = (el.getAttribute && el.getAttribute('role') || '').toLowerCase();
    if (role === 'combobox' || role === 'listbox' || role === 'textbox') return true;
    return false;
  }
  function handler(e) {
    if (e.key === 'Escape' || e.keyCode === 27) {
      // Try each accessible document to figure out the active element
      let active = null;
      try { active = window.parent.document.activeElement; } catch (err) {}
      if (!active) { try { active = document.activeElement; } catch (err) {} }
      if (isInteractive(active)) return;  // let ESC blur the field naturally
      e.preventDefault();
      clickClose();
    }
  }
  document.addEventListener('keydown', handler, true);
  window.addEventListener('keydown', handler, true);
  try { window.parent.document.addEventListener('keydown', handler, true); } catch (e) {}
  try { window.parent.addEventListener('keydown', handler, true); } catch (e) {}
  try { window.top.document.addEventListener('keydown', handler, true); } catch (e) {}
  try { window.top.addEventListener('keydown', handler, true); } catch (e) {}
  // Bring focus into the iframe so its own keydown fires if parent is cross-origin
  try { window.focus(); } catch (e) {}
})();
</script>
</body></html>
"""


VICTORIOUS_HTML = """
<!DOCTYPE html><html><head></head><body>
<script src="https://cdnjs.cloudflare.com/ajax/libs/tone/14.8.49/Tone.js"></script>
<script>
(async function() {
  try { await Tone.start(); } catch (e) {}
  Tone.Destination.volume.value = -4;
  const reverb = new Tone.Reverb({ decay: 4, wet: 0.4 }).toDestination();
  const brass = new Tone.PolySynth(Tone.Synth, {
    oscillator: { type: 'sawtooth' },
    envelope: { attack: 0.05, decay: 0.4, sustain: 0.6, release: 1.2 }
  }).connect(reverb);
  brass.volume.value = -10;
  const bells = new Tone.PluckSynth({ attackNoise: 0.3, dampening: 6000, resonance: 0.95 }).connect(reverb);
  bells.volume.value = -4;

  // Bright C major fanfare with bell arpeggio
  const now = Tone.now();
  // Arpeggio rising
  const arp = ['C4','E4','G4','C5','E5','G5','C6'];
  arp.forEach((n, i) => bells.triggerAttackRelease(n, '8n', now + i * 0.13));
  // Triumphant chord stabs
  brass.triggerAttackRelease(['C4','E4','G4'], '4n', now + 1.0);
  brass.triggerAttackRelease(['F4','A4','C5'], '4n', now + 1.45);
  brass.triggerAttackRelease(['G4','B4','D5'], '4n', now + 1.9);
  brass.triggerAttackRelease(['C5','E5','G5','C6'], '2n', now + 2.35);
  // Final cymbal-ish flourish
  bells.triggerAttackRelease('C7', '4n', now + 2.5);
  bells.triggerAttackRelease('G6', '4n', now + 2.65);
  bells.triggerAttackRelease('C7', '2n', now + 2.85);
})();
</script>
</body></html>
"""


# -----------------------------------------------------------------------------
# Reveal animation (renders as a full-page overlay; no JS in body)
# -----------------------------------------------------------------------------
def reveal_overlay_html(letter: str) -> str:
    return f"""
<style>
  .reveal-overlay {{
    position: fixed; top: 0; left: 0;
    width: 100vw; height: 100vh;
    background: radial-gradient(circle at center, #2a1f0c 0%, #0a0a0a 50%, #000 100%), #000;
    z-index: 999990; overflow: hidden;
    font-family: 'Cinzel', Georgia, serif;
  }}
  .ring {{
    position: absolute; top: 50%; left: 50%;
    width: 520px; height: 520px; margin: -260px 0 0 -260px;
    border: 3px solid #d4af37; border-radius: 50%;
    opacity: 0; animation: ringExpand 2.6s ease-out forwards;
  }}
  .ring.r2 {{ animation-delay: 0.3s; border-color: #f5d76e; }}
  .ring.r3 {{ animation-delay: 0.6s; border-color: #b8941f; }}
  .ring.r4 {{ animation-delay: 0.9s; border-color: #d4af37; }}

  .mask-wrap {{
    position: absolute; top: 50%; left: 50%;
    width: 480px; height: 370px; margin: -185px 0 0 -240px;
    animation: maskSpin 2.8s cubic-bezier(.2,.7,.2,1) forwards,
               maskFade 0.7s ease-in 2.6s forwards;
    transform-origin: center;
  }}

  .flash {{
    position: absolute; top: 0; left: 0; width: 100vw; height: 100vh;
    background: rgba(245,215,110,0); pointer-events: none;
    animation: flashIn 0.4s ease-out 3.0s forwards;
  }}
  @keyframes flashIn {{
    0% {{ background: rgba(245,215,110,0); }}
    20% {{ background: rgba(255,245,200,0.85); }}
    100% {{ background: rgba(245,215,110,0); }}
  }}

  .letter-reveal {{
    position: absolute; top: 50%; left: 50%;
    transform: translate(-50%, -50%) scale(0);
    font-size: 420px; font-weight: 800; color: #f5d76e;
    text-shadow:
      0 0 30px rgba(245,215,110,0.95),
      0 0 80px rgba(212,175,55,0.85),
      0 0 160px rgba(184,148,31,0.7),
      0 0 220px rgba(184,148,31,0.5);
    opacity: 0; letter-spacing: 8px; line-height: 1;
    animation: letterIn 1.1s cubic-bezier(.2,.9,.2,1.2) 3.0s forwards;
  }}
  .subtitle {{
    position: absolute; bottom: 12vh; left: 0; right: 0;
    text-align: center; color: #d4af37; font-size: 28px;
    letter-spacing: 14px; text-transform: uppercase; font-weight: 600;
    opacity: 0; animation: fadeIn 1.0s ease 3.8s forwards;
  }}
  .top-ornament {{
    position: absolute; top: 6vh; left: 0; right: 0;
    text-align: center; color: #d4af37; font-size: 20px;
    letter-spacing: 16px; text-transform: uppercase;
    opacity: 0; animation: fadeIn 1s ease 0.2s forwards;
  }}
  .sparkle {{
    position: absolute; width: 6px; height: 6px;
    background: #f5d76e; border-radius: 50%;
    box-shadow: 0 0 12px #f5d76e, 0 0 24px #d4af37;
    opacity: 0; animation: sparkleFloat 3.5s ease-in-out infinite;
  }}
  @keyframes maskSpin {{
    0% {{ transform: rotate(0deg) scale(0.2); opacity: 0; }}
    25% {{ opacity: 1; }}
    100% {{ transform: rotate(1080deg) scale(1.3); opacity: 1; }}
  }}
  @keyframes maskFade {{ to {{ opacity: 0; transform: rotate(1080deg) scale(1.9); }} }}
  @keyframes ringExpand {{
    0% {{ transform: scale(0.1); opacity: 0; }}
    50% {{ opacity: 0.85; }}
    100% {{ transform: scale(2.4); opacity: 0; }}
  }}
  @keyframes letterIn {{
    0% {{ transform: translate(-50%, -50%) scale(0) rotate(-25deg); opacity: 0; }}
    55% {{ transform: translate(-50%, -50%) scale(1.2) rotate(3deg); opacity: 1; }}
    100% {{ transform: translate(-50%, -50%) scale(1) rotate(0deg); opacity: 1; }}
  }}
  @keyframes fadeIn {{ to {{ opacity: 1; }} }}
  @keyframes sparkleFloat {{
    0%, 100% {{ opacity: 0; transform: translateY(0) scale(0.5); }}
    50% {{ opacity: 1; transform: translateY(-40px) scale(1.3); }}
  }}
</style>
<div class="reveal-overlay">
  <div class="top-ornament">&#10086; &nbsp; The Masquerade &nbsp; &#10086;</div>
  <div class="ring r1"></div>
  <div class="ring r2"></div>
  <div class="ring r3"></div>
  <div class="ring r4"></div>

  <div class="sparkle" style="top:14%; left:10%; animation-delay:0.2s;"></div>
  <div class="sparkle" style="top:22%; left:85%; animation-delay:0.7s;"></div>
  <div class="sparkle" style="top:70%; left:8%; animation-delay:1.1s;"></div>
  <div class="sparkle" style="top:80%; left:80%; animation-delay:1.6s;"></div>
  <div class="sparkle" style="top:12%; left:55%; animation-delay:2.0s;"></div>
  <div class="sparkle" style="top:85%; left:42%; animation-delay:2.4s;"></div>
  <div class="sparkle" style="top:38%; left:18%; animation-delay:2.8s;"></div>
  <div class="sparkle" style="top:55%; left:90%; animation-delay:3.2s;"></div>
  <div class="sparkle" style="top:25%; left:30%; animation-delay:3.6s;"></div>
  <div class="sparkle" style="top:65%; left:65%; animation-delay:4.0s;"></div>

  <div class="mask-wrap">
    <svg viewBox="0 0 480 370" xmlns="http://www.w3.org/2000/svg" width="100%" height="100%">
      <defs>
        <linearGradient id="gMask" x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stop-color="#f5d76e"/>
          <stop offset="50%" stop-color="#d4af37"/>
          <stop offset="100%" stop-color="#8a6a14"/>
        </linearGradient>
      </defs>
      <path d="M240,180 C 200,70 50,70 30,180 C 20,260 110,300 170,280 C 210,266 232,234 240,200 Z"
            fill="url(#gMask)" stroke="#f5d76e" stroke-width="3"/>
      <path d="M240,180 C 280,70 430,70 450,180 C 460,260 370,300 310,280 C 270,266 248,234 240,200 Z"
            fill="url(#gMask)" stroke="#f5d76e" stroke-width="3"/>
      <ellipse cx="125" cy="180" rx="40" ry="26" fill="#000"/>
      <ellipse cx="355" cy="180" rx="40" ry="26" fill="#000"/>
      <path d="M240,110 Q260,40 300,55 Q275,90 240,110 Z" fill="#f5d76e"/>
      <path d="M240,110 Q220,40 180,55 Q205,90 240,110 Z" fill="#f5d76e"/>
      <path d="M240,90 Q250,20 268,30 Q258,70 240,90 Z" fill="#d4af37"/>
      <path d="M240,90 Q230,20 212,30 Q222,70 240,90 Z" fill="#d4af37"/>
      <circle cx="70" cy="160" r="4" fill="#f5d76e"/>
      <circle cx="85" cy="220" r="4" fill="#f5d76e"/>
      <circle cx="395" cy="220" r="4" fill="#f5d76e"/>
      <circle cx="410" cy="160" r="4" fill="#f5d76e"/>
      <circle cx="240" cy="245" r="6" fill="#f5d76e"/>
    </svg>
  </div>

  <div class="flash"></div>
  <div class="letter-reveal">{letter}</div>
  <div class="subtitle">The Murderer</div>
</div>
"""


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def reset_round_first_asker(key: str):
    """Pick a fresh random asker for the given session_state key."""
    st.session_state[key] = random.choice(PLAYER_NAMES)


def reset_closing_state():
    st.session_state.closing_step = "audio"
    st.session_state.accusation_order = None
    st.session_state.accusation_index = 0
    st.session_state.accusations = {}
    st.session_state.final_order = None
    st.session_state.final_index = 0
    st.session_state.results_revealed = False


# -----------------------------------------------------------------------------
# Sidebar
# -----------------------------------------------------------------------------
st.sidebar.markdown("## 🎭 Masquerade")
section = st.sidebar.radio("View", ["Players", "Facilitator"])
st.sidebar.markdown("---")
st.sidebar.caption("Players: see your character & secret letter.")
st.sidebar.caption("Facilitator: control rounds, reveal the murderer.")


# We don't yet know the stage; CSS will be re-injected once we do.
# Inject baseline CSS first so the password gate looks right.
hide_chrome_now = st.session_state.reveal_active  # reveal overlay hides chrome
inject_global_css(
    is_facilitator=(section == "Facilitator" and st.session_state.facilitator_ok),
    hide_chrome=hide_chrome_now,
)


# =============================================================================
# PLAYER VIEW
# =============================================================================
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

    st.stop()


# =============================================================================
# FACILITATOR VIEW
# =============================================================================
# Password gate
if not st.session_state.facilitator_ok:
    st.title("🎭 Facilitator Console")
    pw = st.text_input("Facilitator password", type="password")
    if st.button("Enter"):
        if pw == FACILITATOR_PASSWORD:
            st.session_state.facilitator_ok = True
            st.rerun()
        else:
            st.error("Incorrect password.")
    st.stop()


# -----------------------------------------------------------------------------
# FULLSCREEN REVEAL OVERLAY (highest priority — covers everything else)
# -----------------------------------------------------------------------------
if st.session_state.reveal_active and st.session_state.murderer_letter is not None:
    # Re-inject CSS with hide_chrome=True so the sidebar/header disappear
    inject_global_css(is_facilitator=True, hide_chrome=True)
    # Visual overlay (no JS allowed via markdown — that's fine, animations are pure CSS)
    st.markdown(
        reveal_overlay_html(st.session_state.murderer_letter),
        unsafe_allow_html=True,
    )
    # Thunder (separate 0-height iframe with Web Audio API)
    components.html(THUNDER_HTML, height=0)
    # ESC-to-close handler (separate 0-height iframe)
    components.html(ESC_CLOSE_HTML, height=0)
    # Top-LEFT close control (rendered above the overlay via CSS).
    # Targets the stButton wrapping our primary button.
    st.markdown(
        """
        <style>
        div[data-testid="stButton"]:has(button[kind="primary"]) {
            position: fixed; top: 24px; left: 32px;
            z-index: 999999; width: auto !important;
        }
        div[data-testid="stButton"]:has(button[kind="primary"]) button {
            background: rgba(10,7,3,0.85);
            border: 2px solid #d4af37;
            color: #f5d76e;
            box-shadow: 0 0 22px rgba(245,215,110,0.5);
            backdrop-filter: blur(4px);
        }
        div[data-testid="stButton"]:has(button[kind="primary"]) button:hover {
            background: rgba(212,175,55,0.95);
            color: #0a0a0a;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    if st.button("✕  Close Reveal  (Esc)", type="primary", key="close_reveal"):
        st.session_state.reveal_active = False
        st.rerun()
    st.stop()


# -----------------------------------------------------------------------------
# Stage selector (Setup, Round 1–4, Closing)
# -----------------------------------------------------------------------------
# When stage is Closing, hide chrome for fullscreen feel — but we need to know
# the stage BEFORE rendering, so we read it from a sidebar radio too.
stage = st.sidebar.radio("Stage", ROUND_STAGES, index=ROUND_STAGES.index(
    st.session_state.get("_stage", "Setup")
), key="_stage")

# If Closing, re-inject CSS with chrome hidden (sidebar will still be visible only briefly during script run)
if stage == "Closing":
    inject_global_css(is_facilitator=True, hide_chrome=True)


# -----------------------------------------------------------------------------
# Hero header (not on Closing — Closing has its own cinematic header)
# -----------------------------------------------------------------------------
if stage != "Closing":
    st.markdown(
        """
        <div class="facilitator-hero">
            <div class="ornament">&#10086; &nbsp;&#9728;&nbsp; &#10086;</div>
            <div class="title">MASQUERADE</div>
            <div class="subtitle">&middot; A Murder Mystery &middot;</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Background music bar (skip on Closing — Closing has its own audio)
    components.html(background_music_html(st.session_state.music_on), height=64)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)


# =============================================================================
# SETUP
# =============================================================================
if stage == "Setup":
    st.markdown(
        "<h2 style='text-align:center'>Setup &mdash; Select the Murderer</h2>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='text-align:center; font-size:1.15rem; color:#d4af37;'>"
        "Press the button below. The masquerade will reveal a letter — "
        "the player holding that letter is the murderer."
        "</p>",
        unsafe_allow_html=True,
    )

    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_b:
        sub_a, sub_b = st.columns(2)
        with sub_a:
            if st.button("🎭  Reveal the Murderer", use_container_width=True):
                chosen = random.choice(LETTERS)
                st.session_state.murderer_letter = chosen
                st.session_state.murderer_name = letter_to_name(chosen)
                # Reset closing flow whenever a new murderer is picked
                reset_closing_state()
                st.session_state.reveal_active = True
                st.rerun()
        with sub_b:
            if st.session_state.murderer_letter is not None:
                if st.button("🔄  Reset", use_container_width=True):
                    st.session_state.murderer_letter = None
                    st.session_state.murderer_name = None
                    st.session_state.reveal_active = False
                    reset_closing_state()
                    st.rerun()

    if st.session_state.murderer_letter is not None and not st.session_state.reveal_active:
        st.markdown(
            f"""
            <div style="text-align:center; margin-top:40px;">
                <p style="color:#d4af37; letter-spacing:6px; font-size:14px;">THE MURDERER'S LETTER</p>
                <div style="font-family:'Cinzel',serif; font-size:140px; color:#f5d76e;
                            text-shadow: 0 0 30px rgba(245,215,110,0.7), 0 0 60px rgba(212,175,55,0.4);
                            letter-spacing:8px; line-height:1;">
                    {st.session_state.murderer_letter}
                </div>
                <p style="color:#b8941f; margin-top:16px;">
                    Only the player holding letter
                    <b>{st.session_state.murderer_letter}</b>
                    knows who they are.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("▶  Replay Reveal Animation"):
            st.session_state.reveal_active = True
            st.rerun()


# =============================================================================
# ROUND 1 (with Groups expander)
# =============================================================================
elif stage == "Round 1":
    st.markdown("<h2 style='text-align:center;'>Round 1</h2>", unsafe_allow_html=True)

    left, center, right = st.columns([1, 4, 1])
    with center:
        # Audio clue
        for item in ROUND_MEDIA["Round 1"]:
            st.markdown(
                f"<div class='media-card'><div class='media-title'>&#10086; {item['label']} &#10086;</div></div>",
                unsafe_allow_html=True,
            )
            if item.get("type") == "audio":
                st.audio(item["url"])
            elif item.get("type") == "video":
                st.video(item["url"])
            else:
                st.markdown(f"[Open {item['label']}]({item['url']})")
            st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

        # Groups expander
        with st.expander("🎭  Reveal the 3 Groups  🎭", expanded=False):
            groups = load_groups()
            gcols = st.columns(3)
            for i, (gname, members) in enumerate(groups.items()):
                with gcols[i]:
                    names_html = "".join(f"<span class='name'>{n}</span>" for n in members)
                    st.markdown(
                        f"<div class='group-card'><h4>{gname}</h4>{names_html}</div>",
                        unsafe_allow_html=True,
                    )

        st.markdown(
            f"<p style='text-align:center; margin-top:24px;'>"
            f"<a href='{DROPBOX_FOLDER_URL}' target='_blank' style='color:#d4af37; letter-spacing:2px;'>"
            f"&#128193; Open shared Dropbox folder</a></p>",
            unsafe_allow_html=True,
        )


# =============================================================================
# ROUND 2, 3, 4 — Random first asker + answer checklist
# =============================================================================
elif stage in ("Round 2", "Round 3", "Round 4"):
    asker_key   = f"round{stage[-1]}_asker"
    answered_key = f"round{stage[-1]}_answered"

    st.markdown(f"<h2 style='text-align:center;'>{stage}</h2>", unsafe_allow_html=True)

    left, center, right = st.columns([1, 4, 1])
    with center:
        # Audio clue(s)
        for item in ROUND_MEDIA[stage]:
            st.markdown(
                f"<div class='media-card'><div class='media-title'>&#10086; {item['label']} &#10086;</div></div>",
                unsafe_allow_html=True,
            )
            if item.get("type") == "audio":
                st.audio(item["url"])
            elif item.get("type") == "video":
                st.video(item["url"])
            else:
                st.markdown(f"[Open {item['label']}]({item['url']})")
            st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

        # First-asker expander
        with st.expander("🎭  Reveal who asks the first question  🎭", expanded=False):
            # Pick on first reveal
            if not st.session_state.get(asker_key):
                reset_round_first_asker(asker_key)

            asker = st.session_state[asker_key]
            st.markdown(
                f"<div class='asker-reveal'>"
                f"<div class='label'>Asks the First Question</div>"
                f"<div class='name'>{asker}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )
            c1, c2 = st.columns([1, 1])
            with c1:
                if st.button("🔁  Pick again", key=f"repick_{stage}"):
                    reset_round_first_asker(asker_key)
                    st.rerun()

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

        # Player checklist
        st.markdown(
            f"<h3 style='text-align:center; margin-top:24px;'>Answers Tracker</h3>"
            f"<p style='text-align:center; color:#d4af37;'>Check off each player as they answer.</p>",
            unsafe_allow_html=True,
        )
        # Two-column checklist
        col_l, col_r = st.columns(2)
        answered = st.session_state[answered_key]
        for i, n in enumerate(PLAYER_NAMES):
            col = col_l if i % 2 == 0 else col_r
            with col:
                role = PLAYERS_ROLES[n]
                new_val = st.checkbox(
                    f"{n}  —  *{role}*",
                    value=answered.get(n, False),
                    key=f"chk_{stage}_{n}",
                )
                if new_val != answered.get(n, False):
                    answered[n] = new_val
                    st.session_state[answered_key] = answered

        # Summary
        done_count = sum(1 for v in st.session_state[answered_key].values() if v)
        st.markdown(
            f"<p style='text-align:center; color:#d4af37; margin-top:18px; letter-spacing:3px;'>"
            f"{done_count} / {len(PLAYER_NAMES)} answered</p>",
            unsafe_allow_html=True,
        )

        if st.button("🧹  Clear checklist", key=f"clear_{stage}"):
            st.session_state[answered_key] = {n: False for n in PLAYER_NAMES}
            st.rerun()

        st.markdown(
            f"<p style='text-align:center; margin-top:24px;'>"
            f"<a href='{DROPBOX_FOLDER_URL}' target='_blank' style='color:#d4af37; letter-spacing:2px;'>"
            f"&#128193; Open shared Dropbox folder</a></p>",
            unsafe_allow_html=True,
        )


# =============================================================================
# CLOSING (fullscreen, multi-step)
# =============================================================================
elif stage == "Closing":
    # ESC-to-close handler (clicks the Exit button on Escape)
    components.html(ESC_CLOSE_HTML, height=0)

    # Top-LEFT exit button. on_click runs before the next rerun, so it
    # can safely set the stage radio's session_state value.
    def _exit_closing_cb():
        st.session_state._stage = "Setup"

    st.markdown(
        """
        <style>
        div[data-testid="stButton"]:has(button[kind="primary"]) {
            position: fixed; top: 18px; left: 24px;
            z-index: 999999; width: auto !important;
        }
        div[data-testid="stButton"]:has(button[kind="primary"]) button {
            background: rgba(10,7,3,0.85);
            border: 2px solid #d4af37;
            color: #f5d76e;
            box-shadow: 0 0 22px rgba(245,215,110,0.5);
            backdrop-filter: blur(4px);
            padding: 0.5em 1.2em;
            font-size: 0.85rem;
        }
        div[data-testid="stButton"]:has(button[kind="primary"]) button:hover {
            background: rgba(212,175,55,0.95);
            color: #0a0a0a;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.button(
        "✕  Exit Closing  (Esc)",
        type="primary",
        key="exit_closing",
        on_click=_exit_closing_cb,
    )

    step = st.session_state.closing_step

    # ---- STEP 1: Closing audio clue ----
    if step == "audio":
        st.markdown(
            f"""
            <div class='closing-stage'>
                <div class='stage-title'>The Closing</div>
                <div class='stage-sub'>One final clue echoes through the ballroom</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        left, center, right = st.columns([1, 4, 1])
        with center:
            st.markdown(
                f"<div class='media-card'><div class='media-title'>&#10086; {CLOSING_AUDIO['label']} &#10086;</div></div>",
                unsafe_allow_html=True,
            )
            st.audio(CLOSING_AUDIO["url"])
            st.markdown("<div style='height:30px'></div>", unsafe_allow_html=True)
            c1, c2, c3 = st.columns([1, 2, 1])
            with c2:
                if st.button("▶  Continue to Accusations", use_container_width=True):
                    # Shuffle the accusation order; murderer not special yet
                    order = list(PLAYER_NAMES)
                    random.shuffle(order)
                    st.session_state.accusation_order = order
                    st.session_state.accusation_index = 0
                    st.session_state.accusations = {}
                    st.session_state.closing_step = "accusations"
                    st.rerun()

    # ---- STEP 2: Accusations ----
    elif step == "accusations":
        order = st.session_state.accusation_order or []
        idx = st.session_state.accusation_index

        st.markdown(
            f"""
            <div class='closing-stage'>
                <div class='stage-title'>Accusations</div>
                <div class='stage-sub'>Each guest must point a finger</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if idx < len(order):
            current = order[idx]
            current_role = PLAYERS_ROLES[current]
            left, center, right = st.columns([1, 3, 1])
            with center:
                st.markdown(
                    f"""
                    <div class='closing-stage' style='padding-top:0;'>
                        <span class='progress-pill'>Accuser {idx + 1} of {len(order)}</span>
                        <div class='big-name'>{current}</div>
                        <p style='color:#d4af37; letter-spacing:4px; font-style:italic;'>the {current_role}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                st.markdown(
                    "<p style='text-align:center; font-size:1.2rem; color:#f5d76e;'>"
                    "Whom do you accuse?</p>",
                    unsafe_allow_html=True,
                )
                options = [n for n in PLAYER_NAMES if n != current]
                pre = st.session_state.accusations.get(current, "")
                accused = st.selectbox(
                    "Accuse:",
                    [""] + options,
                    index=([""] + options).index(pre) if pre in options else 0,
                    format_func=lambda x: "— choose the accused —" if x == "" else f"{x}  ({PLAYERS_ROLES[x]})",
                    key=f"accuse_{current}",
                    label_visibility="collapsed",
                )

                st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
                cb1, cb2, cb3 = st.columns([1, 1, 1])
                with cb1:
                    if idx > 0 and st.button("◀  Back"):
                        st.session_state.accusation_index = idx - 1
                        st.rerun()
                with cb2:
                    disabled = not accused
                    if st.button("Lock in accusation  ▶", disabled=disabled, use_container_width=True):
                        st.session_state.accusations[current] = accused
                        st.session_state.accusation_index = idx + 1
                        st.rerun()
        else:
            # All accusations locked in — show summary + advance
            st.markdown(
                """
                <div class='closing-stage'>
                    <div class='stage-sub'>All accusations have been made</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            left, center, right = st.columns([1, 3, 1])
            with center:
                rows = ""
                for n in order:
                    accused = st.session_state.accusations.get(n, "—")
                    rows += (
                        f"<div class='results-row'><span>{n}</span>"
                        f"<span>accuses</span>"
                        f"<span style='color:#f5d76e;'><b>{accused}</b></span></div>"
                    )
                st.markdown(rows, unsafe_allow_html=True)

                st.markdown("<div style='height:30px'></div>", unsafe_allow_html=True)
                cb1, cb2 = st.columns(2)
                with cb1:
                    if st.button("◀  Edit accusations"):
                        st.session_state.accusation_index = len(order) - 1
                        st.rerun()
                with cb2:
                    if st.button("▶  Continue to Final Statements", use_container_width=True):
                        # Build final order: innocents shuffled, then murderer last
                        murderer = st.session_state.murderer_name
                        innocents = [n for n in PLAYER_NAMES if n != murderer]
                        random.shuffle(innocents)
                        st.session_state.final_order = innocents + ([murderer] if murderer else [])
                        st.session_state.final_index = 0
                        st.session_state.closing_step = "statements"
                        st.rerun()

    # ---- STEP 3: Final Statements ----
    elif step == "statements":
        order = st.session_state.final_order or []
        idx = st.session_state.final_index
        murderer = st.session_state.murderer_name

        st.markdown(
            f"""
            <div class='closing-stage'>
                <div class='stage-title'>Final Statements</div>
                <div class='stage-sub'>Each guest defends &mdash; or confesses</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if idx < len(order):
            current = order[idx]
            is_guilty = (current == murderer)
            current_role = PLAYERS_ROLES[current]
            banner = (
                "<div class='guilty-banner'>&#9760;  GUILTY  &#9760;</div>"
                if is_guilty
                else "<div class='innocent-banner'>&#10026;  INNOCENT  &#10026;</div>"
            )
            prompt = (
                "Read your <b>GUILTY</b> final statement."
                if is_guilty
                else "Read your <b>INNOCENT</b> final statement."
            )
            left, center, right = st.columns([1, 3, 1])
            with center:
                st.markdown(
                    f"""
                    <div class='closing-stage' style='padding-top:0;'>
                        <span class='progress-pill'>{idx + 1} of {len(order)}</span>
                        <div class='big-name'>{current}</div>
                        <p style='color:#d4af37; letter-spacing:4px; font-style:italic;'>the {current_role}</p>
                        <div class='prompt-card'>
                            {banner}
                            <p style='font-size:1.3rem; margin-top:14px;'>{prompt}</p>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                cb1, cb2, cb3 = st.columns([1, 2, 1])
                with cb2:
                    if st.button("▶  Next", use_container_width=True, key=f"next_stmt_{idx}"):
                        st.session_state.final_index = idx + 1
                        st.rerun()
        else:
            st.markdown(
                """
                <div class='closing-stage'>
                    <div class='stage-sub'>All statements heard. The truth awaits&hellip;</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            left, center, right = st.columns([1, 2, 1])
            with center:
                if st.button("▶  Proceed to the Reveal", use_container_width=True):
                    st.session_state.closing_step = "reveal"
                    st.session_state.results_revealed = False
                    st.rerun()

    # ---- STEP 4: Reveal ----
    elif step == "reveal":
        st.markdown(
            """
            <div class='closing-stage'>
                <div class='stage-title'>The Truth</div>
                <div class='stage-sub'>The mask is lifted</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        left, center, right = st.columns([1, 3, 1])
        with center:
            if not st.session_state.results_revealed:
                if st.button("✨  REVEAL THE MURDERER  ✨", use_container_width=True):
                    st.session_state.results_revealed = True
                    st.rerun()
            else:
                murderer = st.session_state.murderer_name
                murderer_letter = st.session_state.murderer_letter
                murderer_role = PLAYERS_ROLES.get(murderer, "?")

                st.markdown(
                    f"""
                    <div class='closing-stage' style='padding-top:0;'>
                        <p style='color:#d4af37; letter-spacing:8px; font-size:1rem;'>THE MURDERER WAS</p>
                        <div class='big-name' style='color:#ef4444; text-shadow: 0 0 28px rgba(239,68,68,0.6);'>
                            {murderer or '???'}
                        </div>
                        <p style='color:#f5d76e; letter-spacing:4px; font-style:italic; font-size:1.3rem;'>
                            the {murderer_role} &nbsp; &middot; &nbsp; letter <b>{murderer_letter}</b>
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                # Build results rows
                accusation_order = st.session_state.accusation_order or []
                accusations = st.session_state.accusations or {}
                rows = ""
                correct_accusers_in_order = []
                for n in accusation_order:
                    accused = accusations.get(n, "—")
                    if accused == murderer and accused is not None:
                        rows += (
                            f"<div class='results-row correct'>"
                            f"<span><b>{n}</b> accused <b>{accused}</b></span>"
                            f"<span class='verdict' style='color:#4ade80;'>&#10003; CORRECT</span></div>"
                        )
                        correct_accusers_in_order.append(n)
                    else:
                        rows += (
                            f"<div class='results-row wrong'>"
                            f"<span><b>{n}</b> accused <b>{accused}</b></span>"
                            f"<span class='verdict' style='color:#ef4444;'>&#10007; wrong</span></div>"
                        )

                st.markdown(rows, unsafe_allow_html=True)

                # Best Inspector = first correct accuser
                if correct_accusers_in_order:
                    best = correct_accusers_in_order[0]
                    best_role = PLAYERS_ROLES[best]
                    st.markdown(
                        f"""
                        <div class='inspector-crown'>
                            <div class='label'>&#128081;  Best Inspector  &#128081;</div>
                            <div class='name'>{best}</div>
                            <div style='color:#d4af37; letter-spacing:3px; font-style:italic;'>the {best_role}</div>
                            <p style='color:#f5d76e; margin-top:16px;'>First to correctly name the murderer.</p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        """
                        <div class='inspector-crown' style='border-color:#ef4444;'>
                            <div class='label' style='color:#ef4444;'>&#9760;  The Murderer Walks Free  &#9760;</div>
                            <p style='color:#f5d76e; margin-top:8px; font-style:italic;'>No one named the killer.</p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                # Music — victorious if anyone correctly accused, otherwise tragic + thunder
                if correct_accusers_in_order:
                    components.html(VICTORIOUS_HTML, height=0)
                else:
                    components.html(TRAGIC_HTML, height=0)

                st.markdown("<div style='height:30px'></div>", unsafe_allow_html=True)
                bb1, bb2 = st.columns(2)
                with bb1:
                    if st.button("🔁  Replay Reveal"):
                        st.session_state.results_revealed = False
                        st.rerun()
                with bb2:
                    if st.button("🎭  Start a new game"):
                        st.session_state.murderer_letter = None
                        st.session_state.murderer_name = None
                        st.session_state.reveal_active = False
                        reset_closing_state()
                        # Reset round trackers too
                        st.session_state.round2_asker = None
                        st.session_state.round3_asker = None
                        st.session_state.round4_asker = None
                        st.session_state.round2_answered = {n: False for n in PLAYER_NAMES}
                        st.session_state.round3_answered = {n: False for n in PLAYER_NAMES}
                        st.session_state.round4_answered = {n: False for n in PLAYER_NAMES}
                        st.session_state._stage = "Setup"
                        st.rerun()

    # Closing internal navigation: small jump-step buttons
    st.markdown("<div style='height:40px'></div>", unsafe_allow_html=True)
    nav_cols = st.columns(5)
    labels = [("audio", "Audio"), ("accusations", "Accusations"), ("statements", "Statements"), ("reveal", "Reveal"), (None, "↺  Restart Closing")]
    for col, (target, label) in zip(nav_cols, labels):
        with col:
            if target is None:
                if st.button(label, use_container_width=True, key="closing_restart"):
                    reset_closing_state()
                    st.rerun()
            else:
                if st.button(label, use_container_width=True, key=f"jump_{target}",
                             disabled=(st.session_state.closing_step == target)):
                    st.session_state.closing_step = target
                    if target == "accusations" and st.session_state.accusation_order is None:
                        order = list(PLAYER_NAMES)
                        random.shuffle(order)
                        st.session_state.accusation_order = order
                        st.session_state.accusation_index = 0
                        st.session_state.accusations = {}
                    if target == "statements" and st.session_state.final_order is None:
                        murderer = st.session_state.murderer_name
                        innocents = [n for n in PLAYER_NAMES if n != murderer]
                        random.shuffle(innocents)
                        st.session_state.final_order = innocents + ([murderer] if murderer else [])
                        st.session_state.final_index = 0
                    st.rerun()


# -----------------------------------------------------------------------------
# Footer (non-Closing)
# -----------------------------------------------------------------------------
if stage != "Closing":
    st.markdown("<div style='height:60px'></div>", unsafe_allow_html=True)
    foot_l, foot_c, foot_r = st.columns([3, 1, 3])
    with foot_c:
        if st.button("Log out", use_container_width=True):
            st.session_state.facilitator_ok = False
            st.session_state.murderer_letter = None
            st.session_state.murderer_name = None
            st.session_state.reveal_active = False
            reset_closing_state()
            st.rerun()
