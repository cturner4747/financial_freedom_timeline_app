import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Financial Freedom Timeline Planner", layout="wide")

st.markdown(
    '''
    <style>
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        h1 {
            text-align: center;
            font-size: 2rem;
            margin-bottom: 1.5rem;
        }
        .stSlider > div {
            padding: 0.5rem 0 !important;
        }
    </style>
    ''',
    unsafe_allow_html=True
)

st.title("📈 20-Year Financial Plan")

# Strategy Toggles
col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    push_hard = st.toggle("Push-Hard Upfront", value=False)
with col2:
    rental_2 = st.toggle("Add Rental #2")
    rental_2_year = st.number_input("Rental #2 Year", value=6, min_value=1, max_value=20) if rental_2 else None
with col3:
    rental_3 = st.toggle("Add Rental #3")
    rental_3_year = st.number_input("Rental #3 Year", value=8, min_value=1, max_value=20) if rental_3 else None

st.markdown("---")

# Income and Debt Inputs
st.subheader("Initial Financial Inputs")
income = st.slider("🎯 Year 0 Primary Income ($)", 0, 300000, 140000, step=1000)
loan = st.slider("💳 Year 1 Student Loan Balance ($)", 0, 1000000, 510000, step=5000)

st.markdown("---")

# Rental and Extra Income
st.subheader("Ongoing Yearly Cash Flow")
rent = st.slider("🏠 Rent for Primary Rental ($/yr)", 0, 60000, 30000, step=1000)
side_income = st.slider("💼 Secondary Income ($/yr)", 0, 100000, 30000, step=1000)

# Timeline simulation
years = np.arange(0, 21)
cash_flow = []
for y in years:
    base = 0
    if y == 0:
        base += income
    if y == 1:
        base -= loan / 20
    if y >= 2:
        base += rent + side_income
    if rental_2 and y >= rental_2_year:
        base += 24000
    if rental_3 and y >= rental_3_year:
        base += 30000
    if push_hard and y < 2:
        base -= 15000
    cash_flow.append(base)

# Plotting
fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(years, cash_flow, color='green', linewidth=2)
ax.axhline(y=10000, color='orange', linestyle='--')
ax.axhline(y=0, color='red', linestyle='--')
ax.set_xlabel("Year")
ax.set_ylabel("Annual Cash Flow")
ax.set_title("Projected Annual Cash Flow")
ax.grid(True)
ax.legend(["Sustainable", "Tight Buffer", "At Risk"])

st.pyplot(fig)

# Summary
final_cash = cash_flow[-1]
if final_cash >= 30000:
    st.success("🟢 Financial plan looks sustainable.")
elif final_cash >= 10000:
    st.warning("🟡 Tight buffer — consider adjusting inputs.")
else:
    st.error("🔴 Risk of cash flow shortfall detected.")
