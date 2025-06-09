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

# --- Retirement/IRA ---
st.header("💼 Retirement Investments")
retirement_start = st.number_input("Current Retirement Balance", value=80000)
retirement_contribution = st.number_input("Annual Contributions", value=12000)
retirement_growth = st.slider("Annual Growth Rate (%)", 0.0, 10.0, 7.0)

# --- Push-Hard Toggle ---
st.header("💪 Effort Mode")
push_hard = st.toggle("Push-Hard Upfront Mode")
push_income_boost = 10000 if push_hard else 0

# --- Simulation ---
st.header("📊 20-Year Financial Projection")
years = list(range(1, 21))
cash_flow = []
cumulative_savings = []
retirement_balance = []
home_equity = []
rental_equity = []
net_worth = []
flags = []
advice = []

retirement = retirement_start
savings = 0
home_value = home_loan_amount
home_loan = home_loan_amount

for year in years:
    # --- Income Calculation ---
    income = (
        cody_primary + lauren_primary +
        cody_secondary + lauren_secondary +
        push_income_boost * (1 if year <= 2 else 0)
    )

    # --- Rental Income ---
    rental_net = 0
    rental_eq = 0
    if year >= rental1_start:
        rental_net += (rental1_monthly - rental1_mortgage) * 12
        rental_eq += rental1_mortgage * 12 * (year - rental1_start + 1)
    if year >= rental2_start:
        rental_net += (rental2_monthly - rental2_mortgage) * 12
        rental_eq += rental2_mortgage * 12 * (year - rental2_start + 1)
    income += rental_net

    # --- Expense Calculation ---
    expenses = base_expenses * ((1 + expense_inflation / 100) ** (year - 1))
    heloc_payment = (heloc_amount / heloc_term_years) if year >= heloc_start and heloc_amount > 0 else 0
    net = income - expenses - heloc_payment

    # --- Retirement & Savings ---
    retirement = retirement * (1 + retirement_growth / 100) + retirement_contribution
    savings += max(net, 0)

    # --- Equity & Net Worth ---
    home_eq = (home_loan_amount / 30) * 12 * year
    networth = savings + home_eq + rental_eq + retirement

    # --- Risk Flagging ---
    if net < 0:
        flag = "🔴"
    elif net < 10000:
        flag = "🟡"
    else:
        flag = "🟢"

    # --- Strategy Advice ---
    suggest = ""
    if net > 15000 and year >= 5:
        suggest = "📌 Consider adding rental property"
    elif net < 0:
        suggest = "⚠️ Review expenses or income"
    elif year == 10 and retirement < 250000:
        suggest = "💡 Consider increasing retirement savings"
    else:
        suggest = ""

    # --- Append Data ---
    cash_flow.append(net)
    cumulative_savings.append(savings)
    retirement_balance.append(retirement)
    home_equity.append(home_eq)
    rental_equity.append(rental_eq)
    net_worth.append(networth)
    flags.append(flag)
    advice.append(suggest)

# --- DataFrame & Display ---
df = pd.DataFrame({
    "Year": years,
    "Net Cash Flow": cash_flow,
    "Cumulative Savings": cumulative_savings,
    "Retirement Balance": retirement_balance,
    "Home Equity": home_equity,
    "Rental Equity": rental_equity,
    "Net Worth": net_worth,
    "Risk": flags,
    "Advice": advice
})

st.line_chart(df.set_index("Year")[["Net Cash Flow", "Net Worth"]])
st.dataframe(df)

# --- Summary ---
st.subheader("📌 Key Assumptions Summary")
st.write(f"Expense Inflation: {expense_inflation:.1f}%, HELOC: ${heloc_amount} over {heloc_term_years} years")
st.write(f"Push-Hard Mode: {'Enabled' if push_hard else 'Disabled'}, Boost: ${push_income_boost}/yr")
st.write(f"Retirement Growth: {retirement_growth:.1f}%, Annual Contribution: ${retirement_contribution}")

