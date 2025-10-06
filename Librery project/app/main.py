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
from core import functional as fn


st.set_page_config(page_title="Library Recommender", page_icon="📚", layout="wide")

# Навигация
st.sidebar.title("Menu")
page = st.sidebar.radio("Navigation", ["Overview", "Data", "Functional Core", "Reports", "Tests", "About"], index=1)

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

    DATA = st.session_state.get("DATA")
    if not DATA:
        st.info("Сначала загрузите seed во вкладке Data.")
        st.stop()

    # Распаковка
    books  = DATA["books"]
    ratings = DATA["ratings"]
    reviews = DATA["reviews"]
    loans   = DATA["loans"]
    genres  = DATA["genres"]

    # Диагностика (видно ли данные тут)
    with st.expander("🔧 Debug (types & counts)"):
        st.write({k: len(v) for k, v in DATA.items()})
        st.write("Тип первого Book:", type(books[0]).__name__ if books else "—")
        st.write("Тип первого Rating:", type(ratings[0]).__name__ if ratings else "—")

    # --- Книги с высоким рейтингом ---
    threshold = st.number_input("Порог рейтинга", 0.0, 5.0, 4.0, 0.1, key="thr")
    if st.button("Показать книги с рейтингом ≥ threshold", key="btn_high"):
        try:
            res = fn.books_with_avg_ge(ratings, books, threshold)
            table = [{"id": b.id, "title": b.title, "year": b.year} for b in res]
            if table:
                st.table(table)
                st.metric("Найдено книг", len(table))
            else:
                st.warning("Нет книг с таким рейтингом")
        except Exception as e:
            st.exception(e)

    # --- Топ-N книг ---
    top_n = st.number_input("Сколько книг в топе?", min_value=1, max_value=50, value=5, step=1, key="topn")
    if st.button("Показать Top-N книг", key="btn_top"):
        try:
            res = fn.top_books_by_avg(ratings, books, int(top_n))
            rows = []
            for bid, avg in res:
                b = next((x for x in books if x.id == bid), None)
                rows.append({"id": bid, "title": b.title if b else "(unknown)", "avg": round(avg, 2)})
            st.dataframe(rows, use_container_width=True)
        except Exception as e:
            st.exception(e)

    # --- Активные займы пользователя ---
    user_id = st.text_input("User ID", "u1", key="uid")
    if st.button("Проверить активные займы пользователя", key="btn_loans"):
        try:
            has_loan = fn.user_has_active_loan(loans, user_id)
            (st.success if has_loan else st.error)(f"{user_id}: {'есть' if has_loan else 'нет'} активных займов")
        except Exception as e:
            st.exception(e)

    # --- Рекурсивная проверка жанра ---
    genre_id = st.text_input("Genre ID", "g1", key="gid")
    book_id  = st.text_input("Book ID", "b1", key="bid")
    if st.button("Принадлежит ли книга жанру (включая поджанры)?", key="btn_genre"):
        try:
            book = next((b for b in books if b.id == book_id), None)
            if not book:
                st.error(f"Книга {book_id} не найдена")
            else:
                ok = fn.book_in_genre_recursive(book, genres, genre_id)
                (st.success if ok else st.error)(f"{book.title} → {genre_id}: {ok}")
        except Exception as e:
            st.exception(e)

elif page == "Reports":
    st.header("📊 Reports")
    
    # Прямые импорты чтобы избежать циклических зависимостей
    from core.transforms import load_seed
    
    try:
        from core.memo import recommend_for_user, measure_recommendation_performance
        memo_available = True
    except ImportError as e:
        st.error(f"Модуль рекомендаций недоступен: {e}")
        memo_available = False
    
    # Загружаем данные
    data = load_seed("data/seed.json")
    books = data["books"]
    ratings = data["ratings"]
    users = data["users"]
    
    if not books:
        st.warning("Сначала загрузите данные во вкладке 'Data'")
    elif not memo_available:
        st.warning("Модуль рекомендаций не загружен")
    else:
        st.subheader("Рекомендации с кэшированием")
        
        # Выбор пользователя
        user_options = [f"{user.id} - {user.name}" for user in users]
        selected_user = st.selectbox("Выберите пользователя:", user_options, key="user_select_reports")
        
        if selected_user and st.button("Получить рекомендации", key="get_recommendations"):
            user_id = selected_user.split(" - ")[0]
            
            with st.spinner("Формируем рекомендации..."):
                recommendations = recommend_for_user(user_id, tuple(ratings), tuple(books))
                
                if recommendations:
                    st.success(f"Найдено {len(recommendations)} рекомендаций!")
                    for i, book_id in enumerate(recommendations, 1):
                        book = next((b for b in books if b.id == book_id), None)
                        if book:
                            st.write(f"{i}. **{book.title}**")
                            st.write(f"   Жанры: {', '.join(book.genres)}")
                            st.write("---")
                else:
                    st.warning("Рекомендации не найдены")
        
        # Измерение производительности
        st.subheader("Измерение производительности")
        if st.button("Измерить производительность кэша", key="measure_perf"):
            with st.spinner("Измеряем..."):
                perf_data = measure_recommendation_performance()
                
                if "error" in perf_data:
                    st.error(perf_data["error"])
                else:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Первый вызов", f"{perf_data['first_call_avg_ms']}ms")
                    with col2:
                        st.metric("С кэшем", f"{perf_data['second_call_avg_ms']}ms")
                    with col3:
                        st.metric("Ускорение", f"{perf_data['speedup']}x")

elif page == "Tests":
    st.header("Tests")
    st.write("PYTHONPATH=. pytest -q")

elif page == "About":
    st.header("About")
    st.write("labwork by aituar rinat")

