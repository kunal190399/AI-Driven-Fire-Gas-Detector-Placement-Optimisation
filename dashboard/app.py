"""Streamlit explorer for the synthetic detector placement prototype."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import streamlit as st
import matplotlib.pyplot as plt
from firegas.facility import Facility
from firegas.optimisation import optimise, choose_compromise
from firegas.dispersion import all_concentrations, grid_for
from firegas.reporting import _draw_facility
from firegas.coverage import evaluate_layout

st.set_page_config(page_title="Fire & Gas Placement Lab", layout="wide")
st.title("Fire & Gas Detector Placement Lab")
st.caption("Synthetic research prototype — not for operational safety design.")
facility_path = Path(__file__).resolve().parents[1] / "data/facilities/process_unit.json"
facility = Facility.from_json(facility_path)
with st.sidebar:
    st.header("Optimisation settings")
    population = st.slider("Population size", 8, 80, 32, step=4)
    generations = st.slider("Generations", 2, 60, 20, step=2)
    max_detectors = st.slider("Maximum detectors", 1, 12, 6)
    threshold = st.slider("Response threshold", 0.05, 0.8, 0.25, step=0.05)
    run = st.button("Run optimisation", type="primary")
if "front" not in st.session_state:
    st.session_state.front = optimise(facility, population, generations, max_detectors, threshold)
if run:
    st.session_state.front = optimise(facility, population, generations, max_detectors, threshold)
front = st.session_state.front
best = choose_compromise(front)
cost, mean_risk, worst_risk, masks = evaluate_layout(facility, best.genes, threshold)
a, b, c = st.columns(3)
a.metric("Detectors in compromise", len(best.genes))
b.metric("Mean uncovered risk", f"{mean_risk:.1%}")
c.metric("Worst-scenario uncovered risk", f"{worst_risk:.1%}")
left, right = st.columns(2)
with left:
    st.subheader("Synthetic facility and selected locations")
    fig, ax = plt.subplots(figsize=(7, 4))
    _draw_facility(ax, facility)
    for i, (x, y) in enumerate(facility.candidate_points):
        ax.scatter(x, y, c="royalblue", s=18, alpha=.45)
        if i in best.genes: ax.scatter(x, y, c="crimson", marker="^", s=100)
    st.pyplot(fig); plt.close(fig)
with right:
    st.subheader("Scenario 1 relative concentration")
    xx, yy = grid_for(facility); field = all_concentrations(facility)[0]
    fig, ax = plt.subplots(figsize=(7, 4))
    contour = ax.contourf(xx, yy, field, levels=18, cmap="inferno")
    fig.colorbar(contour, ax=ax)
    _draw_facility(ax, facility)
    st.pyplot(fig); plt.close(fig)
st.subheader("Pareto trade-offs")
st.dataframe([{"detector_count":len(cand.genes), "cost":cand.objectives[0],
               "mean_uncovered_risk":cand.objectives[1],
               "worst_uncovered_risk":cand.objectives[2],
               "candidate_indices":cand.genes} for cand in front], use_container_width=True)
st.warning("Model outputs are dimensionless illustrative estimates. Validate any future model against domain experts, recognised engineering methods and site data.")
