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

- # Rasch CAT App

A web-based **Rasch Computerized Adaptive Testing (CAT)** application developed for the **2024 Emergency Medicine Specialist Physician Examination in Taiwan (2024 ERCAT)**.  
This project demonstrates how a functional Rasch-CAT app can be developed rapidly using a **Large Language Model (LLM)-assisted workflow**, and deployed online through **Google App Engine (GAE)**.

---

## Overview

Computerized adaptive testing (CAT) tailors item selection to an examinee’s estimated ability, thereby improving measurement efficiency and reducing testing burden. This repository provides a practical implementation of a **Rasch-based CAT app** built with **Flask**, using a **replay bundle (RB)** generated from Rasch analysis.

The app supports:

- loading a Rasch-CAT item bank from a replay bundle
- administering CAT through a web interface
- updating ability estimates after each response using **Expected A Posteriori (EAP)** estimation with a normal prior
- applying stopping rules based on **standard error (SE)** or maximum item count
- presenting results on a **KIDMAP dashboard** with fit statistics
- deployment to **Google App Engine (GAE)**

This project uses the **2024 Emergency Medicine Specialist Physician Examination in Taiwan** as an example application.

---

## Features

- **Rasch CAT engine**
  - adaptive item selection
  - iterative theta and SE updating
  - stopping rules for efficient testing

- **Web-based delivery**
  - Flask-based interface
  - browser-based test administration
  - simple deployment to cloud hosting

- **Result reporting**
  - final ability estimate
  - response history
  - Rasch KIDMAP dashboard
  - fit plots for interpretation

- **Cloud deployment**
  - ready for deployment with `app.yaml`
  - compatible with **Google App Engine**

---

## Workflow

The app follows four major stages:

1. **Build the Rasch CAT app**
   - prepare the item bank and replay bundle
   - implement the Flask-based app
   - load the Rasch-CAT item bank, routes, and app settings

2. **Run CAT**
   - start the test from a web interface
   - select items sequentially
   - record responses
   - update ability estimate (theta) and SE after each item using **EAP**
   - continue until stopping criteria are met

3. **Show results**
   - final ability estimate
   - response history
   - KIDMAP dashboard with fit statistics and plots

4. **Deploy to GAE**
   - prepare `app.py`, `requirements.txt`, and `app.yaml`
   - deploy using `gcloud app deploy`
   - access the app through a public web URL

---

## Repository Structure

A typical project structure is shown below:

```text
RaschCAT/
├─ app.py
├─ app.yaml
├─ requirements.txt
├─ README.md
├─ static/
├─ templates/
├─ replay_bundle/
│  ├─ metadata.json
│  ├─ item_estimates.csv
│  ├─ person_estimates.csv
│  ├─ fixed_item_delta.csv
│  ├─ response_category.csv
│  └─ pic/
└─ docs/
- Next item = maximum Fisher information at current theta
- Theta update = EAP on a fixed grid with normal prior from person estimates
- Stops when posterior SE <= requested threshold or max items reached

## Notes
- The parser tries to split options from Chinese exam text like `（A）...（B）...`.
- If option parsing is imperfect, the full item text is still shown and the user can choose A/B/C/D/E.
