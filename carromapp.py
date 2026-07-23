import streamlit as st
import pandas as pd
import datetime

st.set_page_config(page_title="4-Player Carrom Tracker", layout="wide", initial_sidebar_state="collapsed")

# --- SAFE TOAST NOTIFICATIONS ---
if "flash_msg" in st.session_state:
    st.toast(st.session_state.flash_msg["msg"], icon=st.session_state.flash_msg["icon"])
    del st.session_state.flash_msg

# --- WIN CELEBRATION (fires once, right after a win is registered) ---
if st.session_state.get("win_celebrate"):
    st.balloons()
    del st.session_state["win_celebrate"]

# ============================================================
#  DESIGN SYSTEM
#  A carrom board's own materials, told back to itself:
#  walnut frame, bleached-cream playing field, felt-green
#  scoring turf, and the two coin colours (black/ivory) plus
#  the red queen as the single "alert" accent.
# ============================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Oswald:wght@500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@500;700&display=swap');

:root {
    --wood-dark: #2C1810;
    --wood-mid: #5C3A21;
    --wood-light: #8A5A34;
    --cream: #F2E6CC;
    --cream-dim: #D9C9A3;
    --felt: #1B4332;
    --felt-light: #2D6A4F;
    --gold: #C9A227;
    --gold-bright: #E4C245;
    --coin-black: #171512;
    --coin-white: #F5F0E6;
    --queen-red: #B23A2E;
}

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(14px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes coinFlip {
    0%   { transform: rotateY(0deg) scale(0.7); opacity: 0; }
    50%  { transform: rotateY(180deg) scale(1.05); opacity: 1; }
    100% { transform: rotateY(360deg) scale(1); opacity: 1; }
}
@keyframes pulseGold {
    0%, 100% { box-shadow: 0 0 0 0 rgba(228,194,69,0.55), 0 6px 14px rgba(0,0,0,0.35); }
    50%      { box-shadow: 0 0 20px 6px rgba(228,194,69,0.55), 0 6px 14px rgba(0,0,0,0.35); }
}
@keyframes shimmerMove {
    0%   { background-position: 0% 50%; }
    100% { background-position: 200% 50%; }
}
@keyframes crownBob {
    0%, 100% { transform: translateY(0); }
    50%      { transform: translateY(-3px); }
}
@media (prefers-reduced-motion: reduce) {
    .coin-card, .coin-badge, .coin-card.leader { animation: none !important; }
}

.stApp {
    background:
        radial-gradient(ellipse at top, #241108 0%, #140b06 55%, #0d0704 100%);
    color: var(--cream);
}

header { visibility: hidden; }
#MainMenu { visibility: hidden; }

/* ---------- HERO BANNER ---------- */
.carrom-hero {
    position: relative;
    margin: -1rem -1rem 1.5rem -1rem;
    padding: 2.2rem 2rem 1.6rem 2rem;
    background:
        repeating-linear-gradient(100deg, rgba(0,0,0,0.10) 0px, rgba(0,0,0,0.10) 2px, transparent 2px, transparent 22px),
        linear-gradient(135deg, var(--wood-dark) 0%, var(--wood-mid) 55%, var(--wood-light) 100%);
    border-bottom: 4px solid var(--gold);
    box-shadow: 0 8px 24px rgba(0,0,0,0.45);
}
.carrom-hero::before, .carrom-hero::after {
    content: "";
    position: absolute;
    top: 14px;
    width: 14px; height: 14px;
    border-radius: 50%;
    background: radial-gradient(circle at 35% 30%, var(--coin-white), var(--coin-black) 75%);
    box-shadow: 0 0 0 3px rgba(201,162,39,0.35);
}
.carrom-hero::before { left: 18px; }
.carrom-hero::after { right: 18px; }
.carrom-hero h1 {
    font-family: 'Oswald', sans-serif;
    font-weight: 700;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    font-size: 2.3rem;
    margin: 0;
    color: var(--cream);
    text-shadow: 0 2px 0 rgba(0,0,0,0.4);
}
.carrom-hero p {
    margin: 0.35rem 0 0 0;
    color: var(--cream-dim);
    font-size: 0.95rem;
    letter-spacing: 0.01em;
}
.carrom-hero .tag {
    display: inline-block;
    margin-top: 0.7rem;
    padding: 0.2rem 0.7rem;
    border: 1px solid var(--gold);
    border-radius: 999px;
    color: var(--gold-bright);
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    letter-spacing: 0.06em;
}

/* ---------- SECTION LABELS ---------- */
h3, .stMarkdown h3 {
    font-family: 'Oswald', sans-serif !important;
    letter-spacing: 0.03em;
    text-transform: uppercase;
    font-size: 1.05rem !important;
    color: var(--gold-bright) !important;
    border-left: 3px solid var(--gold);
    padding-left: 0.6rem;
    margin-top: 1.2rem !important;
}
.stMarkdown h4 { font-family: 'Oswald', sans-serif !important; color: var(--cream); }

/* ---------- PLAYER SCOREBOARD CARDS (coin-badge design) ---------- */
.coin-card {
    position: relative;
    background: linear-gradient(160deg, var(--felt) 0%, #123526 100%);
    border: 1px solid rgba(201,162,39,0.35);
    border-top: 3px solid var(--gold);
    border-radius: 10px;
    padding: 1rem 0.9rem 0.8rem 0.9rem;
    text-align: center;
    box-shadow: 0 6px 14px rgba(0,0,0,0.35), inset 0 1px 0 rgba(255,255,255,0.03);
    margin-bottom: 0.6rem;
    animation: fadeInUp 0.5s ease both;
    transition: transform 0.18s ease, box-shadow 0.18s ease;
}
.coin-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 22px rgba(0,0,0,0.45);
}
.coin-card.leader {
    border-top-color: var(--gold-bright);
    animation: fadeInUp 0.5s ease both, pulseGold 2.4s ease-in-out infinite;
}
.coin-card .crown {
    position: absolute;
    top: -14px; left: 50%;
    transform: translateX(-50%);
    font-size: 1.1rem;
    animation: crownBob 1.8s ease-in-out infinite;
}
.coin-card .pname {
    font-family: 'Oswald', sans-serif;
    text-transform: uppercase;
    letter-spacing: 0.03em;
    font-size: 0.92rem;
    color: var(--cream);
    margin-bottom: 0.55rem;
}
.coin-badge {
    width: 74px; height: 74px;
    margin: 0 auto 0.5rem auto;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    background: radial-gradient(circle at 35% 30%, var(--coin-white) 0%, #cfc4a8 45%, var(--coin-black) 100%);
    border: 2px solid var(--gold);
    box-shadow: 0 4px 10px rgba(0,0,0,0.5), inset 0 0 8px rgba(0,0,0,0.4);
    animation: coinFlip 0.6s ease-out both;
    transform-style: preserve-3d;
    transition: transform 0.2s ease;
}
.coin-card:hover .coin-badge { transform: scale(1.08); }
.coin-badge span {
    font-family: 'JetBrains Mono', monospace;
    font-weight: 700;
    font-size: 1.35rem;
    color: var(--wood-dark);
}
.coin-card .status {
    font-size: 0.68rem;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    color: var(--gold-bright);
    margin-bottom: 0.4rem;
}
.coin-card .status.below { color: var(--queen-red); }
.coin-card .substats {
    font-size: 0.8rem;
    color: var(--cream-dim);
    margin-bottom: 0.35rem;
}
.freq-box {
    background: rgba(0,0,0,0.25);
    border: 1px solid rgba(201,162,39,0.25);
    border-radius: 8px;
    padding: 0.4rem 0.5rem;
    font-size: 0.75rem;
    color: var(--cream-dim);
    text-align: left;
}

/* ---------- TABS (styled as the wooden rail dividers) ---------- */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: rgba(0,0,0,0.25);
    padding: 6px;
    border-radius: 10px;
    border: 1px solid rgba(201,162,39,0.25);
}
button[data-baseweb="tab"] {
    font-family: 'Oswald', sans-serif !important;
    text-transform: uppercase;
    letter-spacing: 0.03em;
    font-size: 0.95rem !important;
    padding-top: 12px !important;
    padding-bottom: 12px !important;
    color: var(--cream-dim) !important;
    border-radius: 8px !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
    background: linear-gradient(160deg, var(--felt-light), var(--felt)) !important;
    color: var(--gold-bright) !important;
    box-shadow: inset 0 0 0 1px var(--gold);
}
.stTabs [data-baseweb="tab-highlight"] { background-color: var(--gold) !important; transition: left 0.25s ease, width 0.25s ease; }
button[data-baseweb="tab"] { transition: color 0.15s ease, background 0.15s ease; }

/* ---------- BUTTONS ---------- */
.stButton > button {
    border-radius: 8px !important;
    border: 1px solid rgba(201,162,39,0.4) !important;
    font-family: 'Inter', sans-serif;
    font-weight: 600;
    transition: transform 0.06s ease, box-shadow 0.15s ease;
}
.stButton > button:hover { transform: translateY(-1px); box-shadow: 0 4px 10px rgba(0,0,0,0.35); }
.stButton > button:active { transform: translateY(1px) scale(0.97); box-shadow: 0 2px 4px rgba(0,0,0,0.4) !important; }
.stButton > button[kind="primary"] {
    background: linear-gradient(160deg, var(--gold-bright), var(--gold)) !important;
    color: var(--wood-dark) !important;
    border: none !important;
    font-family: 'Oswald', sans-serif;
    text-transform: uppercase;
    letter-spacing: 0.03em;
}
.stButton > button[kind="secondary"] {
    background: rgba(255,255,255,0.05) !important;
    color: var(--cream) !important;
}

/* ---------- PROGRESS BAR (fills like the board's scoring cap) ---------- */
.stProgress > div > div > div {
    background: linear-gradient(90deg, var(--gold), var(--gold-bright), var(--gold)) !important;
    background-size: 200% 100%;
    animation: shimmerMove 1.8s linear infinite;
    transition: width 0.4s ease;
}
.stProgress > div > div { background: rgba(255,255,255,0.08) !important; border-radius: 8px; }

/* ---------- INPUTS / SELECT ---------- */
.stSelectbox div[data-baseweb="select"] {
    border-radius: 8px;
    border: 1px solid rgba(201,162,39,0.35) !important;
}

/* ---------- EXPANDER / DATAFRAME ---------- */
.streamlit-expanderHeader, div[data-testid="stExpander"] summary {
    font-family: 'Oswald', sans-serif !important;
    color: var(--gold-bright) !important;
    letter-spacing: 0.02em;
}
div[data-testid="stDataFrame"] { border: 1px solid rgba(201,162,39,0.3); border-radius: 8px; overflow: hidden; }

/* ---------- DIALOG ---------- */
div[role="dialog"] {
    border-radius: 16px;
    background: linear-gradient(165deg, #1c1108, #0f0906) !important;
    border: 1px solid var(--gold);
}

/* ---------- MISC ---------- */
hr, .stDivider { border-color: rgba(201,162,39,0.25) !important; }
.stCaption, [data-testid="stCaptionContainer"] { color: var(--cream-dim) !important; }
</style>
""", unsafe_allow_html=True)

# --- HERO ---
st.markdown("""
<div class="carrom-hero">
    <h1>&#127919; 4-Player Club Carrom Tracker</h1>
    <p>Live multi-player dashboard &middot; base rating starts at 2.0 &middot; shot accuracy tracked in real time</p>
    <span class="tag">LIVE SCORING SESSION</span>
</div>
""", unsafe_allow_html=True)

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
if 'show_summary' not in st.session_state:
    st.session_state.show_summary = False
if 'last_match_summary' not in st.session_state:
    st.session_state.last_match_summary = []

for i, p in enumerate(players):
    if f"{p}_name" not in st.session_state:
        st.session_state[f"{p}_name"] = default_assignments[i]
    if f"{p}_won" not in st.session_state:
        st.session_state[f"{p}_won"] = False
    if f"{p}_Missed_Shot" not in st.session_state:
        st.session_state[f"{p}_Missed_Shot"] = 0
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

def get_accuracy(p):
    """Calculates accuracy by factoring in pots, missed empty turns, and ALL shot-consuming fouls."""
    pots = sum(st.session_state[f"{p}_{k}"] for k in coin_pot_keys)
    
    # Automatically sums all fouls + red attempts as missed/wasted shots
    foul_shots = sum(st.session_state[f"{p}_{k}"] for k in foul_keys)
    other_shots = st.session_state[f"{p}_Red Attempt"] + foul_shots
    misses = st.session_state[f"{p}_Missed_Shot"]
    
    total_shots = pots + other_shots + misses
    acc_percent = (pots / total_shots * 100) if total_shots > 0 else 0.0
    return acc_percent, pots, total_shots

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
def adjust_counter(p, action, delta):
    new_val = st.session_state[f"{p}_{action}"] + delta
    if new_val >= 0:
        st.session_state[f"{p}_{action}"] = new_val

def toggle_win(p):
    st.session_state[f"{p}_won"] = not st.session_state[f"{p}_won"]
    if st.session_state[f"{p}_won"]:
        st.session_state["win_celebrate"] = True

def reset_player_callback(p):
    st.session_state[f"{p}_won"] = False
    st.session_state[f"{p}_Missed_Shot"] = 0
    for action in list(multipliers.keys()) + list(penalties.keys()):
        st.session_state[f"{p}_{action}"] = 0

def save_match_callback():
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    players_saved = 0
    st.session_state.last_match_summary = []
    
    for p in players:
        total_actions = sum(st.session_state[f"{p}_{a}"] for a in list(multipliers.keys()) + list(penalties.keys())) + st.session_state[f"{p}_Missed_Shot"]
        if total_actions > 0 or st.session_state[f"{p}_won"]:
            net_c, _, _ = get_net_coins(p)
            acc_pct, pots, total_shots = get_accuracy(p)
            top_shot, _, top_foul, _ = get_most_frequent(p)
            
            entry = {
                "Match_ID": f"M-{st.session_state.match_id:04d}",
                "Timestamp": timestamp,
                "Player": st.session_state[f"{p}_name"],
                "Won": "Yes" if st.session_state[f"{p}_won"] else "No",
                "Final_Rating": round(calculate_rating(p), 2),
                "Accuracy": f"{acc_pct:.1f}%",
                "Total_Shots": total_shots,
                "Net_Coins": net_c,
                "Favored_Shot": top_shot,
                "Main_Foul": top_foul
            }
            for action in multipliers.keys(): entry[action] = st.session_state[f"{p}_{action}"]
            for foul in penalties.keys(): entry[foul] = st.session_state[f"{p}_{foul}"]
            entry["Missed_Shots"] = st.session_state[f"{p}_Missed_Shot"]
                
            st.session_state.match_log.append(entry)
            st.session_state.last_match_summary.append(entry)
            players_saved += 1
            
    if players_saved > 0:
        st.session_state.match_id += 1
        for p in players:
            reset_player_callback(p)
        st.session_state.show_summary = True
        st.session_state.flash_msg = {"msg": f"Match saved successfully for {players_saved} players!", "icon": "✅"}
    else:
        st.session_state.flash_msg = {"msg": "No points scored yet. Tap some counters before saving.", "icon": "⚠️"}

# --- MODAL DIALOG COMPONENT (POST-GAME SUMMARY WINDOW) ---
@st.dialog("🏆 Post-Game Match Summary", width="large")
def post_game_summary():
    st.caption("Perfect for screenshots! Contains full match breakdown.")
    
    if len(st.session_state.last_match_summary) > 0:
        cols = st.columns(len(st.session_state.last_match_summary))
        for idx, p_data in enumerate(st.session_state.last_match_summary):
            with cols[idx]:
                st.subheader(f"{'👑 ' if p_data['Won'] == 'Yes' else ''}{p_data['Player']}")
                st.metric("Final Rating", f"{p_data['Final_Rating']:.2f}", f"Accuracy: {p_data['Accuracy']}")
                st.write("---")
                
                st.markdown("**🟢 Shots Executed:**")
                shots_exist = False
                for action in multipliers.keys():
                    if p_data[action] > 0:
                        st.markdown(f"- {action}: `{p_data[action]}`")
                        shots_exist = True
                if not shots_exist: st.markdown("- *None*")
                
                st.markdown("**🔴 Fouls & Misses:**")
                st.markdown(f"- Missed Shots: `{p_data['Missed_Shots']}`")
                for foul in penalties.keys():
                    if p_data[foul] > 0:
                        st.markdown(f"- {foul}: `{p_data[foul]}`")
    
    st.write("---")
    if st.button("❌ Close Summary Window", use_container_width=True, type="primary"):
        st.session_state.show_summary = False
        st.rerun()

if st.session_state.show_summary:
    post_game_summary()

# --- LIVE SCOREBOARD DASHBOARD (coin-badge cards) ---
st.write("### 🏆 Live Match Scoreboard")

# Work out who's currently leading (only crown someone once ratings have moved)
ratings = {p: calculate_rating(p) for p in players}
has_activity = any(r != 2.0 for r in ratings.values())
leader_p = max(ratings, key=ratings.get) if has_activity else None

dash_cols = st.columns(4)
for i, p in enumerate(players):
    current_rating = ratings[p]
    net_c, _, _ = get_net_coins(p)
    acc_pct, _, _ = get_accuracy(p)
    top_shot, shot_count, top_foul, foul_count = get_most_frequent(p)
    below = current_rating < 2.0
    is_leader = (p == leader_p)

    with dash_cols[i]:
        st.markdown(f"""
        <div class="coin-card {'leader' if is_leader else ''}" style="animation-delay:{i*0.08:.2f}s" title="{st.session_state[f'{p}_name']}: {current_rating:.2f} rating, {acc_pct:.0f}% accuracy">
            {'<div class="crown">&#128081;</div>' if is_leader else ''}
            <div class="pname">{st.session_state[f'{p}_name']}</div>
            <div class="coin-badge"><span>{current_rating:.2f}</span></div>
            <div class="status {'below' if below else ''}">{'Below 2.0 Baseline' if below else ('In The Lead' if is_leader else 'Active')}</div>
            <div class="substats">🪙 {net_c} net &nbsp;|&nbsp; 🎯 {acc_pct:.0f}% acc</div>
            <div class="freq-box">
                🔥 {top_shot} ({shot_count})<br>
                ❌ {top_foul} ({foul_count})
            </div>
        </div>
        """, unsafe_allow_html=True)
st.divider()

# --- PLAYER TABS FOR TAPPING ---
tabs = st.tabs([st.session_state[f"{p}_name"] for p in players])

for i, p in enumerate(players):
    with tabs[i]
        capped_val = get_capped_pos(p)
        net_c, p_c, _ = get_net_coins(p)
        acc_pct, pots, total_shots = get_accuracy(p)
        top_shot, shot_count, top_foul, foul_count = get_most_frequent(p)
        
        st.progress(capped_val / 10.0, text=f"Positive Score Cap Progression: {capped_val:.2f} / 10.00")
        
        stat_cols = st.columns(2)
        stat_cols[0].markdown(f"🎯 **Accuracy:** `{acc_pct:.1f}%` *({pots}/{total_shots})* &nbsp;&nbsp;|&nbsp;&nbsp; 🪙 **Net Coins:** `{net_c}`")
        stat_cols[1].markdown(f"🔥 **Top Shot:** `{top_shot}` ({shot_count}) &nbsp;&nbsp;|&nbsp;&nbsp; ❌ **Top Foul:** `{top_foul}` ({foul_count})")
        
        st.write("---")
        
        setup_cols = st.columns([3, 1])
        setup_cols[0].selectbox("Select Player", options=ROSTER, key=f"{p}_name", label_visibility="collapsed")
        setup_cols[1].button(f"🧹 Reset Form", key=f"reset_{p}", use_container_width=True, on_click=reset_player_callback, args=(p,))
            
        st.write("---")
        
        # --- NEW MISSED SHOT TRACKER UI ---
        st.markdown("**⚪ Missed Shots (Empty Turns)**")
        miss_cols = st.columns([1, 1, 2, 4])
        miss_cols[0].button("➖", key=f"sub_{p}_miss", use_container_width=True, on_click=adjust_counter, args=(p, "Missed_Shot", -1))
        miss_cols[1].markdown(f"<h4 style='text-align: center; margin:0;'>{st.session_state[f'{p}_Missed_Shot']}</h4>", unsafe_allow_html=True)
        miss_cols[2].button("➕ Missed Shot", key=f"add_{p}_miss", use_container_width=True, on_click=adjust_counter, args=(p, "Missed_Shot", 1))
        miss_cols[3].markdown(f"<div style='color: #94a3b8; padding-top: 8px;'>*Tap for any shot where no coin or foul is made.*</div>", unsafe_allow_html=True)
        
        st.write("---")
        
        col_pos, col_neg = st.columns(2)
        with col_pos:
            st.subheader("➕ Successful Pots")
            grid_cols = st.columns(2)
            for idx, (action, weight) in enumerate(multipliers.items()):
                c_col = grid_cols[idx % 2]
                
                if action in coin_pot_keys:
                    c_col.caption(f"**{action}** ({weight}x) 🪙")
                else:
                    c_col.caption(f"**{action}** ({weight}x)")
                
                b_cols = c_col.columns([1, 1.5, 1])
                b_cols[0].button("➖", key=f"sub_{p}_{action}", use_container_width=True, on_click=adjust_counter, args=(p, action, -1))
                b_cols[1].markdown(f"<h4 style='text-align: center; margin:0;'>{st.session_state[f'{p}_{action}']}</h4>", unsafe_allow_html=True)
                b_cols[2].button("➕", key=f"add_{p}_{action}", use_container_width=True, on_click=adjust_counter, args=(p, action, 1))
                c_col.write("") 
                
        with col_neg:
            st.subheader("⚠️ Fouls & Penalties")
            grid_cols_neg = st.columns(2)
            for idx, (foul, penalty) in enumerate(penalties.items()):
                c_col = grid_cols_neg[idx % 2]
                c_col.caption(f"**{foul}** (-{penalty}x) ❌")
                
                b_cols = c_col.columns([1, 1.5, 1])
                b_cols[0].button("➖", key=f"sub_{p}_{foul}", use_container_width=True, on_click=adjust_counter, args=(p, foul, -1))
                b_cols[1].markdown(f"<h4 style='text-align: center; margin:0; color: #ff4b4b;'>{st.session_state[f'{p}_{foul}']}</h4>", unsafe_allow_html=True)
                b_cols[2].button("➕", key=f"add_{p}_{foul}", use_container_width=True, on_click=adjust_counter, args=(p, foul, 1))
                c_col.write("")
                
        # --- SAFE SINGLE-BUTTON MATCH WON TOGGLE ---
        st.write("---")
        btn_label = "✅ MATCH WON BONUSED (+1.0 applied) — Tap to Remove" if st.session_state[f"{p}_won"] else "🏆 REGISTER MATCH WIN (+1.0 Bonus)"
        btn_type = "secondary" if st.session_state[f"{p}_won"] else "primary"
        st.button(btn_label, key=f"btn_won_{p}", use_container_width=True, type=btn_type, on_click=toggle_win, args=(p,))

st.divider()

# --- SAVE & EXPORT LOGIC ---
st.button("💾 SAVE MATCH FOR ALL ACTIVE PLAYERS", type="primary", use_container_width=True, on_click=save_match_callback)

# --- GOOGLE SHEETS EXPORT DASHBOARD ---
if st.session_state.match_log:
    with st.expander("📂 View Session Log & Export Data", expanded=True):
        log_df = pd.DataFrame(st.session_state.match_log)
        st.dataframe(log_df, use_container_width=True)
        
        csv_data = log_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download CSV Format", 
            data=csv_data, 
            file_name=f"carrom_4p_export_{datetime.datetime.now().strftime('%Y%m%d')}.csv", 
            mime='text/csv',
            use_container_width=True
        )
