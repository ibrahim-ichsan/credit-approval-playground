# Credit Approval Playground

An educational Streamlit prototype for an illustrative vehicle-finance affordability result. It is not a real credit score, lending decision, or financial advice.

## Run locally

1. Create a `.env` file beside `app.py`:

   ```env
   GEMINI_API_KEY=your-key
   ```

2. Create and activate a virtual environment:

   ```powershell
   py -m venv .venv
   .venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

3. Start the app:

   ```powershell
   streamlit run app.py
   ```

## Design rule

The calculation and policy outcome are deterministic Python code. Gemini is used only to explain those already-computed results in plain language.
