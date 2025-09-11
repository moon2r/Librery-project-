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

    # Кнопка: создать демо seed.json
    if st.button("Create demo seed.json"):
        demo = {
            "authors": [
                {"id": "a1", "name": "Айзек Азимов"},
                {"id": "a2", "name": "Стивен Кинг"}
            ],
            "books": [
                {"id": "b1", "title": "Основание", "author_ids": ["a1"], "genres": ["g1"], "tags": ["t1"], "year": 1951},
                {"id": "b2", "title": "Оно", "author_ids": ["a2"], "genres": ["g2"], "tags": ["t2"], "year": 1986}
            ],
            "users": [
                {"id": "u1", "name": "User 1"},
                {"id": "u2", "name": "User 2"}
            ],
            "ratings": [
                {"user_id": "u1", "book_id": "b1", "value": 5},
                {"user_id": "u2", "book_id": "b1", "value": 4},
                {"user_id": "u1", "book_id": "b2", "value": 3}
            ],
            "reviews": [
                {"id": "rv1", "user_id": "u1", "book_id": "b1", "text": "Очень понравилось!", "ts": "2025-09-10T12:00:00"},
                {"id": "rv2", "user_id": "u2", "book_id": "b2", "text": "Было страшно, но круто", "ts": "2025-09-10T13:00:00"}
            ],
            "loans": [
                {"id": "l1", "user_id": "u1", "book_id": "b1", "start": "2025-09-01", "end": None, "status": "active"},
                {"id": "l2", "user_id": "u2", "book_id": "b2", "start": "2025-09-05", "end": "2025-09-08", "status": "returned"}
            ],
            "tags": [
                {"id": "t1", "name": "sci-fi", "parent_id": None},
                {"id": "t2", "name": "horror", "parent_id": None}
            ],
            "genres": [
                {"id": "g1", "name": "fiction", "parent_id": None},
                {"id": "g2", "name": "thriller", "parent_id": None}
            ]
        }
        seed_path.parent.mkdir(parents=True, exist_ok=True)
        seed_path.write_text(json.dumps(demo, ensure_ascii=False, indent=2), encoding="utf-8")
        st.success(f"Demo seed.json written to: {seed_path}")

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
