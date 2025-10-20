from typing import TypeVar, Generic, Callable, Any, Tuple, Dict
from functools import wraps
from core.domain import Book, Rating, Review, User
from core.transforms import avg_rating_for_book

T = TypeVar('T')
E = TypeVar('E')
U = TypeVar('U')

# ========== MAYBE ==========

class Maybe(Generic[T]):
    """Container for optional values"""
    
    @staticmethod
    def just(value: T) -> 'Just[T]':
        return Just(value)
    
    @staticmethod
    def nothing() -> 'Nothing':
        return Nothing()
    
    @staticmethod
    def from_value(value: T | None) -> 'Maybe[T]':
        return Just(value) if value is not None else Nothing()

class Just(Maybe[T]):
    def __init__(self, value: T):
        self._value = value
    
    def map(self, fn: Callable[[T], U]) -> 'Maybe[U]':
        return Just(fn(self._value))
    
    def bind(self, fn: Callable[[T], Maybe[U]]) -> Maybe[U]:
        return fn(self._value)
    
    def get_or_else(self, default: T) -> T:
        return self._value
    
    def is_just(self) -> bool:
        return True
    
    def is_nothing(self) -> bool:
        return False
    
    def __eq__(self, other):
        return isinstance(other, Just) and self._value == other._value
    
    def __str__(self):
        return f"Just({self._value})"

class Nothing(Maybe[Any]):
    def map(self, fn: Callable[[Any], Any]) -> 'Nothing':
        return self
    
    def bind(self, fn: Callable[[Any], Maybe[Any]]) -> 'Nothing':
        return self
    
    def get_or_else(self, default: T) -> T:
        return default
    
    def is_just(self) -> bool:
        return False
    
    def is_nothing(self) -> bool:
        return True
    
    def __eq__(self, other):
        return isinstance(other, Nothing)
    
    def __str__(self):
        return "Nothing"

# ========== EITHER ==========

class Either(Generic[E, T]):
    """Container for operations that can fail"""
    
    @staticmethod
    def right(value: T) -> 'Right[T]':
        return Right(value)
    
    @staticmethod
    def left(error: E) -> 'Left[E]':
        return Left(error)

class Right(Either[Any, T]):
    def __init__(self, value: T):
        self._value = value
    
    def map(self, fn: Callable[[T], U]) -> 'Either[Any, U]':
        return Right(fn(self._value))
    
    def bind(self, fn: Callable[[T], Either[E, U]]) -> 'Either[E, U]':
        return fn(self._value)
    
    def get_or_else(self, default: T) -> T:
        return self._value
    
    def is_right(self) -> bool:
        return True
    
    def is_left(self) -> bool:
        return False
    
    def __eq__(self, other):
        return isinstance(other, Right) and self._value == other._value
    
    def __str__(self):
        return f"Right({self._value})"

class Left(Either[E, Any]):
    def __init__(self, error: E):
        self._error = error
    
    def map(self, fn: Callable[[Any], Any]) -> 'Left[E]':
        return self
    
    def bind(self, fn: Callable[[Any], Either[E, Any]]) -> 'Left[E]':
        return self
    
    def get_or_else(self, default: T) -> T:
        return default
    
    def is_right(self) -> bool:
        return False
    
    def is_left(self) -> bool:
        return True
    
    def __eq__(self, other):
        return isinstance(other, Left) and self._error == other._error
    
    def __str__(self):
        return f"Left({self._error})"

# ========== SAFE OPERATIONS ==========

def safe_book(books: Tuple[Book, ...], book_id: str) -> Maybe[Book]:
    """Safe book lookup by ID"""
    book = next((b for b in books if b.id == book_id), None)
    return Maybe.from_value(book)

def safe_user(users: Tuple[User, ...], user_id: str) -> Maybe[User]:
    """Safe user lookup by ID"""
    user = next((u for u in users if u.id == user_id), None)
    return Maybe.from_value(user)

# ========== VALIDATION ==========

def validate_rating(rating: Rating, 
                   books: Tuple[Book, ...], 
                   users: Tuple[User, ...],
                   existing_ratings: Tuple[Rating, ...]) -> Either[Dict[str, str], Rating]:
    """Rating validation"""
    errors = {}
    
    # Value range check
    if not (1 <= rating.value <= 5):
        errors["value"] = "Rating must be between 1 and 5"
    
    # Book existence check
    if not any(b.id == rating.book_id for b in books):
        errors["book_id"] = f"Book with ID {rating.book_id} not found"
    
    # User existence check
    if not any(u.id == rating.user_id for u in users):
        errors["user_id"] = f"User with ID {rating.user_id} not found"
    
    # Duplicate check
    if any(r.user_id == rating.user_id and r.book_id == rating.book_id 
           for r in existing_ratings):
        errors["duplicate"] = "User already rated this book"
    
    return Either.left(errors) if errors else Either.right(rating)

def validate_review(review: Review,
                   books: Tuple[Book, ...],
                   users: Tuple[User, ...]) -> Either[Dict[str, str], Review]:
    """Review validation"""
    errors = {}
    
    # Book existence
    if not any(b.id == review.book_id for b in books):
        errors["book_id"] = f"Book with ID {review.book_id} not found"
    
    # User existence
    if not any(u.id == review.user_id for u in users):
        errors["user_id"] = f"User with ID {review.user_id} not found"
    
    # Text validation
    if not review.text or len(review.text.strip()) < 10:
        errors["text"] = "Review text must contain at least 10 characters"
    
    return Either.left(errors) if errors else Either.right(review)

# ========== PIPELINES ==========

def add_rating_pipeline(rating: Rating,
                       ratings: Tuple[Rating, ...],
                       books: Tuple[Book, ...],
                       users: Tuple[User, ...]) -> Either[Dict[str, str], Tuple[Rating, ...]]:
    """Rating addition pipeline"""
    
    def add_rating(valid_rating: Rating) -> Either[Dict[str, str], Tuple[Rating, ...]]:
        return Either.right(ratings + (valid_rating,))
    
    return validate_rating(rating, books, users, ratings).bind(add_rating)

def add_review_pipeline(review: Review,
                       reviews: Tuple[Review, ...],
                       books: Tuple[Book, ...],
                       users: Tuple[User, ...],
                       ratings: Tuple[Rating, ...]) -> Either[Dict[str, str], Tuple[Review, ...]]:
    """Review addition pipeline"""
    
    def add_review(valid_review: Review) -> Either[Dict[str, str], Tuple[Review, ...]]:
        new_reviews = reviews + (valid_review,)
        return Either.right(new_reviews)
    
    return validate_review(review, books, users).bind(add_review)

def safe_book_analysis(books: Tuple[Book, ...], 
                      book_id: str, 
                      ratings: Tuple[Rating, ...]) -> Maybe[Tuple[str, float]]:
    """Safe book analysis with Maybe composition"""
    
    def calculate_avg(book: Book) -> Maybe[Tuple[str, float]]:
        avg = avg_rating_for_book(ratings, book.id)
        return Maybe.just((book.title, avg))
    
    return safe_book(books, book_id).bind(calculate_avg)

# ========== DEMOS ==========

def demonstrate_maybe_usage():
    """Maybe usage demonstration"""
    books = (
        Book("1", "Book 1", ("author1",), ("fiction",), ("adventure",), 2020),
        Book("2", "Book 2", ("author2",), ("non-fiction",), ("science",), 2021),
    )
    
    result = (safe_book(books, "1")
             .map(lambda book: book.title.upper())
             .get_or_else("Book not found"))
    
    return result

def demonstrate_either_usage():
    """Either usage demonstration"""
    books = (Book("1", "Book 1", ("author1",), ("fiction",), ("adventure",), 2020),)
    users = (User("user1", "John Doe"),)
    ratings = ()
    
    rating = Rating("user1", "1", 4)
    
    result = (validate_rating(rating, books, users, ratings)
             .map(lambda r: f"Rating {r.value} accepted")
             .get_or_else("Validation error"))
    
    return result