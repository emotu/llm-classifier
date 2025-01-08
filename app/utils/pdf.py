import pathlib

from google.cloud import storage
from weasyprint import CSS, HTML

from app.config import settings


def generate_pdf(content: str) -> bytes:
    """Generate a PDF document from HTML content.

    Takes HTML content as a string and converts it to a PDF document using WeasyPrint
    with custom CSS styling.

    Args:
        content (str): HTML content to convert to PDF

    Returns:
        bytes: Generated PDF document as bytes

    Example:
        ```python
        html = "<h1>Hello World</h1>"
        pdf_bytes = generate_pdf(html)
        ```

    Notes:
        - Uses print.css stylesheet from static directory
        - Returns raw PDF bytes that can be written to file or uploaded
    """
    # Generate PDF
    css_path = pathlib.Path(__file__).parent.parent / "static" / "print.css"
    doc = HTML(string=content).write_pdf(
        stylesheets=[CSS(css_path)]
    )

    # Return the doc URL and the doc bytes
    print("----> I am about to return the doc")
    return doc


def upload_pdf(filename: str, doc: bytes) -> str:
    """Upload a PDF document to Google Cloud Storage.

    Takes a filename and PDF document bytes and uploads to the configured GCS bucket.

    Args:
        filename (str): Name to give the uploaded file
        doc (bytes): PDF document bytes to upload

    Returns:
        str: Public URL of the uploaded file

    Example:
        ```python
        pdf_bytes = generate_pdf("<h1>Hello</h1>")
        url = upload_pdf("doc.pdf", pdf_bytes)
        print(url) # https://storage.googleapis.com/bucket/doc.pdf
        ```

    Notes:
        - Uses GCP_STORAGE_BUCKET from settings
        - Sets content-type to application/pdf
        - Returns public URL for accessing the file
    """
    client = storage.Client()
    bucket = client.bucket(settings.GCP_STORAGE_BUCKET)
    blob = bucket.blob(filename)
    blob.upload_from_string(doc, content_type="application/pdf")
    return blob.public_url


def download_pdf(url: str) -> bytes:
    """Download a PDF document from Google Cloud Storage.

    Takes a URL and downloads the PDF document bytes from GCS.

    Args:
        url (str): URL or path of the file to download from GCS

    Returns:
        bytes: Raw PDF document bytes

    Example:
        ```python
        pdf_bytes = download_pdf("path/to/doc.pdf") 
        with open("local.pdf", "wb") as f:
            f.write(pdf_bytes)
        ```

    Notes:
        - Uses GCP_STORAGE_BUCKET from settings
        - Returns raw bytes that can be written to file
        - URL can be full GCS URL or just the path portion
    """
    client = storage.Client()
    bucket = client.bucket(settings.GCP_STORAGE_BUCKET)
    blob = bucket.blob(url)
    return blob.download_as_bytes()
