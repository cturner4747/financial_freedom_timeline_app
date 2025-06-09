import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Financial Freedom Timeline Planner", layout="wide")

st.title("20-Year Financial Plan")

# Sidebar toggles
push_hard = st.checkbox("Push-Hard Upfront")
rental_2 = st.checkbox("Consider Rental #2 in Year:")
rental_2_year = st.number_input(" ", value=6, min_value=1, max_value=20) if rental_2 else None
rental_3 = st.checkbox("Explore Rental #3 Later in Year:")
rental_3_year = st.number_input("  ", value=8, min_value=1, max_value=20) if rental_3 else None

# Simulated inputs per year
years = np.arange(0, 21)
primary_income = st.slider("Year 0  Primary income", 0, 300000, 140000, step=1000)
student_loan = st.slider("Year 1  Student loan balance", 0, 1000000, 510000, step=1000)
rent_primary = st.slider("Year 2  Rent for Primary Rental", 0, 60000, 30000, step=1000)
secondary_income = st.slider("Year 2  Secondary income", 0, 100000, 30000, step=1000)

# Generate simulated cash flow (basic logic)
cash_flow = []
for y in years:
    base = 0
    if y == 0:
        base += primary_income
    if y == 1:
        base -= student_loan / 20
    if y >= 2:
        base += rent_primary + secondary_income
    if rental_2 and y >= rental_2_year:
        base += 24000
    if rental_3 and y >= rental_3_year:
        base += 30000
    if push_hard and y < 2:
        base -= 15000  # simulated push-hard grind cost
    cash_flow.append(base)

# Determine color zones
risk_colors = []
for val in cash_flow:
    if val >= 30000:
        risk_colors.append("ð¢ Sustainable")
    elif val >= 10000:
        risk_colors.append("ð¡ Tight buffer")
    else:
        risk_colors.append("ð´ At risk")

# Plot
fig, ax = plt.subplots()
ax.plot(years, cash_flow, color='green', linewidth=2)
ax.axhline(y=10000, color='yellow', linestyle='--')
ax.axhline(y=0, color='red', linestyle='--')
ax.set_xlabel("Year")
ax.set_ylabel("Annual Cash Flow")
ax.set_title("Cash Flow Over 20 Years")

# Legend
plt.legend(["Sustainable", "Tight buffer", "At risk"])
st.pyplot(fig)
