# Rasch CAT App

A small Flask app that builds a Rasch CAT from `replay_bundle.zip`.

## Uses
- `response_category.csv`: item text and answer key
- `fixed_item_delta.csv`: item difficulties
- `person_estimates.csv`: prior mean and prior SD for EAP

## Run
```bash
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000`

## CAT logic
- Dichotomous Rasch scoring (`correct=1`, `incorrect=0`)
- Next item = maximum Fisher information at current theta
- Theta update = EAP on a fixed grid with normal prior from person estimates
- Stops when posterior SE <= requested threshold or max items reached

## Notes
- The parser tries to split options from Chinese exam text like `（A）...（B）...`.
- If option parsing is imperfect, the full item text is still shown and the user can choose A/B/C/D/E.
