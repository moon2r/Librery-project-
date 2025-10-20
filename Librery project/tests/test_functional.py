from core.domain import Book, Rating, Review, Loan, Genre
from core import functional as fn


GENRES = (
    Genre(id="g1", name="root", parent_id=None),
    Genre(id="g2", name="child", parent_id="g1"),
    Genre(id="g3", name="other", parent_id=None),
)

BOOKS = (
    Book(id="b1", title="Book One", author_ids=(), genres=("g2",), tags=(), year=2020),
    Book(id="b2", title="Book Two", author_ids=(), genres=("g3",), tags=(), year=2021),
)

RATINGS = (
    Rating(user_id="u1", book_id="b1", value=5),
    Rating(user_id="u2", book_id="b1", value=3),
    Rating(user_id="u3", book_id="b2", value=2),
)

REVIEWS = (
    Review(id="r1", user_id="u1", book_id="b1", text="ok", ts="2025-01-01T00:00:00"),
)

LOANS = (
    Loan(id="l1", user_id="u1", book_id="b1", start="2025-01-01", end=None, status="active"),
    Loan(id="l2", user_id="u1", book_id="b2", start="2025-01-02", end="2025-01-10", status="returned"),
)

# ------------------ ТЕСТЫ ------------------

def test_user_has_active_loan_true_false():
    assert fn.user_has_active_loan(LOANS, "u1") is True
    assert fn.user_has_active_loan(LOANS, "u2") is False

def test_book_has_reviews_true_false():
    assert fn.book_has_reviews(REVIEWS, "b1") is True
    assert fn.book_has_reviews(REVIEWS, "b2") is False

def test_book_avg_ge_predicate():
    assert fn.book_avg_ge(RATINGS, "b1", 4.0) is True
    assert fn.book_avg_ge(RATINGS, "b1", 4.1) is False
    assert fn.book_avg_ge(RATINGS, "b2", 2.1) is False

def test_books_with_avg_ge_filters_correctly():
    res = fn.books_with_avg_ge(RATINGS, BOOKS, 3.5)
    ids = tuple(b.id for b in res)
    assert ids == ("b1",)  

def test_top_books_by_avg_sorted_and_limited():
    top = fn.top_books_by_avg(RATINGS, BOOKS, 2)
    assert top[0][0] == "b1" and top[0][1] >= top[1][1]
    top1 = fn.top_books_by_avg(RATINGS, BOOKS, 1)
    assert len(top1) == 1 and top1[0][0] == "b1"

def test_genre_ancestors_chain():
    ancestors = fn.genre_ancestors(GENRES, "g2")
    assert tuple(g.id for g in ancestors) == ("g1",)
    assert fn.genre_ancestors(GENRES, "g1") == ()

def test_book_in_genre_recursive_true_for_ancestor():
    assert fn.book_in_genre_recursive(BOOKS[0], GENRES, "g1") is True
    assert fn.book_in_genre_recursive(BOOKS[0], GENRES, "g3") is False
