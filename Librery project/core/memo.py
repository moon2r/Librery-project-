from functools import lru_cache
from typing import Tuple, List, Dict, Any
import time

from .domain import Book, Rating
from .transforms import load_seed 


@lru_cache(maxsize=128)
def recommend_for_user(
    user_id: str,
    ratings_index: Tuple[Rating, ...],
    books_index: Tuple[Book, ...]
) -> Tuple[str, ...]:
    user_ratings = [r for r in ratings_index if r.user_id == user_id]
    
    if not user_ratings:
        return tuple()
    
    user_profile = _build_user_profile(user_ratings, books_index)

    book_scores = []
    for book in books_index:
        if not any(r.book_id == book.id for r in user_ratings):
            score = _calculate_similarity(user_profile, book)
            book_scores.append((book.id, score))
    
    book_scores.sort(key=lambda x: x[1], reverse=True)
    return tuple(book_id for book_id, _ in book_scores[:10])


def _build_user_profile(user_ratings: List[Rating], books: Tuple[Book, ...]) -> Dict[str, Dict[str, float]]:
    profile = {'genres': {}, 'authors': {}, 'tags': {}}
    
    for rating in user_ratings:
        book = next((b for b in books if b.id == rating.book_id), None)
        if book:
            weight = max(0, rating.value - 3)  # Вес оценки
            
            for genre in book.genres:
                profile['genres'][genre] = profile['genres'].get(genre, 0) + weight
            
            for author_id in book.author_ids:
                profile['authors'][author_id] = profile['authors'].get(author_id, 0) + weight
            
            for tag in book.tags:
                profile['tags'][tag] = profile['tags'].get(tag, 0) + weight
    
    return profile


def _calculate_similarity(profile: Dict[str, Dict[str, float]], book: Book) -> float:
    score = 0.0
    
    for genre in book.genres:
        score += profile['genres'].get(genre, 0)
    
    for author_id in book.author_ids:
        score += profile['authors'].get(author_id, 0)
    
    for tag in book.tags:
        score += profile['tags'].get(tag, 0)
    
    return score


def measure_recommendation_performance() -> Dict[str, Any]:
    try:
        data = load_seed("data/seed.json")  
        books = tuple(data["books"])
        ratings = tuple(data["ratings"])
        
        users_with_ratings = list({r.user_id for r in ratings})
        test_users = users_with_ratings[:5] if len(users_with_ratings) >= 5 else users_with_ratings
        
        if not test_users:
            return {"error": "Нет пользователей с оценками"}
        
        start_time = time.time()
        for user_id in test_users:
            recommend_for_user(user_id, ratings, books)
        first_call_time = time.time() - start_time
        
        start_time = time.time()
        for user_id in test_users:
            recommend_for_user(user_id, ratings, books)
        second_call_time = time.time() - start_time
        
        return {
            "first_call_avg_ms": round((first_call_time / len(test_users)) * 1000, 2),
            "second_call_avg_ms": round((second_call_time / len(test_users)) * 1000, 2),
            "speedup": round(first_call_time / second_call_time, 2) if second_call_time > 0 else 0,
            "users_tested": len(test_users)
        }
    
    except Exception as e:
        return {"error": str(e)}