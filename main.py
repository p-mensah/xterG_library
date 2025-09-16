# from fastapi import FastAPI, HTTPException, Query
# from pydantic import BaseModel
# from typing import List, Optional, Dict
# from pymongo import MongoClient
# from pymongo.errors import PyMongoError
# import requests
# from db import collection  # your MongoDB collection

# app = FastAPI()

# GOOGLE_BOOKS_API_URL = "https://www.googleapis.com/books/v1/volumes"
# MAX_RESULTS = 10


# # Pydantic models
# class Book(BaseModel):
#     title: str
#     authors: List[str] = []
#     published_date: str = "Unknown"
#     publisher: Optional[str] = None
#     description: Optional[str] = None
#     user_status: str = "unread"  # "reading", "finished", "unread"
#     book_id: str  # unique Google Books ID


# class BookItem(BaseModel):
#     id: Optional[str] = None
#     volumeInfo: Optional[dict] = {}


# class SaveBooksRequest(BaseModel):
#     books: List[BookItem]


# # 1. Search books from Google Books API
# @app.get("/fetch_books/", tags=["Fetch Books"])
# def fetch_books(query: str):
#     try:
#         params = {"q": query, "maxResults": MAX_RESULTS}
#         response = requests.get(GOOGLE_BOOKS_API_URL, params=params, timeout=5)
#         response.raise_for_status()
#         data = response.json()
#         books = []
#         for item in data.get("items", []):
#             volume = item.get("volumeInfo", {})
#             book = {
#                 "book_id": item.get("id"),
#                 "title": volume.get("title"),
#                 "authors": volume.get("authors", []),
#                 "published_date": volume.get("publishedDate", "Unknown"),
#                 "publisher": volume.get("publisher"),
#                 "user_status": "unread", # Default status for fetched books
#             }
#             books.append(book)
#         return books
#     except requests.RequestException as e:
#         raise HTTPException(status_code=503, detail=f"Google Books API error: {e}")


# # 2. Add new books to MongoDB bookshelf
# @app.post("/save_book_by_id/", tags=["Save Book"])
# def save_book_by_id(
#     book_id: str,
#     user_status: str = Query("unread", description="User's reading status for the book"),
# ):
#     try:
#         # 1. Fetch book details from Google Books API
#         params = {"q": f"id:{book_id}"}
#         response = requests.get(GOOGLE_BOOKS_API_URL, params=params, timeout=5)
#         response.raise_for_status()
#         data = response.json()

#         if not data.get("items"):
#             raise HTTPException(status_code=404, detail=f"Book with ID '{book_id}' not found on Google Books.")

#         item = data["items"]
#         volume = item.get("volumeInfo", {})

#         # 2. Construct Book object
#         book_to_save = Book(
#             book_id=item.get("id"),
#             title=volume.get("title"),
#             authors=volume.get("authors", []),
#             published_date=volume.get("publishedDate", "Unknown"),
#             publisher=volume.get("publisher"),
#             user_status=user_status,
#         )

#         # 3. Check if book already exists in MongoDB
#         if collection.find_one({"book_id": book_id}):
#             raise HTTPException(status_code=409, detail=f"Book with ID '{book_id}' already exists in your bookshelf.")

#         # 4. Save the book to MongoDB
#         collection.insert_one(book_to_save.dict())

#         return {"message": "Book saved successfully to bookshelf", "book": book_to_save.dict()}

#     except requests.RequestException as e:
#         raise HTTPException(status_code=503, detail=f"Google Books API error: {e}")
#     except PyMongoError as e:
#         raise HTTPException(status_code=500, detail=f"Database error: {e}")
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error saving book: {e}")

# # 3. Fetch all books from bookshelf
# @app.get("/bookshelf/", tags=["Bookshelf"])
# def fetch_bookshelf():
#     books = list(collection.find({}, {"_id": 0}))
#     return books


# # 4. Search books in bookshelf by title or author
# @app.get("/search_bookshelf/", tags=["Bookshelf"])
# def search_bookshelf(
#     title: Optional[str] = None,
#     author: Optional[str] = None,
# ):
#     query = {}
#     if title:
#         query["title"] = {"$regex": title, "$options": "i"}  # case-insensitive regex
#     if author:
#         query["authors"] = {"$elemMatch": {"$regex": author, "$options": "i"}}
#     if not query:
#         raise HTTPException(status_code=400, detail="Provide at least title or author to search")
#     books = list(collection.find(query, {"_id": 0}))
#     return books


# # 5. Recommend books based on authors of a given book title
# @app.get("/recommendations/{title}", tags=["Recommendations"])
# def recommend_books(title: str):
#     book = collection.find_one({"title": title})
#     if not book:
#         raise HTTPException(status_code=404, detail="Book not found in bookshelf")

#     authors = book.get("authors", [])
#     if not authors:
#         raise HTTPException(status_code=404, detail="No authors found for this book")

#     recommendations = []
#     seen_ids = set()
#     for author in authors:
#         try:
#             response = requests.get(GOOGLE_BOOKS_API_URL, params={"q": f"inauthor:{author}", "maxResults": 5}, timeout=5)
#             response.raise_for_status()
#             data = response.json()
#             for item in data.get("items", []):
#                 vol = item.get("volumeInfo", {})
#                 book_id = item.get("id")
#                 title_ = vol.get("title")
#                 if book_id and title_ and title_ != title and book_id not in seen_ids:
#                     recommendations.append({
#                         "title": title_,
#                         "authors": vol.get("authors", []),
#                         "published_date": vol.get("publishedDate", "Unknown"),
#                         "book_id": book_id,
#                     })
#                     seen_ids.add(book_id)
#         except requests.RequestException:
#             continue

#     return recommendations


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
    title: str
    authors: List[str] = []
    published_date: str = "Unknown"
    publisher: Optional[str] = None
    user_status: str = "unread"  
    book_id: str 


class BookItem(BaseModel):
    id: Optional[str] = None
    volumeInfo: Optional[dict] = {}


# 1. Search for books using the Google Books API

@app.get("/fetch_books/", tags=["Fetch Books"])
def fetch_books(query: str):
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
    books = list(collection.find({}, {"_id": 0}))
    return books


#  4. Search book in bookshelf by either book id, title or author


@app.get("/search_bookshelf/", tags=["Bookshelf"])
def search_bookshelf(search: str):
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
