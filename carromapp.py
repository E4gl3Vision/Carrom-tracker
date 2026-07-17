import streamlit as st
import pandas as pd
import datetime

st.set_page_config(page_title="4-Player Carrom Tracker", layout="wide", initial_sidebar_state="collapsed")

# --- PREMIUM STYLING ---
st.markdown("""
<style>
    .stApp { background-color: #0f172a; color: #f8fafc; }
    div[data-testid="metric-container"] {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 16px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    }
    .freq-box {
        background-color: rgba(30, 41, 59, 0.5);
        border: 1px solid #475569;
        border-radius: 0 0 16px 16px;
        padding: 10px;
        font-size: 0.8rem;
        color: #94a3b8;
        text-align: center;
        backdrop-filter: blur(5px);
    }
    h1, h2, h3 { color: #fcd34d !important; font-weight: 700 !important; }
    div.stButton > button { border-radius: 8px !important; font-weight: 600 !important; }
    div[role="dialog"] { border-radius: 16px; }
</style>
""", unsafe_allow_html=True)

st.title("🎯 4-Player Club Carrom Tracker")

# --- DATA DICTIONARIES ---
ROSTER = ["Abhinaba", "Agniva", "Debottam", "Krish", "Orghya", "Pushpak", "Raktim", "Shakir", "Soumya", "Guest 1", "Guest 2"]
multipliers = {
    'Near Base': 0.7, 'Far Base': 0.9, 'Close Free Inch': 0.9, 'Close Crowd Inch': 1.0,
    'Medium Free Inch': 0.95, 'Medium Crowd Inch': 1.15, 'Far Free Inch': 1.15, 'Far Crowd Inch': 1.3,
    'Single Rebound': 1.2, 'Double Rebound': 1.5, 'Red Cover': 1.5, 'Red Attempt': 0.5,
    'Return Shot': 1.1, 'Jhaanke Bok': 1.0, 'Assist': 0.75, 
    '3-Shot Streak': 1.0, '4-Shot Streak': 1.5, '5+ Shot Streak': 2.0
}
penalties = {'Opponent Coin Only': 0.7, 'Pocketed Striker': 0.75, 'Double Fine': 0.65}
players = ["P1", "P2", "P3", "P4"]
default_assignments = ["Pushpak", "Soumya", "Raktim", "Agniva"]

# --- INITIALIZE STATE ---
if 'match_log' not in st.session_state: st.session_state.match_log = []
if 'show_summary' not in st.session_state: st.session_state.show_summary = False
if 'last_summary_data' not in st.session_state: st.session_state.last_summary_data = []

for i, p in enumerate(players):
    if f"{p}_name" not in st.session_state: st.session_state[f"{p}_name"] = default_assignments[i]
    if f"{p}_won" not in st.session_state: st.session_state[f"{p}_won"] = False
    if f"{p}_Missed_Shot" not in st.session_state: st.session_state[f"{p}_Missed_Shot"] = 0
    for action in list(multipliers.keys()) + list(penalties.keys()):
        if f"{p}_{action}" not in st.session_state: st.session_state[f"{p}_{action}"] = 0

# --- HELPERS ---
def calculate_rating(p):
    pots = sum(st.session_state[f"{p}_{a}"] * w for a, w in multipliers.items())
    fouls = sum(st.session_state[f"{p}_{f}"] * w for f, w in penalties.items())
    win = 1.0 if st.session_state[f"{p}_won"] else 0.0
    return 2.0 + min(10.0, pots + win) - fouls

def get_accuracy(p):
    pots = sum(st.session_state[f"{p}_{k}"] for k in multipliers.keys() if 'Streak' not in k and 'Attempt' not in k)
    foul_shots = sum(st.session_state[f"{p}_{k}"] for k in penalties.keys())
    total = pots + st.session_state[f"{p}_Red Attempt"] + foul_shots + st.session_state[f"{p}_Missed_Shot"]
    return (pots / total * 100) if total > 0 else 0.0, pots, total

def adjust(p, action, delta):
    if st.session_state[f"{p}_{action}"] + delta >= 0: st.session_state[f"{p}_{action}"] += delta

def save_match():
    st.session_state.last_summary_data = []
    for p in players:
        entry = {"Player": st.session_state[f"{p}_name"], "Rating": calculate_rating(p), "Acc": get_accuracy(p)[0]}
        st.session_state.last_summary_data.append(entry)
    st.session_state.match_log.append(st.session_state.last_summary_data)
    st.session_state.show_summary = True

# --- MODAL ---
@st.dialog("Match Summary")
def show_modal():
    for p in st.session_state.last_summary_data:
        st.write(f"**{p['Player']}**: {p['Rating']:.1f} Rating | {p['Acc']:.0f}% Acc")
    if st.button("Close"): st.session_state.show_summary = False; st.rerun()

if st.session_state.show_summary: show_modal()

# --- UI ---
st.write("### 🏆 Live Match Scoreboard")
dash_cols = st.columns(4)
for i, p in enumerate(players):
    rating, acc = calculate_rating(p), get_accuracy(p)[0]
    with dash_cols[i]:
        st.markdown(f"**{st.session_state[f'{p}_name']}**")
        st.markdown(f"<h2 style='color:{'#fcd34d' if rating > 5 else '#94a3b8'};'>{rating:.1f}</h2>", unsafe_allow_html=True)
        st.caption(f"{'🔥' if acc > 50 else '🧊'} Acc: {acc:.0f}%")

st.divider()
tabs = st.tabs([st.session_state[f"{p}_name"] for p in players])

for i, p in enumerate(players):
    with tabs[i]:
        acc, pots, total = get_accuracy(p)
        st.markdown(f"**Accuracy:** `{acc:.1f}%` *({pots}/{total})*")
        
        setup_cols = st.columns([3, 1])
        setup_cols[0].selectbox("Player", ROSTER, key=f"{p}_name", label_visibility="collapsed")
        if setup_cols[1].button("🧹 Reset", key=f"res_{p}"):
            for k in list(multipliers.keys()) + list(penalties.keys()) + ["Missed_Shot"]: st.session_state[f"{p}_{k}"] = 0
            st.session_state[f"{p}_won"] = False; st.rerun()
            
        st.markdown("**⚪ Missed Shots**")
        m_cols = st.columns([1, 1, 3])
        m_cols[0].button("➖", key=f"sub_m{p}", on_click=adjust, args=(p, "Missed_Shot", -1))
        m_cols[1].markdown(f"#### {st.session_state[f'{p}_Missed_Shot']}")
        m_cols[2].button("➕ Missed", key=f"add_m{p}", on_click=adjust, args=(p, "Missed_Shot", 1))

        shot_mode = st.radio("Complexity", ["Standard", "Advanced"], horizontal=True)
        for action, weight in multipliers.items():
            if shot_mode == "Standard" and weight > 1.2: continue
            c = st.columns([3, 1, 1.5, 1])
            c[0].write(f"**{action}** ({weight}x)")
            c[1].button("➖", key=f"s{p}{action}", on_click=adjust, args=(p, action, -1))
            c[2].markdown(f"<center>{st.session_state[f'{p}_{action}']}</center>", unsafe_allow_html=True)
            c[3].button("➕", key=f"a{p}{action}", on_click=adjust, args=(p, action, 1))

        if st.button("🏆 Register Win (+1.0)", key=f"w{p}", type="primary" if not st.session_state[f"{p}_won"] else "secondary"):
            st.session_state[f"{p}_won"] = not st.session_state[f"{p}_won"]; st.rerun()

if st.button("💾 SAVE MATCH", type="primary", use_container_width=True): save_match(); st.rerun()
    
