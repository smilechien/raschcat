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


Data Source

This project uses:

200 questions and answers from the 2024 Emergency Medicine Specialist Physician Examination in Taiwan

item difficulties estimated using ChatGPT 5.4 Thinking

simulated response data for 1,000 persons × 200 items

a replay bundle generated from RaschOnline

Methods Summary

Item source: 2024 ERCAT questions and answers

Difficulty estimation: prompts submitted to ChatGPT 5.4 Thinking

Response generation: Rasch simulation

CAT engine: EAP updating with a normal prior

Stopping rules: target SE and/or maximum number of items

Output: ability estimate, fit indices, KIDMAP dashboard

Requirements

Python 3.10+

Flask

NumPy

Pandas

Matplotlib

Gunicorn (for deployment)

Google Cloud SDK (for GAE deployment)

Install dependencies with:

pip install -r requirements.txt
Run Locally

Clone the repository:

git clone https://github.com/your-username/RaschCAT.git
cd RaschCAT

Install dependencies:

pip install -r requirements.txt

Run the app locally:

python app.py

Then open your browser and visit:

http://127.0.0.1:5000

If your local configuration uses a different port or entry point, adjust accordingly.

Deploy to Google App Engine

Make sure the Google Cloud SDK is installed and initialized.

1. Initialize Google Cloud
gcloud init
2. Set your project
gcloud config set project YOUR_PROJECT_ID
3. Deploy the app
gcloud app deploy
4. Open the deployed app
gcloud app browse
How CAT Works in This App

The app loads the replay bundle and item bank

The examinee starts the test

One item is presented at a time

The response is scored

Ability (theta) and SE are updated using Expected A Posteriori (EAP) estimation

The next item is selected adaptively

The process stops when the target precision or maximum item count is reached

Results are displayed on the dashboard

Output

The app provides:

final ability estimate (theta)

standard error (SE)

response history

item path used during CAT

KIDMAP display

fit indices such as INFIT and OUTFIT

Example Use Case

This repository demonstrates the development of a Rasch-CAT app for the:

2024 Emergency Medicine Specialist Physician Examination in Taiwan

The project serves as a proof of concept showing that a web-based Rasch-CAT system can be developed rapidly and deployed online using an LLM-assisted workflow.

Limitations

This repository should be interpreted as a proof of concept.

Item difficulties were estimated through LLM prompting rather than empirical calibration from real examinee data.

Response data were generated through Rasch simulation.

The example focuses on one specialist examination in emergency medicine.

Further validation with real candidates is needed before operational use in high-stakes testing.

Citation

If you use this repository, please cite the associated study:

Chien, T.-W. (2026). A Rasch CAT App for the 2024 Emergency Medicine Specialist Physician Examination in Taiwan.

You may also cite the repository as:

Chien, T.-W. (2026). RaschCAT [Computer software]. GitHub. https://github.com/your-username/RaschCAT
References

Chen, K.-L., Huang, C.-Y., Chen, C.-T., Chow, J. C., & Chou, W. (2021). Development of the computerized adaptive test of motor development (MD-CAT) adopting multidimensional Rasch analysis. Archives of Physical Medicine and Rehabilitation, 102(11), 2185–2192.e2. https://doi.org/10.1016/j.apmr.2021.06.007

Chien, T.-W., Lai, W.-P., Lu, C.-W., Wang, W.-C., Chen, S.-C., Wang, H.-Y., & Su, S.-B. (2011). Web-based computer adaptive assessment of individual perceptions of job satisfaction for hospital workplace employees. BMC Medical Research Methodology, 11, 47. https://doi.org/10.1186/1471-2288-11-47

Gershon, R. C. (2005). Computer adaptive testing. Journal of Applied Measurement, 6(1), 109–127.

Linacre, J. M. (2007). A user’s guide to Winsteps/Ministep Rasch-model computer programs. Winsteps.com.

Ma, S.-C., Chou, W., Chien, T.-W., Chow, J. C., Yeh, Y.-T., Chou, P.-H., & Lee, H.-F. (2020). An app for detecting bullying of nurses using convolutional neural networks and web-based computerized adaptive testing: Development and usability study. JMIR mHealth and uHealth, 8(5), e16747. https://doi.org/10.2196/16747

Masters, G. N. (1994). Rasch KIDMAP: A history. Rasch Measurement Transactions, 8(2), 366.

OpenAI. (2026). Introducing GPT-5.4. OpenAI. https://openai.com/

Seo, D. G., & Choi, J. (2018). Post-hoc simulation study of computerized adaptive testing for the Korean Medical Licensing Examination. Journal of Educational Evaluation for Health Professions, 15, 14. https://doi.org/10.3352/jeehp.2018.15.14

Xu, L., Jiang, Z., Han, Y., Liang, H., & Ouyang, J. (2023). Developing computerized adaptive testing for a national health professionals exam: An attempt from psychometric simulations. Perspectives on Medical Education, 12(1), 462–471. https://doi.org/10.5334/pme.855

License

Specify your license here, for example:

MIT License

or

Apache License 2.0
Acknowledgments

This project was developed as an example of rapid Rasch-CAT app development using an LLM-assisted workflow, integrating psychometric modeling, simulation, replay bundle generation, and cloud deployment.



- The parser tries to split options from Chinese exam text like `（A）...（B）...`.
- If option parsing is imperfect, the full item text is still shown and the user can choose A/B/C/D/E.
