# --- Force project root into sys.path (before any other imports) ---
import os, sys
from pathlib import Path

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
# -------------------------------------------------------------------

import json
import streamlit as st
from core.transforms import load_seed, avg_rating_for_book
from core.domain import Rating

st.set_page_config(page_title="Library Recommender", page_icon="📚", layout="wide")

# Навигация
st.sidebar.title("Menu")
page = st.sidebar.radio("Navigation", ["Overview", "Data", "Functional Core", "Tests", "About"], index=1)

# Состояние приложения
if "DATA" not in st.session_state:
    st.session_state["DATA"] = None

DATA = st.session_state["DATA"]

if page == "Data":
    st.header("Data")
    seed_path = Path(__file__).parents[1] / "data" / "seed.json"
    st.code(str(seed_path), language="bash")

    # Диагностика файла
    exists = seed_path.exists()
    size = seed_path.stat().st_size if exists else 0
    st.write(f"Exists: {exists}, Size: {size} bytes")

    if exists and size > 0:
        try:
            preview = seed_path.read_text(encoding="utf-8")[:200]
            st.text_area("Preview (first 200 chars)", preview, height=120)
        except Exception as e:
            st.error(f"Cannot read file: {e}")
            
    # Кнопка: загрузить seed
    if st.button("Load seed", type="primary"):
        try:
            st.session_state["DATA"] = load_seed(str(seed_path))
            st.success("✅ Seed loaded")
        except Exception as e:
            st.error(f"❌ {e}")

    # Показать счётчики
    if st.session_state["DATA"]:
        st.subheader("Counts")
        for k, v in st.session_state["DATA"].items():
            st.write(f"- {k}: {len(v)}")

elif page == "Overview":
    st.header("Overview")
    if not DATA:
        st.info("Перейди во вкладку Data и нажми «Load seed».")
    else:
        n_books = len(DATA["books"])
        n_authors = len(DATA["authors"])
        n_users = len(DATA["users"])

        # Средний рейтинг по каталогу (среднее по средним)
        ratings = tuple(Rating(**r) if isinstance(r, dict) else r for r in DATA["ratings"])
        totals = []
        for b in DATA["books"]:
            bid = b["id"] if isinstance(b, dict) else b.id
            totals.append(avg_rating_for_book(ratings, bid))
        avg_catalog = (sum(totals) / len(totals)) if totals else 0.0

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("#Books", n_books)
        c2.metric("#Authors", n_authors)
        c3.metric("#Users", n_users)
        c4.metric("Avg rating (catalog)", round(avg_catalog, 2))

elif page == "Functional Core":
    st.header("Functional Core")
    st.write("Здесь позже появятся предикаты и рекурсия (Лаба 2).")

elif page == "Tests":
    st.header("Tests")
    st.write("Запускай в терминале: `pytest -q`.")

elif page == "About":
    st.header("About")
    st.write("Одностраничное демо: доменные модели, загрузка seed, чистые функции и базовый UI.")
