
"""
This module implements a lightweight FastAPI application for managing a digital bookshelf.

It allows users to search for books via the Google Books API, save them to a MongoDB
bookshelf, and perform various queries and recommendations. The application provides
endpoints for fetching books, saving them by ID, retrieving the entire bookshelf,
searching for specific books, and getting recommendations based on authors.
"""
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from pymongo.errors import PyMongoError
import requests
from db import collection  

app = FastAPI()

GOOGLE_BOOKS_API_URL = "https://www.googleapis.com/books/v1/volumes"
MAX_RESULTS = 10


class Book(BaseModel):
    """
    Represents a book in the user's bookshelf.

    Attributes:
        title (str): The title of the book.
        authors (List[str]): A list of authors of the book.
        published_date (str): The publication date of the book.
        publisher (Optional[str]): The publisher of the book.
        user_status (str): The user's reading status for the book (e.g., "unread", "reading", "finished").
        book_id (str): The unique Google Books ID for the book.
    """
    title: str
    authors: List[str] = []
    published_date: str = "Unknown"
    publisher: Optional[str] = None
    user_status: str = "unread"  
    book_id: str 


class BookItem(BaseModel):
    """
    Represents a book item as returned by the Google Books API.

    Attributes:
        id (Optional[str]): The unique Google Books ID for the book.
        volumeInfo (Optional[dict]): A dictionary containing detailed information about the book.
    """
    id: Optional[str] = None
    volumeInfo: Optional[dict] = {}


# 1. Search for books using the Google Books API

@app.get("/fetch_books/", tags=["Fetch Books"])
def fetch_books(query: str):
    """
    Searches for books on the Google Books API based on a query.

    Args:
        query (str): The search term to use for finding books.

    Returns:
        List[dict]: A list of books matching the search query.

    Raises:
        HTTPException: If there is an error communicating with the Google Books API.
    """
    try:
        params = {"q": query, "maxResults": MAX_RESULTS}
        response = requests.get(GOOGLE_BOOKS_API_URL, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()

        books = []
        for item in data.get("items", []):
            volume = item.get("volumeInfo", {})
            book = {
                "book_id": item.get("id"),
                "title": volume.get("title"),
                "authors": volume.get("authors", []),
                "published_date": volume.get("publishedDate", "Unknown"),
                "publisher": volume.get("publisher"),
                "user_status": "unread",  # Default status
            }
            books.append(book)
        return books

    except requests.RequestException as e:
        raise HTTPException(status_code=503, detail=f"Google Books API error: {e}")



# 2. Add new book to MongoDB from Google Books using book id.
#  This should save into the bookshelf library

@app.post("/save_book_by_id/", tags=["Save Book"])
def save_book_by_id(
    book_id: str,
    user_status: str = Query(
        "unread", description="User's reading status for the book"
    ),
):
    """
    Saves a book to the user's bookshelf using its Google Books ID.

    Args:
        book_id (str): The Google Books ID of the book to save.
        user_status (str, optional): The user's reading status for the book. Defaults to "unread".

    Returns:
        dict: A message confirming the book was saved and the book data.

    Raises:
        HTTPException: If the book is not found on Google Books, if the book already exists in the bookshelf,
                       or if there is a database or API error.
    """
    try:
        # fetch directly by volume ID (fixed)
        response = requests.get(f"{GOOGLE_BOOKS_API_URL}/{book_id}", timeout=5)
        if response.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail=f"Book with ID '{book_id}' not found on Google Books.",
            )
        response.raise_for_status()
        data = response.json()

        volume = data.get("volumeInfo", {})

     
        book_to_save = Book(
            book_id=data.get("id"),
            title=volume.get("title"),
            authors=volume.get("authors", []),
            published_date=volume.get("publishedDate", "Unknown"),
            publisher=volume.get("publisher"),
            user_status=user_status,
        )

        # Check if book already exists
        if collection.find_one({"book_id": book_id}):
            raise HTTPException(
                status_code=409,
                detail=f"Book with ID '{book_id}' already exists in your bookshelf.",
            )

        # Save to MongoDB
        collection.insert_one(book_to_save.dict())

        return {
            "message": "Book saved successfully to bookshelf",
            "book": book_to_save.dict(),
        }

    except requests.RequestException as e:
        raise HTTPException(status_code=503, detail=f"Google Books API error: {e}")
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving book: {e}")



# 3. Fetch all books from bookshelf

@app.get("/bookshelf/", tags=["Bookshelf"])
def fetch_bookshelf():
    """
    Retrieves all books from the user's bookshelf.

    Returns:
        List[dict]: A list of all books in the bookshelf.
    """
    books = list(collection.find({}, {"_id": 0}))
    return books


#  4. Search book in bookshelf by either book id, title or author


@app.get("/search_bookshelf/", tags=["Bookshelf"])
def search_bookshelf(search: str):
    """
    Searches for books in the bookshelf by ID, title, or author.

    Args:
        search (str): The search term to use.

    Returns:
        List[dict]: A list of books matching the search criteria.

    Raises:
        HTTPException: If the search term is empty.
    """
    if not search.strip():
        raise HTTPException(status_code=400, detail="Search term cannot be empty")
    query = {
        "$or": [
            {"book_id": {"$regex": search, "$options": "i"}},
            {"title": {"$regex": search, "$options": "i"}},
            {"authors": {"$elemMatch": {"$regex": search, "$options": "i"}}},
        ]
    }

    books = list(collection.find(query, {"_id": 0}))
    return books


# Recommend books based on authors of a given book title


@app.get("/recommendations/{title}", tags=["Recommendations"])
def recommend_books(title: str):
    """
    Recommends books based on the authors of a book in the bookshelf.

    Args:
        title (str): The title of the book to get recommendations for.

    Returns:
        List[dict]: A list of recommended books.

    Raises:
        HTTPException: If the book is not found in the bookshelf or has no authors.
    """
    book = collection.find_one({"title": title})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found in bookshelf")

    authors = book.get("authors", [])
    if not authors:
        raise HTTPException(status_code=404, detail="No authors found for this book")

    recommendations = []
    seen_ids = set()

    for author in authors:
        try:
            response = requests.get(
                GOOGLE_BOOKS_API_URL,
                params={"q": f"inauthor:{author}", "maxResults": 5},
                timeout=5,
            )
            response.raise_for_status()
            data = response.json()

            for item in data.get("items", []):
                vol = item.get("volumeInfo", {})
                rec_book_id = item.get("id")
                rec_title = vol.get("title")

                if (
                    rec_book_id
                    and rec_title
                    and rec_title != title
                    and rec_book_id not in seen_ids
                ):
                    recommendations.append(
                        {
                            "title": rec_title,
                            "authors": vol.get("authors", []),
                            "published_date": vol.get("publishedDate", "Unknown"),
                            "book_id": rec_book_id,
                        }
                    )
                    seen_ids.add(rec_book_id)

        except requests.RequestException:
            continue

    return recommendations
