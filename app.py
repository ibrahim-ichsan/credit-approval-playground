import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from google import genai


ROOT = Path(__file__).resolve().parent
# Works whether .env is inside this project or one folder above it during class.
load_dotenv(ROOT / ".env")
load_dotenv(ROOT.parent / ".env")

MODEL_CANDIDATES = ["models/gemini-3.6-flash", "models/gemini-3.5-flash-lite"]


def monthly_payment(principal: float, annual_rate: float, term_months: int) -> float:
    """Return the monthly annuity payment for an illustrative loan."""
    monthly_rate = annual_rate / 12
    if monthly_rate == 0:
        return principal / term_months
    return principal * monthly_rate * (1 + monthly_rate) ** term_months / (
        (1 + monthly_rate) ** term_months - 1
    )


def policy_outcome(dsr: float, deposit_ratio: float, employment: str) -> tuple[str, str, int]:
    """Return a transparent illustrative policy result; this is not real lending logic."""
    employment_adjustment = {
        "Permanent employment": 8,
        "Contract employment": 2,
        "Self-employed": 0,
        "Student / other": -9,
    }[employment]
    score = max(15, min(95, round(92 - dsr * 75 + deposit_ratio * 12 + employment_adjustment)))

    if dsr <= 0.42 and score >= 65:
        return "Ready for a review", "green", score
    if dsr <= 0.55 and score >= 48:
        return "Let's review your plan", "orange", score
    return "Try a different structure", "red", score


@st.cache_resource
def get_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is missing. Add it to .env and restart Streamlit.")
    return genai.Client(api_key=api_key)


def explain_with_gemini(price, deposit, term, payment, dsr, outcome):
    """Ask Gemini to explain deterministic results in plain English only."""
    prompt = f"""
You are a careful financial-education assistant. Explain this illustrative vehicle-finance
calculator result in plain English in 3 short bullet points. Do not claim approval, do not
give financial advice, and do not invent any new figures.

Vehicle price: EUR {price:,.0f}
Deposit: EUR {deposit:,.0f}
Term: {term} months
Estimated monthly payment: EUR {payment:,.0f}
Debt-service ratio: {dsr:.0%}
Illustrative policy outcome: {outcome}
"""
    client = get_gemini_client()
    last_error = None
    for model in MODEL_CANDIDATES:
        try:
            return client.models.generate_content(model=model, contents=prompt).text
        except Exception as error:
            last_error = error
    raise RuntimeError(f"Gemini could not respond: {last_error}")


st.set_page_config(page_title="CreditFlow Playground", page_icon="💳", layout="wide")

st.markdown(
    """
    <style>
      .stApp { background: #f4f8fc; }
      h1, h2, h3 { color: #061d51; }
      .hero { background: linear-gradient(115deg, #061d51, #0a80ec); padding: 2.7rem;
              border-radius: 1.3rem; color: white; margin-bottom: 1.5rem; }
      .hero h1 { color: white; margin: 0; }
      .hero p { color: #d5ecff; max-width: 46rem; }
      .stButton > button { width: 100%; background: #087ff0; color: white; border: 0;
                            border-radius: .6rem; padding: .7rem; font-weight: 700; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
      <p style="letter-spacing: .12em; font-weight: 700; font-size: .75rem;">CREDITFLOW / PLAYGROUND</p>
      <h1>See a credit decision before you apply.</h1>
      <p>Explore a transparent, illustrative affordability result for a vehicle purchase. No real application is submitted.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

left, right = st.columns([1.25, 0.75], gap="large")

with left:
    st.subheader("Tell us about your plan")
    price = st.slider("Vehicle price (€)", min_value=10_000, max_value=80_000, value=28_000, step=500)
    deposit, term = st.columns(2)
    with deposit:
        deposit_value = st.number_input("Deposit (€)", min_value=0, max_value=price, value=min(4_000, price), step=500)
    with term:
        term_months = st.selectbox("Term", [24, 36, 48, 60], index=1, format_func=lambda n: f"{n} months")

    st.divider()
    st.caption("APPLICANT SNAPSHOT · Used only in this browser session")
    income, commitments = st.columns(2)
    with income:
        monthly_income = st.number_input("Monthly income (€)", min_value=0, value=3_200, step=100)
    with commitments:
        monthly_commitments = st.number_input("Monthly commitments (€)", min_value=0, value=450, step=50)
    employment = st.selectbox(
        "Employment status",
        ["Permanent employment", "Contract employment", "Self-employed", "Student / other"],
    )

principal = max(price - deposit_value, 0)
payment = monthly_payment(principal, 0.064, term_months) if principal else 0
dsr = (monthly_commitments + payment) / monthly_income if monthly_income else 1
outcome, outcome_color, score = policy_outcome(dsr, deposit_value / price, employment)

with right:
    st.subheader("Your illustrative offer")
    st.metric("Estimated monthly payment", f"€{payment:,.0f}")
    st.caption("At an illustrative 6.4% effective annual rate")
    st.metric("Amount financed", f"€{principal:,.0f}")
    st.metric("Debt-service ratio", f"{dsr:.0%}")
    st.metric("Illustrative readiness score", f"{score} / 100")
    st.info("Learning tool only. This does not assess credit history, identity, or real eligibility.")

st.divider()
st.subheader(outcome)
if outcome_color == "green":
    st.success("The example monthly payment is within this demo's affordability threshold.")
elif outcome_color == "orange":
    st.warning("The example is close to the demo threshold. A larger deposit or longer term may change the illustration.")
else:
    st.error("The example commitments are above this demo's affordability threshold. Try a lower price, larger deposit, or longer term.")

if st.button("Ask Gemini to explain this result"):
    with st.spinner("Gemini is writing an explanation..."):
        try:
            explanation = explain_with_gemini(price, deposit_value, term_months, payment, dsr, outcome)
            st.markdown(explanation)
        except Exception as error:
            st.error(str(error))
