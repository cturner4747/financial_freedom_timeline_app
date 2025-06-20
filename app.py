import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Financial Freedom Timeline Planner", layout="wide")

st.title("📈 Financial Freedom Timeline Planner")

def calc_pmt(rate, nper, pv):
    if rate == 0:
        return pv / nper
    return (pv * rate) / (1 - (1 + rate) ** -nper)

# --- HOME & LOAN INPUTS ---
st.header("🏡 Home & Loan Details")
col1, col2, col3 = st.columns(3)
with col1:
    home_value = st.number_input("Home Value", value=789560)
    home_loan = st.number_input("Home Loan Amount", value=510000)
    mortgage_rate = st.number_input("Mortgage Interest Rate (%)", value=6.5)
with col2:
    down_payment = st.number_input("Down Payment", value=100000)
    mortgage_years = st.number_input("Mortgage Term (years)", value=30)
    mortgage_start_year = st.number_input("Mortgage Start Year", value=1)
with col3:
    heloc_used = st.number_input("HELOC Amount Used (optional)", value=0)
    heloc_rate = st.number_input("HELOC Interest Rate (%)", value=8.0)
    heloc_term = st.number_input("HELOC Term (years)", value=5)
    heloc_start_year = st.number_input("HELOC Repayment Start Year", value=2)

# --- INCOME INPUTS ---
st.header("👨‍👩‍👧 Income Sources")
col1, col2 = st.columns(2)
with col1:
    cody_primary = st.number_input("Cody's Primary Income (annual)", value=90000)
    cody_primary_raise = st.slider("Cody Primary Raise %", 0.0, 10.0, 2.0)
    cody_secondary = st.number_input("Cody's Secondary Income (annual)", value=5000)
    cody_secondary_raise = st.slider("Cody Secondary Raise %", 0.0, 10.0, 0.0)
with col2:
    lauren_primary = st.number_input("Lauren's Primary Income (annual)", value=75000)
    lauren_primary_raise = st.slider("Lauren Primary Raise %", 0.0, 10.0, 2.0)
    lauren_secondary = st.number_input("Lauren's Secondary Income (annual)", value=0)
    lauren_secondary_raise = st.slider("Lauren Secondary Raise %", 0.0, 10.0, 0.0)

# --- RENTAL INPUTS ---
st.header("🏠 Rental Properties (Net Monthly Rent - Mortgage)")
col1, col2 = st.columns(2)
with col1:
    rental1_start = st.number_input("Rental #1: Start Year", value=1)
    rental1_monthly_net = st.number_input("Rental #1: Net Monthly Cash Flow", value=700)
    rental1_appreciation = st.slider("Rental #1: Annual Appreciation (%)", 0.0, 10.0, 3.0)
with col2:
    rental2_on = st.checkbox("Add Rental #2?")
    rental2_start = st.number_input("Rental #2: Start Year", value=5) if rental2_on else 99
    rental2_monthly_net = st.number_input("Rental #2: Net Monthly Cash Flow", value=700) if rental2_on else 0
    rental2_appreciation = st.slider("Rental #2: Annual Appreciation (%)", 0.0, 10.0, 3.0) if rental2_on else 0

# --- EXPENSES ---
st.header("📉 Expense Assumptions")
col1, col2 = st.columns(2)
with col1:
    base_expenses = st.number_input("Annual Living Expenses (starting)", value=75000)
    expense_inflation = st.slider("Annual Expense Inflation (%)", 0.0, 10.0, 3.0)
    stress_test = st.checkbox("Add +5% Stress-Test Inflation?")
with col2:
    emergency_fund = st.number_input("Target Emergency Fund", value=25000)
    income_drop = st.checkbox("Toggle 10% Income Drop Scenario")

# --- RETIREMENT & SAVINGS ---
st.header("💼 Retirement Investments")
col1, col2 = st.columns(2)
with col1:
    retirement_start = st.number_input("Current Retirement Balance", value=80000)
    retirement_contribution = st.number_input("Annual Contributions", value=12000)
    retirement_raise = st.slider("Retirement Contribution Raise %", 0.0, 10.0, 0.0)
with col2:
    retirement_growth = st.slider("Annual Growth Rate (%)", 0.0, 10.0, 7.0)

# --- FRUGAL MODE ---
st.header("🛑 Frugal Mode")
frugal_mode = st.checkbox("Activate Frugal Mode")
frugal_start = st.number_input("Frugal Mode Start Year", value=1) if frugal_mode else None
frugal_end = st.number_input("Frugal Mode End Year", value=2) if frugal_mode else None
frugal_cut = st.slider("Frugal Mode Expense Cut (%)", 0, 50, 15) if frugal_mode else 0
frugal_pause_ret = st.checkbox("Pause Retirement Contributions in Frugal Mode") if frugal_mode else False

# --- STUDENT LOAN ---
st.header("🎓 Student Loan")
col1, col2, col3 = st.columns(3)
with col1:
    student_loan_balance = st.number_input("Student Loan Starting Balance", value=160000)
    student_loan_rate = st.number_input("Student Loan Interest Rate (%)", value=6.8)
with col2:
    student_loan_payment = st.number_input("Monthly Payment", value=650)
    student_loan_term = st.number_input("Student Loan Payment Duration (years)", value=20)
with col3:
    forgiveness_toggle = st.checkbox("Enable Loan Forgiveness?")
    forgiveness_year = st.number_input("Forgiveness Year", value=20) if forgiveness_toggle else 99

# --- PUSH-HARD TOGGLE ---
push_hard = st.toggle("💪 Push-Hard Upfront Mode (bonus income early)", value=False)
push_income_boost = 10000 if push_hard else 0

# --- YEARS & INITIALS ---
years = list(range(1, 21))
df = pd.DataFrame({"Year": years})

# --- SIMULATION LOOP ---
mortgage_payment = calc_pmt(mortgage_rate/100/12, mortgage_years*12, home_loan)
heloc_annual_payment = (heloc_used / heloc_term) if heloc_used > 0 else 0
student_loan_bal = student_loan_balance
retirement = retirement_start
savings = 0
home_equity = down_payment
rental1_equity = 0
rental2_equity = 0
networths, cash_flows, cumulative_savings, risk_flags, advice_list = [], [], [], [], []
retirement_balances, home_equities, rental_equities = [], [], []

# --- For raises ---
cody_p, cody_s = cody_primary, cody_secondary
lauren_p, lauren_s = lauren_primary, lauren_secondary
ret_contrib = retirement_contribution

for y in years:
    # Raises applied yearly
    if y > 1:
        cody_p *= (1 + cody_primary_raise / 100)
        cody_s *= (1 + cody_secondary_raise / 100)
        lauren_p *= (1 + lauren_primary_raise / 100)
        lauren_s *= (1 + lauren_secondary_raise / 100)
        ret_contrib *= (1 + retirement_raise / 100)
    # --- Incomes ---
    income = (
        cody_p + lauren_p + cody_s + lauren_s +
        push_income_boost * (1 if y <= 2 else 0)
    )
    if income_drop:
        income *= 0.9

    # --- Rental ---
    rental_income = 0
    if y >= rental1_start:
        rental_income += rental1_monthly_net * 12
        rental1_equity += (rental1_monthly_net * 12) * 0.3
    if rental2_on and y >= rental2_start:
        rental_income += rental2_monthly_net * 12
        rental2_equity += (rental2_monthly_net * 12) * 0.3

    # --- Expenses ---
    exp_infl = expense_inflation + (5 if stress_test else 0)
    expenses = base_expenses * ((1 + exp_infl/100) ** (y-1))
    # Apply Frugal Mode if active this year
    if frugal_mode and frugal_start <= y <= frugal_end:
        expenses *= (1 - frugal_cut/100)
        if frugal_pause_ret:
            ret_contrib_this_year = 0
        else:
            ret_contrib_this_year = ret_contrib
    else:
        ret_contrib_this_year = ret_contrib

    # --- Loan & Debt ---
    mortg = mortgage_payment * 12 if y >= mortgage_start_year else 0
    heloc_pay = heloc_annual_payment if (heloc_used > 0 and y >= heloc_start_year and y < heloc_start_year+heloc_term) else 0

    # --- Student Loan Logic ---
    sl_pay = student_loan_payment * 12 if (not forgiveness_toggle or y < forgiveness_year) and student_loan_bal > 0 else 0
    student_loan_interest = student_loan_bal * student_loan_rate / 100 if student_loan_bal > 0 else 0
    student_loan_bal = max(0, student_loan_bal + student_loan_interest - sl_pay)
    if forgiveness_toggle and y == forgiveness_year:
        student_loan_bal = 0

    # --- Retirement Growth ---
    retirement = retirement * (1 + retirement_growth/100) + ret_contrib_this_year

    # --- Equity Tracking ---
    home_equity = min(home_value, home_equity + mortg)
    rental1_equity *= (1 + rental1_appreciation / 100)
    rental2_equity *= (1 + rental2_appreciation / 100) if rental2_on else 0

    # --- Cash Flow ---
    net = income + rental_income - expenses - mortg - heloc_pay - sl_pay
    savings += max(net, 0)
    net_worth = savings + home_equity + rental1_equity + rental2_equity + retirement - student_loan_bal

    # --- Risk Flags & Guidance ---
    if net < 0:
        risk = "🔴"
        advice = "⚠️ Tight year: review expenses or defer big investments"
    elif net < 10000:
        risk = "🟡"
        advice = "Consider delaying new rental or boosting income"
    else:
        risk = "🟢"
        advice = ""
    if net > 20000 and (not rental2_on or (rental2_on and y < rental2_start)):
        advice = "Good cash flow: consider new rental or extra investment"

    # --- Collect for table ---
    cash_flows.append(net)
    cumulative_savings.append(savings)
    retirement_balances.append(retirement)
    home_equities.append(home_equity)
    rental_equities.append(rental1_equity + rental2_equity)
    networths.append(net_worth)
    risk_flags.append(risk)
    advice_list.append(advice)

df["Net Cash Flow"] = cash_flows
df["Cumulative Savings"] = cumulative_savings
df["Retirement Balance"] = retirement_balances
df["Home Equity"] = home_equities
df["Rental Equity"] = rental_equities
df["Net Worth"] = networths
df["Risk"] = risk_flags
df["Advice"] = advice_list

st.line_chart(df.set_index("Year")[["Net Cash Flow", "Net Worth"]])
st.dataframe(df.style.applymap(
    lambda v: 'background-color: #fdd' if v == "🔴" else ('background-color: #ffd' if v == "🟡" else ''), subset=['Risk']
))

# --- Segment Trends Chart ---
st.subheader("💵 Trend: Savings, Retirement, Equity, and Net Worth Over Time")
trend_df = df.set_index("Year")[["Cumulative Savings", "Retirement Balance", "Home Equity", "Rental Equity", "Net Worth"]]
trend_df.columns = ["Savings", "Retirement", "Home Eq", "Rent Eq", "Net Worth"]  # Short labels for wrapping
st.line_chart(trend_df)

st.subheader("📌 Assumptions & Strategic Summary")
st.write(f"Base Expenses: ${base_expenses:,.0f}, Inflation: {expense_inflation:.1f}%{' (+5%)' if stress_test else ''}")
st.write(f"Push-Hard Mode: {'Enabled' if push_hard else 'Disabled'}, Boost: ${push_income_boost}/yr (Years 1–2)")
st.write(f"Home Loan: ${home_loan:,.0f} at {mortgage_rate:.2f}%, Term: {mortgage_years} yrs, Start Year: {mortgage_start_year}")
st.write(f"Retirement Growth: {retirement_growth:.1f}%, Annual Contribution: ${retirement_contribution:,.0f} (+{retirement_raise:.1f}%/yr)")
st.write(f"Student Loan: ${student_loan_balance:,.0f} at {student_loan_rate:.2f}% for {student_loan_term} yrs{' (forgiveness enabled)' if forgiveness_toggle else ''}")

st.success("See year-by-year risk flags and suggestions above to decide when to add rentals, pay down debt, or increase investments.")
