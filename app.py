import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Financial Freedom Timeline Planner", layout="wide")
st.title("📈 Financial Freedom Timeline Planner")

# --- Income Inputs ---
st.header("Income Sources")
col1, col2 = st.columns(2)
with col1:
    cody_primary   = st.number_input("Cody’s Primary Income (Annual)", value=90000)
    cody_secondary = st.number_input("Cody’s Secondary Income (Annual)", value=5000)
with col2:
    lauren_primary   = st.number_input("Lauren’s Primary Income (Annual)", value=75000)
    lauren_secondary = st.number_input("Lauren’s Secondary Income (Annual)", value=0)

# --- Rental Property Inputs ---
st.header("🏠 Rental Properties")
r1_rent     = st.number_input("Rental 1: Monthly Rent", value=2200)
r1_mortgage = st.number_input("Rental 1: Monthly Mortgage", value=1500)
r1_start    = st.number_input("Rental 1 Start Year", value=1)

r2_rent     = st.number_input("Rental 2: Monthly Rent", value=2200)
r2_mortgage = st.number_input("Rental 2: Monthly Mortgage", value=1600)
r2_start    = st.number_input("Rental 2 Start Year", value=5)

# --- Expense Assumptions ---
st.header("📉 Expenses and Assumptions")
base_expenses     = st.number_input("Annual Living Expenses (Starting)", value=75000)
expense_inflation = st.slider("Annual Expense Inflation Rate (%)", 0.0, 10.0, 3.0)

# --- Home Loan / HELOC Inputs ---
st.header("🏡 Home Loan & HELOC")
home_loan_amount = st.number_input("New Home Loan Amount", value=510000)
heloc_amount     = st.number_input("HELOC Amount (if used)", value=0)
heloc_start      = st.number_input("HELOC Repayment Start Year", value=2)
heloc_term       = st.number_input("HELOC Term (Years)", value=5)

# --- Effort Mode Toggle ---
st.header("💪 Effort Mode")
push_hard        = st.toggle("Push-Hard Upfront Mode")  # or st.checkbox if preferred
push_income_boost = 10000 if push_hard else 0

# --- Retirement Account Simulation ---
st.header("💼 Retirement Accounts")
cody_ret_initial   = st.number_input("Cody’s Initial Retirement Balance",   value=50000)
lauren_ret_initial = st.number_input("Lauren’s Initial Retirement Balance", value=50000)
retirement_growth  = st.slider("Annual Retirement Growth Rate (%)", 0.0, 15.0, 7.0)

# --- Run 20-Year Simulation ---
st.header("📊 20-Year Projection Data")
years = list(range(1, 21))
net_cash_flows = []
cumulative_savings = []
ret_balances = []
flags = []

# initialize retirement balance
ret_balance = cody_ret_initial + lauren_ret_initial

for year in years:
    # income
    income = (
        cody_primary + lauren_primary +
        cody_secondary + lauren_secondary +
        push_income_boost * (1 if year <= 2 else 0)
    )
    # rental cash flow
    rental_cf = 0
    if year >= r1_start:
        rental_cf += (r1_rent - r1_mortgage) * 12
    if year >= r2_start:
        rental_cf += (r2_rent - r2_mortgage) * 12
    income += rental_cf

    # expenses & HELoC payment
    expenses = base_expenses * ((1 + expense_inflation / 100) ** (year - 1))
    heloc_payment = (heloc_amount / heloc_term) if year >= heloc_start and heloc_amount > 0 else 0

    # net cash flow
    net_cf = income - expenses - heloc_payment
    net_cash_flows.append(net_cf)

    # cumulative savings
    cum_sav = net_cf if year == 1 else cumulative_savings[-1] + net_cf
    cumulative_savings.append(cum_sav)

    # retirement growth
    ret_balance = ret_balance * (1 + retirement_growth/100)
    ret_balances.append(ret_balance)

    # flag: red if negative; yellow if small positive; green otherwise
    if net_cf < 0:
        flags.append("🔴")
    elif net_cf < base_expenses * 0.1:
        flags.append("🟡")
    else:
        flags.append("🟢")

# assemble DataFrame
df = pd.DataFrame({
    "Year": years,
    "Net Cash Flow": net_cash_flows,
    "Cumulative Savings": cumulative_savings,
    "Retirement Balance": ret_balances,
})
df["Net Worth"] = df["Cumulative Savings"] + df["Retirement Balance"]
df["Flag"] = flags

# --- Charts & Tables ---
st.subheader("Net Cash Flow, Savings & Net Worth Over Time")
st.line_chart(df.set_index("Year")[["Net Cash Flow", "Cumulative Savings", "Net Worth"]])

st.subheader("🚦 Cash-Flow Flags by Year")
st.table(df[["Year", "Net Cash Flow", "Flag"]])

# --- Assumption Recap ---
st.subheader("📌 Assumptions Summary")
st.write(f"- Base Expenses: ${base_expenses:,.0f}; Inflation: {expense_inflation:.1f}%/yr")
st.write(f"- Push-Hard Mode: {'Enabled' if push_hard else 'Disabled'} (Boost of ${push_income_boost}/yr for Years 1–2)")
st.write(f"- Rental Starts: R1 in Year {r1_start}, R2 in Year {r2_start}")
st.write(f"- Heloc: ${heloc_amount:,.0f} over {heloc_term} yrs, payments begin Year {heloc_start}")
st.write(f"- Retirement Growth Rate: {retirement_growth:.1f}% on initial combined balance of ${cody_ret_initial + lauren_ret_initial:,.0f}")

# --- Strategy Recommendations ---
st.subheader("🔍 Strategy Recommendations")
positive_years = df.loc[df["Net Cash Flow"] > 0, "Year"]
neg_years = df.loc[df["Net Cash Flow"] < 0, "Year"].tolist()

if not positive_years.empty:
    first_pos = int(positive_years.iloc[0])
    st.write(f"- 🟢 Your net cash flow first turns positive in **Year {first_pos}**. "
             "Consider that milestone a potential window to acquire another rental property or boost investments.")
else:
    st.write("- ⚠️ Your cash flow remains negative through Year 20—consider tightening expenses or reevaluating financing.")

if neg_years:
    st.write(f"- 🔴 Years with negative cash flow: {neg_years}. "
             "During these periods, prioritize expense control and avoid new leverage.")
