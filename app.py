import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Financial Freedom Timeline Planner", layout="wide")
st.title("Financial Freedom Timeline Planner — Net Worth + Modes + Retirement + 10 Properties + HELOC + Liquidations + Pharmacy Buy-In")

# -----------------------------
# Helpers
# -----------------------------
def amort_payment(principal: float, annual_rate: float, years: int) -> float:
    """Monthly payment (P&I) for fixed-rate amortizing loan."""
    r = annual_rate / 12.0
    n = years * 12
    if principal <= 0:
        return 0.0
    if r == 0:
        return principal / n
    return principal * (r * (1 + r) ** n) / ((1 + r) ** n - 1)

def mortgage_balance(principal: float, annual_rate: float, years: int, months_paid: int) -> float:
    """Remaining balance after months_paid payments, fixed-rate fully amortizing."""
    r = annual_rate / 12.0
    n = years * 12
    m = max(0, min(int(months_paid), n))
    if principal <= 0:
        return 0.0
    if r == 0:
        return principal * (1 - m / n)
    pmt = amort_payment(principal, annual_rate, years)
    bal = principal * (1 + r) ** m - pmt * (((1 + r) ** m - 1) / r)
    return max(0.0, bal)

def income_stream(base: float, growth_pct: float, year: int, start_year: int) -> float:
    if year < start_year:
        return 0.0
    t = year - start_year
    return float(base * ((1 + growth_pct / 100.0) ** t))

def grow_balance(balance: float, annual_return_pct: float) -> float:
    """Apply annual return to a balance (end-of-year style)."""
    return float(balance * (1.0 + annual_return_pct / 100.0))

def annual_amort_step(balance: float, annual_rate: float, annual_payment: float, extra_principal: float = 0.0):
    """
    One year amortization step (simple annual approximation).
    Returns: (payment_effective, interest, principal_paid, end_balance)
    """
    if balance <= 0:
        return 0.0, 0.0, 0.0, 0.0
    interest = balance * annual_rate
    scheduled_principal = max(0.0, annual_payment - interest)
    total_principal = min(balance, scheduled_principal + max(0.0, extra_principal))
    payment_effective = interest + total_principal
    end_balance = max(0.0, balance - total_principal)
    return payment_effective, interest, total_principal, end_balance

def progressive_tax(taxable_income: float, brackets):
    """
    brackets: list of tuples (rate, lower, upper_or_None)
    Example: [(0.10, 0, 24800), (0.12, 24800, 100800), ... (0.37, 768700, None)]
    Returns tax amount.
    """
    ti = max(0.0, float(taxable_income))
    tax = 0.0
    for rate, lower, upper in brackets:
        if ti <= lower:
            continue
        if upper is None:
            amt = ti - lower
        else:
            amt = min(ti, upper) - lower
        if amt > 0:
            tax += amt * rate
    return max(0.0, tax)

def fica_employee_tax(wages: float, ss_wage_base: float, ss_rate: float = 0.062, medicare_rate: float = 0.0145,
                      addl_medicare_rate: float = 0.009, addl_medicare_threshold: float = 250000.0):
    """
    Employee-side FICA approximation:
      - SS: 6.2% up to wage base
      - Medicare: 1.45% all wages
      - Additional Medicare: 0.9% above threshold
    Threshold default assumes Married Filing Jointly. You can override.
    """
    w = max(0.0, float(wages))
    ss_tax = min(w, ss_wage_base) * ss_rate
    medicare_tax = w * medicare_rate
    addl = max(0.0, w - addl_medicare_threshold) * addl_medicare_rate
    return ss_tax + medicare_tax + addl

# -----------------------------
# Sidebar: Global settings + Modes
# -----------------------------
with st.sidebar:
    st.header("Global Settings")
    horizon_years = st.slider("Horizon (years)", 5, 40, 20, step=1)
    years = np.arange(0, horizon_years + 1)

    st.divider()
    st.header("Modes")

    push_hard = st.checkbox("Push-Hard Upfront", value=False)
    if push_hard:
        push_years = st.number_input("Push-hard duration (years)", 1, 10, 2)
        push_extra_income = st.number_input("Push-hard extra annual income", 0, 300000, 0, step=1000)
        push_extra_cost = st.number_input("Push-hard annual cost", 0, 200000, 15000, step=1000)
    else:
        push_years = 0
        push_extra_income = 0.0
        push_extra_cost = 0.0

    frugal_mode = st.checkbox("Frugal Mode", value=False)
    if frugal_mode:
        frugal_start = st.number_input("Frugal start year", 0, horizon_years, 0)
        frugal_years = st.number_input("Frugal duration (years)", 1, 20, 2)
        frugal_expense_reduction_pct = st.slider("Expense reduction (%)", 0.0, 60.0, 15.0, 0.5)
    else:
        frugal_start = 0
        frugal_years = 0
        frugal_expense_reduction_pct = 0.0

    st.divider()
    st.header("Portfolio Settings")
    max_props = st.slider("Max properties", 1, 10, 10)

    st.divider()
    st.header("HELOC Assumptions")
    heloc_rate = st.slider("HELOC rate (%)", 0.0, 15.0, 9.0, 0.1)

    st.divider()
    st.header("Cash Behavior")
    reinvest_surplus = st.checkbox("Reinvest annual surplus into investable cash", value=True)

# -----------------------------
# Income (Gross -> Net)
# -----------------------------
st.subheader("Household Income (Gross → Net)")

ic1, ic2, ic3, ic4 = st.columns(4)
with ic1:
    cody_gross0 = st.number_input("Cody GROSS income (Year 0, annual)", 0, 2000000, 140000, step=1000)
with ic2:
    lauren_gross0 = st.number_input("Lauren GROSS income (Year 0, annual)", 0, 2000000, 75000, step=1000)
with ic3:
    cody_growth = st.slider("Cody income growth (%/yr)", 0.0, 15.0, 0.0, 0.1)
with ic4:
    lauren_growth = st.slider("Lauren income growth (%/yr)", 0.0, 15.0, 2.0, 0.1)

ic5, ic6, ic7, ic8 = st.columns(4)
with ic5:
    cody_income_start = st.number_input("Cody income starts in year", 0, 40, 0)
with ic6:
    lauren_income_start = st.number_input("Lauren income starts in year", 0, 40, 0)
with ic7:
    other_income0 = st.number_input("Other household income (Year 0, annual)", 0, 2000000, 0, step=1000)
with ic8:
    other_income_growth = st.slider("Other income growth (%/yr)", 0.0, 15.0, 0.0, 0.1)

ic9, ic10 = st.columns(2)
with ic9:
    other_income_start = st.number_input("Other household income starts in year", 0, 40, 0)
with ic10:
    other_income_is_net = st.checkbox("Other household income is already NET (don’t tax it)", value=True)

st.divider()
st.subheader("Taxes & Net Pay (toggle)")

tx1, tx2, tx3, tx4 = st.columns(4)
with tx1:
    tax_mode = st.selectbox(
        "Net-pay method",
        ["Simple effective tax %", "Estimate taxes (federal + optional state + optional FICA)"],
        index=0
    )
with tx2:
    filing_status = st.selectbox("Filing status (for estimator)", ["Married Filing Jointly", "Single", "Head of Household", "Married Filing Separately"], index=0)
with tx3:
    include_state_tax = st.checkbox("Include state tax (flat %)", value=False)
with tx4:
    state_tax_pct = st.slider("State tax (%)", 0.0, 15.0, 0.0, 0.1, disabled=not include_state_tax)

tx5, tx6, tx7, tx8 = st.columns(4)
with tx5:
    # Used in Simple mode
    cody_effective_tax_pct = st.slider("Cody effective tax % (simple mode)", 0.0, 60.0, 25.0, 0.5, disabled=(tax_mode != "Simple effective tax %"))
with tx6:
    lauren_effective_tax_pct = st.slider("Lauren effective tax % (simple mode)", 0.0, 60.0, 20.0, 0.5, disabled=(tax_mode != "Simple effective tax %"))
with tx7:
    other_effective_tax_pct = st.slider(
        "Other income tax % (if not already net)",
        0.0, 60.0, 0.0, 0.5,
        disabled=(tax_mode != "Simple effective tax %" or other_income_is_net)
    )
with tx8:
    show_tax_line_item = st.checkbox("Show estimated taxes as a line item in results", value=True)

# Estimator settings
est1, est2, est3, est4 = st.columns(4)
with est1:
    include_fica = st.checkbox("Include employee FICA (estimator)", value=True, disabled=(tax_mode != "Estimate taxes (federal + optional state + optional FICA)"))
with est2:
    assume_employee_contribs_pretax = st.checkbox("Treat 401(k) employee contributions as pre-tax (estimator)", value=True, disabled=(tax_mode != "Estimate taxes (federal + optional state + optional FICA)"))
with est3:
    tax_year = st.selectbox("Tax year tables (estimator)", ["2026"], index=0, disabled=(tax_mode != "Estimate taxes (federal + optional state + optional FICA)"))
with est4:
    addl_medicare_threshold = st.number_input(
        "Additional Medicare threshold (estimator, $)",
        0, 1000000, 250000,
        step=10000,
        disabled=(tax_mode != "Estimate taxes (federal + optional state + optional FICA)" or not include_fica)
    )

# 2026 tables (hardcoded for offline use)
# Brackets commonly published for 2026 (10/12/22/24/32/35/37) + standard deduction.
# (You can update these numbers later without changing the rest of the model.)
STD_DEDUCTION_2026 = {
    "Single": 16100.0,
    "Married Filing Separately": 16100.0,
    "Married Filing Jointly": 32200.0,
    "Head of Household": 24150.0,
}
BRACKETS_2026 = {
    "Single": [
        (0.10, 0, 12400),
        (0.12, 12400, 50400),
        (0.22, 50400, 105700),
        (0.24, 105700, 201775),
        (0.32, 201775, 256225),
        (0.35, 256225, 640600),
        (0.37, 640600, None),
    ],
    "Married Filing Jointly": [
        (0.10, 0, 24800),
        (0.12, 24800, 100800),
        (0.22, 100800, 211400),
        (0.24, 211400, 403550),
        (0.32, 403550, 512450),
        (0.35, 512450, 768700),
        (0.37, 768700, None),
    ],
    "Head of Household": [
        (0.10, 0, 17700),
        (0.12, 17700, 67450),
        (0.22, 67450, 105700),
        (0.24, 105700, 201750),
        (0.32, 201750, 256200),
        (0.35, 256200, 640600),
        (0.37, 640600, None),
    ],
    "Married Filing Separately": [
        (0.10, 0, 12400),
        (0.12, 12400, 50400),
        (0.22, 50400, 105700),
        (0.24, 105700, 201775),
        (0.32, 201775, 256225),
        (0.35, 256225, 384350),
        (0.37, 384350, None),
    ],
}

# SSA 2026 wage base (hardcoded for offline; update if needed)
SS_WAGE_BASE_2026 = 184500.0

# -----------------------------
# Expenses
# -----------------------------
st.subheader("Household Expenses (annual)")
e1, e2 = st.columns(2)
with e1:
    base_living_expenses = st.number_input("Core annual expenses (non-property, excluding primary mortgage)", 0, 600000, 90000, step=1000)
with e2:
    expense_growth = st.slider("Expense growth / inflation (%/yr)", 0.0, 10.0, 0.0, 0.1)

# -----------------------------
# Primary Residence / New House Mortgage (PITI + escrow)
# -----------------------------
st.subheader("Primary Residence (New House) — Mortgage + Escrow (PITI)")

nh0, nh1, nh2, nh3 = st.columns(4)
with nh0:
    new_home_enabled = st.checkbox("Include new house payment in cashflow", value=True)
with nh1:
    new_home_start_year = st.number_input("New house payment starts in year", 0, horizon_years, 0, disabled=not new_home_enabled)
with nh2:
    compute_loan_from_price = st.checkbox("Compute loan amount from price/down", value=False, disabled=not new_home_enabled)
with nh3:
    include_new_home_equity_in_networth = st.checkbox("Include new home equity in Net Worth (simple)", value=False, disabled=not new_home_enabled)

nh4, nh5, nh6, nh7 = st.columns(4)
with nh4:
    new_home_purchase_price = st.number_input("Home purchase price ($)", 0, 10000000, 0, step=5000, disabled=not (new_home_enabled and compute_loan_from_price))
with nh5:
    new_home_down_pct = st.slider("Down payment (%)", 0.0, 80.0, 20.0, 0.5, disabled=not (new_home_enabled and compute_loan_from_price))
with nh6:
    new_home_loan_amount = st.number_input("Loan amount (mortgage principal) ($)", 0, 10000000, 0, step=5000, disabled=not (new_home_enabled and not compute_loan_from_price))
with nh7:
    new_home_rate_pct = st.slider("Mortgage rate (%)", 0.0, 15.0, 7.0, 0.1, disabled=not new_home_enabled)

nh8, nh9, nh10, nh11 = st.columns(4)
with nh8:
    new_home_term_years = st.number_input("Mortgage term (years)", 1, 40, 30, disabled=not new_home_enabled)
with nh9:
    new_home_property_tax_annual = st.number_input("Property tax (annual $)", 0, 200000, 0, step=250, disabled=not new_home_enabled)
with nh10:
    new_home_insurance_annual = st.number_input("Home insurance (annual $)", 0, 200000, 0, step=250, disabled=not new_home_enabled)
with nh11:
    new_home_hoa_monthly = st.number_input("HOA (monthly $)", 0, 5000, 0, step=25, disabled=not new_home_enabled)

nh12, nh13, nh14, nh15 = st.columns(4)
with nh12:
    new_home_pmi_monthly = st.number_input("PMI (monthly $)", 0, 5000, 0, step=25, disabled=not new_home_enabled)
with nh13:
    new_home_value_growth_pct = st.slider("Home value growth (%/yr) (for equity calc)", -5.0, 15.0, 3.0, 0.1, disabled=not (new_home_enabled and include_new_home_equity_in_networth))
with nh14:
    new_home_sell_year = st.number_input("Sell new home in year (0 = never)", 0, horizon_years, 0, disabled=not (new_home_enabled and include_new_home_equity_in_networth))
with nh15:
    new_home_selling_cost_pct = st.slider("Selling costs (% of value)", 0.0, 12.0, 6.0, 0.5, disabled=not (new_home_enabled and include_new_home_equity_in_networth))

# Resolve loan amount if computed from price/down
if new_home_enabled and compute_loan_from_price:
    new_home_loan_amount_eff = max(0.0, float(new_home_purchase_price) * (1.0 - float(new_home_down_pct) / 100.0))
else:
    new_home_loan_amount_eff = float(new_home_loan_amount)

# -----------------------------
# Mortgage Prepay Savings (Pharmacy scenario tie-in)
# -----------------------------
st.subheader("Mortgage Prepay Savings (Optional)")

mp1, mp2, mp3, mp4 = st.columns(4)
with mp1:
    include_mortgage_prepay_savings = st.checkbox("Include mortgage prepay savings in cash flow", value=True)
with mp2:
    mortgage_prepay_amount = st.number_input("Mortgage prepay amount ($)", 0, 5000000, 71000, step=1000, disabled=not include_mortgage_prepay_savings)
with mp3:
    mortgage_savings_annual = st.number_input("Annual mortgage savings ($/yr)", 0, 500000, 8000, step=250, disabled=not include_mortgage_prepay_savings)
with mp4:
    mortgage_savings_start_year = st.number_input("Mortgage savings start year", 0, horizon_years, 0, disabled=not include_mortgage_prepay_savings)

st.caption("This models the $/yr savings as additional free cash flow starting at the selected year (does not change property amortization here).")

# -----------------------------
# Pharmacy Buy-In (NEW)
# -----------------------------
st.subheader("Pharmacy Buy-In Scenario (NEW)")

pb0, pb1, pb2, pb3 = st.columns(4)
with pb0:
    pharmacy_buyin_enabled = st.checkbox("Enable pharmacy buy-in scenario", value=False)
with pb1:
    pharmacy_buyin_year = st.number_input("Buy-in year", 0, horizon_years, 0, disabled=not pharmacy_buyin_enabled)
with pb2:
    pharmacy_buyin_price = st.number_input("Buy-in price ($)", 0, 5000000, 120000, step=1000, disabled=not pharmacy_buyin_enabled)
with pb3:
    pharmacy_cash_down = st.number_input("Your cash down ($)", 0, 5000000, 47000, step=1000, disabled=not pharmacy_buyin_enabled)

pb4, pb5, pb6, pb7 = st.columns(4)
with pb4:
    pharmacy_expected_profit = st.number_input("Your expected annual profit from stake ($)", 0, 2000000, 30000, step=1000, disabled=not pharmacy_buyin_enabled)
with pb5:
    pharmacy_profit_start_year = st.number_input("Profit starts in year", 0, horizon_years, int(pharmacy_buyin_year), disabled=not pharmacy_buyin_enabled)
with pb6:
    seller_note_years = st.number_input("Seller note term (years)", 1, 15, 5, step=1, disabled=not pharmacy_buyin_enabled)
with pb7:
    seller_note_rate_pct = st.slider("Seller note rate (%)", 0.0, 15.0, 5.5, 0.1, disabled=not pharmacy_buyin_enabled)

pb_growth1, pb_growth2 = st.columns(2)
with pb_growth1:
    pharmacy_profit_growth_pct = st.slider(
        "Pharmacy profit growth (%/yr)",
        -20.0, 30.0, 0.0, 0.1,
        disabled=not pharmacy_buyin_enabled
    )
with pb_growth2:
    pharmacy_profit_growth_start_year = st.number_input(
        "Profit growth starts in year",
        0, horizon_years, int(pharmacy_profit_start_year),
        disabled=not pharmacy_buyin_enabled
    )

pb8, pb9, pb10, pb11 = st.columns(4)
with pb8:
    include_pharmacy_equity_in_networth = st.checkbox("Include pharmacy equity in Net Worth", value=True, disabled=not pharmacy_buyin_enabled)
with pb9:
    pharmacy_equity_growth_pct = st.slider("Pharmacy equity value growth (%/yr)", -10.0, 20.0, 0.0, 0.1, disabled=not pharmacy_buyin_enabled)
with pb10:
    enable_accel_paydown = st.checkbox("Enable accelerated principal paydown", value=True, disabled=not pharmacy_buyin_enabled)
with pb11:
    accel_year = st.number_input("Apply extra principal in year", 0, horizon_years, 2, disabled=not (pharmacy_buyin_enabled and enable_accel_paydown))

pb12, pb13, pb14 = st.columns(3)
with pb12:
    lauren_dist_lump = st.number_input("Lauren distribution (lump sum extra principal) ($)", 0, 5000000, 20000, step=1000, disabled=not (pharmacy_buyin_enabled and enable_accel_paydown))
with pb13:
    extra_principal_recurring = st.number_input("Recurring extra principal (annual) ($)", 0, 5000000, 0, step=1000, disabled=not (pharmacy_buyin_enabled and enable_accel_paydown))
with pb14:
    recurring_extra_start_year = st.number_input("Recurring extra starts year", 0, horizon_years, 2, disabled=not (pharmacy_buyin_enabled and enable_accel_paydown))

# -----------------------------
# Retirement (NEW)
# -----------------------------
st.subheader("Retirement Contributions & Employer Match (NEW)")

rt0, rt1, rt2 = st.columns(3)
with rt0:
    retirement_return = st.slider("Assumed retirement account return (%/yr)", 0.0, 15.0, 7.0, 0.1)
with rt1:
    include_retirement_in_networth = st.checkbox("Include retirement balances in Net Worth", value=True)
with rt2:
    count_retirement_contrib_as_expense = st.checkbox("Treat retirement contributions as cash outflow", value=True)

st.caption("Simple model: contributions + employer match go into retirement accounts each year, then the balance grows by the assumed return.")

rb1, rb2 = st.columns(2)
with rb1:
    cody_ret_balance0 = st.number_input("Cody retirement starting balance", 0, 5000000, 0, step=1000)
with rb2:
    lauren_ret_balance0 = st.number_input("Lauren retirement starting balance", 0, 5000000, 0, step=1000)

st.markdown("**Cody: contributions + employer match**")
c1, c2, c3, c4 = st.columns(4)
with c1:
    cody_contrib_pct = st.slider("Cody employee contribution (% of gross income)", 0.0, 30.0, 0.0, 0.5)
with c2:
    cody_employer_match_pct = st.slider("Cody employer match (% of gross income)", 0.0, 15.0, 0.0, 0.5)
with c3:
    cody_match_cap_pct = st.slider("Cody match cap (match only up to % contributed)", 0.0, 15.0, 0.0, 0.5)
with c4:
    cody_contrib_start_year = st.number_input("Cody retirement contributions start year", 0, horizon_years, 0)

st.markdown("**Lauren: contributions + employer match**")
l1, l2, l3, l4 = st.columns(4)
with l1:
    lauren_contrib_pct = st.slider("Lauren employee contribution (% of gross income)", 0.0, 30.0, 0.0, 0.5)
with l2:
    lauren_employer_match_pct = st.slider("Lauren employer match (% of gross income)", 0.0, 15.0, 0.0, 0.5)
with l3:
    lauren_match_cap_pct = st.slider("Lauren match cap (match only up to % contributed)", 0.0, 15.0, 0.0, 0.5)
with l4:
    lauren_contrib_start_year = st.number_input("Lauren retirement contributions start year", 0, horizon_years, 0)

st.markdown("**Optional: Flat annual IRA contributions (after-tax cash outflow)**")
ira1, ira2 = st.columns(2)
with ira1:
    cody_ira_annual = st.number_input("Cody IRA contribution (annual $)", 0, 100000, 0, step=500)
with ira2:
    lauren_ira_annual = st.number_input("Lauren IRA contribution (annual $)", 0, 100000, 0, step=500)

# -----------------------------
# Student Loans (interest-based aggregate)
# -----------------------------
st.subheader("Student Loans (interest-based aggregate)")

sl1, sl2, sl3, sl4 = st.columns(4)
with sl1:
    student_loan_balance0 = st.number_input("Starting student loan balance", 0, 3000000, 232000, step=1000)
with sl2:
    student_loan_interest_rate = st.slider("Aggregate student loan interest rate (%)", 0.0, 15.0, 6.8, 0.1)
with sl3:
    student_loan_years = st.number_input("Repayment horizon (years)", 1, 40, 20)
with sl4:
    student_loan_start_year = st.number_input("Repayment starts in year", 0, horizon_years, 1)

def student_loan_annual_payment(principal: float, annual_rate_pct: float, years_term: int) -> float:
    r = (annual_rate_pct / 100.0) / 12.0
    n = years_term * 12
    if principal <= 0:
        return 0.0
    if r == 0:
        return principal / max(years_term, 1)
    pmt_m = principal * (r * (1 + r) ** n) / ((1 + r) ** n - 1)
    return float(pmt_m * 12.0)

student_loan_payment_annual = student_loan_annual_payment(
    student_loan_balance0, student_loan_interest_rate, int(student_loan_years)
)

def student_loan_remaining(year: int) -> float:
    if year < student_loan_start_year:
        return float(student_loan_balance0)

    r = (student_loan_interest_rate / 100.0) / 12.0
    n = int(student_loan_years) * 12
    pmt_m = (student_loan_payment_annual / 12.0)

    months_paid = (year - student_loan_start_year + 1) * 12
    months_paid = min(months_paid, n)

    if r == 0:
        bal = student_loan_balance0 - pmt_m * months_paid
        return float(max(0.0, bal))

    bal = student_loan_balance0 * (1 + r) ** months_paid - pmt_m * (((1 + r) ** months_paid - 1) / r)
    return float(max(0.0, bal))

# -----------------------------
# Capital / reserves
# -----------------------------
st.subheader("Capital / Reserves")
cc1, cc2 = st.columns(2)
with cc1:
    starting_cash = st.number_input("Starting investable cash", 0, 5000000, 40000, step=1000)
with cc2:
    min_cash_reserve = st.number_input("Minimum cash reserve (model can still dip below)", 0, 5000000, 15000, step=1000)

# -----------------------------
# Properties
# -----------------------------
st.subheader("Properties (up to 10) — Existing Property + HELOC + Liquidation")
st.caption(
    "Use 'Existing at Year 0' for your current home converting to a rental. "
    "That uses current value + current mortgage balance (no down payment deducted)."
)

properties = []

for i in range(max_props):
    default_enabled = (i == 0)
    default_buy_year = 0 if i == 0 else 2

    with st.expander(f"Property {i+1}", expanded=(i == 0)):
        top1, top2, top3, top4 = st.columns(4)
        enabled = top1.checkbox("Enabled", value=default_enabled, key=f"p_enabled_{i}")
        name = top2.text_input("Name", value=("Current Home → Rental" if i == 0 else f"Rental {i+1}"), key=f"p_name_{i}")
        purchase_year = top3.number_input("Purchase year", 0, horizon_years, default_buy_year, key=f"p_buy_{i}")
        liquidation_year = top4.number_input("Liquidation year (0 = never)", 0, horizon_years, 0, key=f"p_sell_{i}")

        ex1, ex2, ex3 = st.columns(3)
        is_existing = ex1.checkbox("Existing at Year 0 (already owned)", value=(i == 0), key=f"p_exist_{i}")
        existing_value = ex2.number_input(
            "Current market value (Year 0)",
            0, 5000000,
            292000 if i == 0 else 200000,
            step=1000,
            key=f"p_exist_val_{i}",
            disabled=not is_existing
        )
        existing_mort_balance = ex3.number_input(
            "Current mortgage balance (Year 0)",
            0, 5000000,
            232000 if i == 0 else 160000,
            step=1000,
            key=f"p_exist_mort_{i}",
            disabled=not is_existing
        )

        if is_existing:
            purchase_year = 0

        r1, r2, r3, r4 = st.columns(4)
        purchase_price = r1.number_input(
            "Purchase price / basis",
            50000, 5000000,
            int(existing_value) if is_existing else 200000,
            step=5000,
            key=f"p_price_{i}",
            disabled=is_existing
        )
        down_pct = r2.slider("Down payment (%)", 0.0, 50.0, 20.0, 0.5, key=f"p_down_{i}", disabled=is_existing)
        mortgage_rate = r3.slider(
            "Mortgage rate (%)",
            0.0, 15.0,
            2.87 if (i == 0 and is_existing) else 7.0,
            0.1,
            key=f"p_rate_{i}"
        )
        term_years = r4.number_input(
            "Remaining term (years)",
            1, 40,
            27 if (i == 0 and is_existing) else 30,
            key=f"p_term_{i}"
        )

        r5, r6, r7, r8 = st.columns(4)
        gross_rent_month = r5.number_input("Gross rent (monthly)", 0, 50000, 2000, step=50, key=f"p_rent_{i}")
        tax_ins_month = r6.number_input("Taxes+Ins (monthly)", 0, 20000, 350, step=25, key=f"p_taxins_{i}")
        maintenance_pct = r7.slider("Maintenance (% of rent)", 0.0, 25.0, 8.0, 0.5, key=f"p_maint_{i}")
        vacancy_pct = r8.slider("Vacancy (% of rent)", 0.0, 25.0, 5.0, 0.5, key=f"p_vac_{i}")

        r9, r10, r11, r12 = st.columns(4)
        capex_pct = r9.slider("CapEx reserve (% of rent)", 0.0, 25.0, 5.0, 0.5, key=f"p_capex_{i}")
        pm_enabled = r10.checkbox("Property mgmt?", value=True, key=f"p_pm_on_{i}")
        pm_pct = r11.slider("PM fee (% of rent)", 0.0, 25.0, 10.0, 0.5, key=f"p_pm_{i}") if pm_enabled else 0.0
        value_growth = r12.slider("Home value growth (%/yr)", -5.0, 15.0, 3.0, 0.1, key=f"p_grow_{i}")

        rs1, rs2 = st.columns(2)
        rent_start_year = rs1.number_input("Rent starts in year", 0, horizon_years, int(purchase_year), key=f"p_rent_start_{i}")
        rent_growth = rs2.slider("Rent growth (%/yr)", -5.0, 15.0, 2.0, 0.1, key=f"p_rent_grow_{i}")

        st.markdown("**HELOC settings**")
        h1, h2, h3, h4 = st.columns(4)
        heloc_enabled = h1.checkbox("Enable HELOC", value=False, key=f"p_heloc_on_{i}")
        heloc_cltv = h2.slider("Max CLTV for HELOC (%)", 50.0, 95.0, 80.0, 0.5, key=f"p_cltv_{i}") if heloc_enabled else 0.0
        heloc_draw_year = h3.number_input("HELOC draw year (0 = none)", 0, horizon_years, 0, key=f"p_heloc_draw_year_{i}") if heloc_enabled else 0
        heloc_draw_amount = h4.number_input("HELOC draw amount", 0, 5000000, 0, step=5000, key=f"p_heloc_draw_amt_{i}") if heloc_enabled else 0

        if enabled:
            properties.append({
                "name": name,
                "purchase_year": int(purchase_year),
                "liquidation_year": int(liquidation_year),
                "is_existing": bool(is_existing),

                "value_year0": float(existing_value) if is_existing else float(purchase_price),
                "purchase_price": float(existing_value) if is_existing else float(purchase_price),

                "down_pct": float(down_pct),
                "mortgage_rate": float(mortgage_rate) / 100.0,
                "term_years": int(term_years),
                "mortgage_balance_year0": float(existing_mort_balance) if is_existing else None,

                "gross_rent_month": float(gross_rent_month),
                "tax_ins_month": float(tax_ins_month),
                "maintenance_pct": float(maintenance_pct) / 100.0,
                "vacancy_pct": float(vacancy_pct) / 100.0,
                "capex_pct": float(capex_pct) / 100.0,
                "pm_pct": float(pm_pct) / 100.0,
                "value_growth": float(value_growth) / 100.0,

                "rent_start_year": int(rent_start_year),
                "rent_growth": float(rent_growth) / 100.0,

                "heloc_enabled": bool(heloc_enabled),
                "heloc_cltv": float(heloc_cltv) / 100.0 if heloc_enabled else 0.0,
                "heloc_draw_year": int(heloc_draw_year) if heloc_enabled else 0,
                "heloc_draw_amount": float(heloc_draw_amount) if heloc_enabled else 0.0,
            })

# -----------------------------
# Initialize per-property state
# -----------------------------
prop_state = []
for p in properties:
    if p["is_existing"]:
        loan_principal = p["mortgage_balance_year0"]
    else:
        loan_principal = p["purchase_price"] * (1 - p["down_pct"] / 100.0)

    prop_state.append({
        "loan_principal": float(loan_principal),
        "heloc_balance": 0.0,
        "active": True
    })

# -----------------------------
# Run simulation
# -----------------------------
rows = []
cash = float(starting_cash)
cody_ret = float(cody_ret_balance0)
lauren_ret = float(lauren_ret_balance0)

# Pharmacy state
ph_note_balance = 0.0
ph_annual_payment = 0.0
ph_equity_value = 0.0
ph_active = False

seller_note_rate = (float(seller_note_rate_pct) / 100.0) if pharmacy_buyin_enabled else 0.0

# New home state (for optional equity in net worth)
new_home_active = bool(new_home_enabled)
new_home_down_payment = 0.0
new_home_initial_value = 0.0

if new_home_enabled and include_new_home_equity_in_networth and compute_loan_from_price and new_home_purchase_price > 0:
    new_home_initial_value = float(new_home_purchase_price)
    new_home_down_payment = float(new_home_purchase_price) - float(new_home_loan_amount_eff)

for y in years:
    y = int(y)

    # -------------------------
    # Gross incomes
    # -------------------------
    cody_gross_y = income_stream(cody_gross0, cody_growth, y, int(cody_income_start))
    lauren_gross_y = income_stream(lauren_gross0, lauren_growth, y, int(lauren_income_start))
    other_gross_y = income_stream(other_income0, other_income_growth, y, int(other_income_start))

    # Retirement employee contributions (used both for cashflow + optional tax estimator)
    cody_emp_contrib = 0.0
    cody_match = 0.0
    lauren_emp_contrib = 0.0
    lauren_match = 0.0
    cody_ira = 0.0
    lauren_ira = 0.0

    if y >= int(cody_contrib_start_year):
        cody_emp_contrib = cody_gross_y * (cody_contrib_pct / 100.0)
        effective_contrib_pct = min(cody_contrib_pct, cody_match_cap_pct) if cody_match_cap_pct > 0 else 0.0
        cody_match = cody_gross_y * (min(cody_employer_match_pct, effective_contrib_pct) / 100.0)

    if y >= int(lauren_contrib_start_year):
        lauren_emp_contrib = lauren_gross_y * (lauren_contrib_pct / 100.0)
        effective_contrib_pct = min(lauren_contrib_pct, lauren_match_cap_pct) if lauren_match_cap_pct > 0 else 0.0
        lauren_match = lauren_gross_y * (min(lauren_employer_match_pct, effective_contrib_pct) / 100.0)

    cody_ira = float(cody_ira_annual) if cody_gross_y > 0 else 0.0
    lauren_ira = float(lauren_ira_annual) if lauren_gross_y > 0 else 0.0

    # -------------------------
    # Taxes / Net pay
    # -------------------------
    est_federal_tax = 0.0
    est_state_tax = 0.0
    est_fica_tax = 0.0
    est_total_tax = 0.0

    if tax_mode == "Simple effective tax %":
        cody_net_y = cody_gross_y * (1.0 - cody_effective_tax_pct / 100.0)
        lauren_net_y = lauren_gross_y * (1.0 - lauren_effective_tax_pct / 100.0)
        if other_income_is_net:
            other_net_y = other_gross_y
        else:
            other_net_y = other_gross_y * (1.0 - other_effective_tax_pct / 100.0)

        if show_tax_line_item:
            # In simple mode, "tax" is just gross - net
            est_total_tax = (cody_gross_y - cody_net_y) + (lauren_gross_y - lauren_net_y) + (other_gross_y - other_net_y)

    else:
        # Estimator mode (household-level)
        status_key = filing_status
        std_ded = STD_DEDUCTION_2026.get(status_key, 0.0)
        brackets = BRACKETS_2026.get(status_key, BRACKETS_2026["Married Filing Jointly"])

        household_gross = cody_gross_y + lauren_gross_y + (other_gross_y if not other_income_is_net else 0.0)

        # Pre-tax deductions approximation: 401(k) employee contributions only (optional)
        pretax = 0.0
        if assume_employee_contribs_pretax:
            pretax += cody_emp_contrib + lauren_emp_contrib

        taxable_income = max(0.0, household_gross - pretax - std_ded)
        est_federal_tax = progressive_tax(taxable_income, brackets)

        if include_state_tax and state_tax_pct > 0:
            est_state_tax = max(0.0, household_gross - pretax) * (state_tax_pct / 100.0)

        if include_fica:
            # Approx: apply FICA per-earner (employee-side)
            est_fica_tax = (
                fica_employee_tax(
                    wages=cody_gross_y,
                    ss_wage_base=SS_WAGE_BASE_2026,
                    addl_medicare_threshold=float(addl_medicare_threshold)
                )
                + fica_employee_tax(
                    wages=lauren_gross_y,
                    ss_wage_base=SS_WAGE_BASE_2026,
                    addl_medicare_threshold=float(addl_medicare_threshold)
                )
            )

        est_total_tax = est_federal_tax + est_state_tax + est_fica_tax

        # Net pay: (gross - estimated taxes) + other income if already net
        household_net = max(0.0, (household_gross - est_total_tax)) + (other_gross_y if other_income_is_net else 0.0)

        # Allocate net back proportionally for reporting (so charts still work)
        denom = (cody_gross_y + lauren_gross_y + (other_gross_y if not other_income_is_net else 0.0))
        if denom <= 0:
            cody_net_y = 0.0
            lauren_net_y = 0.0
            other_net_y = other_gross_y if other_income_is_net else 0.0
        else:
            # Net portion attributable to taxable incomes
            taxable_net_pool = max(0.0, household_gross - est_total_tax)
            cody_net_y = taxable_net_pool * (cody_gross_y / denom)
            lauren_net_y = taxable_net_pool * (lauren_gross_y / denom)
            if other_income_is_net:
                other_net_y = other_gross_y
            else:
                other_net_y = taxable_net_pool * (other_gross_y / denom)

    # Base income for cashflow uses NET
    base_income_net_y = cody_net_y + lauren_net_y + other_net_y

    # -------------------------
    # Expenses (inflation)
    # -------------------------
    base_expenses_y = float(base_living_expenses) * ((1 + expense_growth / 100.0) ** y)

    # Push-hard adjustments
    extra_income_y = float(push_extra_income) if (push_hard and y < push_years) else 0.0
    extra_cost_y = float(push_extra_cost) if (push_hard and y < push_years) else 0.0

    # Frugal adjustments
    if frugal_mode and (frugal_start <= y < frugal_start + frugal_years):
        base_expenses_y *= (1.0 - frugal_expense_reduction_pct / 100.0)

    # Treat push-hard extra income as NET (so it affects cashflow)
    income_y = base_income_net_y + extra_income_y
    expenses_y = base_expenses_y + extra_cost_y

    # -------------------------
    # Student loans
    # -------------------------
    sl_remaining = student_loan_remaining(y)
    sl_pay_y = student_loan_payment_annual if (y >= student_loan_start_year and sl_remaining > 0) else 0.0

    # -------------------------
    # Retirement balances
    # -------------------------
    total_ret_contrib_outflow = 0.0
    if count_retirement_contrib_as_expense:
        total_ret_contrib_outflow = cody_emp_contrib + lauren_emp_contrib + cody_ira + lauren_ira

    cody_ret = grow_balance(cody_ret + cody_emp_contrib + cody_match + cody_ira, retirement_return)
    lauren_ret = grow_balance(lauren_ret + lauren_emp_contrib + lauren_match + lauren_ira, retirement_return)
    total_retirement = cody_ret + lauren_ret

    # -------------------------
    # Primary residence / new home payment (PITI)
    # -------------------------
    new_home_piti_y = 0.0
    new_home_value_y = 0.0
    new_home_mort_bal_y = 0.0
    new_home_equity_y = 0.0
    new_home_liquidation_proceeds = 0.0

    if new_home_enabled and y >= int(new_home_start_year) and new_home_loan_amount_eff > 0:
        months_paid = int((y - int(new_home_start_year)) * 12)

        pmt_m = amort_payment(new_home_loan_amount_eff, float(new_home_rate_pct) / 100.0, int(new_home_term_years))
        pi_annual = 12.0 * pmt_m

        escrow_annual = float(new_home_property_tax_annual) + float(new_home_insurance_annual)
        pmi_annual = 12.0 * float(new_home_pmi_monthly)
        hoa_annual = 12.0 * float(new_home_hoa_monthly)

        new_home_piti_y = pi_annual + escrow_annual + pmi_annual + hoa_annual

        if include_new_home_equity_in_networth and compute_loan_from_price and new_home_purchase_price > 0:
            yrs_held = max(0, y - int(new_home_start_year))
            new_home_value_y = float(new_home_purchase_price) * ((1 + float(new_home_value_growth_pct) / 100.0) ** yrs_held)
            new_home_mort_bal_y = mortgage_balance(
                principal=float(new_home_loan_amount_eff),
                annual_rate=float(new_home_rate_pct) / 100.0,
                years=int(new_home_term_years),
                months_paid=months_paid
            )
            new_home_equity_y = max(0.0, new_home_value_y - new_home_mort_bal_y)

            if int(new_home_sell_year) > 0 and y == int(new_home_sell_year):
                sell_cost = (float(new_home_selling_cost_pct) / 100.0) * new_home_value_y
                new_home_liquidation_proceeds = max(0.0, new_home_value_y - sell_cost - new_home_mort_bal_y)
                cash += new_home_liquidation_proceeds
                # Stop counting it after sale (simple: disable)
                new_home_enabled = False

    # -------------------------
    # Properties
    # -------------------------
    rental_cf_y = 0.0
    total_equity = 0.0
    total_heloc = 0.0
    active_props = 0
    acquired_props = 0
    liquidated_props = 0
    heloc_drawn_total = 0.0
    total_property_value = 0.0

    for idx, p in enumerate(properties):
        stt = prop_state[idx]
        if y < p["purchase_year"]:
            continue
        if not stt["active"]:
            continue

        if (not p["is_existing"]) and (y == p["purchase_year"]):
            down_needed = p["purchase_price"] * (p["down_pct"] / 100.0)
            cash -= down_needed
            acquired_props += 1

        yrs_held = y - p["purchase_year"]
        months_paid = int(yrs_held * 12)

        home_value = p["value_year0"] * ((1 + p["value_growth"]) ** yrs_held)
        total_property_value += home_value

        mort_bal = mortgage_balance(
            principal=stt["loan_principal"],
            annual_rate=p["mortgage_rate"],
            years=p["term_years"],
            months_paid=months_paid
        )

        if p["heloc_enabled"] and p["heloc_draw_year"] > 0 and y == p["heloc_draw_year"]:
            allowed_total_debt = p["heloc_cltv"] * home_value
            allowed_heloc = max(0.0, allowed_total_debt - mort_bal)
            draw = min(p["heloc_draw_amount"], allowed_heloc)
            if draw > 0:
                stt["heloc_balance"] += draw
                cash += draw
                heloc_drawn_total += draw

        if y >= p["rent_start_year"]:
            rent_years = y - p["rent_start_year"]
            gross_rent_annual = 12 * p["gross_rent_month"] * ((1 + p["rent_growth"]) ** rent_years)
        else:
            gross_rent_annual = 0.0

        pm_annual = p["pm_pct"] * gross_rent_annual
        maint_annual = p["maintenance_pct"] * gross_rent_annual
        vacancy_annual = p["vacancy_pct"] * gross_rent_annual
        capex_annual = p["capex_pct"] * gross_rent_annual
        tax_ins_annual = 12 * p["tax_ins_month"]

        pmt_month = amort_payment(stt["loan_principal"], p["mortgage_rate"], p["term_years"])
        debt_service_annual = 12 * pmt_month

        heloc_interest_annual = stt["heloc_balance"] * (heloc_rate / 100.0)

        net_prop = gross_rent_annual - (
            pm_annual + maint_annual + vacancy_annual + capex_annual + tax_ins_annual + debt_service_annual + heloc_interest_annual
        )
        rental_cf_y += net_prop

        equity = home_value - mort_bal - stt["heloc_balance"]
        total_equity += equity
        total_heloc += stt["heloc_balance"]
        active_props += 1

        if p["liquidation_year"] > 0 and y == p["liquidation_year"]:
            net_proceeds = max(0.0, home_value - mort_bal - stt["heloc_balance"])
            cash += net_proceeds
            stt["active"] = False
            liquidated_props += 1

    # -------------------------
    # Mortgage savings cashflow (optional)
    # -------------------------
    mort_savings_y = 0.0
    if include_mortgage_prepay_savings and (y >= int(mortgage_savings_start_year)):
        mort_savings_y = float(mortgage_savings_annual)

    # -------------------------
    # Pharmacy buy-in cashflow + note + equity value
    # -------------------------
    ph_profit_y = 0.0
    ph_note_payment_y = 0.0
    ph_note_interest_y = 0.0
    ph_note_principal_y = 0.0
    ph_extra_principal_y = 0.0

    if pharmacy_buyin_enabled:
        if (y == int(pharmacy_buyin_year)) and (not ph_active):
            ph_active = True
            cash -= float(pharmacy_cash_down)
            ph_note_balance = max(0.0, float(pharmacy_buyin_price) - float(pharmacy_cash_down))

            if seller_note_years > 0 and ph_note_balance > 0:
                r = seller_note_rate
                n = int(seller_note_years)
                if r == 0:
                    ph_annual_payment = ph_note_balance / n
                else:
                    ph_annual_payment = ph_note_balance * (r) / (1 - (1 + r) ** (-n))
            else:
                ph_annual_payment = 0.0

            ph_equity_value = float(pharmacy_buyin_price)

        if ph_active and y >= int(pharmacy_buyin_year):
            yrs_since = y - int(pharmacy_buyin_year)
            ph_equity_value = float(pharmacy_buyin_price) * ((1 + float(pharmacy_equity_growth_pct) / 100.0) ** yrs_since)

        # Profit stream (with optional annual growth)
        if ph_active and (y >= int(pharmacy_profit_start_year)):
            if y < int(pharmacy_profit_growth_start_year):
                growth_years = 0
            else:
                growth_years = y - int(pharmacy_profit_growth_start_year)

            ph_profit_y = float(pharmacy_expected_profit) * (
                (1 + float(pharmacy_profit_growth_pct) / 100.0) ** growth_years
            )

        if ph_active and ph_note_balance > 0 and ph_annual_payment > 0:
            extra = 0.0
            if enable_accel_paydown:
                if int(accel_year) > 0 and y == int(accel_year):
                    extra += float(lauren_dist_lump)
                if float(extra_principal_recurring) > 0 and y >= int(recurring_extra_start_year):
                    extra += float(extra_principal_recurring)

            ph_extra_principal_y = extra
            ph_note_payment_y, ph_note_interest_y, ph_note_principal_y, ph_note_balance = annual_amort_step(
                balance=ph_note_balance,
                annual_rate=seller_note_rate,
                annual_payment=float(ph_annual_payment),
                extra_principal=extra
            )

    # -------------------------
    # Net cash flow and cash update
    # -------------------------
    # Note: income_y is NET (per your new requirement).
    net_cash_flow_y = (
        income_y
        - expenses_y
        - new_home_piti_y
        - sl_pay_y
        + rental_cf_y
        + mort_savings_y
        + ph_profit_y
        - ph_note_payment_y
        - total_ret_contrib_outflow
    )

    if reinvest_surplus:
        cash += net_cash_flow_y

    # -------------------------
    # Net worth
    # -------------------------
    net_worth = cash + total_equity - sl_remaining

    if include_retirement_in_networth:
        net_worth += total_retirement

    if pharmacy_buyin_enabled and include_pharmacy_equity_in_networth and ph_active:
        net_worth += (ph_equity_value - ph_note_balance)

    if include_new_home_equity_in_networth:
        net_worth += new_home_equity_y

    status = "🟢 Sustainable" if net_cash_flow_y >= 30000 else ("🟡 Tight buffer" if net_cash_flow_y >= 10000 else "🔴 At risk")

    rows.append({
        "Year": y,

        "Cody Gross": round(cody_gross_y, 2),
        "Lauren Gross": round(lauren_gross_y, 2),
        "Other Gross": round(other_gross_y, 2),

        "Cody Net": round(cody_net_y, 2),
        "Lauren Net": round(lauren_net_y, 2),
        "Other Net": round(other_net_y, 2),

        "Income (Net Total)": round(income_y, 2),

        "Estimated Taxes (Total)": round(est_total_tax, 2) if show_tax_line_item else 0.0,
        "Estimated Federal Tax": round(est_federal_tax, 2) if show_tax_line_item else 0.0,
        "Estimated State Tax": round(est_state_tax, 2) if show_tax_line_item else 0.0,
        "Estimated FICA": round(est_fica_tax, 2) if show_tax_line_item else 0.0,

        "Expenses (non-property)": round(expenses_y, 2),
        "New Home PITI+HOA (annual)": round(new_home_piti_y, 2),

        "Retirement Employee Contrib": round(cody_emp_contrib + lauren_emp_contrib, 2),
        "Retirement Employer Match": round(cody_match + lauren_match, 2),
        "IRA Contributions": round(cody_ira + lauren_ira, 2),
        "Retirement Balance (Total)": round(total_retirement, 2),

        "Student Loan Pay": round(sl_pay_y, 2),
        "Student Loan Remaining": round(sl_remaining, 2),

        "Rental Cash Flow": round(rental_cf_y, 2),
        "Mortgage Savings": round(mort_savings_y, 2),

        "Pharmacy Profit": round(ph_profit_y, 2),
        "Pharmacy Note Payment": round(ph_note_payment_y, 2),
        "Pharmacy Note Interest": round(ph_note_interest_y, 2),
        "Pharmacy Note Principal": round(ph_note_principal_y, 2),
        "Pharmacy Extra Principal": round(ph_extra_principal_y, 2),
        "Pharmacy Note Balance": round(ph_note_balance, 2),
        "Pharmacy Equity Value": round(ph_equity_value, 2) if ph_active else 0.0,

        "Net Cash Flow": round(net_cash_flow_y, 2),

        "Investable Cash": round(cash, 2),
        "Total Property Value (active)": round(total_property_value, 2),
        "Total Equity (active rentals)": round(total_equity, 2),
        "HELOC Outstanding": round(total_heloc, 2),

        "New Home Value": round(new_home_value_y, 2),
        "New Home Mortgage Balance": round(new_home_mort_bal_y, 2),
        "New Home Equity": round(new_home_equity_y, 2),
        "New Home Liquidation Proceeds": round(new_home_liquidation_proceeds, 2),

        "Net Worth": round(net_worth, 2),

        "Active Properties": int(active_props),
        "Acquired This Year": int(acquired_props),
        "Liquidated This Year": int(liquidated_props),
        "HELOC Drawn This Year": round(heloc_drawn_total, 2),

        "Status": status
    })

df = pd.DataFrame(rows)

# -----------------------------
# Outputs
# -----------------------------
st.subheader("Results")

m1, m2, m3, m4, m5, m6 = st.columns(6)
m1.metric("Final Net Worth", f"${df.loc[df.index[-1], 'Net Worth']:,.0f}")
m2.metric("Final Net Cash Flow", f"${df.loc[df.index[-1], 'Net Cash Flow']:,.0f}")
m3.metric("Final Active Properties", f"{df.loc[df.index[-1], 'Active Properties']}")
m4.metric("Final Investable Cash", f"${df.loc[df.index[-1], 'Investable Cash']:,.0f}")
m5.metric("Final Equity (active rentals)", f"${df.loc[df.index[-1], 'Total Equity (active rentals)']:,.0f}")
m6.metric("Final Retirement (total)", f"${df.loc[df.index[-1], 'Retirement Balance (Total)']:,.0f}")

# Net cash flow chart
fig, ax = plt.subplots()
ax.plot(df["Year"], df["Net Cash Flow"], linewidth=2)
ax.axhline(y=30000, linestyle="--")
ax.axhline(y=10000, linestyle="--")
ax.axhline(y=0, linestyle="--")
ax.set_xlabel("Year")
ax.set_ylabel("Annual Net Cash Flow")
ax.set_title("Net Cash Flow Over Time")
st.pyplot(fig)

# Net worth chart
fig2, ax2 = plt.subplots()
ax2.plot(df["Year"], df["Net Worth"], linewidth=2)
ax2.set_xlabel("Year")
ax2.set_ylabel("Dollars")
ax2.set_title("Net Worth Over Time")
st.pyplot(fig2)

# Retirement balance chart
fig3, ax3 = plt.subplots()
ax3.plot(df["Year"], df["Retirement Balance (Total)"], linewidth=2)
ax3.set_xlabel("Year")
ax3.set_ylabel("Dollars")
ax3.set_title("Retirement Balance Over Time")
st.pyplot(fig3)

# Income breakdown chart (NET)
fig4, ax4 = plt.subplots()
ax4.plot(df["Year"], df["Cody Net"], linewidth=2)
ax4.plot(df["Year"], df["Lauren Net"], linewidth=2)
ax4.plot(df["Year"], df["Other Net"], linewidth=2)
ax4.set_xlabel("Year")
ax4.set_ylabel("Dollars")
ax4.set_title("Net Income Breakdown Over Time")
ax4.legend(["Cody Net", "Lauren Net", "Other Net"])
st.pyplot(fig4)

# Active properties chart
fig5, ax5 = plt.subplots()
ax5.plot(df["Year"], df["Active Properties"], linewidth=2)
ax5.set_xlabel("Year")
ax5.set_ylabel("Count")
ax5.set_title("Active Properties Over Time")
st.pyplot(fig5)

# Cash vs equity vs retirement chart
fig6, ax6 = plt.subplots()
ax6.plot(df["Year"], df["Investable Cash"], linewidth=2)
ax6.plot(df["Year"], df["Total Equity (active rentals)"], linewidth=2)
ax6.plot(df["Year"], df["Retirement Balance (Total)"], linewidth=2)
ax6.set_xlabel("Year")
ax6.set_ylabel("Dollars")
ax6.set_title("Cash vs Equity vs Retirement")
ax6.legend(["Investable Cash", "Total Equity (rentals)", "Retirement"])
st.pyplot(fig6)

# Taxes chart (if enabled)
if show_tax_line_item:
    st.subheader("Estimated Taxes (if enabled)")
    figt, axt = plt.subplots()
    axt.plot(df["Year"], df["Estimated Taxes (Total)"], linewidth=2)
    axt.set_xlabel("Year")
    axt.set_ylabel("Dollars")
    axt.set_title("Estimated Taxes (Total) Over Time")
    st.pyplot(figt)

# Pharmacy charts (only if enabled)
if pharmacy_buyin_enabled:
    st.subheader("Pharmacy Buy-In Charts")
    fig7, ax7 = plt.subplots()
    ax7.plot(df["Year"], df["Pharmacy Note Balance"], linewidth=2)
    ax7.set_xlabel("Year")
    ax7.set_ylabel("Dollars")
    ax7.set_title("Pharmacy Seller Note Balance Over Time")
    st.pyplot(fig7)

    fig8, ax8 = plt.subplots()
    ax8.plot(df["Year"], df["Pharmacy Profit"], linewidth=2)
    ax8.plot(df["Year"], df["Pharmacy Note Payment"], linewidth=2)
    ax8.set_xlabel("Year")
    ax8.set_ylabel("Dollars")
    ax8.set_title("Pharmacy Profit vs Note Payment")
    ax8.legend(["Profit", "Note Payment"])
    st.pyplot(fig8)

# New home equity charts (only if enabled)
if new_home_enabled and include_new_home_equity_in_networth:
    st.subheader("New Home Equity Charts")
    fignh, axnh = plt.subplots()
    axnh.plot(df["Year"], df["New Home Equity"], linewidth=2)
    axnh.set_xlabel("Year")
    axnh.set_ylabel("Dollars")
    axnh.set_title("New Home Equity Over Time (simple)")
    st.pyplot(fignh)

st.dataframe(df, use_container_width=True)

with st.expander("Notes / simplifications"):
    st.markdown(
        """
- **Gross → Net income**:
  - All salary inputs are **GROSS**.
  - Cashflow uses **NET** income.
  - You can choose:
    - **Simple effective tax %** (per-person), or
    - **Tax estimator** (household-level progressive federal + optional state + optional employee FICA).
- **Tax estimator** (offline approximation):
  - Uses standard deduction + published 2026 brackets.
  - Optional: treats **401(k) employee contributions** as pre-tax to reduce taxable income.
  - Optional: includes employee-side FICA (SS+Medicare+Additional Medicare).
  - This is planning-level, not a substitute for a tax return.
- **New house mortgage**:
  - Models annual **PITI + HOA + PMI** as a cashflow expense starting at your selected year.
  - Optional simple equity tracking if you enter purchase price + compute loan from price/down.
- **Pharmacy buy-in**:
  - Models cash down + seller note (annual amort approximation).
  - Adds pharmacy profit to cashflow; subtracts seller note payment.
  - Optional accelerated paydown (lump sum + recurring).
- **HELOC**: one draw event per property (for now), capped by CLTV; interest charged annually.
- **Liquidation**: no selling taxes modeled on rentals; new home has a simple selling cost %.
        """
# -----------------------------
# REPORT EXPORT (printable + download)
# -----------------------------
st.subheader("Report")

report_title = st.text_input("Report title", "Financial Freedom Timeline Planner — Report")
report_notes = st.text_area("Report notes (optional)", "")

# Build a clean report-friendly dataframe (optionally hide some columns)
hide_cols_default = [
    # Keep raw gross/net, but hide some very detailed internals if you want
    # "Estimated Federal Tax", "Estimated State Tax", "Estimated FICA",
]
cols_to_hide = st.multiselect("Hide columns in report", options=list(df.columns), default=hide_cols_default)
df_report = df.drop(columns=cols_to_hide, errors="ignore").copy()

def _df_to_markdown_table(dframe: pd.DataFrame) -> str:
    try:
        return dframe.to_markdown(index=False)
    except Exception:
        # fallback if tabulate isn't installed in the runtime
        return dframe.to_csv(index=False)

# Summary snapshot
summary_lines = []
summary_lines.append(f"Report Title: {report_title}")
summary_lines.append(f"Horizon (years): {int(horizon_years)}")
summary_lines.append(f"Final Net Worth: ${df.loc[df.index[-1], 'Net Worth']:,.0f}")
summary_lines.append(f"Final Net Cash Flow: ${df.loc[df.index[-1], 'Net Cash Flow']:,.0f}")
summary_lines.append(f"Final Investable Cash: ${df.loc[df.index[-1], 'Investable Cash']:,.0f}")
summary_lines.append(f"Final Active Properties: {int(df.loc[df.index[-1], 'Active Properties'])}")
summary_lines.append(f"Final Retirement (total): ${df.loc[df.index[-1], 'Retirement Balance (Total)']:,.0f}")
if show_tax_line_item:
    summary_lines.append(f"Final Estimated Taxes (Total): ${df.loc[df.index[-1], 'Estimated Taxes (Total)']:,.0f}")

summary_text = "\n".join(summary_lines)

# 1) PRINT-FRIENDLY VIEW (browser print)
st.markdown("### Print-friendly (browser print)")
st.markdown(
    """
Use your browser print dialog:
- **Mac:** Cmd+P  
- **Windows:** Ctrl+P  
Then choose **Save as PDF**.
"""
)

st.markdown(f"## {report_title}")
st.markdown("### Summary")
st.code(summary_text)

if report_notes.strip():
    st.markdown("### Notes")
    st.write(report_notes)

st.markdown("### Results Table (report)")
st.dataframe(df_report, use_container_width=True)

# 2) DOWNLOADABLE FILES
st.markdown("### Downloads")

# CSV download
csv_bytes = df_report.to_csv(index=False).encode("utf-8")
st.download_button(
    label="Download report table (CSV)",
    data=csv_bytes,
    file_name="financial_report.csv",
    mime="text/csv"
)

# HTML download (good for printing / sharing)
html_table = df_report.to_html(index=False)
html_doc = f"""
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>{report_title}</title>
  <style>
    body {{ font-family: Arial, sans-serif; padding: 24px; }}
    h1, h2, h3 {{ margin: 0.4em 0; }}
    .summary {{ white-space: pre-wrap; background: #f7f7f7; padding: 12px; border-radius: 8px; }}
    table {{ border-collapse: collapse; width: 100%; font-size: 12px; }}
    th, td {{ border: 1px solid #ddd; padding: 6px 8px; }}
    th {{ background: #f0f0f0; }}
    @media print {{
      body {{ padding: 0; }}
      table {{ font-size: 10px; }}
    }}
  </style>
</head>
<body>
  <h1>{report_title}</h1>
  <h2>Summary</h2>
  <div class="summary">{summary_text.replace("\n","<br>")}</div>
  {"<h2>Notes</h2><div class='summary'>" + report_notes.replace("\n","<br>") + "</div>" if report_notes.strip() else ""}
  <h2>Results</h2>
  {html_table}
</body>
</html>
"""
st.download_button(
    label="Download printable report (HTML)",
    data=html_doc.encode("utf-8"),
    file_name="financial_report.html",
    mime="text/html"
)

# Optional: Markdown download (nice for Notion / email)
md_doc = f"# {report_title}\n\n## Summary\n\n```\n{summary_text}\n```\n\n"
if report_notes.strip():
    md_doc += f"## Notes\n\n{report_notes}\n\n"
md_doc += "## Results Table\n\n" + _df_to_markdown_table(df_report) + "\n"
st.download_button(
    label="Download report (Markdown)",
    data=md_doc.encode("utf-8"),
    file_name="financial_report.md",
    mime="text/markdown"
)
    )
