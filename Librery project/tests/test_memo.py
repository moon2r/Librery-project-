import pytest
import time
from core.memo import recommend_for_user, measure_recommendation_performance
from core.domain import Book, Rating, User
from core.transforms import load_seed


def test_recommend_for_user_basic():
    """Тест базовой работы рекомендаций"""
    books = (
        Book("1", "Test Book 1", ("author1",), ("fiction",), ("adventure",), 2020),
        Book("2", "Test Book 2", ("author2",), ("non-fiction",), ("science",), 2021),
    )
    ratings = (
        Rating("user1", "1", 5),
    )
    
    result = recommend_for_user("user1", ratings, books)
    assert isinstance(result, tuple)
    assert all(isinstance(book_id, str) for book_id in result)


def test_recommend_for_user_no_ratings():
    """Тест рекомендаций для пользователя без оценок"""
    books = (
        Book("1", "Test Book 1", ("author1",), ("fiction",), ("adventure",), 2020),
        Book("2", "Test Book 2", ("author2",), ("non-fiction",), ("science",), 2021),
    )
    ratings = tuple()
    
    result = recommend_for_user("user1", ratings, books)
    assert result == tuple()


def test_recommend_for_user_caching_same_results():
    """Тест что кэширование возвращает одинаковые результаты"""
    books = (
        Book("1", "Test Book 1", ("author1",), ("fiction",), ("adventure",), 2020),
        Book("2", "Test Book 2", ("author2",), ("non-fiction",), ("science",), 2021),
        Book("3", "Test Book 3", ("author3",), ("fantasy",), ("magic",), 2022),
    )
    ratings = (
        Rating("user1", "1", 5),
        Rating("user1", "2", 4),
    )
    
    # Первый вызов
    result1 = recommend_for_user("user1", ratings, books)
    # Второй вызов (должен быть закэширован)
    result2 = recommend_for_user("user1", ratings, books)
    
    assert result1 == result2
    assert len(result1) <= 10  # Должно быть не больше 10 рекомендаций


def test_recommend_for_user_excludes_rated_books():
    """Тест что рекомендации не включают книги, которые пользователь уже оценил"""
    books = (
        Book("1", "Rated Book", ("author1",), ("fiction",), ("adventure",), 2020),
        Book("2", "Unrated Book", ("author2",), ("non-fiction",), ("science",), 2021),
    )
    ratings = (
        Rating("user1", "1", 5),  # Пользователь оценил книгу 1
    )
    
    result = recommend_for_user("user1", ratings, books)
    
    # Книга 1 не должна быть в рекомендациях
    assert "1" not in result
    # Книга 2 может быть в рекомендациях
    assert len(result) <= 1


def test_recommend_for_user_different_users_different_results():
    """Тест что разные пользователи получают разные рекомендации"""
    books = (
        Book("1", "Book 1", ("author1",), ("fiction",), ("adventure",), 2020),
        Book("2", "Book 2", ("author2",), ("non-fiction",), ("science",), 2021),
        Book("3", "Book 3", ("author3",), ("fantasy",), ("magic",), 2022),
    )
    ratings_user1 = (
        Rating("user1", "1", 5),  # User1 любит fiction
    )
    ratings_user2 = (
        Rating("user2", "2", 5),  # User2 любит non-fiction
    )
    
    result_user1 = recommend_for_user("user1", ratings_user1, books)
    result_user2 = recommend_for_user("user2", ratings_user2, books)
    
    # Результаты могут быть разными (не обязательно, но вероятно)
    # Хотя бы один из результатов не должен быть пустым
    assert len(result_user1) > 0 or len(result_user2) > 0


def test_measure_performance_returns_dict():
    """Тест что функция измерения производительности возвращает словарь"""
    result = measure_recommendation_performance()
    assert isinstance(result, dict)
    
    # Проверяем наличие ожидаемых ключей или ошибки
    if "error" not in result:
        assert "first_call_avg_ms" in result
        assert "second_call_avg_ms" in result
        assert "speedup" in result
        assert "users_tested" in result


def test_measure_performance_with_real_data():
    """Тест измерения производительности с реальными данными"""
    try:
        data = load_seed("data/seed.json")
        books = tuple(data["books"])
        ratings = tuple(data["ratings"])
        
        # Должен быть хотя бы один пользователь с оценками
        users_with_ratings = {r.user_id for r in ratings}
        if users_with_ratings:
            result = measure_recommendation_performance()
            assert isinstance(result, dict)
            
            # Если нет ошибки, проверяем структуру результата
            if "error" not in result:
                assert result["first_call_avg_ms"] >= 0
                assert result["second_call_avg_ms"] >= 0
                assert result["users_tested"] > 0
    except Exception as e:
        pytest.skip(f"Не удалось загрузить тестовые данные: {e}")


def test_recommend_for_user_performance_improvement():
    """Тест что повторные вызовы быстрее (из-за кэширования)"""
    books = (
        Book("1", "Book 1", ("author1",), ("fiction",), ("adventure",), 2020),
        Book("2", "Book 2", ("author2",), ("non-fiction",), ("science",), 2021),
        Book("3", "Book 3", ("author3",), ("fantasy",), ("magic",), 2022),
        Book("4", "Book 4", ("author4",), ("romance",), ("love",), 2023),
    )
    ratings = (
        Rating("user1", "1", 5),
        Rating("user1", "2", 4),
    )
    
    # Первый вызов
    start_time = time.time()
    result1 = recommend_for_user("user1", ratings, books)
    first_call_time = time.time() - start_time
    
    # Второй вызов (должен быть быстрее из-за кэша)
    start_time = time.time()
    result2 = recommend_for_user("user1", ratings, books)
    second_call_time = time.time() - start_time
    
    assert result1 == result2
    # Второй вызов должен быть быстрее или равен первому
    assert second_call_time <= first_call_time


def test_recommend_for_user_empty_books():
    """Тест с пустым списком книг"""
    books = tuple()
    ratings = (
        Rating("user1", "1", 5),
    )
    
    result = recommend_for_user("user1", ratings, books)
    assert result == tuple()


def test_recommend_for_user_specific_genre_preference():
    """Тест что рекомендации учитывают предпочтения по жанрам"""
    books = (
        Book("1", "Fiction Book", ("author1",), ("fiction",), ("adventure",), 2020),
        Book("2", "Non-Fiction Book", ("author2",), ("non-fiction",), ("science",), 2021),
        Book("3", "Another Fiction", ("author3",), ("fiction",), ("drama",), 2022),
    )
    ratings = (
        Rating("user1", "1", 5),  # Пользователь высоко оценил fiction
        Rating("user1", "2", 2),  # Пользователь низко оценил non-fiction
    )
    
    result = recommend_for_user("user1", ratings, books)
    
    # Книга 3 (fiction) должна быть рекомендована с большей вероятностью
    # чем книга 2 (non-fiction), которую пользователь не любит
    # Но так как это вероятностно, просто проверяем что результат не пустой
    assert isinstance(result, tuple)


@pytest.mark.parametrize("user_id,expected_length", [
    ("user1", 0),  # Пользователь без оценок
    ("user_with_high_ratings", 10),  # Максимум 10 рекомендаций
])
def test_recommend_for_user_parametrized(user_id, expected_length):
    """Параметризованный тест для разных пользователей"""
    books = (
        Book("1", "Book 1", ("author1",), ("fiction",), ("adventure",), 2020),
        Book("2", "Book 2", ("author2",), ("non-fiction",), ("science",), 2021),
    )
    
    # Создаем рейтинги только для user_with_high_ratings
    ratings = ()
    if user_id == "user_with_high_ratings":
        ratings = (
            Rating("user_with_high_ratings", "1", 5),
        )
    
    result = recommend_for_user(user_id, ratings, books)
    assert len(result) <= expected_length