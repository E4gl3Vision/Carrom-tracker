import streamlit as st
import pandas as pd
import datetime

st.set_page_config(page_title="Carrom Live Tracker", layout="wide")

st.title("🎯 Club Carrom Rating Tracker")
st.caption("Tap counts live at the board. Perfect for mobile & tablet browsers.")

# Game configurations
multipliers = {
    'Near Base': 0.7, 'Far Base': 0.9, 'Close Free Inch': 0.9, 'Close Crowd Inch': 1.0,
    'Medium Free Inch': 0.95, 'Medium Crowd Inch': 1.15, 'Far Free Inch': 1.15, 'Far Crowd Inch': 1.3,
    'Single Rebound': 1.2, 'Double Rebound': 1.5, 'Red Cover': 1.5, 'Red Attempt': 0.5,
    'Return Shot': 1.1, '3-Shot Streak': 0.7, '4-Shot Streak': 0.8, '5+ Shot Streak': 1.0
}
penalties = {
    'Opponent Coin Only': 0.7, 'Opponent Coin + Yours': 0.4, 'Pocketed Striker': 0.75, 'Double Fine': 0.65
}

if 'match_log' not in st.session_state:
    st.session_state.match_log = []

# Sidebar configurations
st.sidebar.header("🕹️ Match Setup")
player_name = st.sidebar.text_input("Player Name", value="Raktim")
match_won = st.sidebar.checkbox("Match Won? (+1.0 Bonus)")

if st.sidebar.button("🧹 Reset Current Counters"):
    for key in list(multipliers.keys()) + list(penalties.keys()):
        st.session_state[f"counter_{key}"] = 0
    st.rerun()

col_pos, col_neg = st.columns(2)

with col_pos:
    st.subheader("➕ Successful Pots")
    grid_cols = st.columns(2)
    for idx, (action, weight) in enumerate(multipliers.items()):
        c_col = grid_cols[idx % 2]
        if f"counter_{action}" not in st.session_state:
            st.session_state[f"counter_{action}"] = 0
            
        # Large UI layout designed for tablet finger tapping
        st.markdown(f"**{action}** ({weight}x)")
        b_cols = st.columns([1, 2, 1])
        if b_cols[0].button("➖", key=f"sub_{action}"):
            if st.session_state[f"counter_{action}"] > 0:
                st.session_state[f"counter_{action}"] -= 1
                st.rerun()
        b_cols[1].markdown(f"<h3 style='text-align: center; margin:0;'>{st.session_state[f'counter_{action}']}</h3>", unsafe_allow_html=True)
        if b_cols[2].button("➕", key=f"add_{action}"):
            st.session_state[f"counter_{action}"] += 1
            st.rerun()
        st.write("---")

with col_neg:
    st.subheader("⚠️ Fouls & Penalties")
    grid_cols_neg = st.columns(2)
    for idx, (foul, penalty) in enumerate(penalties.items()):
        c_col = grid_cols_neg[idx % 2]
        if f"counter_{foul}" not in st.session_state:
            st.session_state[f"counter_{foul}"] = 0
            
        st.markdown(f"**{foul}** (-{penalty}x)")
        b_cols = st.columns([1, 2, 1])
        if b_cols[0].button("➖", key=f"sub_{foul}"):
            if st.session_state[f"counter_{foul}"] > 0:
                st.session_state[f"counter_{foul}"] -= 1
                st.rerun()
        b_cols[1].markdown(f"<h3 style='text-align: center; margin:0; color: #d9534f;'>{st.session_state[f'counter_{foul}']}</h3>", unsafe_allow_html=True)
        if b_cols[2].button("➕", key=f"add_{foul}"):
            st.session_state[f"counter_{foul}"] += 1
            st.rerun()
        st.write("---")

# Rating Math Logic
raw_positive = sum(st.session_state[f"counter_{action}"] * w for action, w in multipliers.items()) + (1.0 if match_won else 0.0)
capped_positive = min(10.0, raw_positive)
total_penalties = sum(st.session_state[f"counter_{foul}"] * p for foul, p in penalties.items())
final_live_rating = capped_positive - total_penalties

st.write("## 🎛️ Live Metrics Dashboard")
m_cols = st.columns(4)
m_cols[0].metric("Raw Value", f"{raw_positive:.2f}")
m_cols[1].metric("Capped Positive", f"{capped_positive:.2f}")
m_cols[2].metric("Penalties", f"-{total_penalties:.2f}")
m_cols[3].metric("🎯 LIVE RATING", f"{final_live_rating:.2f}")

if st.button("💾 Save Match Entry", type="primary", use_container_width=True):
    entry = {"Timestamp": datetime.datetime.now().strftime("%H:%M:%S"), "Player": player_name, "Won": "Yes" if match_won else "No", "Rating": round(final_live_rating, 2)}
    for action in multipliers.keys(): entry[action] = st.session_state[f"counter_{action}"]
    for foul in penalties.keys(): entry[foul] = st.session_state[f"counter_{foul}"]
    st.session_state.match_log.append(entry)
    st.success(f"Saved entry for {player_name} (Rating: {final_live_rating:.2f})")

if st.session_state.match_log:
    st.write("### 📜 Today's Match Log")
    log_df = pd.DataFrame(st.session_state.match_log)
    st.dataframe(log_df, use_container_width=True)
    st.download_button(label="📥 Download Session CSV", data=log_df.to_csv(index=False).encode('utf-8'), file_name="carrom_session_output.csv", mime='text/csv')
