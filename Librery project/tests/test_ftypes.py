import pytest
from core.ftypes import (
    Maybe, Just, Nothing, Either, Right, Left,
    safe_book, validate_rating, add_rating_pipeline,
    safe_book_analysis
)
from core.domain import Book, Rating, User


def test_maybe_just_operations():
    """Тест 1: Maybe операции с Just"""
    # Создание и базовые операции
    just = Maybe.just(5)
    assert just.is_just() == True
    assert just.is_nothing() == False
    
    # Map преобразование
    doubled = just.map(lambda x: x * 2)
    assert doubled == Just(10)
    
    # Bind композиция
    composed = just.bind(lambda x: Maybe.just(x + 3))
    assert composed == Just(8)
    
    # Получение значения
    assert just.get_or_else(0) == 5


def test_maybe_nothing_operations():
    """Тест 2: Maybe операции с Nothing"""
    nothing = Maybe.nothing()
    assert nothing.is_just() == False
    assert nothing.is_nothing() == True
    
    # Map и bind не выполняют функцию
    result = nothing.map(lambda x: x * 2)
    assert result == Nothing()
    
    result = nothing.bind(lambda x: Maybe.just(10))
    assert result == Nothing()
    
    # Возвращает значение по умолчанию
    assert nothing.get_or_else("default") == "default"


def test_either_validation_success():
    """Тест 3: Either успешная валидация"""
    books = (Book("1", "Book 1", ("author1",), ("fiction",), ("adventure",), 2020),)
    users = (User("1", "John Doe"),)
    ratings = ()
    
    rating = Rating("1", "1", 4)
    result = validate_rating(rating, books, users, ratings)
    
    assert result.is_right() == True
    assert result.get_or_else(None) == rating


def test_either_validation_errors():
    """Тест 4: Either валидация с ошибками"""
    books = (Book("1", "Book 1", ("author1",), ("fiction",), ("adventure",), 2020),)
    users = (User("1", "John Doe"),)
    ratings = ()
    
    # Неверный рейтинг
    rating = Rating("1", "1", 6)
    result = validate_rating(rating, books, users, ratings)
    
    assert result.is_left() == True
    assert "value" in result._error
    
    # Несуществующая книга
    rating = Rating("1", "999", 4)
    result = validate_rating(rating, books, users, ratings)
    
    assert result.is_left() == True
    assert "book_id" in result._error


def test_safe_operations_and_pipeline():
    """Тест 5: Безопасные операции и пайплайны"""
    books = (
        Book("1", "Book 1", ("author1",), ("fiction",), ("adventure",), 2020),
        Book("2", "Book 2", ("author2",), ("non-fiction",), ("science",), 2021),
    )
    users = (User("1", "John Doe"),)
    ratings = (Rating("1", "1", 4),)
    
    # Безопасный поиск существующей книги
    book_result = safe_book(books, "1")
    assert book_result.is_just() == True
    assert book_result.get_or_else(None).title == "Book 1"
    
    # Безопасный поиск несуществующей книги
    book_result = safe_book(books, "999")
    assert book_result.is_nothing() == True
    
    # Безопасный анализ книги
    analysis_result = safe_book_analysis(books, "1", ratings)
    assert analysis_result.is_just() == True
    title, avg = analysis_result.get_or_else(("", 0.0))
    assert title == "Book 1"
    assert avg == 4.0
    
    # Пайплайн добавления рейтинга
    new_rating = Rating("1", "2", 5)  # Оценка для другой книги
    pipeline_result = add_rating_pipeline(new_rating, ratings, books, users)
    assert pipeline_result.is_right() == True