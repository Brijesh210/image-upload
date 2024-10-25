from flask import Flask, render_template, request, redirect, url_for
from azure.storage.blob import BlobServiceClient
import os
from dotenv import load_dotenv


app = Flask(__name__)
load_dotenv()

CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
CONTAINER_NAME = "uploaded-images"

blob_service_client = BlobServiceClient.from_connection_string(CONNECTION_STRING)
container_client = blob_service_client.get_container_client(CONTAINER_NAME)


try:
    container_client.get_container_properties()
except Exception as e:
    container_client = blob_service_client.create_container(CONTAINER_NAME)


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
            {"url": blob_url, "name": blob.name, "last_modified": blob.last_modified,"user_ip": user_ip, "user_agent": user_agent}
        )
        

    blob_info.sort(key=lambda x: x["last_modified"], reverse=True)

    page = int(request.args.get("page", 1))
    per_page = 9
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


@app.route("/upload", methods=["POST"])
def upload_image():

    files = request.files.getlist("file")

    if len(files) == 0:
        return "No files selected", 400

    if len(files) > 10:
        return "You can upload up to 10 files only", 400

    user_ip = request.remote_addr
    print(f'hello {user_ip}')
    user_agent = request.form.get("user_agent")

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
