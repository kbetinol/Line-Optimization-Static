
import streamlit as st
import pandas as pd
from itertools import combinations
from collections import defaultdict
import numpy as np
# Load data
line_data = pd.read_csv('CleanedLineData.csv')
individual_data = pd.read_csv('CleanedForwardsData.csv')

# Prepare data (reuse the calculate_line_score and pair metrics logic)
pair_metrics = defaultdict(lambda: [0, 0, 0, 0, 0, 0])  # [Possession %, Puck Time in OZ %, Shots for %, xG %, Game Score, count]

for _, row in line_data.iterrows():
    players = row["Line"].split(" / ")
    metrics = row[["Possession %", "Puck time in OZ %", "Shot Attempts %", "xG %", "Game Score"]]
    metrics = metrics.replace("_", np.nan).astype(float).fillna(0).values
    for pair in combinations(players, 2):
        pair_metrics[tuple(sorted(pair))][:5] = [
            sum(x) for x in zip(pair_metrics[tuple(sorted(pair))][:5], metrics)
        ]
        pair_metrics[tuple(sorted(pair))][5] += 1  # Count appearances

# Calculate average pair metrics
avg_pair_metrics = {
    pair: [m / values[5] for m in values[:5]]  # Divide total metrics by count
    for pair, values in pair_metrics.items()
}

# Prepare individual metrics
individual_metrics = individual_data.set_index("Name")[
    ["Possession %", "Puck Time in OZ %", "Shots for %", "xG %", "Game Score"]
].to_dict(orient="index")

def calculate_line_score(selected_players, pair_metrics, individual_metrics):
    line_score = 0
    pairs = list(combinations(selected_players, 2))
    for pair in pairs:
        if tuple(sorted(pair)) in pair_metrics:
            pair_score = sum(pair_metrics[tuple(sorted(pair))])
        else:
            player_a, player_b = pair
            if player_a in individual_metrics and player_b in individual_metrics:
                metric_a = individual_metrics[player_a]
                metric_b = individual_metrics[player_b]
                pair_score = sum(
                    (metric_a[metric] + metric_b[metric]) / 2
                    for metric in metric_a.keys()
                )
            else:
                pair_score = 0
        line_score += pair_score
    return line_score

# Streamlit UI
st.title("UBC Whky Line Experimentation Platform")

players = individual_data["Name"].tolist()
selected_players = st.multiselect("Select 3 Players for the Line", players)

if len(selected_players) == 3:
    score = calculate_line_score(selected_players, avg_pair_metrics, individual_metrics)
    st.write(f"Line Score for {selected_players}: {score}")

if "saved_lines" not in st.session_state:
    st.session_state["saved_lines"] = []

if st.button("Save Line"):
    if len(selected_players) == 3:
        st.session_state["saved_lines"].append((selected_players, score))
        st.success("Line saved!")

# Display saved lines
st.write("Saved Lines:")
for i, (line, score) in enumerate(st.session_state["saved_lines"], start=1):
    st.write(f"Line {i}: {line} - Score: {score}")
