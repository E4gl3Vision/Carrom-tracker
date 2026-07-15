import streamlit as st
import pandas as pd
import datetime

st.set_page_config(page_title="4-Player Carrom Tracker", layout="wide", initial_sidebar_state="collapsed")

# --- SAFE TOAST NOTIFICATIONS ---
if "flash_msg" in st.session_state:
    st.toast(st.session_state.flash_msg["msg"], icon=st.session_state.flash_msg["icon"])
    del st.session_state.flash_msg

# --- CUSTOM UI CSS TWEAKS ---
st.markdown("""
<style>
    div[data-testid="metric-container"] {
        background-color: #262730;
        border: 1px solid #3d3f4b;
        padding: 5% 10%;
        border-radius: 12px 12px 0px 0px; 
        border-bottom: none;
    }
    .freq-box {
        background-color: #1e1f26;
        border: 1px solid #3d3f4b;
        border-top: none;
        border-radius: 0px 0px 12px 12px;
        padding: 5px 10%;
        font-size: 0.8rem;
        color: #94a3b8;
        margin-bottom: 15px;
        text-align: center;
    }
    button[data-baseweb="tab"] {
        font-size: 1.1rem !important;
        padding-top: 15px !important;
        padding-bottom: 15px !important;
    }
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

st.title("🎯 4-Player Club Carrom Tracker")
st.caption("Carrom Rating Calculator.")

# --- DATA DICTIONARIES ---
ROSTER = [
    "Abhinaba", "Agniva", "Debottam", "Krish", "Orghya", 
    "Pushpak", "Raktim", "Shakir", "Soumya", 
    "Jethu", "Guest 2", "Guest 3", "Guest 4"
]

multipliers = {
    'Near Base': 0.7, 'Far Base': 0.9, 'Close Free Inch': 0.9, 'Close Crowd Inch': 1.0,
    'Medium Free Inch': 0.95, 'Medium Crowd Inch': 1.15, 'Far Free Inch': 1.15, 'Far Crowd Inch': 1.3,
    'Single Rebound': 1.2, 'Double Rebound': 1.5, 'Red Cover': 1.5, 'Red Attempt': 0.5,
    'Return Shot': 1.1, 'Jhaanke Bok': 1.0, 'Assist': 0.75, 
    '3-Shot Streak': 1.0, '4-Shot Streak': 1.5, '5+ Shot Streak': 2.0
}

penalties = {
    'Opponent Coin Only': 0.7, 'Pocketed Striker': 0.75, 'Double Fine': 0.65
}

coin_pot_keys = [k for k in multipliers.keys() if 'Streak' not in k and 'Attempt' not in k]
foul_keys = list(penalties.keys())
players = ["P1", "P2", "P3", "P4"]
default_assignments = ["Pushpak", "Soumya", "Raktim", "Agniva"]

# --- INITIALIZE STATE ---
if 'match_log' not in st.session_state:
    st.session_state.match_log = []
if 'match_id' not in st.session_state:
    st.session_state.match_id = 1

for i, p in enumerate(players):
    if f"{p}_name" not in st.session_state:
        st.session_state[f"{p}_name"] = default_assignments[i]
    if f"{p}_won" not in st.session_state:
        st.session_state[f"{p}_won"] = False
    for action in list(multipliers.keys()) + list(penalties.keys()):
        if f"{p}_{action}" not in st.session_state:
            st.session_state[f"{p}_{action}"] = 0

# --- HELPER FUNCTIONS ---
def get_capped_pos(p):
    raw_pos = sum(st.session_state[f"{p}_{action}"] * w for action, w in multipliers.items())
    if st.session_state[f"{p}_won"]:
        raw_pos += 1.0
    return min(10.0, raw_pos)

def calculate_rating(p):
    capped_pos = get_capped_pos(p)
    total_foul = sum(st.session_state[f"{p}_{foul}"] * w for foul, w in penalties.items())
    return 2.0 + capped_pos - total_foul

def get_net_coins(p):
    pots = sum(st.session_state[f"{p}_{k}"] for k in coin_pot_keys)
    fouls = sum(st.session_state[f"{p}_{k}"] for k in foul_keys)
    return pots - fouls, pots, fouls

def get_most_frequent(p):
    top_shot = "None"
    top_shot_val = 0
    for action in multipliers.keys():
        val = st.session_state[f"{p}_{action}"]
        if val > top_shot_val:
            top_shot_val = val
            top_shot = action
            
    top_foul = "None"
    top_foul_val = 0
    for foul in penalties.keys():
        val = st.session_state[f"{p}_{foul}"]
        if val > top_foul_val:
            top_foul_val = val
            top_foul = foul
            
    return top_shot, top_shot_val, top_foul, top_foul_val

# --- STREAMLIT CALLBACKS ---
def reset_player_callback(p):
    st.session_state[f"{p}_won"] = False
    for action in list(multipliers.keys()) + list(penalties.keys()):
        st.session_state[f"{p}_{action}"] = 0

def save_match_callback():
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    players_saved = 0
    
    for p in players:
        total_actions = sum(st.session_state[f"{p}_{a}"] for a in list(multipliers.keys()) + list(penalties.keys()))
        if total_actions > 0 or st.session_state[f"{p}_won"]:
            net_c, _, _ = get_net_coins(p)
            top_shot, _, top_foul, _ = get_most_frequent(p)
            
            entry = {
                "Match_ID": f"M-{st.session_state.match_id:04d}",
                "Timestamp": timestamp,
                "Player": st.session_state[f"{p}_name"],
                "Won": "Yes" if st.session_state[f"{p}_won"] else "No",
                "Final_Rating": round(calculate_rating(p), 2),
                "Net_Coins": net_c,
                "Favored_Shot": top_shot,
                "Main_Foul": top_foul
            }
            for action in multipliers.keys(): entry[action] = st.session_state[f"{p}_{action}"]
            for foul in penalties.keys(): entry[foul] = st.session_state[f"{p
                                                                            
