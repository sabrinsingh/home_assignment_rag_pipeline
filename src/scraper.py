import time
from datetime import datetime, timezone
from io import BytesIO
from bs4 import BeautifulSoup
from requests.exceptions import RequestException

from rag_utils import get_minio_client, safe_get

BASE_URL = "https://books.toscrape.com"
START_URL = f"{BASE_URL}/catalogue/page-1.html"
MAX_BOOKS = 50
HEADERS = {"User-Agent": "Mozilla/5.0"}
RAW_FOLDER = "raw"

client, MINIO_BUCKET = get_minio_client()

MAX_RETRIES = 5
RETRY_BACKOFF = [1, 2, 4, 8, 16]  # Backoff durations in seconds

def safe_get_with_retries(url: str, headers: dict, retries: int = MAX_RETRIES) -> str | None:
    for attempt in range(retries):
        try:
            response = safe_get(url, headers=headers)
            if response:
                return response
            else:
                print(f"❌ Request attempt {attempt + 1} failed for {url}")
        except (RequestException, Exception) as e:
            print(f"❌ Attempt {attempt + 1} error for {url}: {e}")
        
        backoff_time = RETRY_BACKOFF[min(attempt, len(RETRY_BACKOFF) - 1)]
        print(f"⏳ Retrying in {backoff_time} seconds...")
        time.sleep(backoff_time)
    return None

def get_book_links(max_books: int = MAX_BOOKS) -> list[str]:
    book_links = []
    page = 1

    while len(book_links) < max_books:
        url = f"{BASE_URL}/catalogue/page-{page}.html"
        res = safe_get_with_retries(url, headers=HEADERS)
        if not res:
            print("❌ Failed to get page, stopping.")
            break

        soup = BeautifulSoup(res.text, "html.parser")
        articles = soup.select("article.product_pod")

        if not articles:
            break  # No more books/pages

        for book in articles:
            href = book.find("a")["href"]
            full_link = BASE_URL + "/catalogue/" + href.strip().replace('../../../', '')
            book_links.append(full_link)
            if len(book_links) >= max_books:
                break

        page += 1
        time.sleep(1)

    return book_links

def download_book_details(book_url: str) -> dict | None:
    res = safe_get_with_retries(book_url, headers=HEADERS)
    if not res:
        return None

    soup = BeautifulSoup(res.text, "html.parser")

    title_tag = soup.select_one("div.product_main h1")
    price_tag = soup.select_one("p.price_color")
    availability_tag = soup.select_one("p.availability")
    description_tag = soup.select_one("#product_description + p")

    title = title_tag.text.strip() if title_tag else "Unknown Title"
    price = price_tag.text.strip() if price_tag else "N/A"
    availability = availability_tag.text.strip() if availability_tag else "N/A"
    description = description_tag.text.strip() if description_tag else "No description available."

    return {
        "title": title,
        "price": price,
        "availability": availability,
        "description": description,
        "link": book_url,
    }

def scrape_books_to_minio() -> list[dict]:
    print("📘 Starting scrape from books.toscrape.com...")
    links = get_book_links(MAX_BOOKS)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    records = []

    for i, link in enumerate(links):
        print(f"[{i + 1}/{len(links)}] Processing: {link}")
        data = download_book_details(link)
        if not data:
            print("⚠️ Skipping due to missing data.")
            continue

        content = (
            f"Title: {data['title']}\n"
            f"Price: {data['price']}\n"
            f"Availability: {data['availability']}\n"
            f"Link: {data['link']}\n\n"
            f"{data['description']}"
        )
        object_name = f"{RAW_FOLDER}/toscrape_{timestamp}_{i}.txt"

        try:
            content_bytes = content.encode("utf-8")
            content_stream = BytesIO(content_bytes)

            client.put_object(
                bucket_name=MINIO_BUCKET,
                object_name=object_name,
                data=content_stream,
                length=len(content_bytes),
                content_type="text/plain",
            )
            print(f"[{i}] ✅ Uploaded {object_name} to MinIO")

            records.append(
                {
                    "title": data["title"],
                    "price": data["price"],
                    "availability": data["availability"],
                    "link": data["link"],
                    "minio_object": object_name,
                }
            )
        except Exception as e:
            print(f"[{i}] ❌ Failed to upload: {e}")

        time.sleep(1)

    print("✅ Done scraping and uploading.")
    return records

if __name__ == "__main__":
    scrape_books_to_minio()
