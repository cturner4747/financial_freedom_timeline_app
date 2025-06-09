import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Financial Freedom Timeline Planner", layout="wide")

st.title("📈 Financial Freedom Timeline Planner")

# --- Income Inputs ---
st.header("Income Sources")
col1, col2 = st.columns(2)
with col1:
    cody_primary = st.number_input("Cody’s Primary Income (Annual)", value=90000)
    cody_secondary = st.number_input("Cody’s Secondary Income (Annual)", value=5000)
with col2:
    lauren_primary = st.number_input("Lauren’s Primary Income (Annual)", value=75000)
    lauren_secondary = st.number_input("Lauren’s Secondary Income (Annual)", value=0)

# --- Rental Property Inputs ---
st.header("🏠 Rental Properties")
rental1_monthly = st.number_input("Rental 1: Monthly Rent", value=2200)
rental1_mortgage = st.number_input("Rental 1: Monthly Mortgage", value=1500)
rental1_start = st.number_input("Rental 1 Start Year", value=1)

rental2_monthly = st.number_input("Rental 2: Monthly Rent", value=2200)
rental2_mortgage = st.number_input("Rental 2: Monthly Mortgage", value=1600)
rental2_start = st.number_input("Rental 2 Start Year", value=5)

# --- Expense Assumptions ---
st.header("📉 Expenses and Assumptions")
base_expenses = st.number_input("Annual Living Expenses (Starting)", value=75000)
expense_inflation = st.slider("Annual Expense Inflation Rate (%)", min_value=0.0, max_value=10.0, value=3.0)

# --- Loan Inputs ---
st.header("🏡 Home Loan and HELOC")
home_loan_amount = st.number_input("New Home Loan Amount", value=510000)
heloc_amount = st.number_input("HELOC Amount (if used)", value=0)
heloc_start = st.number_input("HELOC Repayment Start Year", value=2)
heloc_term_years = st.number_input("HELOC Term (Years)", value=5)

# --- Push-Hard Toggle ---
st.header("💪 Effort Mode")
push_hard = st.toggle("Push-Hard Upfront Mode")
push_income_boost = 10000 if push_hard else 0

# --- Simulation ---
st.header("📊 20-Year Financial Projection")
years = list(range(1, 21))
data = []

for year in years:
    income = (
        cody_primary + lauren_primary +
        cody_secondary + lauren_secondary +
        push_income_boost * (1 if year <= 2 else 0)
    )

    rental_income = 0
    if year >= rental1_start:
        rental_income += (rental1_monthly - rental1_mortgage) * 12
    if year >= rental2_start:
        rental_income += (rental2_monthly - rental2_mortgage) * 12
    income += rental_income

    expenses = base_expenses * ((1 + expense_inflation / 100) ** (year - 1))
    heloc_payment = (heloc_amount / heloc_term_years) if year >= heloc_start and heloc_amount > 0 else 0
    net_cash_flow = income - expenses - heloc_payment
    data.append(net_cash_flow)

df = pd.DataFrame({
    "Year": years,
    "Net Cash Flow": data
})

st.line_chart(df.set_index("Year"))

# --- Assumption Summary ---
st.subheader("📌 Assumptions Summary")
st.write(f"Base Expenses: ${base_expenses:,.0f}, Inflation: {expense_inflation:.1f}%")
st.write(f"Push-Hard Mode: {'Enabled' if push_hard else 'Disabled'}, Boost: ${push_income_boost}/year (Years 1–2)")
st.write(f"Rental Start Years: R1 = Year {rental1_start}, R2 = Year {rental2_start}")
