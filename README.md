# xterG_library

A lightweight FastAPI application that lets you search for books via the Google Books API, save them to a MongoDB “bookshelf,” and perform flexible queries and recommendations.

## Features

- **Fetch books from Google Books**: Search for books by keyword.
- **Save books to your bookshelf**: Save a book to your MongoDB bookshelf by its Google Books volume ID.
- **View your bookshelf**: Retrieve all saved books.
- **Search your bookshelf**: Search saved books by ID, title, or author.
- **Get book recommendations**: Recommend related books based on an author.

## Prerequisites

- Python 3.9+
- A MongoDB instance (local or Atlas)
- Access to the Google Books API (no API key required for basic volume lookup)

## Setup

1. **Clone the repository:**

   ```bash
   git clone https://github.com/your-username/xterG_library.git
   cd xterG_library
   ```

2. **Create and activate a virtual environment:**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. **Install the dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Set up your environment variables:**

   Create a `.env` file in the root of the project and add your MongoDB connection string:

   ```
   MONGO_URI="your_mongodb_connection_string"
   ```

5. **Run the application:**

   ```bash
   uvicorn main:app --reload
   ```

   The application will be running at `http://127.0.0.1:8000`.

## API Endpoints

You can access the interactive API documentation at `http://127.0.0.1:8000/docs`.

### Fetch Books

- **GET `/fetch_books/`**

  Searches for books on the Google Books API.

  - **Query Parameter:**
    - `query` (string, required): The search term.

  - **Example:**

    ```bash
    curl -X GET "http://127.0.0.1:8000/fetch_books/?query=python"
    ```

### Save Book

- **POST `/save_book_by_id/`**

  Saves a book to your bookshelf.

  - **Query Parameters:**
    - `book_id` (string, required): The Google Books ID of the book.
    - `user_status` (string, optional): The reading status ("unread", "reading", "finished"). Defaults to "unread".

  - **Example:**

    ```bash
    curl -X POST "http://127.0.0.1:8000/save_book_by_id/?book_id=some_book_id&user_status=reading"
    ```

### Bookshelf

- **GET `/bookshelf/`**

  Retrieves all books from your bookshelf.

  - **Example:**

    ```bash
    curl -X GET "http://127.0.0.1:8000/bookshelf/"
    ```

- **GET `/search_bookshelf/`**

  Searches for books on your bookshelf.

  - **Query Parameter:**
    - `search` (string, required): The search term (can be a book ID, title, or author).

  - **Example:**

    ```bash
    curl -X GET "http://127.0.0.1:8000/search_bookshelf/?search=some_author"
    ```

### Recommendations

- **GET `/recommendations/{title}`**

  Recommends books based on the authors of a book in your bookshelf.

  - **Path Parameter:**
    - `title` (string, required): The title of the book in your bookshelf.

  - **Example:**

    ```bash
    curl -X GET "http://127.0.0.1:8000/recommendations/some_book_title"
    ```
