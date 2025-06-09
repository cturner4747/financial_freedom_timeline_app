
import streamlit as st

st.set_page_config(page_title="HELOC Decision Tool", layout="centered")

st.title("🏠 HELOC vs. Mortgage Tool")
st.markdown("Use this tool to compare your monthly cash flow and equity outcomes when using a HELOC vs. increasing your mortgage.")

# Input sliders
mortgage_amount = st.slider("New Mortgage Loan Amount ($)", 480000, 540000, 510000, step=5000)
heloc_amount = st.slider("HELOC Used for Construction ($)", 0, 40000, 20000, step=5000)
heloc_interest = st.slider("HELOC Interest Rate (%)", 3.0, 10.0, 7.5, step=0.1)
mortgage_rate = st.slider("Mortgage Rate (%)", 5.0, 8.0, 6.5, step=0.1)
monthly_rent_surplus = st.slider("Monthly Rental Surplus Applied to HELOC ($)", 0, 1000, 700, step=50)
lump_sum_payment = st.slider("One-Time HELOC Lump Sum Payment ($)", 0, 40000, 0, step=5000)

# Calculations
monthly_heloc_interest = (heloc_amount * (heloc_interest / 100)) / 12
monthly_mortgage_payment = (mortgage_amount * (mortgage_rate / 100)) / 12
months_to_payoff_heloc = (heloc_amount - lump_sum_payment) / max(monthly_rent_surplus - monthly_heloc_interest, 1)

# Display results
st.subheader("💵 Monthly Payment Comparison")
st.markdown(f"**Mortgage Monthly Payment:** ${monthly_mortgage_payment:,.2f}")
st.markdown(f"**HELOC Interest-Only Payment (approx):** ${monthly_heloc_interest:,.2f}")
st.markdown(f"**Estimated Time to Pay Off HELOC:** {months_to_payoff_heloc:.1f} months")

st.subheader("📈 Strategy Summary")
st.markdown(f"- Total Loan Exposure: **${mortgage_amount + heloc_amount:,.0f}**")
st.markdown(f"- Rental Income Contribution: **${monthly_rent_surplus:,.0f}/mo** toward HELOC")
st.markdown(f"- Lump Sum Applied: **${lump_sum_payment:,.0f}**")
st.markdown(f"- Estimated Full Payoff Timeline: **{months_to_payoff_heloc:.1f} months**")

st.info("💡 Use this to decide whether a HELOC + lower mortgage combo improves your flexibility and short-term cash flow.")
