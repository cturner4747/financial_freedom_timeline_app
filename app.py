# (Truncated header and other sections for brevity — these remain unchanged)
# Assume everything up to RENTAL INPUTS is unchanged

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

# --- RENTAL ADJUSTMENTS ---
st.header("🔧 Rental Property Adjustments")
vacancy_pct = st.slider("Vacancy + Maintenance Loss (%)", 0.0, 30.0, 15.0)

# --- (Expenses, Retirement, Student Loan, Push-Hard Toggle, etc. remain unchanged)

# --- SIMULATION LOOP ---
# All earlier setup code remains unchanged

for y in years:
    # --- Income with raises ---
    cody_inc = cody_primary * ((1 + cody_raise_pct / 100) ** (y - 1)) if cody_raise_on else cody_primary
    cody_sec_inc = cody_secondary * ((1 + cody_secondary_raise_pct / 100) ** (y - 1)) if cody_secondary_raise_on else cody_secondary
    lauren_inc = lauren_primary * ((1 + lauren_raise_pct / 100) ** (y - 1)) if lauren_raise_on else lauren_primary
    lauren_sec_inc = lauren_secondary * ((1 + lauren_secondary_raise_pct / 100) ** (y - 1)) if lauren_secondary_raise_on else lauren_secondary

    income = (
        cody_inc + lauren_inc +
        cody_sec_inc + lauren_sec_inc +
        push_income_boost * (1 if y <= 2 else 0)
    )

    if income_drop:
        income *= 0.9

    # --- Rental ---
    rental_income = 0
    if y >= rental1_start:
        net_rent1 = rental1_monthly_net * 12 * (1 - vacancy_pct / 100)
        rental_income += net_rent1
        rental1_equity += net_rent1 * 0.3
    if rental2_on and y >= rental2_start:
        net_rent2 = rental2_monthly_net * 12 * (1 - vacancy_pct / 100)
        rental_income += net_rent2
        rental2_equity += net_rent2 * 0.3

    # --- Expenses ---
    exp_infl = expense_inflation + (5 if stress_test else 0)
    expenses = base_expenses * ((1 + exp_infl / 100) ** (y - 1))

    # --- Debt Payments ---
    mortg = mortgage_payment * 12 if y >= mortgage_start_year else 0
    heloc_pay = heloc_annual_payment if (heloc_used > 0 and y >= heloc_start_year and y < heloc_start_year + heloc_term) else 0

    # --- Student Loan ---
    sl_pay = student_loan_payment * 12 if (not forgiveness_toggle or y < forgiveness_year) and student_loan_bal > 0 else 0
    student_loan_interest = student_loan_bal * student_loan_rate / 100 if student_loan_bal > 0 else 0
    student_loan_bal = max(0, student_loan_bal + student_loan_interest - sl_pay)
    if forgiveness_toggle and y == forgiveness_year:
        student_loan_bal = 0

    # --- Retirement ---
    retirement = retirement * (1 + retirement_growth / 100) + retirement_contribution

    # --- Equity Tracking ---
    home_equity = min(home_value, home_equity + mortg)
    rental1_equity *= (1 + rental1_appreciation / 100)
    rental2_equity *= (1 + rental2_appreciation / 100) if rental2_on else 0

    # --- Cash Flow ---
    net = income + rental_income - expenses - mortg - heloc_pay - sl_pay
    savings += max(net, 0)
    net_worth = savings + home_equity + rental1_equity + rental2_equity + retirement - student_loan_bal

    # --- Risk Flags ---
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

    # --- Collect Results ---
    cash_flows.append(net)
    cumulative_savings.append(savings)
    retirement_balances.append(retirement)
    home_equities.append(home_equity)
    rental_equities.append(rental1_equity + rental2_equity)
    networths.append(net_worth)
    risk_flags.append(risk)
    advice_list.append(advice)

# --- Output remains unchanged (DataFrame, Charts, Summary)


