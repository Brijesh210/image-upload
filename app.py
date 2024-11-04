from flask import Flask, render_template, request, redirect, url_for, send_file
from azure.storage.blob import BlobServiceClient
import os
from dotenv import load_dotenv
from io import BytesIO
from flask_limiter import Limiter
import requests
from flask_limiter.util import get_remote_address


app = Flask(__name__)
load_dotenv()


limiter = Limiter(app, key_func=get_remote_address)
CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
CONTAINER_NAME = "uploaded-images"

blob_service_client = BlobServiceClient.from_connection_string(CONNECTION_STRING)
container_client = blob_service_client.get_container_client(CONTAINER_NAME)


try:
    container_client.get_container_properties()
except Exception as e:
    container_client = blob_service_client.create_container(CONTAINER_NAME)


def get_blob_info():
    """Retrieve blob information from Azure Blob storage."""
    blobs = container_client.list_blobs()
    blob_info = []
    for blob in blobs:
        blob_client = container_client.get_blob_client(blob.name)
        blob_properties = blob_client.get_blob_properties()
        user_ip = blob_properties.metadata.get("user_ip")
        user_agent = blob_properties.metadata.get("user_agent")
        blob_url = f"https://{blob_service_client.account_name}.blob.core.windows.net/{CONTAINER_NAME}/{blob.name}"
        blob_info.append(
            {
                "url": blob_url,
                "name": blob.name,
                "last_modified": blob.last_modified,
                "user_ip": user_ip,
                "user_agent": user_agent,
            }
        )
    return sorted(blob_info, key=lambda x: x["last_modified"], reverse=True)


@app.route("/")
def index():

    blobs = container_client.list_blobs()

    blob_info = []

    for blob in blobs:

        blob_client = container_client.get_blob_client(blob.name)
        blob_properties = blob_client.get_blob_properties()
        user_ip = blob_properties.metadata.get("user_ip")
        user_agent = blob_properties.metadata.get("user_agent")

        blob_url = f"https://{blob_service_client.account_name}.blob.core.windows.net/{CONTAINER_NAME}/{blob.name}"

        blob_info.append(
            {
                "url": blob_url,
                "name": blob.name,
                "last_modified": blob.last_modified,
                "user_ip": user_ip,
                "user_agent": user_agent,
            }
        )

    blob_info.sort(key=lambda x: x["last_modified"], reverse=True)

    page = int(request.args.get("page", 1))
    per_page = 21
    total_blobs = len(blob_info)
    total_pages = int(total_blobs / per_page) + 1
    start = (page - 1) * per_page
    end = start + per_page

    paginated_blobs = blob_info[start:end]

    for bob in blob_info:
        print(bob["name"])

    has_next = end < total_blobs
    has_prev = start > 0

    return render_template(
        "index.html",
        blobs=paginated_blobs,
        current_page=page,
        has_next=has_next,
        has_prev=has_prev,
        total_pages=total_pages,
    )


@app.route("/delete")
def delete_page():
    """Page for deleting images with delete buttons."""
    blob_info = get_blob_info()
    page = int(request.args.get("page", 1))
    per_page = 25
    total_blobs = len(blob_info)
    total_pages = (total_blobs + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = start + per_page

    paginated_blobs = blob_info[start:end]
    has_next = end < total_blobs
    has_prev = start > 0

    return render_template(
        "delete.html",
        blobs=paginated_blobs,
        current_page=page,
        has_next=has_next,
        has_prev=has_prev,
        total_pages=total_pages,
    )


@app.route("/delete_image/<blob_name>", methods=["POST"])
def delete_image(blob_name):
    """Delete an image from the Azure Blob storage."""
    blob_client = container_client.get_blob_client(blob_name)
    blob_client.delete_blob()
    return redirect(url_for("delete_page"))


@app.route("/download/<blob_name>", methods=["GET"])
def download_image(blob_name):
    blob_client = container_client.get_blob_client(blob_name)
    download_stream = blob_client.download_blob()
    blob_data = BytesIO(download_stream.readall())

    return send_file(
        blob_data, as_attachment=True, download_name=blob_name, mimetype="image/jpeg"
    )


def is_vpn_ip(ip):
    # Example of a simple VPN detection API call

    apiKey = os.getenv("VPN_API")
    url = f"https://api.ipapi.is?q={ip}&key={apiKey}"

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad responses
        data = response.json()
        print(data)
        print("good to go")
        return data.get("is_vpn", False)  # Adjust based on actual API response
    except requests.exceptions.RequestException as e:
        print(f"Error checking VPN status: {e}")
        return False


@app.route("/upload", methods=["POST"])
@limiter.limit("5 per minute")  # Limit to 5 uploads per minute
def upload_image():

    files = request.files.getlist("file")

    if len(files) == 0:
        return "No files selected", 400

    if len(files) > 10:
        return "You can upload up to 10 files only", 400

    user_ip = (
        request.headers.get("X-Forwarded-For", request.remote_addr)
        .split(",")[0]
        .strip()
    )
    user_agent = request.headers.get("User-Agent", "Unknown")

    if is_vpn_ip(user_ip):
        return "VPN usage is not allowed. Please disable your VPN and try again.", 403

    for file in files:
        if file.filename == "":
            return "No selected file", 400

        blob_client = container_client.get_blob_client(file.filename)

        blob_client.upload_blob(
            file,
            overwrite=True,
            metadata={"user_ip": user_ip, "user_agent": user_agent},
        )

    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
