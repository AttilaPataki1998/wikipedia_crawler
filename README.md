# Wikipedia Article Analyzer API

A FastAPI-based server that analyzes the textual content of Wikipedia articles. It provides endpoints to compute word frequencies and filter keywords based on percentile thresholds. Built using modern Python tools such as `wikipedia-api`, `TextBlob`, `Polars`, and `FastAPI`.

---

## Features

- Fetches and analyzes Wikipedia article content.
- Computes word frequency distributions.
- Recursively follows linked articles up to a configurable depth.
- Filters out common words or user-defined ignore lists.
- Applies percentile-based keyword filtering.
- Built-in rate limiting to protect the API.
- Asynchronous and performant API with clean code structure.

---

## Technologies Used

| Tool         | Purpose                          |
|--------------|----------------------------------|
| FastAPI      | Web server and API framework     |
| wikipedia-api| Fetch Wikipedia article content  |
| TextBlob     | NLP and word frequency analysis  |
| Polars       | High-performance DataFrame ops   |
| slowapi      | Rate limiting middleware         |
| Pydantic     | Request validation               |

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/AttilaPataki1998/wikipedia_crawler.git
cd wikipedia_crawler
```

### 2. Create a Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

If you don't have a `requirements.txt` yet:

```bash
pip install fastapi uvicorn wikipedia-api textblob polars slowapi
```

---

## Running the Server

```bash
fastapi run app.py
```

Once running, navigate to:  
`http://127.0.0.1:8000/docs` — interactive Swagger UI

---

## API Endpoints

### `GET /word-frequency`

Get word frequencies for a given article and its linked pages.

**Query Parameters:**
- `article` (str): Title of the main Wikipedia article.
- `depth` (int): Number of levels to follow linked articles.

```http
GET /word-frequency?article=Python_(programming_language)&depth=1
```

---

### `POST /keywords`

Compute word frequencies and filter by ignored words and percentile threshold.

**Payload Example:**
```json
{
  "article": "Python (programming language)",
  "depth": 1,
  "ignore_list": ["python", "programming"],
  "percentile": 5
}
```

---

## Rate Limiting

The API includes IP-based rate limiting via `slowapi`.

| Endpoint           | Limit         |
|--------------------|---------------|
| `/word-frequency`  | 30 requests/min |
| `/keywords`        | 15 requests/min  |

---

## Testing Ideas

The project includes unit tests for the main functionalities.
to run the tests, use the following command in the wiki_crawler directory:

```bash
pytest tests/
```

---

## Future Improvements

- Add Redis-backed rate limiting for distributed setups.
- Integrate `spaCy` for more advanced NLP.
- Add caching for article data to reduce redundant requests.
- Improve response schema (e.g., sorted frequencies, metadata).
- Add authentication to manage user-based limits.

---

## Author

Developed as part of a senior Python developer take-home assignment.  
For inquiries, reach out at: `atti.pataki1998@gmail.com`

---

## License

This project does not contain a license file yet.