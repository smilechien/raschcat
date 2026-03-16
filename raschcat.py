from __future__ import annotations

import html
import io
import json
import math
import os
import re
import zipfile
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from flask import Flask, abort, redirect, render_template_string, request, send_from_directory, session, url_for

APP_TITLE = "Rasch CAT App of Specialist Physician Test for Emergency Medical Doctor (2024) in Taiwan"
DEFAULT_BUNDLE = Path(__file__).with_name("replay_bundle.zip")
SECRET_KEY = os.environ.get("CAT_SECRET_KEY", "rasch-cat-demo-secret")
IMG_EXTS = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg")
OPTION_LABELS = ["A", "B", "C", "D", "E", "F", "G"]

README_FALLBACK = """# Rasch CAT App\n\nThis app reads `response_category.csv` with columns `key, no, link, item, item2`.\n\n- `item` = Chinese item text\n- `item2` = English item text\n- `link` = optional figure / picture / graph path or URL\n- If `link` is a local PNG or image file name, place the file under `pic/`\n- You can store images either inside `replay_bundle.zip` under `pic/` or beside `app.py` in a local `pic/` folder\n\nModes:\n1. CAT mode selects the next item by maximum Rasch information\n2. non-CAT mode presents all items in fixed item-number order like a traditional test\n\nThe examinee view does not show the hidden answer key or per-item score.\n"""

LABELS = {
    "en": {
        "home_title": APP_TITLE,
        "home_intro": "This app uses replay_bundle.zip as the item bank.",
        "choose_language": "Language",
        "lang_zh": "Chinese",
        "lang_en": "English",
        "choose_mode": "Test mode",
        "mode_cat": "CAT",
        "mode_linear": "non-CAT",
        "start_test": "Start test",
        "start_cat": "Start CAT",
        "start_linear": "Start non-CAT",
        "max_items": "Maximum CAT items",
        "stop_se": "Stop CAT when SE ≤",
        "start_theta": "Starting theta",
        "readme": "README",
        "works": "How the test works",
        "sel_info_cat": "Selected by maximum information from the remaining items.",
        "sel_info_linear": "Presented in fixed item-number order so every item can be reviewed.",
        "figure_ref": "Figure / graph reference",
        "open_ref": "Open reference link",
        "submit": "Submit answer",
        "responses": "Response history",
        "new_test": "Start over",
        "final_theta": "Final theta",
        "post_se": "Posterior SE",
        "percentile": "Percentile",
        "items_used": "Items used",
        "reason": "Reason",
        "answer_hidden": "The answer key and per-item score are hidden from the examinee view.",
        "item": "Item",
        "difficulty": "Difficulty",
        "your_answer": "Your answer",
        "theta_after": "Theta after item",
        "se_after": "SE after item",
        "reference": "Reference",
        "open": "Open",
        "question": "Question",
        "home_loaded": "Loaded bundle",
        "home_summary_items": "Items",
        "home_summary_mean": "Person prior mean",
        "home_summary_sd": "Prior SD",
        "structure": "Expected response_category.csv structure",
        "columns": "Columns",
        "kidmap": "KIDMAP dashboard",
        "person_fit": "Person fit",
        "infit_mnsq": "INFIT MNSQ",
        "outfit_mnsq": "OUTFIT MNSQ",
        "item_fit": "Bank item fit",
        "answered_items": "Answered items",
        "mode": "Mode",
        "mode_cat_short": "CAT",
        "mode_linear_short": "non-CAT",
        "home_note": "In non-CAT mode, all items are shown in fixed order and every figure linked in response_category.csv can be checked on the test screen if the file exists.",
    },
    "zh": {
        "home_title": APP_TITLE,
        "home_intro": "本系統使用 replay_bundle.zip 作為題庫。",
        "choose_language": "作答語言",
        "lang_zh": "中文",
        "lang_en": "英文",
        "choose_mode": "測驗模式",
        "mode_cat": "CAT 自適應測驗",
        "mode_linear": "non-CAT 傳統逐題測驗",
        "start_test": "開始測驗",
        "start_cat": "開始 CAT",
        "start_linear": "開始 non-CAT",
        "max_items": "CAT 最多題數",
        "stop_se": "CAT 當 SE ≤ 時停止",
        "start_theta": "起始能力值 theta",
        "readme": "說明",
        "works": "測驗流程",
        "sel_info_cat": "下一題依目前 theta 的最大資訊量選取。",
        "sel_info_linear": "依題號固定順序逐題呈現，可逐題檢查圖片是否正確顯示。",
        "figure_ref": "圖表／圖片參考",
        "open_ref": "開啟參考連結",
        "submit": "送出答案",
        "responses": "作答紀錄",
        "new_test": "重新測驗",
        "final_theta": "最終 theta",
        "post_se": "後驗 SE",
        "percentile": "百分等級",
        "items_used": "已作答題數",
        "reason": "停止原因",
        "answer_hidden": "考生頁面不顯示標準答案與逐題得分。",
        "item": "題目",
        "difficulty": "難度",
        "your_answer": "你的答案",
        "theta_after": "作答後 theta",
        "se_after": "作答後 SE",
        "reference": "參考圖",
        "open": "開啟",
        "question": "題目",
        "home_loaded": "已載入題庫",
        "home_summary_items": "題數",
        "home_summary_mean": "受試者先驗平均",
        "home_summary_sd": "先驗標準差",
        "structure": "response_category.csv 欄位結構",
        "columns": "欄位",
        "kidmap": "KIDMAP 儀表板",
        "person_fit": "個人配適統計",
        "infit_mnsq": "INFIT MNSQ",
        "outfit_mnsq": "OUTFIT MNSQ",
        "item_fit": "題庫試題配適",
        "answered_items": "已作答題目",
        "mode": "模式",
        "mode_cat_short": "CAT",
        "mode_linear_short": "non-CAT",
        "home_note": "在 non-CAT 模式下，題目會依固定題號順序全部呈現；只要 response_category.csv 的 link 能對到實際檔案，每題的圖片都會在作答頁顯示。",
    },
}

HOME_TMPL = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{{ title }}</title>
  <style>
    body { font-family: Arial, sans-serif; max-width: 1100px; margin: 24px auto; padding: 0 16px; line-height: 1.55; }
    .card { border: 1px solid #ddd; border-radius: 12px; padding: 18px; margin-bottom: 18px; }
    .muted { color: #555; }
    .btn { display: inline-block; background: #2563eb; color: white; padding: 10px 16px; border-radius: 8px; text-decoration: none; border: 0; cursor: pointer; }
    code { background: #f4f4f4; padding: 2px 6px; border-radius: 6px; }
    .inline-fields label { display: inline-block; margin-right: 16px; margin-bottom: 10px; }
    pre { white-space: pre-wrap; word-break: break-word; background: #fafafa; padding: 12px; border-radius: 10px; border: 1px solid #eee; }
    table { border-collapse: collapse; width: 100%; }
    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; vertical-align: top; }
    .modebox { display: inline-block; margin-right: 18px; margin-bottom: 10px; }
    .small { font-size: 0.94rem; }
  </style>
</head>
<body>
  <h1>{{ labels.home_title }}</h1>
  <div class="card">
    <p>{{ labels.home_intro }}</p>
    <ul>
      <li><code>response_category.csv</code> → <code>key, no, link, item, item2</code></li>
      <li><code>fixed_item_delta.csv</code> → Rasch item difficulty</li>
      <li><code>person_estimates.csv</code> → prior mean and SD</li>
      <li><code>pic/</code> → optional local figures for the <code>link</code> column</li>
    </ul>
    <p class="muted">{{ labels.home_loaded }}: <strong>{{ bundle_name }}</strong></p>
    <p class="muted">{{ labels.home_summary_items }}: <strong>{{ summary.n_items }}</strong> | {{ labels.home_summary_mean }}: <strong>{{ '%.3f'|format(summary.prior_mean) }}</strong> | {{ labels.home_summary_sd }}: <strong>{{ '%.3f'|format(summary.prior_sd) }}</strong></p>
    <form method="post" action="{{ url_for('start_test') }}">
      <div class="inline-fields">
        <label>{{ labels.choose_language }}
          <select name="language">
            <option value="zh">{{ labels.lang_zh }}</option>
            <option value="en">{{ labels.lang_en }}</option>
          </select>
        </label>
      </div>
      <div class="inline-fields">
        <label>{{ labels.max_items }} <input type="number" name="max_items" min="5" max="60" value="20"></label>
        <label>{{ labels.stop_se }} <input type="number" step="0.01" name="stop_se" min="0.15" max="1.00" value="0.32"></label>
        <label>{{ labels.start_theta }} <input type="number" step="0.01" name="start_theta" value="{{ '%.2f'|format(summary.prior_mean) }}"></label>
      </div>
      <div style="margin-top:14px; display:flex; gap:12px; flex-wrap:wrap;">
        <button class="btn" type="submit" name="mode" value="cat">{{ labels.start_cat }}</button>
        <button class="btn" type="submit" name="mode" value="linear">{{ labels.start_linear }}</button>
      </div>
      <p class="muted small" style="margin-top:10px;">{{ labels.choose_mode }}: <strong>{{ labels.mode_cat }}</strong> / <strong>{{ labels.mode_linear }}</strong></p>
    </form>
    <p class="muted small" style="margin-top:14px;">{{ labels.home_note }}</p>
  </div>

  <div class="card">
    <h2>{{ labels.structure }}</h2>
    <table>
      <thead><tr><th>{{ labels.columns }}</th><th>Description</th></tr></thead>
      <tbody>
        <tr><td><code>key</code></td><td>Hidden correct answer key, such as A/B/C/D.</td></tr>
        <tr><td><code>no</code></td><td>Item number.</td></tr>
        <tr><td><code>link</code></td><td>Optional figure path or URL. Local image files can be placed in <code>pic/</code>.</td></tr>
        <tr><td><code>item</code></td><td>Chinese item text including options.</td></tr>
        <tr><td><code>item2</code></td><td>English item text including options.</td></tr>
      </tbody>
    </table>
  </div>

  <div class="card">
    <h2>{{ labels.works }}</h2>
    <ol>
      <li>Choose Chinese or English before starting.</li>
      <li>Choose CAT or non-CAT mode on the homepage.</li>
      <li>CAT mode selects the remaining item with maximum Rasch information at the current theta.</li>
      <li>non-CAT mode presents all items in ascending item-number order.</li>
      <li>Ability is updated by EAP on a fixed grid with a normal prior.</li>
      <li>The result page shows final theta, SE, percentile, person INFIT/OUTFIT MNSQ, and the KIDMAP dashboard.</li>
    </ol>
    <p class="muted">{{ labels.answer_hidden }}</p>
  </div>

  <div class="card">
    <h2>{{ labels.readme }}</h2>
    <pre>{{ readme_text }}</pre>
  </div>
</body>
</html>
"""

ITEM_TMPL = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{{ title }}</title>
  <style>
    body { font-family: Arial, sans-serif; max-width: 1100px; margin: 24px auto; padding: 0 16px; line-height: 1.6; }
    .card { border: 1px solid #ddd; border-radius: 12px; padding: 18px; margin-bottom: 18px; }
    .muted { color: #555; }
    .btn { display: inline-block; background: #2563eb; color: white; padding: 10px 16px; border-radius: 8px; text-decoration: none; border: 0; cursor: pointer; }
    .stat { display: inline-block; margin-right: 16px; margin-bottom: 10px; padding: 8px 12px; background: #f7f7f7; border-radius: 10px; }
    .option { display: block; padding: 12px 14px; margin: 12px 0; border: 1px solid #ddd; border-radius: 10px; cursor: pointer; }
    .opt-row { display: flex; align-items: flex-start; gap: 10px; }
    .opt-radio { margin-top: 4px; }
    .opt-label { min-width: 1.8em; font-weight: 700; }
    .opt-text { flex: 1; white-space: pre-wrap; word-break: break-word; }
    textarea { width: 100%; height: 280px; }
    .refbox { background: #f8fafc; border: 1px solid #dbeafe; }
    .refimg { max-width: 100%; max-height: 520px; border: 1px solid #ddd; border-radius: 8px; display: block; margin-top: 10px; }
  </style>
</head>
<body>
  <h1>{{ title }}</h1>
  <div class="card">
    <div class="stat">{{ labels.mode }}: {{ mode_name }}</div>
    <div class="stat">{{ labels.item }} {{ progress.answered + 1 }} / {{ progress.max_items }}</div>
    <div class="stat">Theta {{ '%.3f'|format(progress.theta) }}</div>
    <div class="stat">SE {{ '%.3f'|format(progress.se) }}</div>
    <div class="stat">{{ labels.choose_language }}: {{ language_name }}</div>
    <p class="muted">{{ progress.info_line }}</p>
  </div>

  <div class="card">
    <h2>{{ item.item_id }} · {{ labels.question }} {{ item.no }}</h2>
    <p style="white-space: pre-wrap;">{{ item.stem }}</p>
  </div>

  {% if item.link_href %}
  <div class="card refbox">
    <h3>{{ labels.figure_ref }}</h3>
    <p><a href="{{ item.link_href }}" target="_blank" rel="noopener">{{ labels.open_ref }}</a></p>
    {% if item.is_image_link %}
      <img class="refimg" src="{{ item.link_href }}" alt="Reference image for item {{ item.no }}">
    {% endif %}
  </div>
  {% endif %}

  <div class="card">
    <form method="post" action="{{ url_for('submit_answer') }}">
      {% for label, text in item.options.items() %}
      <label class="option">
        <span class="opt-row">
          <input class="opt-radio" type="radio" name="answer" value="{{ label }}" required>
          <span class="opt-label">{{ label }}</span>
          <span class="opt-text">{{ text }}</span>
        </span>
      </label>
      {% endfor %}
      {% if item.options|length == 0 %}
      <p class="muted">Choice parsing was not perfect, so the full item text is shown below. Select the best option label.</p>
      <textarea readonly>{{ item.full_text }}</textarea>
      <div style="margin-top:12px;">
        {% for label in ['A','B','C','D','E'] %}
          <label class="option">
            <span class="opt-row">
              <input class="opt-radio" type="radio" name="answer" value="{{ label }}" required>
              <span class="opt-label">{{ label }}</span>
              <span class="opt-text">Choose {{ label }}</span>
            </span>
          </label>
        {% endfor %}
      </div>
      {% endif %}
      <div style="margin-top:14px;"><button class="btn" type="submit">{{ labels.submit }}</button></div>
    </form>
  </div>
</body>
</html>
"""

RESULT_TMPL = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{{ title }}</title>
  <style>
    body { font-family: Arial, sans-serif; max-width: 1100px; margin: 24px auto; padding: 0 16px; line-height: 1.6; }
    .card { border: 1px solid #ddd; border-radius: 12px; padding: 18px; margin-bottom: 18px; }
    .btn { display: inline-block; background: #2563eb; color: white; padding: 10px 16px; border-radius: 8px; text-decoration: none; border: 0; cursor: pointer; }
    .stat { display: inline-block; margin-right: 16px; margin-bottom: 10px; padding: 10px 12px; background: #f7f7f7; border-radius: 10px; }
    table { border-collapse: collapse; width: 100%; }
    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; vertical-align: top; }
    .muted { color: #555; }
  </style>
</head>
<body>
  <h1>{{ title }}</h1>
  <div class="card">
    <div class="stat">{{ labels.mode }} {{ result.mode_name }}</div>
    <div class="stat">{{ labels.final_theta }} {{ '%.3f'|format(result.theta) }}</div>
    <div class="stat">{{ labels.post_se }} {{ '%.3f'|format(result.se) }}</div>
    <div class="stat">{{ labels.percentile }} {{ '%.1f'|format(result.percentile) }}</div>
    <div class="stat">{{ labels.items_used }} {{ result.n_answered }}</div>
    <div class="stat">{{ labels.reason }} {{ result.stop_reason }}</div>
  </div>
  <div class="card">
    <div class="stat">{{ labels.infit_mnsq }} {{ '%.3f'|format(result.infit_mnsq) }}</div>
    <div class="stat">{{ labels.outfit_mnsq }} {{ '%.3f'|format(result.outfit_mnsq) }}</div>
    <p class="muted">{{ labels.answer_hidden }}</p>
    <p class="muted">CAT commonly targets items near the current theta. When model probabilities stay near 0.5, even random dichotomous answers can leave INFIT/OUTFIT close to 1.0; that is not necessarily a coding error.</p>
    <div style="margin-top:12px;"><a class="btn" href="{{ url_for('index') }}">{{ labels.new_test }}</a></div>
  </div>
  <div class="card">
    <h2>{{ labels.responses }}</h2>
    <table>
      <thead>
        <tr>
          <th>#</th>
          <th>{{ labels.item }}</th>
          <th>{{ labels.difficulty }}</th>
          <th>{{ labels.your_answer }}</th>
          <th>{{ labels.theta_after }}</th>
          <th>{{ labels.se_after }}</th>
          {% if result.has_links %}<th>{{ labels.reference }}</th>{% endif %}
        </tr>
      </thead>
      <tbody>
      {% for row in result.history %}
        <tr>
          <td>{{ loop.index }}</td>
          <td>{{ row.item_id }}</td>
          <td>{{ '%.3f'|format(row.delta) }}</td>
          <td>{{ row.answer }}</td>
          <td>{{ '%.3f'|format(row.theta) }}</td>
          <td>{{ '%.3f'|format(row.se) }}</td>
          {% if result.has_links %}
            <td>{% if row.link_href %}<a href="{{ row.link_href }}" target="_blank" rel="noopener">{{ labels.open }}</a>{% endif %}</td>
          {% endif %}
        </tr>
      {% endfor %}
      </tbody>
    </table>
  </div>

  <div class="card">
    <h2>{{ labels.kidmap }}</h2>
    <div>{{ result.kidmap_svg|safe }}</div>
    <p class="muted">{{ labels.answered_items }}: {{ result.answered_ids|join(', ') }}</p>
  </div>

  <div class="card">
    <h2>{{ labels.item_fit }}</h2>
    <div>{{ result.itemfit_svg|safe }}</div>
  </div>
</body>
</html>
"""


@dataclass
class ItemRecord:
    item_id: str
    no: int
    key: str
    full_text_zh: str
    stem_zh: str
    options_zh: Dict[str, str]
    full_text_en: str
    stem_en: str
    options_en: Dict[str, str]
    delta: float
    link: str = ""

    def text_for(self, language: str) -> Dict[str, object]:
        if language == "en":
            return {
                "full_text": self.full_text_en or self.full_text_zh,
                "stem": self.stem_en or self.stem_zh,
                "options": self.options_en or self.options_zh,
            }
        return {
            "full_text": self.full_text_zh,
            "stem": self.stem_zh,
            "options": self.options_zh,
        }


def _zip_name_map(zf: zipfile.ZipFile) -> Dict[str, str]:
    return {name.lower(): name for name in zf.namelist()}


def _zip_read_bytes(zf: zipfile.ZipFile, wanted_name: str) -> bytes:
    name_map = _zip_name_map(zf)
    hit = name_map.get(wanted_name.lower())
    if not hit:
        raise KeyError(f"{wanted_name} not found in ZIP. Available: {zf.namelist()}")
    return zf.read(hit)


def _read_csv_bytes_robust(raw: bytes, *, csv_name: str = "csv") -> pd.DataFrame:
    encodings = ["utf-8", "utf-8-sig", "cp950", "big5", "gb18030", "latin1"]
    last_err = None
    for enc in encodings:
        try:
            return pd.read_csv(io.BytesIO(raw), encoding=enc)
        except UnicodeDecodeError as e:
            last_err = e
        except pd.errors.ParserError:
            try:
                return pd.read_csv(io.BytesIO(raw), encoding=enc, engine="python")
            except Exception as e:
                last_err = e
        except Exception as e:
            last_err = e
    raise ValueError(f"Unable to read {csv_name}. Tried encodings: {encodings}. Last error: {last_err}")


def _read_text_bytes_robust(raw: bytes, *, text_name: str = "text") -> str:
    encodings = ["utf-8", "utf-8-sig", "cp950", "big5", "gb18030", "latin1"]
    last_err = None
    for enc in encodings:
        try:
            return raw.decode(enc)
        except UnicodeDecodeError as e:
            last_err = e
    raise ValueError(f"Unable to decode {text_name}. Tried encodings: {encodings}. Last error: {last_err}")




def _trapz_compat(y: np.ndarray, x: np.ndarray) -> float:
    if hasattr(np, "trapezoid"):
        return float(np.trapezoid(y, x))
    return float(np.trapz(y, x))


class RaschCATBank:
    def __init__(self, bundle_path: Path) -> None:
        self.bundle_path = bundle_path
        self.extract_dir = Path(os.environ.get("TMPDIR") or tempfile.gettempdir()) / "raschcat_bundle_cache"
        self.local_pic_dir = Path(__file__).with_name("pic")
        self.readme_text = README_FALLBACK
        self.items: List[ItemRecord] = []
        self.item_lookup: Dict[str, ItemRecord] = {}
        self.theta_grid = np.linspace(-6.0, 6.0, 2401)
        self.prior_mean = 0.0
        self.prior_sd = 1.0
        self.person_distribution = np.array([0.0])
        self.person_df = pd.DataFrame()
        self.item_fit_df = pd.DataFrame()
        self._load()

    def _extract_selected_files(self, zf: zipfile.ZipFile) -> None:
        self.extract_dir.mkdir(parents=True, exist_ok=True)
        needed = []
        for name in zf.namelist():
            low = name.lower()
            if low in {"response_category.csv", "fixed_item_delta.csv", "person_estimates.csv", "item_estimates.csv", "metadata.json", "readme.md"} or low.startswith("pic/"):
                needed.append(name)
        for name in needed:
            target = self.extract_dir / name
            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(name) as src, open(target, "wb") as dst:
                dst.write(src.read())

    def _load(self) -> None:
        if not self.bundle_path.exists():
            raise FileNotFoundError(f"Bundle not found: {self.bundle_path}")
        with zipfile.ZipFile(self.bundle_path, "r") as zf:
            self._extract_selected_files(zf)
            response_df = _read_csv_bytes_robust(_zip_read_bytes(zf, "response_category.csv"), csv_name="response_category.csv")
            delta_df = _read_csv_bytes_robust(_zip_read_bytes(zf, "fixed_item_delta.csv"), csv_name="fixed_item_delta.csv")
            person_df = _read_csv_bytes_robust(_zip_read_bytes(zf, "person_estimates.csv"), csv_name="person_estimates.csv")
            item_fit_df = _read_csv_bytes_robust(_zip_read_bytes(zf, "item_estimates.csv"), csv_name="item_estimates.csv")
            metadata = json.loads(_read_text_bytes_robust(_zip_read_bytes(zf, "metadata.json"), text_name="metadata.json"))
            name_map = _zip_name_map(zf)
            if "readme.md" in name_map:
                self.readme_text = _read_text_bytes_robust(zf.read(name_map["readme.md"]), text_name="README.md")

        response_df = response_df.copy()
        expected_cols = ["key", "no", "link", "item", "item2"]
        for col in expected_cols:
            if col not in response_df.columns:
                response_df[col] = ""
        response_df["link"] = response_df["link"].fillna("").astype(str).str.strip()
        response_df["item"] = response_df["item"].fillna("").astype(str)
        response_df["item2"] = response_df["item2"].fillna("").astype(str)

        delta_df = delta_df.copy()
        delta_df["no"] = delta_df["ITEM"].astype(str).str.extract(r"(\d+)").astype(int)
        merged = response_df.merge(delta_df[["no", "ITEM", "DELTA"]], on="no", how="left")
        merged["ITEM"] = merged["ITEM"].fillna(merged["no"].map(lambda x: f"Q{x:03d}"))

        self.person_df = person_df.copy()
        self.item_fit_df = item_fit_df.copy()
        measures = pd.to_numeric(person_df.get("MEASURE"), errors="coerce").dropna().to_numpy()
        if measures.size > 5:
            self.prior_mean = float(np.mean(measures))
            self.prior_sd = float(np.std(measures, ddof=1))
            self.person_distribution = measures
        self.prior_sd = max(self.prior_sd, 0.5)
        self.model = metadata.get("model", "Rasch")

        items: List[ItemRecord] = []
        for row in merged.itertuples(index=False):
            stem_zh, options_zh = parse_item_text(str(row.item))
            english_text = str(row.item2).strip() or str(row.item)
            stem_en, options_en = parse_item_text(english_text)
            rec = ItemRecord(
                item_id=str(row.ITEM),
                no=int(row.no),
                key=str(row.key).strip().upper(),
                full_text_zh=str(row.item),
                stem_zh=stem_zh,
                options_zh=options_zh,
                full_text_en=english_text,
                stem_en=stem_en,
                options_en=options_en,
                delta=float(row.DELTA),
                link=str(getattr(row, "link", "") or "").strip(),
            )
            items.append(rec)
        items.sort(key=lambda x: x.no)
        self.items = items
        self.item_lookup = {x.item_id: x for x in items}

    def probability(self, theta: np.ndarray | float, delta: float) -> np.ndarray | float:
        x = np.clip(np.asarray(theta) - delta, -35, 35)
        return 1.0 / (1.0 + np.exp(-x))

    def information(self, theta: float, delta: float) -> float:
        p = float(self.probability(theta, delta))
        return p * (1.0 - p)

    def posterior(self, responses: List[Tuple[str, int]], start_theta: float | None = None) -> Tuple[float, float, np.ndarray]:
        grid = self.theta_grid
        mu = self.prior_mean if start_theta is None else float(start_theta)
        sd = self.prior_sd
        log_post = -0.5 * ((grid - mu) / sd) ** 2 - np.log(sd * math.sqrt(2.0 * math.pi))
        for item_id, score in responses:
            delta = self.item_lookup[item_id].delta
            p = np.clip(self.probability(grid, delta), 1e-12, 1 - 1e-12)
            log_post += np.log(p) if score == 1 else np.log(1.0 - p)
        log_post -= np.max(log_post)
        post = np.exp(log_post)
        den = _trapz_compat(post, grid)
        if not np.isfinite(den) or den <= 0:
            den = 1.0
        post = post / den
        mean = _trapz_compat(grid * post, grid)
        var = _trapz_compat(((grid - mean) ** 2) * post, grid)
        se = max(math.sqrt(max(var, 1e-10)), 1e-6)
        return mean, se, post

    def select_next_item(self, administered: List[str], theta: float) -> ItemRecord:
        used = set(administered)
        remaining = [item for item in self.items if item.item_id not in used]
        if not remaining:
            raise RuntimeError("No remaining items.")
        return max(remaining, key=lambda item: (self.information(theta, item.delta), -abs(item.delta - theta)))

    def next_linear_item(self, administered: List[str]) -> Optional[ItemRecord]:
        used = set(administered)
        for item in self.items:
            if item.item_id not in used:
                return item
        return None

    def percentile(self, theta: float) -> float:
        vals = self.person_distribution
        if vals.size == 0:
            z = (theta - self.prior_mean) / self.prior_sd
            return 100.0 * (0.5 * (1 + math.erf(z / math.sqrt(2))))
        return 100.0 * float(np.mean(vals <= theta))

    def local_asset_path(self, raw_link: str) -> Optional[Path]:
        raw = (raw_link or "").strip().replace("\\", "/")
        if not raw or re.match(r"^[a-z]+://", raw, re.I):
            return None
        candidate = raw.lstrip("./")
        candidate_path = self.extract_dir / candidate
        if candidate_path.exists():
            return candidate_path
        local_path = Path(__file__).parent / candidate
        if local_path.exists():
            return local_path
        if "/" not in candidate and candidate.lower().endswith(IMG_EXTS):
            candidate = f"pic/{candidate}"
            candidate_path = self.extract_dir / candidate
            if candidate_path.exists():
                return candidate_path
            local_path = Path(__file__).parent / candidate
            if local_path.exists():
                return local_path
        return None


def ordered_options(options: Dict[str, str]) -> Dict[str, str]:
    if not options:
        return {}
    ordered: Dict[str, str] = {}
    for lab in OPTION_LABELS:
        if lab in options:
            ordered[lab] = options[lab]
    for lab in sorted(options.keys()):
        if lab not in ordered:
            ordered[lab] = options[lab]
    return ordered


def parse_item_text(text: str) -> Tuple[str, Dict[str, str]]:
    clean = re.sub(r"\s+", " ", text).strip()
    pattern_cn = re.compile(r"[（(]([A-E])[）)]")
    matches = list(pattern_cn.finditer(clean))
    if matches:
        stem = clean[: matches[0].start()].strip()
        options: Dict[str, str] = {}
        for i, match in enumerate(matches):
            label = match.group(1).upper()
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(clean)
            options[label] = clean[start:end].strip(" ;；。 ")
        return stem, ordered_options(options)
    pattern_en = re.compile(r"(?:^|\s)([A-E])[\.、:：]\s*")
    matches = list(pattern_en.finditer(clean))
    if matches:
        stem = clean[: matches[0].start()].strip()
        options: Dict[str, str] = {}
        for i, match in enumerate(matches):
            label = match.group(1).upper()
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(clean)
            options[label] = clean[start:end].strip(" ;；。 ")
        return stem, ordered_options(options)
    return clean, {}


def _svg_wrap(width: int, height: int, inner: str) -> str:
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img">{inner}</svg>'


def make_combined_kidmap_svg(person_values: np.ndarray, theta: float, person_se: float, rows: List[Dict[str, object]], infit_mnsq: float = 1.0, outfit_mnsq: float = 1.0) -> str:
    values = np.asarray(person_values, dtype=float)
    values = values[np.isfinite(values)]
    item_deltas = np.array([float(r.get("delta", 0.0)) for r in rows], dtype=float) if rows else np.array([], dtype=float)
    se_band = max(float(person_se or 0.0), 0.0)
    ymin = min(values.min() if values.size else theta, item_deltas.min() if item_deltas.size else theta, theta - se_band, theta) - 0.6
    ymax = max(values.max() if values.size else theta, item_deltas.max() if item_deltas.size else theta, theta + se_band, theta) + 0.6
    if ymax <= ymin:
        ymax = ymin + 1.0

    width, height = 980, 680
    left, right, top, bottom = 68, 28, 56, 56
    strip_w, gap_w = 152, 18
    x0, y0 = left, top
    plot_h = height - top - bottom
    resid_x0 = x0 + strip_w + gap_w
    plot_w = width - resid_x0 - right
    xmin, xmax = -4.0, 4.0

    def xmap(val: float) -> float:
        val = max(xmin, min(xmax, val))
        return resid_x0 + (val - xmin) / (xmax - xmin) * plot_w

    def ymap(val: float) -> float:
        return y0 + (ymax - val) / (ymax - ymin) * plot_h

    parts = [f'<rect x="0" y="0" width="{width}" height="{height}" fill="white"/>']

    title = f'KIDMAP — Measure {theta:.2f} (SE {se_band:.2f})  INFIT {infit_mnsq:.2f}  OUTFIT {outfit_mnsq:.2f}'
    parts.append(f'<text x="{x0}" y="26" font-size="16" font-weight="700" fill="#111827">{html.escape(title)}</text>')

    for t in range(math.floor(ymin), math.ceil(ymax) + 1):
        y = ymap(float(t))
        parts.append(f'<line x1="{x0}" y1="{y:.1f}" x2="{resid_x0+plot_w}" y2="{y:.1f}" stroke="#eef2f7"/>')
        parts.append(f'<text x="{x0-12}" y="{y+4:.1f}" text-anchor="end" font-size="11" fill="#4b5563">{t}</text>')

    # left panel: person distribution as horizontal bars
    parts.append(f'<rect x="{x0}" y="{y0}" width="{strip_w}" height="{plot_h}" fill="#f8fafc" stroke="#e5e7eb"/>')
    parts.append(f'<text x="{x0 + strip_w/2:.1f}" y="46" text-anchor="middle" font-size="15" font-weight="700" fill="#1f2937">Persons (distribution)</text>')
    parts.append(f'<text x="{x0 + strip_w/2:.1f}" y="{height-16}" text-anchor="middle" font-size="11" fill="#64748b">Count</text>')

    if values.size:
        n_bins = max(14, min(28, int(round((ymax - ymin) * 4))))
        edges = np.linspace(ymin, ymax, n_bins + 1)
        counts, _ = np.histogram(values, bins=edges)
        max_count = max(int(counts.max()), 1)
        inner_left = x0 + 8
        usable_w = strip_w - 18
        for i, count in enumerate(counts):
            if count <= 0:
                continue
            y_top = ymap(edges[i + 1])
            y_bot = ymap(edges[i])
            bar_h = max(2.0, y_bot - y_top - 1.5)
            cy = y_top + (y_bot - y_top) / 2.0
            bar_w = usable_w * (count / max_count)
            parts.append(f'<rect x="{inner_left:.1f}" y="{cy - bar_h/2:.1f}" width="{bar_w:.1f}" height="{bar_h:.1f}" rx="2" fill="#4361c2" fill-opacity="0.82" stroke="#3148a5" stroke-opacity="0.55"/>')
        # simple count ticks
        for frac in (0.0, 0.5, 1.0):
            xv = inner_left + usable_w * frac
            label = int(round(max_count * frac))
            parts.append(f'<line x1="{xv:.1f}" y1="{y0+plot_h}" x2="{xv:.1f}" y2="{y0+plot_h+4}" stroke="#64748b"/>')
            parts.append(f'<text x="{xv:.1f}" y="{y0+plot_h+18}" text-anchor="middle" font-size="10" fill="#64748b">{label}</text>')

    sep_x = resid_x0 - gap_w/2
    parts.append(f'<line x1="{sep_x:.1f}" y1="{y0}" x2="{sep_x:.1f}" y2="{y0+plot_h}" stroke="#cbd5e1" stroke-width="1"/>')
    parts.append(f'<text x="{resid_x0 + plot_w/2:.1f}" y="46" text-anchor="middle" font-size="15" font-weight="700" fill="#1f2937">KIDMAP (cell ZSTD)</text>')

    # vertical ZSTD guides
    for zv in (-2, 2):
        x = xmap(float(zv))
        parts.append(f'<line x1="{x:.1f}" y1="{y0}" x2="{x:.1f}" y2="{y0+plot_h}" stroke="#dc2626" stroke-width="2" stroke-dasharray="6,4"/>')
        parts.append(f'<text x="{x:.1f}" y="{height-20}" text-anchor="middle" font-size="11" fill="#dc2626">{zv}</text>')
    x_zero = xmap(0.0)
    parts.append(f'<line x1="{x_zero:.1f}" y1="{y0}" x2="{x_zero:.1f}" y2="{y0+plot_h}" stroke="#cbd5e1" stroke-width="1.2" stroke-dasharray="4,4"/>')
    parts.append(f'<text x="{x_zero:.1f}" y="{height-20}" text-anchor="middle" font-size="11" fill="#64748b">0</text>')

    parts.append(f'<line x1="{resid_x0}" y1="{y0+plot_h}" x2="{resid_x0+plot_w}" y2="{y0+plot_h}" stroke="#374151"/>')
    parts.append(f'<text x="{(resid_x0+resid_x0+plot_w)/2:.1f}" y="{height-16}" text-anchor="middle" font-size="12">ZSTD</text>')
    parts.append(f'<text x="{x0-52}" y="{y0-8}" font-size="12" fill="#4b5563">Logit</text>')

    # person measure solid line and SE band dashed lines
    theta_y = ymap(theta)
    parts.append(f'<line x1="{x0}" y1="{theta_y:.1f}" x2="{resid_x0+plot_w}" y2="{theta_y:.1f}" stroke="#dc2626" stroke-width="2"/>')
    parts.append(f'<text x="{resid_x0+plot_w-6}" y="{max(16, theta_y-6):.1f}" text-anchor="end" font-size="12" fill="#991b1b">Measure {theta:.2f}</text>')
    if se_band > 1e-9:
        for band_val, band_lab in ((theta + se_band, '+SE'), (theta - se_band, '-SE')):
            by = ymap(band_val)
            parts.append(f'<line x1="{x0}" y1="{by:.1f}" x2="{resid_x0+plot_w}" y2="{by:.1f}" stroke="#dc2626" stroke-width="1.6" stroke-dasharray="4,4"/>')
            parts.append(f'<text x="{resid_x0+plot_w-6}" y="{max(16, by-4):.1f}" text-anchor="end" font-size="11" fill="#991b1b">{band_lab} ({band_val:.2f})</text>')

    if rows:
        ses = [float(r.get("item_se", 0.12) or 0.12) for r in rows]
        max_se = max(ses) if ses else 0.12
        min_se = min(ses) if ses else 0.12

        def rmap(se: float) -> float:
            if max_se <= min_se + 1e-9:
                return 8.0
            return 5.0 + (se - min_se) / (max_se - min_se) * 9.0

        for row in rows:
            delta = float(row.get("delta", 0.0))
            z = float(row.get("zscore", 0.0))
            se = float(row.get("item_se", 0.12) or 0.12)
            score = int(row.get("score", 0))
            item_id = html.escape(str(row.get("item_id", "")))
            x = xmap(z)
            y = ymap(delta)
            r = rmap(se)
            fill = '#2563eb' if score == 1 else '#dc2626'
            stroke = '#1e3a8a' if score == 1 else '#7f1d1d'
            stroke_w = 1.5 if abs(z) > 2 else 1.1
            parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{fill}" fill-opacity="0.78" stroke="{stroke}" stroke-width="{stroke_w}"/>')
            tx = min(resid_x0 + plot_w - 4, x + r + 5)
            parts.append(f'<text x="{tx:.1f}" y="{y+4:.1f}" font-size="10" fill="#111827">{item_id}</text>')

    legend_y = height - 38
    parts.append(f'<circle cx="{resid_x0+12}" cy="{legend_y}" r="6" fill="#2563eb" fill-opacity="0.78" stroke="#1e3a8a" stroke-width="1"/>')
    parts.append(f'<text x="{resid_x0+24}" y="{legend_y+4}" font-size="11">correct</text>')
    parts.append(f'<circle cx="{resid_x0+92}" cy="{legend_y}" r="6" fill="#dc2626" fill-opacity="0.78" stroke="#7f1d1d" stroke-width="1"/>')
    parts.append(f'<text x="{resid_x0+104}" y="{legend_y+4}" font-size="11">incorrect</text>')
    parts.append(f'<line x1="{resid_x0+186}" y1="{legend_y}" x2="{resid_x0+226}" y2="{legend_y}" stroke="#dc2626" stroke-width="2" stroke-dasharray="4,4"/>')
    parts.append(f'<text x="{resid_x0+234}" y="{legend_y+4}" font-size="11">Measure ± SE</text>')
    parts.append(f'<line x1="{resid_x0+330}" y1="{legend_y}" x2="{resid_x0+370}" y2="{legend_y}" stroke="#dc2626" stroke-width="2" stroke-dasharray="6,4"/>')
    parts.append(f'<text x="{resid_x0+378}" y="{legend_y+4}" font-size="11">ZSTD ±2</text>')
    parts.append(f'<text x="{resid_x0+462}" y="{legend_y+4}" font-size="11">bubble size ∝ item SE</text>')
    return _svg_wrap(width, height, ''.join(parts))


def make_itemfit_svg(item_df: pd.DataFrame, answered_ids: List[str]) -> str:
    if item_df is None or item_df.empty or 'MEASURE' not in item_df.columns or 'INFIT_ZSTD' not in item_df.columns:
        return _svg_wrap(900, 260, '<text x="20" y="40">No item fit Z-score data available.</text>')
    df = item_df.copy()
    df['ITEM'] = df['ITEM'].astype(str)
    xvals = pd.to_numeric(df['MEASURE'], errors='coerce')
    yvals = pd.to_numeric(df['INFIT_ZSTD'], errors='coerce')
    keep = xvals.notna() & yvals.notna()
    df = df.loc[keep, ['ITEM']].copy()
    df['x'] = xvals[keep].astype(float).to_numpy()
    df['y'] = yvals[keep].astype(float).to_numpy()
    width, height = 900, 260
    left, right, top, bottom = 52, 18, 20, 34
    x0, y0 = left, height - bottom
    plot_w, plot_h = width - left - right, height - top - bottom
    xmin, xmax = float(df['x'].min()), float(df['x'].max())
    ymin, ymax = float(min(-3.0, df['y'].min() - 0.5)), float(max(3.0, df['y'].max() + 0.5))
    if xmax <= xmin:
        xmax = xmin + 1.0
    if ymax <= ymin:
        ymax = ymin + 1.0
    parts = [f'<rect x="0" y="0" width="{width}" height="{height}" fill="white"/>',
             f'<line x1="{x0}" y1="{y0}" x2="{x0+plot_w}" y2="{y0}" stroke="#444"/>',
             f'<line x1="{x0}" y1="{top}" x2="{x0}" y2="{y0}" stroke="#444"/>']
    for yv in [-2, 0, 2]:
        yy = y0 - (yv - ymin) / (ymax - ymin) * plot_h
        parts.append(f'<line x1="{x0}" y1="{yy:.1f}" x2="{x0+plot_w}" y2="{yy:.1f}" stroke="#d1d5db" stroke-dasharray="4,4"/>')
        parts.append(f'<text x="{x0-8}" y="{yy+4:.1f}" text-anchor="end" font-size="11">{yv}</text>')
    answered = set(answered_ids)
    for row in df.itertuples(index=False):
        x = x0 + (float(row.x) - xmin) / (xmax - xmin) * plot_w
        y = y0 - (float(row.y) - ymin) / (ymax - ymin) * plot_h
        highlight = row.ITEM in answered
        r = 4.5 if highlight else 2.5
        fill = '#dc2626' if highlight else '#6b7280'
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{fill}" opacity="0.85"/>')
    return _svg_wrap(width, height, ''.join(parts))


def compute_person_fit(responses: List[Tuple[str, int]], theta: float) -> Tuple[float, float]:
    if not responses:
        return 1.0, 1.0
    numer = 0.0
    denom = 0.0
    outfit_terms = []
    for item_id, score in responses:
        item = BANK.item_lookup.get(item_id)
        if not item:
            continue
        p = float(np.clip(BANK.probability(theta, item.delta), 1e-8, 1 - 1e-8))
        var = max(p * (1.0 - p), 1e-8)
        resid2 = (float(score) - p) ** 2
        numer += resid2
        denom += var
        outfit_terms.append(resid2 / var)
    infit = numer / denom if denom > 0 else 1.0
    outfit = float(np.mean(outfit_terms)) if outfit_terms else 1.0
    return infit, outfit


def build_dashboard_data(state: dict) -> Dict[str, object]:
    responses = [tuple(x) for x in state.get('responses', [])]
    history = state.get('history', [])
    answered_ids = [item_id for item_id, _ in responses]
    final_theta = float(state.get('theta', BANK.prior_mean))
    residual_rows = []
    score_lookup = {item_id: int(score) for item_id, score in responses}
    item_stats = BANK.item_fit_df.copy() if isinstance(BANK.item_fit_df, pd.DataFrame) else pd.DataFrame()
    item_se_map = {}
    if not item_stats.empty and 'ITEM' in item_stats.columns and 'SE' in item_stats.columns:
        item_se_map = dict(zip(item_stats['ITEM'].astype(str), pd.to_numeric(item_stats['SE'], errors='coerce').fillna(0.12)))
    for row in history:
        item_id = str(row.get('item_id', ''))
        item = BANK.item_lookup.get(item_id)
        if not item:
            continue
        score = int(score_lookup.get(item_id, 0))
        p = float(np.clip(BANK.probability(final_theta, item.delta), 1e-8, 1 - 1e-8))
        z = (score - p) / math.sqrt(max(p * (1 - p), 1e-8))
        residual_rows.append({
            'item_id': item_id,
            'delta': float(item.delta),
            'score': score,
            'zscore': float(z),
            'item_se': float(item_se_map.get(item_id, 0.12) or 0.12),
        })
    infit_mnsq, outfit_mnsq = compute_person_fit(responses, final_theta)
    final_se = float(state.get('se', BANK.prior_sd))
    return {
        'answered_ids': answered_ids,
        'kidmap_svg': make_combined_kidmap_svg(BANK.person_distribution, final_theta, final_se, residual_rows, infit_mnsq, outfit_mnsq),
        'itemfit_svg': make_itemfit_svg(BANK.item_fit_df, answered_ids),
        'infit_mnsq': infit_mnsq,
        'outfit_mnsq': outfit_mnsq,
    }


app = Flask(__name__)
app.secret_key = SECRET_KEY
BANK = RaschCATBank(DEFAULT_BUNDLE)


def get_state() -> dict:
    return session.setdefault("cat_state", {})


def reset_state() -> None:
    session["cat_state"] = {}
    session.modified = True


def get_labels(language: str) -> Dict[str, str]:
    return LABELS[language if language in LABELS else "en"]


def resolve_link_href(raw_link: str) -> Tuple[str, bool]:
    raw = (raw_link or "").strip()
    if not raw:
        return "", False
    if re.match(r"^[a-z]+://", raw, re.I):
        return raw, raw.lower().endswith(IMG_EXTS)
    local_path = BANK.local_asset_path(raw)
    if not local_path:
        return "", False
    try:
        rel = local_path.relative_to(BANK.extract_dir)
    except ValueError:
        rel = local_path.relative_to(Path(__file__).parent)
    rel_path = str(rel).replace("\\", "/")
    return url_for("bundle_asset", asset_path=rel_path), rel_path.lower().endswith(IMG_EXTS)


@app.get("/bundle_asset/<path:asset_path>")
def bundle_asset(asset_path: str):
    asset_path = asset_path.replace("\\", "/")
    for root in (BANK.extract_dir, Path(__file__).parent):
        fp = root / asset_path
        if fp.exists() and fp.is_file():
            return send_from_directory(str(root), asset_path)
    abort(404)


@app.get("/")
def index():
    summary = {
        "n_items": len(BANK.items),
        "prior_mean": BANK.prior_mean,
        "prior_sd": BANK.prior_sd,
    }
    labels = get_labels("en")
    return render_template_string(
        HOME_TMPL,
        title=APP_TITLE,
        bundle_name=BANK.bundle_path.name,
        summary=summary,
        readme_text=BANK.readme_text,
        labels=labels,
    )


@app.post("/start")
def start_test():
    requested_max_items = int(request.form.get("max_items", 20))
    stop_se = float(request.form.get("stop_se", 0.32))
    start_theta = float(request.form.get("start_theta", BANK.prior_mean))
    language = str(request.form.get("language", "zh")).strip().lower()
    mode = str(request.form.get("mode", "cat")).strip().lower()
    if language not in {"zh", "en"}:
        language = "zh"
    if mode not in {"cat", "linear"}:
        mode = "cat"

    theta, se, _ = BANK.posterior([], start_theta=start_theta)
    if mode == "linear":
        first_item = BANK.next_linear_item([])
        max_items = len(BANK.items)
        stop_se = 0.0
    else:
        first_item = BANK.select_next_item([], theta)
        max_items = requested_max_items
    if first_item is None:
        return redirect(url_for("index"))

    session["cat_state"] = {
        "mode": mode,
        "max_items": max_items,
        "requested_max_items": requested_max_items,
        "stop_se": stop_se,
        "start_theta": start_theta,
        "language": language,
        "responses": [],
        "history": [],
        "current_item": first_item.item_id,
        "theta": theta,
        "se": se,
        "stop_reason": "",
    }
    session.modified = True
    return redirect(url_for("show_item"))


@app.get("/item")
def show_item():
    state = get_state()
    if not state or "current_item" not in state:
        return redirect(url_for("index"))
    language = state.get("language", "zh")
    labels = get_labels(language)
    item = BANK.item_lookup[state["current_item"]]
    text_view = item.text_for(language)
    link_href, is_image = resolve_link_href(item.link)
    mode = state.get("mode", "cat")
    progress = {
        "answered": len(state.get("responses", [])),
        "max_items": state["max_items"],
        "theta": state["theta"],
        "se": state["se"],
        "info_line": labels["sel_info_cat"] if mode == "cat" else labels["sel_info_linear"],
    }
    item_view = {
        "item_id": item.item_id,
        "no": item.no,
        "full_text": text_view["full_text"],
        "stem": text_view["stem"],
        "options": text_view["options"],
        "link_href": link_href,
        "is_image_link": is_image,
    }
    language_name = labels["lang_zh"] if language == "zh" else labels["lang_en"]
    mode_name = labels["mode_cat_short"] if mode == "cat" else labels["mode_linear_short"]
    return render_template_string(ITEM_TMPL, title=APP_TITLE, item=item_view, progress=progress, labels=labels, language_name=language_name, mode_name=mode_name)


@app.post("/answer")
def submit_answer():
    state = get_state()
    if not state or "current_item" not in state:
        return redirect(url_for("index"))
    answer = str(request.form.get("answer", "")).strip().upper()
    item = BANK.item_lookup[state["current_item"]]
    score = int(answer == item.key)
    mode = state.get("mode", "cat")

    responses = [tuple(x) for x in state.get("responses", [])]
    responses.append((item.item_id, score))
    theta, se, _ = BANK.posterior(responses, start_theta=state.get("start_theta", BANK.prior_mean))
    history = list(state.get("history", []))
    link_href, _ = resolve_link_href(item.link)
    history.append({
        "item_id": item.item_id,
        "no": item.no,
        "delta": item.delta,
        "answer": answer,
        "theta": theta,
        "se": se,
        "link_href": link_href,
    })

    stop_reason = ""
    if mode == "linear":
        if len(responses) >= len(BANK.items):
            stop_reason = "all_items"
    else:
        if len(responses) >= int(state["max_items"]):
            stop_reason = "max_items"
        elif se <= float(state["stop_se"]):
            stop_reason = "target_se"

    state["responses"] = [list(x) for x in responses]
    state["history"] = history
    state["theta"] = theta
    state["se"] = se
    state["stop_reason"] = stop_reason

    if stop_reason:
        session["cat_state"] = state
        session.modified = True
        return redirect(url_for("show_result"))

    used_ids = [i for i, _ in responses]
    if mode == "linear":
        next_item = BANK.next_linear_item(used_ids)
    else:
        next_item = BANK.select_next_item(used_ids, theta)
    if next_item is None:
        state["stop_reason"] = "all_items"
        session["cat_state"] = state
        session.modified = True
        return redirect(url_for("show_result"))
    state["current_item"] = next_item.item_id
    session["cat_state"] = state
    session.modified = True
    return redirect(url_for("show_item"))


@app.get("/result")
def show_result():
    state = get_state()
    if not state or not state.get("history"):
        return redirect(url_for("index"))
    language = state.get("language", "zh")
    labels = get_labels(language)
    dashboard = build_dashboard_data(state)
    mode = state.get("mode", "cat")
    result = {
        "theta": state["theta"],
        "se": state["se"],
        "percentile": BANK.percentile(state["theta"]),
        "n_answered": len(state["responses"]),
        "stop_reason": state.get("stop_reason", "finished"),
        "history": state["history"],
        "has_links": any(bool((row.get("link_href") or "").strip()) for row in state["history"]),
        "mode_name": labels["mode_cat_short"] if mode == "cat" else labels["mode_linear_short"],
        **dashboard,
    }
    return render_template_string(RESULT_TMPL, title=APP_TITLE, result=result, labels=labels)


@app.get("/reset")
def reset():
    reset_state()
    return redirect(url_for("index"))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)
