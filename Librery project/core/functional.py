from typing import Tuple
from core.domain import Book, Rating, Review, Loan, Genre
from core.transforms import avg_rating_for_book


# ---------- Предикаты (bool-функции) ----------

def user_has_active_loan(loans: Tuple[Loan, ...], user_id: str) -> bool:
    """
    True, если у пользователя есть хотя бы один активный займ.
    """
    return any(l.user_id == user_id and l.status == "active" for l in loans)


def book_has_reviews(reviews: Tuple[Review, ...], book_id: str) -> bool:
    """
    True, если у книги есть хотя бы один отзыв.
    """
    return any(r.book_id == book_id for r in reviews)


def book_avg_ge(ratings: Tuple[Rating, ...], book_id: str, threshold: float) -> bool:
    """
    True, если средний рейтинг книги >= threshold.
    """
    return avg_rating_for_book(ratings, book_id) >= threshold


def book_in_genre(book: Book, genre_id: str) -> bool:
    """
    True, если книга напрямую имеет жанр с данным id.
    """
    return genre_id in book.genres


def book_has_tag(book: Book, tag_id: str) -> bool:
    """
    True, если книга напрямую имеет тег с данным id.
    """
    return tag_id in book.tags


# ---------- Фильтры / выборки ----------

def books_with_avg_ge(ratings: Tuple[Rating, ...], books: Tuple[Book, ...], threshold: float) -> Tuple[Book, ...]:
    """
    Вернёт все книги, у которых средний рейтинг >= threshold.
    """
    return tuple(b for b in books if book_avg_ge(ratings, b.id, threshold))


def books_of_genre(books: Tuple[Book, ...], genre_id: str) -> Tuple[Book, ...]:
    """
    Вернёт все книги данного жанра (прямая принадлежность).
    """
    return tuple(b for b in books if genre_id in b.genres)


def top_books_by_avg(ratings: Tuple[Rating, ...], books: Tuple[Book, ...], n: int) -> Tuple[tuple[str, float], ...]:
    """
    Вернёт top-N книг как кортеж пар (book_id, avg_rating), отсортированных по рейтингу убыванию.
    """
    avgs = [(b.id, avg_rating_for_book(ratings, b.id)) for b in books]
    avgs_sorted = sorted(avgs, key=lambda x: x[1], reverse=True)
    return tuple(avgs_sorted[:n])


# ---------- Рекурсия ----------

def genre_ancestors(genres: Tuple[Genre, ...], genre_id: str) -> Tuple[Genre, ...]:
    """
    Вернёт всех предков жанра (parent -> parent -> ...).
    """
    by_id = {g.id: g for g in genres}

    def recurse(gid: str) -> Tuple[Genre, ...]:
        g = by_id.get(gid)
        if g is None or g.parent_id is None:
            return ()
        parent = by_id.get(g.parent_id)
        return (parent,) + recurse(parent.id)

    return recurse(genre_id)


def book_in_genre_recursive(book: Book, genres: Tuple[Genre, ...], target_genre_id: str) -> bool:
    """
    True, если книга принадлежит target_genre_id или его потомкам.
    """
    # Сначала находим все жанры-потомки
    def descendants(gid: str) -> set[str]:
        children = [g.id for g in genres if g.parent_id == gid]
        result = set(children)
        for c in children:
            result |= descendants(c)
        return result

    valid_ids = {target_genre_id} | descendants(target_genre_id)
    return any(gid in valid_ids for gid in book.genres)
