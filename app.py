from flask import Flask, render_template, request, redirect, url_for
from azure.storage.blob import BlobServiceClient
import os
from dotenv import load_dotenv

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


@app.route("/")
def index():
    # List all blobs in the container
    blobs = [blob.name for blob in container_client.list_blobs()]
    blob_urls = [
        f"https://{blob_service_client.account_name}.blob.core.windows.net/{CONTAINER_NAME}/{blob}"
        for blob in blobs
    ]
    return render_template("index.html", blobs=blob_urls)


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
