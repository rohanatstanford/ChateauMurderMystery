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
        {"label": "Round 1 Audio Clue", "url": "https://www.dropbox.com/scl/fo/6eehtwnqlgbmm2gkj8nit/ALC0yB9IAeIUOI8IM0HayMg/Detective%20Audio%20Files/Masquerade%20Round%201.mp3?rlkey=sgdb5jrpnd6q4ivnppdhkpma5&e=1&raw=1", "type": "audio"},
    ],
    "Round 2": [
        # {"label": "Round 2 Video", "url": "https://www.dropbox.com/.../round2.mp4?raw=1", "type": "video"},
        {"label": "Round 2 Audio Clue", "url": "https://www.dropbox.com/scl/fo/6eehtwnqlgbmm2gkj8nit/APvCW0u3jrwNHaehOwYRKnk/Detective%20Audio%20Files/Masquerade%20Round%202.mp3?rlkey=sgdb5jrpnd6q4ivnppdhkpma5&e=1&raw=1", "type": "audio"},
    ],
    "Round 3": [
        # {"label": "Round 3 Video", "url": "?raw=1", "type": "video"},
        {"label": "Round 3 Audio Clue", "url": "https://www.dropbox.com/scl/fo/6eehtwnqlgbmm2gkj8nit/AJnyG9ebrcbx4KPZhCbrYXc/Detective%20Audio%20Files/Masquerade%20Round%203.mp3?rlkey=sgdb5jrpnd6q4ivnppdhkpma5&e=1&raw=1", "type": "audio"},
    ],
    "Round 4": [
        # {"label": "Round 4 Video", "url": "?raw=1", "type": "video"},
        {"label": "Round 4 Audio Clue", "url": "https://www.dropbox.com/scl/fo/6eehtwnqlgbmm2gkj8nit/ANlg-cmO1jRUt4ZcdZfJEPA/Detective%20Audio%20Files/Masquerade%20Round%204.mp3?rlkey=sgdb5jrpnd6q4ivnppdhkpma5&e=1&raw=1", "type": "audio"},
        {"label": "Round 4 Final Audio Clue", "url": "https://www.dropbox.com/scl/fo/6eehtwnqlgbmm2gkj8nit/AC3yFFFTubPe3QPMm_5Xhc8/Detective%20Audio%20Files/Masquerade%20Round%204%20Final.mp3?rlkey=sgdb5jrpnd6q4ivnppdhkpma5&e=1&raw=1", "type": "audio"},
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
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize session state
if "facilitator_ok" not in st.session_state:
    st.session_state.facilitator_ok = False
if "murderer_letter" not in st.session_state:
    st.session_state.murderer_letter = None
if "reveal_active" not in st.session_state:
    st.session_state.reveal_active = False
if "music_on" not in st.session_state:
    st.session_state.music_on = True


# -----------------------------------------------------------------------------
# Global CSS theme (black & gold masquerade)
# -----------------------------------------------------------------------------
def inject_global_css(is_facilitator: bool, reveal_active: bool):
    """Inject the page CSS. Hides the sidebar / chrome during the fullscreen reveal."""
    hide_chrome = ""
    if reveal_active:
        hide_chrome = """
        section[data-testid="stSidebar"] { display: none !important; }
        header[data-testid="stHeader"] { display: none !important; }
        .stApp > header { display: none !important; }
        .main .block-container { padding-top: 0 !important; }
        """

    player_constrain = ""
    if not is_facilitator:
        # Narrower, centered player view
        player_constrain = """
        .main .block-container {
            max-width: 760px !important;
            padding-top: 3rem !important;
        }
        """
    else:
        # Use the full width on facilitator view
        player_constrain = """
        .main .block-container {
            max-width: 100% !important;
            padding-left: 4rem !important;
            padding-right: 4rem !important;
            padding-top: 2rem !important;
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
        .stRadio > div > label[data-checked="true"],
        .stRadio > div > label:has(input:checked) {{
            border-color: #f5d76e;
            background: linear-gradient(135deg, rgba(212,175,55,0.2), rgba(245,215,110,0.1));
            box-shadow: 0 0 20px rgba(245,215,110,0.3);
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
            position: relative;
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

        /* Make round audio/video bigger */
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

        {player_constrain}
        {hide_chrome}
        </style>
        """,
        unsafe_allow_html=True,
    )


# -----------------------------------------------------------------------------
# Background music (Tone.js procedural ambient)
# -----------------------------------------------------------------------------
def background_music_html(enabled: bool) -> str:
    """A self-contained Tone.js ambient music loop with a Mute toggle.

    Dark D-minor, slow tempo, plucked harp + warm pad + occasional bell —
    evokes Haunting in Venice / Agatha Christie themes.

    The track:
      - starts on first user interaction (the password Enter click satisfies this)
      - persists across reruns by storing play state in sessionStorage
      - pauses automatically when any other <audio>/<video> on the page plays
    """
    enabled_js = "true" if enabled else "false"
    return f"""
<!DOCTYPE html>
<html><head>
<style>
  body {{ margin: 0; background: transparent; font-family: Georgia, serif; }}
  .music-bar {{
    display: flex; align-items: center; justify-content: space-between;
    background: linear-gradient(135deg, rgba(26,18,8,0.9), rgba(42,31,12,0.9));
    border: 1px solid #4a3a14;
    border-radius: 8px;
    padding: 10px 16px;
    color: #d4af37;
    font-size: 13px;
    letter-spacing: 2px;
    text-transform: uppercase;
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
  @keyframes eq {{
    0%,100% {{ transform: scaleY(0.4); }}
    50%     {{ transform: scaleY(1); }}
  }}
  .music-bar.paused .eq span {{ animation-play-state: paused; opacity: 0.3; }}
  .music-bar button {{
    background: linear-gradient(135deg, #d4af37, #b8941f);
    color: #0a0a0a; border: none; padding: 6px 14px;
    font-family: Georgia, serif; font-weight: bold;
    letter-spacing: 2px; cursor: pointer; border-radius: 4px;
    font-size: 12px;
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
    <span class="hint" id="hint">click to begin</span>
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
  // Restore mute preference
  try {{
    const saved = sessionStorage.getItem('masq_music_muted');
    if (saved !== null) muted = saved === '1';
  }} catch (e) {{}}

  // -- Build the soundscape --
  let reverb, harp, pad, bell, loop;

  function buildAudio() {{
    Tone.Destination.volume.value = -6;
    reverb = new Tone.Reverb({{ decay: 9, wet: 0.55 }}).toDestination();
    const delay = new Tone.FeedbackDelay({{ delayTime: '4n.', feedback: 0.3, wet: 0.2 }}).connect(reverb);

    // Plucked harp (the lead)
    harp = new Tone.PluckSynth({{ attackNoise: 0.6, dampening: 2600, resonance: 0.9 }}).connect(delay);
    harp.volume.value = -8;

    // Warm sustained pad
    pad = new Tone.PolySynth(Tone.AMSynth, {{
      harmonicity: 1.5,
      oscillator: {{ type: 'triangle' }},
      envelope: {{ attack: 1.2, decay: 1, sustain: 0.6, release: 4 }},
      modulation: {{ type: 'sine' }},
      modulationEnvelope: {{ attack: 2, decay: 0, sustain: 1, release: 4 }}
    }}).connect(reverb);
    pad.volume.value = -22;

    // Occasional low bell
    bell = new Tone.MetalSynth({{
      frequency: 80,
      envelope: {{ attack: 0.001, decay: 3, release: 2 }},
      harmonicity: 3.1, modulationIndex: 16, resonance: 800, octaves: 1.5
    }}).connect(reverb);
    bell.volume.value = -30;

    // D-minor mysterious progression: Dm | Bb | Gm | A7
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
      // Arpeggio note each beat
      harp.triggerAttackRelease(ch.arp[step], '2n', time);
      // Pad at the start of each chord
      if (step === 0) {{
        pad.triggerAttackRelease(ch.pad, '1m', time);
      }}
      // Bell every 8 beats for atmosphere
      if (beat % 16 === 0) {{
        bell.triggerAttackRelease('C2', '2n', time + 0.05);
      }}
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
    if (started) {{
      Tone.Destination.mute = m;
    }}
    updateUI();
  }}

  function updateUI() {{
    btn.textContent = muted ? 'Play' : 'Pause';
    bar.classList.toggle('paused', muted);
  }}

  btn.addEventListener('click', async () => {{
    if (!started) {{
      await startAudio();
      setMuted(false);
    }} else {{
      setMuted(!muted);
    }}
  }});

  // Auto-start on any click on the parent page (browsers require user gesture)
  function tryAutoStart() {{
    if (!muted && !started) startAudio();
  }}
  document.addEventListener('click', tryAutoStart, {{ once: true }});
  // Also try when this iframe loads (in case password gate already counted)
  window.addEventListener('load', () => {{ if (!muted) tryAutoStart(); }});
  updateUI();

  // Duck when other audio/video on parent page is playing.
  function checkOtherMedia() {{
    if (!started) return;
    try {{
      const parentDoc = window.parent.document;
      const els = parentDoc.querySelectorAll('audio, video');
      let othersPlaying = false;
      els.forEach(el => {{
        if (!el.paused && !el.ended && el.currentTime > 0 && !el.muted) {{
          othersPlaying = true;
        }}
      }});
      // Don't auto-flip user's manual mute; just temporarily duck
      Tone.Destination.volume.value = othersPlaying ? -60 : -6;
    }} catch (e) {{
      // Cross-origin: can't observe. Ignore.
    }}
  }}
  setInterval(checkOtherMedia, 700);
}})();
</script>
</body></html>
"""


# -----------------------------------------------------------------------------
# Reveal animation (renders as a full-page overlay)
# -----------------------------------------------------------------------------
def reveal_overlay_html(letter: str) -> str:
    """Black-and-gold fullscreen masquerade reveal animation."""
    return f"""
<style>
  .reveal-overlay {{
    position: fixed;
    top: 0; left: 0;
    width: 100vw; height: 100vh;
    background:
      radial-gradient(circle at center, #2a1f0c 0%, #0a0a0a 50%, #000 100%),
      #000;
    z-index: 999990;
    overflow: hidden;
    font-family: 'Cinzel', Georgia, serif;
  }}
  .ring {{
    position: absolute;
    top: 50%; left: 50%;
    width: 520px; height: 520px;
    margin: -260px 0 0 -260px;
    border: 3px solid #d4af37;
    border-radius: 50%;
    opacity: 0;
    animation: ringExpand 2.6s ease-out forwards;
  }}
  .ring.r2 {{ animation-delay: 0.3s; border-color: #f5d76e; }}
  .ring.r3 {{ animation-delay: 0.6s; border-color: #b8941f; }}
  .ring.r4 {{ animation-delay: 0.9s; border-color: #d4af37; opacity:0; }}

  .mask-wrap {{
    position: absolute;
    top: 50%; left: 50%;
    width: 480px; height: 370px;
    margin: -185px 0 0 -240px;
    animation: maskSpin 2.8s cubic-bezier(.2,.7,.2,1) forwards,
               maskFade 0.7s ease-in 2.6s forwards;
    transform-origin: center;
  }}

  .letter-reveal {{
    position: absolute;
    top: 50%; left: 50%;
    transform: translate(-50%, -50%) scale(0);
    font-size: 420px;
    font-weight: 800;
    color: #f5d76e;
    text-shadow:
      0 0 30px rgba(245,215,110,0.95),
      0 0 80px rgba(212,175,55,0.85),
      0 0 160px rgba(184,148,31,0.7),
      0 0 220px rgba(184,148,31,0.5);
    opacity: 0;
    letter-spacing: 8px;
    line-height: 1;
    animation: letterIn 1.1s cubic-bezier(.2,.9,.2,1.2) 3.0s forwards;
  }}

  .subtitle {{
    position: absolute;
    bottom: 12vh; left: 0; right: 0;
    text-align: center;
    color: #d4af37;
    font-size: 28px;
    letter-spacing: 14px;
    text-transform: uppercase;
    font-weight: 600;
    opacity: 0;
    animation: fadeIn 1.0s ease 3.8s forwards;
  }}
  .sub-ornament {{
    color: #d4af37;
    font-size: 22px;
    letter-spacing: 12px;
    opacity: 0;
    animation: fadeIn 1.0s ease 4.0s forwards;
  }}

  .top-ornament {{
    position: absolute;
    top: 6vh; left: 0; right: 0;
    text-align: center;
    color: #d4af37;
    font-size: 20px;
    letter-spacing: 16px;
    text-transform: uppercase;
    opacity: 0;
    animation: fadeIn 1s ease 0.2s forwards;
  }}

  .sparkle {{
    position: absolute;
    width: 6px; height: 6px;
    background: #f5d76e;
    border-radius: 50%;
    box-shadow: 0 0 12px #f5d76e, 0 0 24px #d4af37;
    opacity: 0;
    animation: sparkleFloat 3.5s ease-in-out infinite;
  }}

  @keyframes maskSpin {{
    0%   {{ transform: rotate(0deg) scale(0.2); opacity: 0; }}
    25%  {{ opacity: 1; }}
    100% {{ transform: rotate(1080deg) scale(1.3); opacity: 1; }}
  }}
  @keyframes maskFade {{
    to {{ opacity: 0; transform: rotate(1080deg) scale(1.9); }}
  }}
  @keyframes ringExpand {{
    0%   {{ transform: scale(0.1); opacity: 0; }}
    50%  {{ opacity: 0.85; }}
    100% {{ transform: scale(2.4); opacity: 0; }}
  }}
  @keyframes letterIn {{
    0%   {{ transform: translate(-50%, -50%) scale(0) rotate(-25deg); opacity: 0; }}
    55%  {{ transform: translate(-50%, -50%) scale(1.2) rotate(3deg); opacity: 1; }}
    100% {{ transform: translate(-50%, -50%) scale(1) rotate(0deg); opacity: 1; }}
  }}
  @keyframes fadeIn {{ to {{ opacity: 1; }} }}
  @keyframes sparkleFloat {{
    0%, 100% {{ opacity: 0; transform: translateY(0) scale(0.5); }}
    50%      {{ opacity: 1; transform: translateY(-40px) scale(1.3); }}
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
        <filter id="glow"><feGaussianBlur stdDeviation="3"/></filter>
      </defs>
      <!-- Left side -->
      <path d="M240,180
               C 200,70 50,70 30,180
               C 20,260 110,300 170,280
               C 210,266 232,234 240,200 Z"
            fill="url(#gMask)" stroke="#f5d76e" stroke-width="3"/>
      <!-- Right side -->
      <path d="M240,180
               C 280,70 430,70 450,180
               C 460,260 370,300 310,280
               C 270,266 248,234 240,200 Z"
            fill="url(#gMask)" stroke="#f5d76e" stroke-width="3"/>
      <!-- Eye holes -->
      <ellipse cx="125" cy="180" rx="40" ry="26" fill="#000"/>
      <ellipse cx="355" cy="180" rx="40" ry="26" fill="#000"/>
      <!-- Top flourishes -->
      <path d="M240,110 Q260,40 300,55 Q275,90 240,110 Z" fill="#f5d76e"/>
      <path d="M240,110 Q220,40 180,55 Q205,90 240,110 Z" fill="#f5d76e"/>
      <path d="M240,90 Q250,20 268,30 Q258,70 240,90 Z" fill="#d4af37"/>
      <path d="M240,90 Q230,20 212,30 Q222,70 240,90 Z" fill="#d4af37"/>
      <!-- Decorative dots -->
      <circle cx="70" cy="160" r="4" fill="#f5d76e"/>
      <circle cx="85" cy="220" r="4" fill="#f5d76e"/>
      <circle cx="395" cy="220" r="4" fill="#f5d76e"/>
      <circle cx="410" cy="160" r="4" fill="#f5d76e"/>
      <circle cx="240" cy="245" r="6" fill="#f5d76e"/>
    </svg>
  </div>

  <div class="letter-reveal">{letter}</div>
  <div class="subtitle">The Murderer</div>
</div>
"""


# -----------------------------------------------------------------------------
# Sidebar
# -----------------------------------------------------------------------------
st.sidebar.markdown("## 🎭 Masquerade")
section = st.sidebar.radio("View", ["Players", "Facilitator"])
st.sidebar.markdown("---")
st.sidebar.caption("Players: see your character & secret letter.")
st.sidebar.caption("Facilitator: control rounds, reveal the murderer.")


# Inject the page CSS now that we know which view we're in
inject_global_css(
    is_facilitator=(section == "Facilitator" and st.session_state.facilitator_ok),
    reveal_active=st.session_state.reveal_active,
)


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

    # ---------- FULLSCREEN REVEAL OVERLAY (highest priority) ----------
    if st.session_state.reveal_active and st.session_state.murderer_letter is not None:
        # Render fullscreen overlay
        st.markdown(
            reveal_overlay_html(st.session_state.murderer_letter),
            unsafe_allow_html=True,
        )
        # Floating close button above the overlay
        st.markdown(
            """
            <style>
            div[data-testid="stButton"]:has(button[aria-describedby]),
            div[data-testid="stButton"] {
                position: relative;
                z-index: 999999;
            }
            /* Pin the close button to top-right */
            div[data-testid="stVerticalBlock"] > div:has(> div > div[data-testid="stButton"] > button[kind="primary"]) {
                position: fixed;
                top: 24px; right: 32px;
                z-index: 999999;
                width: auto;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
        if st.button("✕  Close Reveal", type="primary", key="close_reveal"):
            st.session_state.reveal_active = False
            st.rerun()
        st.stop()

    # ---------- Hero header ----------
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

    # ---------- Background music bar ----------
    components.html(background_music_html(st.session_state.music_on), height=64)

    # ---------- Stage selector ----------
    stage = st.radio(
        "Game stage",
        ["Setup", "Round 1", "Round 2", "Round 3", "Round 4"],
        horizontal=True,
        label_visibility="collapsed",
    )

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

    # ---------- Setup ----------
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
                    st.session_state.murderer_letter = random.choice(LETTERS)
                    st.session_state.reveal_active = True
                    st.rerun()
            with sub_b:
                if st.session_state.murderer_letter is not None:
                    if st.button("🔄  Reset", use_container_width=True):
                        st.session_state.murderer_letter = None
                        st.session_state.reveal_active = False
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

    # ---------- Rounds ----------
    else:
        st.markdown(
            f"<h2 style='text-align:center;'>{stage}</h2>",
            unsafe_allow_html=True,
        )

        items = ROUND_MEDIA.get(stage, [])

        if not items:
            st.info(
                f"No media configured for **{stage}** yet.\n\n"
                "Edit `ROUND_MEDIA` at the top of `app.py` to add Dropbox links."
            )
            st.markdown(f"[📁 Open shared Dropbox folder]({DROPBOX_FOLDER_URL})")
        else:
            # Center the media using columns
            left, center, right = st.columns([1, 4, 1])
            with center:
                for item in items:
                    kind = item.get("type", "link")
                    st.markdown(
                        f"""
                        <div class="media-card">
                            <div class="media-title">&#10086; {item['label']} &#10086;</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    # Render the actual player just below the title card
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
                    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

                st.markdown(
                    f"<p style='text-align:center; margin-top:24px;'>"
                    f"<a href='{DROPBOX_FOLDER_URL}' target='_blank' "
                    f"style='color:#d4af37; letter-spacing:2px;'>"
                    f"&#128193; Open shared Dropbox folder</a></p>",
                    unsafe_allow_html=True,
                )

    # ---------- Footer ----------
    st.markdown("<div style='height:60px'></div>", unsafe_allow_html=True)
    foot_l, foot_c, foot_r = st.columns([3, 1, 3])
    with foot_c:
        if st.button("Log out", use_container_width=True):
            st.session_state.facilitator_ok = False
            st.session_state.murderer_letter = None
            st.session_state.reveal_active = False
            st.rerun()
