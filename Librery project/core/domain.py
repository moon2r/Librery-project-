from dataclasses import dataclass
from typing import Optional, Tuple, Literal

BookID = str
UserID = str
AuthorID = str
TagID = str
GenreID = str
LoanStatus = Literal["active", "returned", "overdue"]

__all__ = [
    "Author", "Book", "User", "Rating", "Review", "Loan", "Tag", "Genre",
    "BookID", "UserID", "AuthorID", "TagID", "GenreID", "LoanStatus",
]

@dataclass(frozen=True, slots=True)
class Author:
    id: AuthorID
    name: str

@dataclass(frozen=True, slots=True)
class Book:
    id: BookID
    title: str
    author_ids: Tuple[AuthorID, ...]
    genres: Tuple[GenreID, ...]
    tags: Tuple[TagID, ...]
    year: int

@dataclass(frozen=True, slots=True)
class User:
    id: UserID
    name: str

@dataclass(frozen=True, slots=True)
class Rating:
    user_id: UserID
    book_id: BookID
    value: int  # 1..5

@dataclass(frozen=True, slots=True)
class Review:
    id: str
    user_id: UserID
    book_id: BookID
    text: str
    ts: str  # ISO-8601

@dataclass(frozen=True, slots=True)
class Loan:
    id: str
    user_id: UserID
    book_id: BookID
    start: str
    end: Optional[str]
    status: LoanStatus  # "active" | "returned" | "overdue"

@dataclass(frozen=True, slots=True)
class Tag:
    id: TagID
    name: str
    parent_id: Optional[TagID]

@dataclass(frozen=True, slots=True)
class Genre:
    id: GenreID
    name: str
    parent_id: Optional[GenreID]
