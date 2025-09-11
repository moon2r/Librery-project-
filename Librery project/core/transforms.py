import json
from pathlib import Path
from functools import reduce
from typing import Tuple, Dict, Any

from core.domain import Author, Book, User, Rating, Review, Loan, Tag, Genre

def load_seed(path: str) -> Dict[str, Tuple[Any, ...]]:
    file_path = Path(path)
    with file_path.open(encoding="utf-8") as f:
        raw = json.load(f)

    authors = tuple(Author(**a) for a in raw.get("authors", []))
    books = tuple(Book(**b) for b in raw.get("books", []))
    users = tuple(User(**u) for u in raw.get("users", []))
    ratings = tuple(Rating(**r) for r in raw.get("ratings", []))
    reviews = tuple(Review(**rv) for rv in raw.get("reviews", []))
    loans = tuple(Loan(**l) for l in raw.get("loans", []))
    tags = tuple(Tag(**t) for t in raw.get("tags", []))
    genres = tuple(Genre(**g) for g in raw.get("genres", []))

    return {
        "authors": authors,
        "books": books,
        "users": users,
        "ratings": ratings,
        "reviews": reviews,
        "loans": loans,
        "tags": tags,
        "genres": genres,
    }

def add_rating(ratings: Tuple[Rating, ...], r: Rating) -> Tuple[Rating, ...]:
    return ratings + (r,)

def update_loan(
    loans: Tuple[Loan, ...], loan_id: str, status: str, end: str | None
) -> Tuple[Loan, ...]:
    return tuple(
        Loan(
            id=l.id,
            user_id=l.user_id,
            book_id=l.book_id,
            start=l.start,
            end=end if l.id == loan_id else l.end,
            status=status if l.id == loan_id else l.status,
        )
        for l in loans
    )

def avg_rating_for_book(ratings: Tuple[Rating, ...], book_id: str) -> float:
    filtered = tuple(filter(lambda r: r.book_id == book_id, ratings))
    if not filtered:
        return 0.0
    total = reduce(lambda acc, r: acc + r.value, filtered, 0)
    return total / len(filtered)
