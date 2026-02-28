import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Financial Freedom Timeline Planner", layout="wide")
st.title("Financial Freedom Timeline Planner — Net Worth + Modes + 10 Properties + HELOC + Liquidations")

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

def annual_to_monthly(annual: float) -> float:
    return float(annual) / 12.0

def monthly_to_annual(monthly: float) -> float:
    return float(monthly) * 12.0

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
        push_extra_cost = st.number_input("Push-hard annual cost (burnout/childcare/commute/etc.)", 0, 200000, 15000, step=1000)
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
# Income (separate for you + wife)
# -----------------------------
st.subheader("Household Income (separate)")

ic1, ic2, ic3, ic4 = st.columns(4)
with ic1:
    cody_income0 = st.number_input("Cody income (Year 0, annual)", 0, 1000000, 140000, step=1000)
with ic2:
    lauren_income0 = st.number_input("Lauren income (Year 0, annual)", 0, 1000000, 75000, step=1000)
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
    other_income0 = st.number_input("Other household income (Year 0, annual)", 0, 1000000, 0, step=1000)
with ic8:
    other_income_growth = st.slider("Other income growth (%/yr)", 0.0, 15.0, 0.0, 0.1)

st.subheader("Household Expenses (annual)")
e1, e2 = st.columns(2)
with e1:
    base_living_expenses = st.number_input("Core annual expenses (non-property)", 0, 600000, 90000, step=1000)
with e2:
    expense_growth = st.slider("Expense growth / inflation (%/yr)", 0.0, 10.0, 0.0, 0.1)

# -----------------------------
# Student Loans (interest-based)
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
    """Annual payment for amortizing loan (simple aggregate model)."""
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
    """Remaining balance after full years of payments starting at student_loan_start_year."""
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
# Income model (separate earners)
# -----------------------------
def income_stream(base: float, growth_pct: float, year: int, start_year: int) -> float:
    if year < start_year:
        return 0.0
    t = year - start_year
    return float(base * ((1 + growth_pct / 100.0) ** t))

# -----------------------------
# Run simulation
# -----------------------------
rows = []
cash = float(starting_cash)

for y in years:
    y = int(y)

    # Separate incomes
    cody_income_y = income_stream(cody_income0, cody_growth, y, int(cody_income_start))
    lauren_income_y = income_stream(lauren_income0, lauren_growth, y, int(lauren_income_start))
    other_income_y = income_stream(other_income0, other_income_growth, y, 0)

    base_income_y = cody_income_y + lauren_income_y + other_income_y

    # Expenses
    base_expenses_y = float(base_living_expenses) * ((1 + expense_growth / 100.0) ** y)

    # Push-hard adjustments
    extra_income_y = float(push_extra_income) if (push_hard and y < push_years) else 0.0
    extra_cost_y = float(push_extra_cost) if (push_hard and y < push_years) else 0.0

    # Frugal adjustments
    if frugal_mode and (frugal_start <= y < frugal_start + frugal_years):
        base_expenses_y *= (1.0 - frugal_expense_reduction_pct / 100.0)

    income_y = base_income_y + extra_income_y
    expenses_y = base_expenses_y + extra_cost_y

    # Student loan payment active after start year and while balance remains
    sl_remaining = student_loan_remaining(y)
    sl_pay_y = student_loan_payment_annual if (y >= student_loan_start_year and sl_remaining > 0) else 0.0

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

        # Purchase event (ONLY for non-existing properties)
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

        # HELOC draw (one-shot)
        if p["heloc_enabled"] and p["heloc_draw_year"] > 0 and y == p["heloc_draw_year"]:
            allowed_total_debt = p["heloc_cltv"] * home_value
            allowed_heloc = max(0.0, allowed_total_debt - mort_bal)
            draw = min(p["heloc_draw_amount"], allowed_heloc)
            if draw > 0:
                stt["heloc_balance"] += draw
                cash += draw
                heloc_drawn_total += draw

        # Rent starts at rent_start_year and can grow
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

        # Liquidation (end of year)
        if p["liquidation_year"] > 0 and y == p["liquidation_year"]:
            net_proceeds = max(0.0, home_value - mort_bal - stt["heloc_balance"])
            cash += net_proceeds
            stt["active"] = False
            liquidated_props += 1

    net_cash_flow_y = income_y - expenses_y - sl_pay_y + rental_cf_y
    if reinvest_surplus:
        cash += net_cash_flow_y

    # Net worth: Cash + Equity - Student loans remaining
    net_worth = cash + total_equity - sl_remaining

    status = "🟢 Sustainable" if net_cash_flow_y >= 30000 else ("🟡 Tight buffer" if net_cash_flow_y >= 10000 else "🔴 At risk")

    rows.append({
        "Year": y,
        "Cody Income": round(cody_income_y, 2),
        "Lauren Income": round(lauren_income_y, 2),
        "Other Income": round(other_income_y, 2),
        "Income (Total)": round(income_y, 2),
        "Expenses": round(expenses_y, 2),

        "Student Loan Pay": round(sl_pay_y, 2),
        "Student Loan Remaining": round(sl_remaining, 2),

        "Rental Cash Flow": round(rental_cf_y, 2),
        "Net Cash Flow": round(net_cash_flow_y, 2),

        "Investable Cash": round(cash, 2),
        "Total Property Value (active)": round(total_property_value, 2),
        "Total Equity (active)": round(total_equity, 2),
        "HELOC Outstanding": round(total_heloc, 2),

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

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Final Net Worth", f"${df.loc[df.index[-1], 'Net Worth']:,.0f}")
m2.metric("Final Net Cash Flow", f"${df.loc[df.index[-1], 'Net Cash Flow']:,.0f}")
m3.metric("Final Active Properties", f"{df.loc[df.index[-1], 'Active Properties']}")
m4.metric("Final Investable Cash", f"${df.loc[df.index[-1], 'Investable Cash']:,.0f}")
m5.metric("Final Equity (active)", f"${df.loc[df.index[-1], 'Total Equity (active)']:,.0f}")

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
ax2.set_title("Net Worth Over Time (Cash + Equity - Student Loans)")
st.pyplot(fig2)

# Income breakdown chart
fig3, ax3 = plt.subplots()
ax3.plot(df["Year"], df["Cody Income"], linewidth=2)
ax3.plot(df["Year"], df["Lauren Income"], linewidth=2)
ax3.plot(df["Year"], df["Other Income"], linewidth=2)
ax3.set_xlabel("Year")
ax3.set_ylabel("Dollars")
ax3.set_title("Income Breakdown Over Time")
ax3.legend(["Cody", "Lauren", "Other"])
st.pyplot(fig3)

# Active properties chart
fig4, ax4 = plt.subplots()
ax4.plot(df["Year"], df["Active Properties"], linewidth=2)
ax4.set_xlabel("Year")
ax4.set_ylabel("Count")
ax4.set_title("Active Properties Over Time")
st.pyplot(fig4)

# Cash vs equity chart
fig5, ax5 = plt.subplots()
ax5.plot(df["Year"], df["Investable Cash"], linewidth=2)
ax5.plot(df["Year"], df["Total Equity (active)"], linewidth=2)
ax5.set_xlabel("Year")
ax5.set_ylabel("Dollars")
ax5.set_title("Cash vs Equity (Active Properties)")
ax5.legend(["Investable Cash", "Total Equity"])
st.pyplot(fig5)

st.dataframe(df, use_container_width=True)

with st.expander("Notes / simplifications"):
    st.markdown(
        f"""
- **Baseline updates applied**:
  - Lauren income default = **$75,000**
  - Student loan starting balance default = **$232,000**
  - Student loan aggregate interest rate default = **6.8%**
  - Cody income growth default = **0.0%**
  - Lauren income growth default = **2.0%**
- **Student loans** are modeled as a single amortizing loan (aggregate) starting in the chosen year.
- **Net Worth** = Cash + Property Equity − Student Loan Remaining.
- **HELOC**: one draw event per property (for now), capped by CLTV; interest charged annually.
- **Liquidation**: no selling costs/taxes modeled yet.
        """
    )
