import streamlit as st
import pandas as pd
import datetime

st.set_page_config(page_title="4-Player Carrom Tracker", layout="wide", initial_sidebar_state="collapsed")

# --- FIX: Safe Toast Notifications across page refreshes ---
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
st.caption("Live multi-player dashboard with Net Coin tracking and Shot Frequencies.")

# --- DATA DICTIONARIES ---
multipliers = {
    'Near Base': 0.7, 'Far Base': 0.9, 'Close Free Inch': 0.9, 'Close Crowd Inch': 1.0,
    'Medium Free Inch': 0.95, 'Medium Crowd Inch': 1.15, 'Far Free Inch': 1.15, 'Far Crowd Inch': 1.3,
    'Single Rebound': 1.2, 'Double Rebound': 1.5, 'Red Cover': 1.5, 'Red Attempt': 0.5,
    'Return Shot': 1.1, 'Jhaanke Bok': 1.0, '3-Shot Streak': 0.7, '4-Shot Streak': 0.8, '5+ Shot Streak': 1.0
}

penalties = {
    'Opponent Coin Only': 0.7, 'Pocketed Striker': 0.75, 'Double Fine': 0.65
}

coin_pot_keys = [k for k in multipliers.keys() if 'Streak' not in k and 'Attempt' not in k]
foul_keys = list(penalties.keys())

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
def get_capped_pos(p):
    raw_pos = sum(st.session_state[f"{p}_{action}"] * w for action, w in multipliers.items())
    if st.session_state[f"{p}_won"]:
        raw_pos += 1.0
    return min(10.0, raw_pos)

def calculate_rating(p):
    capped_pos = get_capped_pos(p)
    total_foul = sum(st.session_state[f"{p}_{foul}"] * w for foul, w in penalties.items())
    return capped_pos - total_foul

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
    net_c, _, _ = get_net_coins(p)
    top_shot, shot_count, top_foul, foul_count = get_most_frequent(p)
    
    with dash_cols[i]:
        st.metric(
            label=f"{st.session_state[f'{p}_name']} (🪙 {net_c} Coins)", 
            value=f"{current_rating:.2f}",
            delta="Sub-Zero Penalty" if current_rating < 0 else "Active",
            delta_color="inverse" if current_rating < 0 else "off"
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
        net_c, p_c, f_c = get_net_coins(p)
        top_shot, shot_count, top_foul, foul_count = get_most_frequent(p)
        
        st.progress(capped_val / 10.0, text=f"Positive Score Cap Progression: {capped_val:.2f} / 10.00")
        
        stat_cols = st.columns(2)
        stat_cols[0].markdown(f"🪙 **Net Coins Pocketed:** `{net_c}` &nbsp;&nbsp; *(Pots: {p_c} | Fouls: {f_c})*")
        stat_cols[1].markdown(f"🔥 **Top Shot:** `{top_shot}` ({shot_count}) &nbsp;&nbsp;|&nbsp;&nbsp; ❌ **Top Foul:** `{top_foul}` ({foul_count})")
        
        st.write("")
        
        setup_cols = st.columns([2, 1, 1])
        st.session_state[f"{p}_name"] = setup_cols[0].text_input("Edit Name", value=st.session_state[f"{p}_name"], key=f"input_{p}_name", label_visibility="collapsed")
        
        setup_cols[1].toggle("🏆 Match Won (+1.0)", key=f"{p}_won")
        
        if setup_cols[2].button(f"🧹 Reset Form", key=f"reset_{p}", use_container_width=True):
            for action in list(multipliers.keys()) + list(penalties.keys()):
                st.session_state[f"{p}_{action}"] = 0
            st.session_state[f"{p}_won"] = False
            st.rerun()
            
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
                if b_cols[0].button("➖", key=f"sub_{p}_{action}", use_container_width=True):
                    if st.session_state[f"{p}_{action}"] > 0:
                        st.session_state[f"{p}_{action}"] -= 1
                        st.rerun()
                        
                b_cols[1].markdown(f"<h4 style='text-align: center; margin:0;'>{st.session_state[f'{p}_{action}']}</h4>", unsafe_allow_html=True)
                
                if b_cols[2].button("➕", key=f"add_{p}_{action}", use_container_width=True):
                    st.session_state[f"{p}_{action}"] += 1
                    st.rerun()
                c_col.write("") 
                
        with col_neg:
            st.subheader("⚠️ Fouls & Penalties")
            grid_cols_neg = st.columns(2)
            for idx, (foul, penalty) in enumerate(penalties.items()):
                c_col = grid_cols_neg[idx % 2]
                c_col.caption(f"**{foul}** (-{penalty}x) ❌")
                
                b_cols = c_col.columns([1, 1.5, 1])
                if b_cols[0].button("➖", key=f"sub_{p}_{foul}", use_container_width=True):
                    if st.session_state[f"{p}_{foul}"] > 0:
                        st.session_state[f"{p}_{foul}"] -= 1
                        st.rerun()
                        
                b_cols[1].markdown(f"<h4 style='text-align: center; margin:0; color: #ff4b4b;'>{st.session_state[f'{p}_{foul}']}</h4>", unsafe_allow_html=True)
                
                if b_cols[2].button("➕", key=f"add_{p}_{foul}", use_container_width=True):
                    st.session_state[f"{p}_{foul}"] += 1
                    st.rerun()
                c_col.write("")

st.divider()

# --- SAVE & EXPORT LOGIC ---
if st.button("💾 SAVE MATCH FOR ALL ACTIVE PLAYERS", type="primary", use_container_width=True):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    players_saved = 0
    for p in players:
        # FIX: Ensure a player is ONLY saved if they scored real points or won.
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
            for foul in penalties.keys(): entry[foul] = st.session_state[f"{p}_{foul}"]
                
            st.session_state.match_log.append(entry)
            players_saved += 1
            
    if players_saved > 0:
        st.session_state.match_id += 1
        reset_all_counters()
        # FIX: Store notification safely in session state so it survives the rerun
        st.session_state.flash_msg = {"msg": f"Match saved successfully for {players_saved} players!", "icon": "✅"}
    else:
        st.session_state.flash_msg = {"msg": "No points scored yet. Tap some counters before saving.", "icon": "⚠️"}
    
    st.rerun()

# --- GOOGLE SHEETS EXPORT DASHBOARD ---
if st.session_state.match_log:
    # FIX: Automatically expand to display the data immediately after a successful save
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
st.title("🎯 4-Player Carrom Rating Tracker")
st.caption("Live multi-player rating dashboard.")

# --- DATA DICTIONARIES ---
multipliers = {
    'Near Base': 0.7, 'Far Base': 0.9, 'Close Free Inch': 0.9, 'Close Crowd Inch': 1.0,
    'Medium Free Inch': 0.95, 'Medium Crowd Inch': 1.15, 'Far Free Inch': 1.15, 'Far Crowd Inch': 1.3,
    'Single Rebound': 1.2, 'Double Rebound': 1.5, 'Red Cover': 1.5, 'Red Attempt': 0.5,
    'Return Shot': 1.1, 'Jhaanke Bok': 1.0, '3-Shot Streak': 0.7, '4-Shot Streak': 0.8, '5+ Shot Streak': 1.0
}

penalties = {
    'Opponent Coin Only': 0.7, 'Pocketed Striker': 0.75, 'Double Fine': 0.65
}

coin_pot_keys = [k for k in multipliers.keys() if 'Streak' not in k and 'Attempt' not in k]
foul_keys = list(penalties.keys())

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
def get_capped_pos(p):
    raw_pos = sum(st.session_state[f"{p}_{action}"] * w for action, w in multipliers.items())
    if st.session_state[f"{p}_won"]:
        raw_pos += 1.0
    return min(10.0, raw_pos)

def calculate_rating(p):
    capped_pos = get_capped_pos(p)
    total_foul = sum(st.session_state[f"{p}_{foul}"] * w for foul, w in penalties.items())
    return capped_pos - total_foul

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
    net_c, _, _ = get_net_coins(p)
    top_shot, shot_count, top_foul, foul_count = get_most_frequent(p)
    
    with dash_cols[i]:
        st.metric(
            label=f"{st.session_state[f'{p}_name']} (🪙 {net_c} Coins)", 
            value=f"{current_rating:.2f}",
            delta="Sub-Zero Penalty" if current_rating < 0 else "Active",
            delta_color="inverse" if current_rating < 0 else "off"
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
        # --- UI: Cap Progress, Net Coins & Frequency ---
        capped_val = get_capped_pos(p)
        net_c, p_c, f_c = get_net_coins(p)
        top_shot, shot_count, top_foul, foul_count = get_most_frequent(p)
        
        st.progress(capped_val / 10.0, text=f"Positive Score Cap Progression: {capped_val:.2f} / 10.00")
        
        stat_cols = st.columns(2)
        stat_cols[0].markdown(f"🪙 **Net Coins Pocketed:** `{net_c}` &nbsp;&nbsp; *(Pots: {p_c} | Fouls: {f_c})*")
        stat_cols[1].markdown(f"🔥 **Top Shot:** `{top_shot}` ({shot_count}) &nbsp;&nbsp;|&nbsp;&nbsp; ❌ **Top Foul:** `{top_foul}` ({foul_count})")
        
        st.write("")
        
        setup_cols = st.columns([2, 1, 1])
        st.session_state[f"{p}_name"] = setup_cols[0].text_input("Edit Name", value=st.session_state[f"{p}_name"], key=f"input_{p}_name", label_visibility="collapsed")
        
        setup_cols[1].toggle("🏆 Match Won (+1.0)", key=f"{p}_won")
        
        if setup_cols[2].button(f"🧹 Reset Form", key=f"reset_{p}", use_container_width=True):
            for action in list(multipliers.keys()) + list(penalties.keys()):
                st.session_state[f"{p}_{action}"] = 0
            st.session_state[f"{p}_won"] = False
            st.rerun()
            
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
                if b_cols[0].button("➖", key=f"sub_{p}_{action}", use_container_width=True):
                    if st.session_state[f"{p}_{action}"] > 0:
                        st.session_state[f"{p}_{action}"] -= 1
                        st.rerun()
                        
                b_cols[1].markdown(f"<h4 style='text-align: center; margin:0;'>{st.session_state[f'{p}_{action}']}</h4>", unsafe_allow_html=True)
                
                if b_cols[2].button("➕", key=f"add_{p}_{action}", use_container_width=True):
                    st.session_state[f"{p}_{action}"] += 1
                    st.rerun()
                c_col.write("") 
                
        with col_neg:
            st.subheader("⚠️ Fouls & Penalties")
            grid_cols_neg = st.columns(2)
            for idx, (foul, penalty) in enumerate(penalties.items()):
                c_col = grid_cols_neg[idx % 2]
                c_col.caption(f"**{foul}** (-{penalty}x) ❌")
                
                b_cols = c_col.columns([1, 1.5, 1])
                if b_cols[0].button("➖", key=f"sub_{p}_{foul}", use_container_width=True):
                    if st.session_state[f"{p}_{foul}"] > 0:
                        st.session_state[f"{p}_{foul}"] -= 1
                        st.rerun()
                        
                b_cols[1].markdown(f"<h4 style='text-align: center; margin:0; color: #ff4b4b;'>{st.session_state[f'{p}_{foul}']}</h4>", unsafe_allow_html=True)
                
                if b_cols[2].button("➕", key=f"add_{p}_{foul}", use_container_width=True):
                    st.session_state[f"{p}_{foul}"] += 1
                    st.rerun()
                c_col.write("")

st.divider()

# --- SAVE & EXPORT LOGIC ---
if st.button("💾 SAVE MATCH FOR ALL ACTIVE PLAYERS", type="primary", use_container_width=True):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    players_saved = 0
    for p in players:
        total_actions = sum(st.session_state[f"{p}_{a}"] for a in list(multipliers.keys()) + list(penalties.keys()))
        if total_actions > 0 or st.session_state[f"{p}_won"] or st.session_state[f"{p}_name"] != f"Player {p[1]}":
            
            net_c, p_c, f_c = get_net_coins(p)
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
            for foul in penalties.keys(): entry[foul] = st.session_state[f"{p}_{foul}"]
                
            st.session_state.match_log.append(entry)
            players_saved += 1
            
    if players_saved > 0:
        st.session_state.match_id += 1
        reset_all_counters()
        st.toast(f"✅ Match saved successfully for {players_saved} players!", icon="📝")
    else:
        st.toast("⚠️ No points scored yet. Tap some counters before saving.", icon="🛑")
    
    st.rerun()

# --- GOOGLE SHEETS EXPORT DASHBOARD ---
if st.session_state.match_log:
    with st.expander("📂 View Session Log & Export Data", expanded=False):
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
