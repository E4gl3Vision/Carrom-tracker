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
    div[role="dialog"] {
        border-radius: 16px;
    }
</style>
""", unsafe_allow_html=True)

st.title("🎯 4-Player Club Carrom Tracker")
st.caption("Live multi-player dashboard. Base rating starts at 2.0. Includes Shot Accuracy %.")

# --- DATA DICTIONARIES ---
ROSTER = [
    "Abhinaba", "Agniva", "Debottam", "Krish", "Orghya", 
    "Pushpak", "Raktim", "Shakir", "Soumya", 
    "Guest 1", "Guest 2", "Guest 3", "Guest 4"
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

# --- LIVE SCOREBOARD DASHBOARD ---
st.write("### 🏆 Live Match Scoreboard")
dash_cols = st.columns(4)
for i, p in enumerate(players):
    current_rating = calculate_rating(p)
    net_c, _, _ = get_net_coins(p)
    acc_pct, _, _ = get_accuracy(p)
    top_shot, shot_count, top_foul, foul_count = get_most_frequent(p)
    
    with dash_cols[i]:
        st.metric(
            label=f"{st.session_state[f'{p}_name']} (🪙 {net_c} | 🎯 {acc_pct:.0f}%)", 
            value=f"{current_rating:.2f}",
            delta="Below 2.0 Baseline" if current_rating < 2.0 else "Active",
            delta_color="inverse" if current_rating < 2.0 else "off"
        )
        st.markdown(f"""
        <div class="freq-box">
            🔥 {top_shot} ({shot_count})<br>
            ❌ {top_foul} ({foul_count})
        </div>
        """, unsafe_allow_html=True)
st.divider()

# --- PLAYER TABS FOR TAPPING ---
tabs = st.tabs([st.session_state[f"{p}_name"] for p in players])

for i, p in enumerate(players):
    with tabs[i]:
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
        
