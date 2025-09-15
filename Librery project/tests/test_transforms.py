# tests/test_transforms.py
from pathlib import Path
import json

from core.domain import Rating, Loan
from core.transforms import load_seed, add_rating, update_loan, avg_rating_for_book


def _write_tmp_seed(tmp_path: Path) -> Path:
    """Создаёт минимальный seed.json для теста load_seed"""
    data = {
        "authors": [{"id": "a1", "name": "Автор"}],
        "books": [
            {
                "id": "b1",
                "title": "Книга",
                "author_ids": ["a1"],
                "genres": ["g1"],
                "tags": ["t1"],
                "year": 2020,
            }
        ],
        "users": [{"id": "u1", "name": "User 1"}],
        "ratings": [{"user_id": "u1", "book_id": "b1", "value": 5}],
        "reviews": [],
        "loans": [
            {
                "id": "l1",
                "user_id": "u1",
                "book_id": "b1",
                "start": "2025-01-01",
                "end": None,
                "status": "active",
            }
        ],
        "tags": [{"id": "t1", "name": "tag", "parent_id": None}],
        "genres": [{"id": "g1", "name": "genre", "parent_id": None}],
    }
    p = tmp_path / "seed.json"
    p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return p


def test_load_seed_ok(tmp_path: Path):
    """Проверяем загрузку seed.json"""
    seed = _write_tmp_seed(tmp_path)
    data = load_seed(str(seed))
    assert len(data["books"]) == 1
    assert data["books"][0].title == "Книга"
    assert data["authors"][0].name == "Автор"


def test_add_rating_is_immutable():
    """Добавление оценки не меняет исходный кортеж"""
    rs = (Rating("u1", "b1", 5),)
    new_rs = add_rating(rs, Rating("u2", "b1", 4))
    assert len(rs) == 1          # старый остался
    assert len(new_rs) == 2      # новый увеличился


def test_update_loan_only_target_changes():
    """Обновляется только нужный Loan"""
    loans = (
        Loan("l1", "u1", "b1", "2025-01-01", None, "active"),
        Loan("l2", "u2", "b2", "2025-01-02", None, "active"),
    )
    new_loans = update_loan(loans, "l1", "returned", "2025-01-05")
    assert new_loans[0].status == "returned"
    assert new_loans[0].end == "2025-01-05"
    assert new_loans[1] == loans[1]  # второй элемент не изменился


def test_avg_rating_for_book_basic():
    """Средний рейтинг считается правильно"""
    rs = (
        Rating("u1", "b1", 5),
        Rating("u2", "b1", 3),
        Rating("u3", "b2", 4),
    )
    assert abs(avg_rating_for_book(rs, "b1") - 4.0) < 1e-9


def test_avg_rating_for_book_empty_returns_zero():
    """Для книги без оценок возвращается 0"""
    assert avg_rating_for_book((), "bX") == 0.0
