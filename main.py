# 5. 📚 Book Search
# API: Google Books API
# MongoDB: Save { title, authors, published_date, user_status }
# Endpoints:
# GET /books/{title} → search books
# POST /reading-list → save book + status (“reading”, “finished”)
# GET /reading-list → show reading list
# 💡 Extra Challenge: Add “recommendations” (list books by same author).





from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import re
from db import collection

app = FastAPI()
GOOGLE_BOOKS_API_URL = "https://www.googleapis.com/books/v1/volumes"

class Book(BaseModel):
    title: str
    authors: list[str] = []
    published_date: str = "Unknown"
    user_status: str
    book_id: str

@app.get("/books/{title}")
def search_books(title: str):
    response = requests.get(GOOGLE_BOOKS_API_URL, params={"q": title})
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to fetch books")

    data = response.json()
    if "items" not in data:
        raise HTTPException(status_code=404, detail="No books found")

    return [
        {
            "title": item["volumeInfo"].get("title"),
            "authors": item["volumeInfo"].get("authors", []),
            "published_date": item["volumeInfo"].get("publishedDate", "Unknown"),
            "book_id": item.get("id")
        }
        for item in data["items"]
    ]


@app.post("/reading-list")
def add_book(book: Book):
    if collection.find_one({"title": book.title}):
        raise HTTPException(status_code=409, detail="Book already in reading list")
    
    book_dict = book.model_dump()
    inserted_id = collection.insert_one(book_dict).inserted_id
    return {"message": "Book added", "book_id": str(inserted_id)}

@app.get("/reading-list")
def get_reading_list():
    return list(collection.find({}, {"_id": 0}))


@app.get("/recommendations/{title}")
def recommend_books(title: str):
    book = collection.find_one({"title": title})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    authors = book.get("authors", [])
    if not authors:
        raise HTTPException(status_code=404, detail="No authors for recommendations")

    recommendations = []
    for author in authors:
        response = requests.get(GOOGLE_BOOKS_API_URL, params={"q": f"inauthor:{author}"})
        if response.status_code != 200:
            continue

        data = response.json()
        if "items" not in data:
            continue

        for item in data["items"][:3]:
            volume = item["volumeInfo"]
            full_title = volume.get("title")
            # Use regex to search for books with titles that match a specific pattern
            book_id = item.get("id")
            if full_title and book_id and full_title != title:
                # Check for duplicates before adding
                if not any(rec["book_id"] == book_id for rec in recommendations):
                    recommendations.append({
                        "title": full_title,
                        "authors": volume.get("authors", []),
                        "published_date": volume.get("publishedDate", "Unknown"),
                        "book_id": book_id
                    })

    return recommendations