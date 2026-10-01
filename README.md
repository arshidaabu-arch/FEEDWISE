# SmartFeed AI — SIH Prototype

A local Flask prototype for cattle-feed inspection. It supports image upload or webcam capture, optional protein/moisture entries, a transparent demo visual heuristic, recommendations, and SQLite inspection history.

## Important limitations
- The current image analyser is a **demo heuristic**, not a trained AI model. It only flags coarse visual colour/texture patterns that may resemble mould.
- It does not identify fungal species, measure protein/moisture, or detect mycotoxins.
- Protein and moisture values are entered by the user and should come from appropriate instruments/laboratory tests.
- Do not use this prototype to decide whether feed is safe to feed to cattle. Confirm concerns through qualified veterinary/feed laboratory testing.

## Run in VS Code (Windows)
1. Install Python 3.10–3.12 and VS Code.
2. Extract the ZIP, then open the `SmartFeed_AI_Prototype` folder in VS Code.
3. Open Terminal → New Terminal.
4. Create a virtual environment:
   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
   If PowerShell blocks activation, run:
   ```powershell
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   .\.venv\Scripts\Activate.ps1
   ```
5. Install dependencies:
   ```powershell
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```
6. Start the app:
   ```powershell
   python app.py
   ```
7. Open `http://127.0.0.1:5000` in Chrome or Edge. Allow camera permission if using webcam.

The database (`smartfeed.db`) and uploaded images are created automatically.

## Replace demo heuristic with a trained model
Train and validate a classifier on representative feed images with expert-labelled classes. Keep a separate `analyze_image()` interface in `analyzer.py` and load your saved model there. Report dataset, validation metrics, and uncertainty. Do not call the output a confirmed fungal or mycotoxin diagnosis.
