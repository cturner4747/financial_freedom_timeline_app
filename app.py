
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

mortgage_principal = home_loan - heloc_used
mortgage_payment = calc_pmt(mortgage_rate/100/12, mortgage_years*12, mortgage_principal)
heloc_annual_payment = (heloc_used / heloc_term) if heloc_used > 0 else 0

# --- INCOME INPUTS ---
st.header("👨‍👩‍👧 Income Sources")
col1, col2 = st.columns(2)
with col1:
    cody_primary = st.number_input("Cody's Primary Income (annual)", value=90000)
    cody_secondary = st.number_input("Cody's Secondary Income (annual)", value=5000)
    raise_cody_primary = st.checkbox("Apply 3% Annual Raise to Cody's Primary Income", value=True)
    raise_cody_secondary = st.checkbox("Apply 3% Annual Raise to Cody's Secondary Income", value=False)
with col2:
    lauren_primary = st.number_input("Lauren's Primary Income (annual)", value=75000)
    lauren_secondary = st.number_input("Lauren's Secondary Income (annual)", value=0)
    raise_lauren_primary = st.checkbox("Apply 3% Annual Raise to Lauren's Primary Income", value=True)
    raise_lauren_secondary = st.checkbox("Apply 3% Annual Raise to Lauren's Secondary Income", value=False)

# --- RENTAL INPUTS ---
st.header("🏠 Rental Properties (Net Monthly Rent - Mortgage)")
col1, col2 = st.columns(2)
with col1:
    rental1_start = st.number_input("Rental #1: Start Year", value=1)
    rental1_monthly_net = st.number_input("Rental #1: Net Monthly Cash Flow", value=700)
    rental1_vacancy_loss = st.slider("Rental #1: Vacancy + Maintenance Loss (%)", 0, 50, 10)
    rental1_appreciation = st.slider("Rental #1: Annual Appreciation (%)", 0.0, 10.0, 3.0)
with col2:
    rental2_on = st.checkbox("Add Rental #2?")
    rental2_start = st.number_input("Rental #2: Start Year", value=5) if rental2_on else 99
    rental2_monthly_net = st.number_input("Rental #2: Net Monthly Cash Flow", value=700) if rental2_on else 0
    rental2_vacancy_loss = st.slider("Rental #2: Vacancy + Maintenance Loss (%)", 0, 50, 10) if rental2_on else 0
    rental2_appreciation = st.slider("Rental #2: Annual Appreciation (%)", 0.0, 10.0, 3.0) if rental2_on else 0.0

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
    dynamic_contrib = st.checkbox("Enable Dynamic Retirement Growth?", value=False)
    contrib_growth_rate = st.slider("Annual Retirement Contribution Increase (%)", 0.0, 10.0, 2.0) if dynamic_contrib else 0
with col2:
    retirement_growth = st.slider("Annual Growth Rate (%)", 0.0, 10.0, 7.0)

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

# --- FRUGAL MODE TOGGLES ---
st.header("💡 Frugal Mode Settings")
frugal_mode_years = st.multiselect("Select Years to Activate Frugal Mode", options=list(range(1, 21)))
cut_discretionary = st.checkbox("Reduce Discretionary Spending by 15%")
cut_secondary = st.checkbox("Suspend Secondary Incomes")
suspend_retirement = st.checkbox("Suspend Retirement Contributions")

# --- YEARS & INITIAL SETUP ---
years = list(range(1, 21))
df = pd.DataFrame({"Year": years})

mortgage = mortgage_principal
student_loan_bal = student_loan_balance
retirement = retirement_start
savings = 0
home_equity = down_payment
rental1_equity = 0
rental2_equity = 0

networths, cash_flows, cumulative_savings = [], [], []
retirement_balances, home_equities, rental_equities = [], [], []
risk_flags, advice_list = [], []

for y in years:
    # --- Income ---
    inc1 = cody_primary * ((1.03) ** (y - 1) if raise_cody_primary else 1)
    inc2 = cody_secondary * ((1.03) ** (y - 1) if raise_cody_secondary else 1)
    inc3 = lauren_primary * ((1.03) ** (y - 1) if raise_lauren_primary else 1)
    inc4 = lauren_secondary * ((1.03) ** (y - 1) if raise_lauren_secondary else 1)
    income = inc1 + inc3 + (0 if cut_secondary and y in frugal_mode_years else inc2 + inc4) + (push_income_boost if y <= 2 else 0)
    if income_drop:
        income *= 0.9

    # --- Rental Income ---
    rental_income = 0
    if y >= rental1_start:
        rental_income += rental1_monthly_net * 12 * (1 - rental1_vacancy_loss / 100)
        rental1_equity += (rental1_monthly_net * 12) * 0.3
    if rental2_on and y >= rental2_start:
        rental_income += rental2_monthly_net * 12 * (1 - rental2_vacancy_loss / 100)
        rental2_equity += (rental2_monthly_net * 12) * 0.3

    # --- Expenses ---
    exp_infl = expense_inflation + (5 if stress_test else 0)
    adjusted_exp = base_expenses * ((1 + exp_infl/100) ** (y - 1))
    if y in frugal_mode_years and cut_discretionary:
        adjusted_exp *= 0.85

    # --- Loan & Debt Payments ---
    mortg = mortgage_payment * 12 if y >= mortgage_start_year else 0
    heloc_pay = heloc_annual_payment if (heloc_used > 0 and y >= heloc_start_year and y < heloc_start_year+heloc_term) else 0
    sl_pay = student_loan_payment * 12 if (not forgiveness_toggle or y < forgiveness_year) and student_loan_bal > 0 else 0
    student_loan_interest = student_loan_bal * student_loan_rate / 100 if student_loan_bal > 0 else 0
    student_loan_bal = max(0, student_loan_bal + student_loan_interest - sl_pay)
    if forgiveness_toggle and y == forgiveness_year:
        student_loan_bal = 0

    # --- Retirement ---
    rc = 0 if (y in frugal_mode_years and suspend_retirement) else retirement_contribution
    retirement += rc
    if dynamic_contrib:
        retirement_contribution *= (1 + contrib_growth_rate / 100)
    retirement = retirement * (1 + retirement_growth / 100)

    # --- Equity Growth ---
    home_equity = min(home_value, home_equity + mortg)
    rental1_equity *= (1 + rental1_appreciation / 100)
    rental2_equity *= (1 + rental2_appreciation / 100) if rental2_on else 0

    # --- Net Cash Flow ---
    net = income + rental_income - adjusted_exp - mortg - heloc_pay - sl_pay
    savings += max(net, 0)
    net_worth = savings + home_equity + rental1_equity + rental2_equity + retirement - student_loan_bal

    # --- Risk & Advice ---
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

    cash_flows.append(net)
    cumulative_savings.append(savings)
    retirement_balances.append(retirement)
    home_equities.append(home_equity)
    rental_equities.append(rental1_equity + rental2_equity)
    networths.append(net_worth)
    risk_flags.append(risk)
    advice_list.append(advice)

# --- DataFrame & Output ---
df["Net Cash Flow"] = cash_flows
df["Cumulative Savings"] = cumulative_savings
df["Retirement Balance"] = retirement_balances
df["Home Equity"] = home_equities
df["Rental Equity"] = rental_equities
df["Net Worth"] = networths
df["Risk"] = risk_flags
df["Advice"] = advice_list

st.line_chart(df.set_index("Year")[["Net Cash Flow", "Net Worth"]])
st.dataframe(df.style.applymap(lambda v: 'background-color: #fdd' if v == "🔴" else ('background-color: #ffd' if v == "🟡" else ''), subset=['Risk']))

# --- STRATEGIC SUMMARY ---
st.subheader("📘 Assumptions & Strategic Summary")

st.write(f"🏠 Home Loan: ${home_loan:,.0f} at {mortgage_rate:.2f}%, Term: {mortgage_years} yrs, Start: Year {mortgage_start_year}")
st.write(f"🏦 HELOC Used: ${heloc_used:,.0f}, Rate: {heloc_rate:.2f}%, Term: {heloc_term} yrs, Starts: Year {heloc_start_year}")
st.write(f"📉 Mortgage Amount (excluding HELOC): ${mortgage_principal:,.0f}")
st.write(f"👩‍💼 Cody’s Income: ${cody_primary:,.0f} + ${cody_secondary:,.0f}; Lauren’s Income: ${lauren_primary:,.0f} + ${lauren_secondary:,.0f}")
st.write(f"💰 Income Raises: Cody [Primary: {raise_cody_primary}, Secondary: {raise_cody_secondary}], Lauren [Primary: {raise_lauren_primary}, Secondary: {raise_lauren_secondary}]")
st.write(f"🏠 Rental #1 starts Year {rental1_start}, Net ${rental1_monthly_net}/mo, {rental1_vacancy_loss}% loss, {rental1_appreciation}% appreciation")
if rental2_on:
    st.write(f"🏠 Rental #2 starts Year {rental2_start}, Net ${rental2_monthly_net}/mo, {rental2_vacancy_loss}% loss, {rental2_appreciation}% appreciation")
st.write(f"📆 Frugal Mode: {frugal_mode_years}, Reduce Discretionary: {cut_discretionary}, Cut Secondary: {cut_secondary}, Suspend Retirement: {suspend_retirement}")
st.write(f"🎓 Student Loan: ${student_loan_balance:,.0f} at {student_loan_rate}%, ${student_loan_payment}/mo, Forgiveness: {forgiveness_toggle} (Year {forgiveness_year})")
st.write(f"📈 Retirement Start: ${retirement_start:,.0f}, Contrib: ${retirement_contribution:,.0f}/yr, Growth: {retirement_growth}%, Dynamic Growth: {dynamic_contrib} ({contrib_growth_rate}%)")
st.write(f"🛑 Emergency Fund Goal: ${emergency_fund:,.0f}, Income Drop: {income_drop}, Push-Hard Mode: {push_hard}")




