import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Financial Freedom Timeline Planner", layout="wide")
st.title("📈 Financial Freedom Timeline Planner")

# --- Mortgage Payment Helper ---
def calc_pmt(rate, nper, pv):
    if rate == 0:
        return pv / nper
    return (pv * rate) / (1 - (1 + rate) ** -nper)

# All prior code remains unchanged until:
# --- YEARS & SIMULATION SETUP ---
years = list(range(1, 21))

# --- FRUGAL MODE STRATEGY ---
# (Frugal mode UI and toggles remain unchanged)

# --- DYNAMIC RETIREMENT CONTRIBUTION GROWTH ---
# (Dynamic retirement toggles remain unchanged)

# --- SIMULATION SETUP ---


# (Simulation loop remains unchanged except using mortgage_principal instead of home_loan)

# --- ASSUMPTIONS & STRATEGIC SUMMARY ---
# Add this to the summary block
st.write(f"Home Loan: ${mortgage_principal:,.0f} at {mortgage_rate:.2f}%, Term: {mortgage_years} yrs, Start Year: {mortgage_start_year}")
st.write(f"Mortgage Amount (excluding HELOC): ${mortgage_principal:,.0f}")
st.write(f"Mortgage Amount (excluding HELOC): ${mortgage_principal:,.0f}")
heloc_annual_payment = (heloc_used / heloc_term) if heloc_used > 0 else 0



