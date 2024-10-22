from flask import Flask, render_template, request, redirect, url_for, request
from azure.storage.blob import BlobServiceClient
import os
from dotenv import load_dotenv
from math import ceil

app = Flask(__name__)

load_dotenv()

app = Flask(__name__)

# Azure Blob Storage Configuration
CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
CONTAINER_NAME = "uploaded-images"

# Initialize the Blob Service Client
blob_service_client = BlobServiceClient.from_connection_string(CONNECTION_STRING)
container_client = blob_service_client.get_container_client(CONTAINER_NAME)


try:
    container_client.get_container_properties()
except Exception as e:
    container_client = blob_service_client.create_container(CONTAINER_NAME)



@app.route("/", methods=["GET"])
def index():
    # List all blobs in the container
    blobs = [blob.name for blob in container_client.list_blobs()]
    
    # Pagination logic (10 images per page)
    page = int(request.args.get('page', 1))
    per_page = 9
    total_blobs = len(blobs)
    start = (page - 1) * per_page
    end = start + per_page

    # Get blobs for the current page
    paginated_blobs = blobs[start:end]

    # Generate the full URL for each blob in the current page
    blob_urls = [
        f"https://{blob_service_client.account_name}.blob.core.windows.net/{CONTAINER_NAME}/{blob}"
        for blob in paginated_blobs
    ]

    # Check if there are more pages
    has_next = end < total_blobs
    has_prev = start > 0

    return render_template(
        "index.html",
        blobs=blob_urls,
        current_page=page,
        has_next=has_next,
        has_prev=has_prev
    )


# Route to handle the image upload
@app.route("/upload", methods=["POST"])
def upload_image():
    if "file" not in request.files:
        return "No file part", 400
    file = request.files["file"]

    if file.filename == "":
        return "No selected file", 400

    # Upload the file to Azure Blob Storage
    blob_client = container_client.get_blob_client(file.filename)
    blob_client.upload_blob(file, overwrite=True)

    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
