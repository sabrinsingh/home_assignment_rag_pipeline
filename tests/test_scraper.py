import pytest
from unittest.mock import patch, MagicMock
from src.scraper import safe_get_with_retries, get_book_links, download_book_details, scrape_books_to_minio

# --- Test safe_get_with_retries ---

@patch("requests.get")  # patch the actual 'requests.get', not 'src.scraper.requests.get'
def test_safe_get_with_retries_success(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = "Success"
    mock_get.return_value = mock_resp

    response = safe_get_with_retries("http://example.com", headers={})
    assert response is not None
    assert response.text == "Success"

@patch("requests.get")
def test_safe_get_with_retries_failure(mock_get):
    mock_get.side_effect = Exception("Network error")

    response = safe_get_with_retries("http://example.com", headers={}, retries=2)
    assert response is None

# --- Test get_book_links ---

@patch("src.scraper.safe_get_with_retries")
def test_get_book_links(mock_safe_get):
    # Mock the HTML for one book link with relative href
    mock_html = """
    <html>
        <body>
            <article class="product_pod">
                <a href="../../../a-book/index.html"></a>
            </article>
        </body>
    </html>
    """
    mock_resp = MagicMock()
    mock_resp.text = mock_html
    mock_safe_get.return_value = mock_resp

    links = get_book_links(max_books=1)
    assert len(links) == 1
    # Make sure the relative URL is converted properly
    assert links[0] == "https://books.toscrape.com/catalogue/a-book/index.html"

# --- Test download_book_details ---

@patch("src.scraper.safe_get_with_retries")
def test_download_book_details_with_description(mock_safe_get):
    mock_html = """
    <html>
        <div class="product_main">
            <h1>Test Book</h1>
            <p class="price_color">£20.00</p>
            <p class="availability">In stock</p>
        </div>
        <div id="product_description"></div>
        <p>This is the description.</p>
    </html>
    """
    mock_resp = MagicMock()
    mock_resp.text = mock_html
    mock_safe_get.return_value = mock_resp

    details = download_book_details("http://example.com/book")
    assert details["title"] == "Test Book"
    assert details["price"] == "£20.00"
    assert details["availability"] == "In stock"
    assert details["description"] == "This is the description."

@patch("src.scraper.safe_get_with_retries")
def test_download_book_details_without_description(mock_safe_get):
    # No product_description section - should fallback to default string
    mock_html = """
    <html>
        <div class="product_main">
            <h1>Test Book</h1>
            <p class="price_color">£20.00</p>
            <p class="availability">In stock</p>
        </div>
    </html>
    """
    mock_resp = MagicMock()
    mock_resp.text = mock_html
    mock_safe_get.return_value = mock_resp

    details = download_book_details("http://example.com/book")
    assert details["description"] == "No description available."

# --- Test scrape_books_to_minio ---

@patch("src.scraper.safe_get_with_retries")
@patch("src.scraper.download_book_details")
@patch("src.scraper.client")  # your Minio client instance imported in scraper.py as `client`
def test_scrape_books_to_minio(mock_client, mock_download, mock_safe_get):
    # Mock book list HTML
    mock_safe_get.return_value = MagicMock(text="""
    <html>
        <body>
            <article class="product_pod">
                <a href="../../../a-book/index.html"></a>
            </article>
        </body>
    </html>
    """)

    mock_download.return_value = {
        "title": "Test Book",
        "price": "£20.00",
        "availability": "In stock",
        "description": "Book description",
        "link": "https://books.toscrape.com/catalogue/a-book/index.html"
    }

    # Mock the MinIO put_object method
    mock_client.put_object = MagicMock()

    records = scrape_books_to_minio()

    assert isinstance(records, list)
    assert len(records) > 0
    first = records[0]
    assert first["title"] == "Test Book"
    assert first["price"] == "£20.00"
    assert first["availability"] == "In stock"
    assert "minio_object" in first

    # Check put_object was called to upload file
    mock_client.put_object.assert_called()

