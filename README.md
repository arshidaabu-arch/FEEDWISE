# SmartFeed AI — Streamlit version

## Deploy on Streamlit Community Cloud
1. Upload these files to the root of a GitHub repository.
2. In Streamlit Community Cloud, deploy the repository.
3. Set **Main file path** to `app.py`.
4. Streamlit installs packages from `requirements.txt` and runs the app.

## Run locally
```bash
python -m venv .venv
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```
Open the local URL printed in the terminal.

## Limitations
The visual screen is a simple colour heuristic, not a trained fungal classifier. Protein and moisture are manual entries. The app cannot identify fungal species, detect or quantify mycotoxins, or certify feed safety. Use appropriate validated instruments and laboratory tests.
