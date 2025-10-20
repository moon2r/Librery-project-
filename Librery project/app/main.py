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
from core.domain import Rating, Review, Book, User, Author, Loan, Tag, Genre
from core import functional as fn
from core.ftypes import (
    Maybe, Either, safe_book, safe_user, validate_rating, validate_review,
    add_rating_pipeline, add_review_pipeline, safe_book_analysis,
    demonstrate_maybe_usage, demonstrate_either_usage
)


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
    st.header("🧪 Functional Core - Maybe/Either")
    
    DATA = st.session_state.get("DATA")
    if not DATA:
        st.info("Please load seed data first in the 'Data' tab.")
        st.stop()

    # Load data
    books = DATA["books"]
    users = DATA["users"]
    ratings = DATA["ratings"]
    reviews = DATA["reviews"]
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "🔍 Maybe Examples", 
        "✅ Either Examples", 
        "🔄 Validation Pipeline",
        "🎯 Demos"
    ])
    
    with tab1:
        st.subheader("Maybe - Safe Operations")
        st.info("Maybe handles optional values without None checks")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Safe Book Lookup**")
            book_id = st.text_input("Enter Book ID:", value="1", key="maybe_book")
            if st.button("Find Book (Maybe)"):
                result = safe_book(books, book_id)
                
                if result.is_just():
                    book = result.get_or_else(None)
                    st.success(f"✅ Found: **{book.title}**")
                    st.write(f"**Genres:** {', '.join(book.genres)}")
                    st.write(f"**Year:** {book.year}")
                else:
                    st.error("❌ Book not found")
        
        with col2:
            st.write("**Safe User Lookup**")
            user_id = st.text_input("Enter User ID:", value="1", key="maybe_user")
            if st.button("Find User (Maybe)"):
                result = safe_user(users, user_id)
                
                if result.is_just():
                    user = result.get_or_else(None)
                    st.success(f"✅ Found: **{user.name}**")
                else:
                    st.error("❌ User not found")
        
        st.write("---")
        st.write("**Safe Book Analysis**")
        analysis_book_id = st.selectbox("Select book for analysis:", 
                                       [b.id for b in books], 
                                       key="analysis_book")
        if st.button("Analyze Book"):
            result = safe_book_analysis(books, analysis_book_id, ratings)
            
            if result.is_just():
                title, avg_rating = result.get_or_else(("", 0.0))
                st.success(f"**{title}** - Average Rating: **{avg_rating:.2f}** ⭐")
            else:
                st.error("❌ Could not analyze book")

    with tab2:
        st.subheader("Either - Validation with Errors")
        st.info("Either represents operations that can fail with meaningful errors")
        
        st.write("**Rating Validation**")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            selected_user = st.selectbox("User:", 
                                        [f"{u.id} - {u.name}" for u in users],
                                        key="either_user")
            user_id = selected_user.split(" - ")[0] if selected_user else ""
        
        with col2:
            selected_book = st.selectbox("Book:", 
                                        [f"{b.id} - {b.title}" for b in books],
                                        key="either_book")
            book_id = selected_book.split(" - ")[0] if selected_book else ""
        
        with col3:
            rating_value = st.slider("Rating", 1, 5, 3, key="either_rating")
        
        if st.button("Validate Rating (Either)"):
            if user_id and book_id:
                rating = Rating(user_id, book_id, rating_value)
                result = validate_rating(rating, books, users, ratings)
                
                if result.is_right():
                    st.success("✅ Rating is valid!")
                    st.balloons()
                else:
                    st.error("❌ Validation errors:")
                    for field, error in result._error.items():
                        st.write(f"**{field}:** {error}")
            else:
                st.warning("Please select both user and book")
        
        st.write("---")
        st.write("**Review Validation**")
        
        review_user = st.selectbox("Review User:", 
                                  [f"{u.id} - {u.name}" for u in users],
                                  key="review_user")
        review_book = st.selectbox("Review Book:", 
                                  [f"{b.id} - {b.title}" for b in books],
                                  key="review_book")
        review_text = st.text_area("Review Text:", 
                                  "This is a great book with excellent storytelling...")
        
        if st.button("Validate Review"):
            if review_user and review_book:
                user_id = review_user.split(" - ")[0]
                book_id = review_book.split(" - ")[0]
                review = Review("temp_id", user_id, book_id, review_text, "2024-01-01")
                
                result = validate_review(review, books, users)
                
                if result.is_right():
                    st.success("✅ Review is valid!")
                else:
                    st.error("❌ Validation errors:")
                    for field, error in result._error.items():
                        st.write(f"**{field}:** {error}")
            else:
                st.warning("Please select both user and book")

    with tab3:
        st.subheader("🔄 Validation Pipelines")
        st.info("Compose operations using map/bind without exceptions")
        
        st.write("**Add Rating Pipeline**")
        
        pipeline_user = st.selectbox("Pipeline User:", 
                                    [f"{u.id} - {u.name}" for u in users],
                                    key="pipeline_user")
        pipeline_book = st.selectbox("Pipeline Book:", 
                                    [f"{b.id} - {b.title}" for b in books],
                                    key="pipeline_book")
        pipeline_rating = st.slider("Pipeline Rating", 1, 5, 4, key="pipeline_rating")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Run Rating Pipeline"):
                if pipeline_user and pipeline_book:
                    user_id = pipeline_user.split(" - ")[0]
                    book_id = pipeline_book.split(" - ")[0]
                    rating = Rating(user_id, book_id, pipeline_rating)
                    
                    result = add_rating_pipeline(rating, ratings, books, users)
                    
                    if result.is_right():
                        new_ratings = result.get_or_else(ratings)
                        st.success("Rating added successfully!")
                        st.write(f"**Total ratings now:** {len(new_ratings)}")
                    else:
                        st.error("❌ Failed to add rating:")
                        for field, error in result._error.items():
                            st.write(f"**{field}:** {error}")
                else:
                    st.warning("Please select both user and book")
        
        with col2:
            if st.button("Run Review Pipeline"):
                if pipeline_user and pipeline_book:
                    user_id = pipeline_user.split(" - ")[0]
                    book_id = pipeline_book.split(" - ")[0]
                    review = Review("rev_new", user_id, book_id, 
                                   "This book was absolutely fantastic! Highly recommended.", 
                                   "2024-01-01")
                    
                    result = add_review_pipeline(review, reviews, books, users, ratings)
                    
                    if result.is_right():
                        new_reviews = result.get_or_else(None)
                        st.success("Review added successfully!")
                        if new_reviews:
                            st.write(f"**Total reviews now:** {len(new_reviews)}")
                    else:
                        st.error("❌ Failed to add review:")
                        for field, error in result._error.items():
                            st.write(f"**{field}:** {error}")
                else:
                    st.warning("Please select both user and book")
        
        st.write("---")
        st.write("**Pipeline Composition Example**")
        st.code("""
# Instead of:
try:
    validate_rating(rating)
    add_rating(rating)
    update_average(rating.book_id)
except ValidationError as e:
    handle_error(e)

# We use:
result = (validate_rating(rating)
         .bind(add_rating)
         .bind(update_average))
        """)

    with tab4:
        st.subheader("🎯 Functional Patterns Demos")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Maybe Demo**")
            if st.button("Run Maybe Demo"):
                result = demonstrate_maybe_usage()
                st.success(f"Demo result: {result}")
                st.info("""
                **What happened:**
                - safe_book() returned Maybe[Book]
                - .map() transformed the title
                - .get_or_else() provided fallback
                - No None checks needed!
                """)
        
        with col2:
            st.write("**Either Demo**")
            if st.button("Run Either Demo"):
                result = demonstrate_either_usage()
                st.success(f"Demo result: {result}")
                st.info("""
                **What happened:**
                - validate_rating() returned Either[Error, Rating]
                - .map() transformed success case
                - .get_or_else() handled errors
                - No exceptions thrown!
                """)
        
        st.write("---")
        st.write("**Key Benefits**")
        
        benefits = [
            "🚀 **No Null Pointer Exceptions** - Maybe handles missing values",
            "✅ **Explicit Error Handling** - Either makes errors part of the type",
            "🧩 **Composable Operations** - Chain with map/bind", 
            "📝 **Self-documenting Code** - Types show what can fail",
            "🎯 **Business Logic Focus** - No try/except clutter"
        ]
        
        for benefit in benefits:
            st.write(benefit)

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

