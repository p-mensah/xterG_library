# xterG_library

A lightweight FastAPI application that lets you search for books via the Google Books API, save them to a MongoDB “bookshelf,” and perform flexible queries and recommendations.

Features
- Fetch books from Google Books by keyword
- Save a book to MongoDB by Google Books volume ID
- Retrieve all saved books
- Search saved books by ID, title, or author with a single search field
- Recommend related books based on an author

Prerequisites
- Python 3.9+
- MongoDB instance (local or Atlas)
- Google Books API access (no API key required for basic volume lookup)
