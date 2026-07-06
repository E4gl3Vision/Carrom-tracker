import streamlit as st
import pandas as pd
import datetime

st.set_page_config(page_title="4-Player Carrom Tracker", layout="wide")

st.title("🎯 4-Player Club Carrom Tracker")
st.caption("Live multi-player dashboard. Export seamlessly to Google Sheets.")

# --- DATA DICTIONARIES ---
multipliers = {
    'Near Base': 0.7, 'Far Base': 0.9, 'Close Free Inch': 0.9, 'Close Crowd Inch': 1.0,
    'Medium Free Inch': 0.95, 'Medium Crowd Inch': 1.15, 'Far Free Inch': 1.15, 'Far Crowd Inch': 1.3,
    'Single Rebound': 1.2, 'Double Rebound': 1.5, 'Red Cover': 1.5, 'Red Attempt': 0.5,
    'Return Shot': 1.1, '3-Shot Streak': 0.7, '4-Shot Streak': 0.8, '5+ Shot Streak': 1.0
}
penalties = {
    'Opponent Coin Only': 0.7, 'Opponent Coin + Yours': 0.4, 'Pocketed Striker': 0.75, 'Double Fine': 0.65
}

players = ["P1", "P2", "P3", "P4"]

# --- INITIALIZE STATE ---
if 'match_log' not in st.session_state:
    st.session_state.match_log = []
if 'match_id' not in st.session_state:
    st.session_state.match_id = 1

for p in players:
    if f"{p}_name" not in st.session_state:
        st.session_state[f"{p}_name"] = f"Player {p[1]}"
    if f"{p}_won" not in st.session_state:
        st.session_state[f"{p}_won"] = False
    for action in list(multipliers.keys()) + list(penalties.keys()):
        if f"{p}_{action}" not in st.session_state:
            st.session_state[f"{p}_{action}"] = 0

# --- HELPER FUNCTIONS ---
def calculate_rating(p):
    raw_pos = sum(st.session_state[f"{p}_{action}"] * w for action, w in multipliers.items())
    if st.session_state[f"{p}_won"]:
        raw_pos += 1.0
    capped_pos = min(10.0, raw_pos)
    total_foul = sum(st.session_state[f"{p}_{foul}"] * w for foul, w in penalties.items())
    return capped_pos - total_foul

def reset_all_counters():
    for p in players:
        st.session_state[f"{p}_won"] = False
        for action in list(multipliers.keys()) + list(penalties.keys()):
            st.session_state[f"{p}_{action}"] = 0

# --- LIVE SCOREBOARD DASHBOARD ---
st.write("### 🏆 Live Match Scoreboard")
dash_cols = st.columns(4)
for i, p in enumerate(players):
    current_rating = calculate_rating(p)
    with dash_cols[i]:
        st.metric(
            label=st.session_state[f"{p}_name"], 
            value=f"{current_rating:.2f}",
            delta="Sub-Zero" if current_rating < 0 else None,
            delta_color="inverse"
        )
st.divider()

# --- PLAYER TABS FOR TAPPING ---
tabs = st.tabs([st.session_state[f"{p}_name"] for p in players])

for i, p in enumerate(players):
    with tabs[i]:
        # Header setup for the player
        setup_cols = st.columns([2, 1, 1])
        st.session_state[f"{p}_name"] = setup_cols[0].text_input("Player Name", value=st.session_state[f"{p}_name"], key=f"input_{p}_name")
        st.session_state[f"{p}_won"] = setup_cols[1].checkbox("Match Won (+1.0)", value=st.session_state[f"{p}_won"], key=f"input_{p}_won")
        
        if setup_cols[2].button(f"🧹 Reset {st.session_state[f'{p}_name']}", key=f"reset_{p}"):
            for action in list(multipliers.keys()) + list(penalties.keys()):
                st.session_state[f"{p}_{action}"] = 0
            st.session_state[f"{p}_won"] = False
            st.rerun()
            
        st.write("---")
        
        # Split layout for Positive Shots and Penalties
        col_pos, col_neg = st.columns(2)
        
        with col_pos:
            st.subheader("➕ Successful Pots")
            grid_cols = st.columns(2)
            for idx, (action, weight) in enumerate(multipliers.items()):
                c_col = grid_cols[idx % 2]
                c_col.write(f"**{action}** ({weight}x)")
                b_cols = c_col.columns([1, 2, 1])
                
                if b_cols[0].button("➖", key=f"sub_{p}_{action}"):
                    if st.session_state[f"{p}_{action}"] > 0:
                        st.session_state[f"{p}_{action}"] -= 1
                        st.rerun()
                        
                b_cols[1].markdown(f"<h4 style='text-align: center; margin:0;'>{st.session_state[f'{p}_{action}']}</h4>", unsafe_allow_html=True)
                
                if b_cols[2].button("➕", key=f"add_{p}_{action}"):
                    st.session_state[f"{p}_{action}"] += 1
                    st.rerun()
                c_col.write("---")
                
        with col_neg:
            st.subheader("⚠️ Fouls & Penalties")
            grid_cols_neg = st.columns(2)
            for idx, (foul, penalty) in enumerate(penalties.items()):
                c_col = grid_cols_neg[idx % 2]
                c_col.write(f"**{foul}** (-{penalty}x)")
                b_cols = c_col.columns([1, 2, 1])
                
                if b_cols[0].button("➖", key=f"sub_{p}_{foul}"):
                    if st.session_state[f"{p}_{foul}"] > 0:
                        st.session_state[f"{p}_{foul}"] -= 1
                        st.rerun()
                        
                b_cols[1].markdown(f"<h4 style='text-align: center; margin:0; color: #d9534f;'>{st.session_state[f'{p}_{foul}']}</h4>", unsafe_allow_html=True)
                
                if b_cols[2].button("➕", key=f"add_{p}_{foul}"):
                    st.session_state[f"{p}_{foul}"] += 1
                    st.rerun()
                c_col.write("---")

st.divider()

# --- SAVE & EXPORT LOGIC ---
if st.button("💾 SAVE MATCH FOR ALL 4 PLAYERS", type="primary", use_container_width=True):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Save a separate row for each player so it imports cleanly into Google Sheets
    for p in players:
        # Only log active players (e.g. if they scored any points/fouls or changed their default name)
        total_actions = sum(st.session_state[f"{p}_{a}"] for a in list(multipliers.keys()) + list(penalties.keys()))
        if total_actions > 0 or st.session_state[f"{p}_won"] or st.session_state[f"{p}_name"] != f"Player {p[1]}":
            
            entry = {
                "Match_ID": f"M-{st.session_state.match_id:04d}",
                "Timestamp": timestamp,
                "Player": st.session_state[f"{p}_name"],
                "Won": "Yes" if st.session_state[f"{p}_won"] else "No",
                "Final_Rating": round(calculate_rating(p), 2)
            }
            # Append all specific counts
            for action in multipliers.keys(): 
                entry[action] = st.session_state[f"{p}_{action}"]
            for foul in penalties.keys(): 
                entry[foul] = st.session_state[f"{p}_{foul}"]
                
            st.session_state.match_log.append(entry)
            
    st.session_state.match_id += 1
    reset_all_counters()
    st.success("Match saved successfully! Counters reset for the next game.")
    st.rerun()

# --- GOOGLE SHEETS EXPORT DASHBOARD ---
if st.session_state.match_log:
    st.write("### 📜 Session Data (Ready for Google Sheets)")
    log_df = pd.DataFrame(st.session_state.match_log)
    st.dataframe(log_df, use_container_width=True)
    
    csv_data = log_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download CSV Format", 
        data=csv_data, 
        file_name=f"carrom_4p_export_{datetime.datetime.now().strftime('%Y%m%d')}.csv", 
        mime='text/csv'
    )
