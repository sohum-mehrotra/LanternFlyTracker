from flask import Flask, request, jsonify, render_template
from azure.storage.blob import BlobServiceClient, ContentSettings
from datetime import datetime
import os

app = Flask(__name__)

# Environment variables
STORAGE_ACCOUNT_URL = os.getenv("STORAGE_ACCOUNT_URL")
IMAGES_CONTAINER = os.getenv("IMAGES_CONTAINER", "lanternfly-images-469n70cr")
CONN_STR = os.getenv("AZURE_STORAGE_CONNECTION_STRING")

# Create BlobServiceClient
bsc = BlobServiceClient.from_connection_string(CONN_STR)
cc = bsc.get_container_client(IMAGES_CONTAINER)

@app.route("/api/v1/upload", methods=["POST"])
def upload():
    try:
        f = request.files["file"]
        if not f:
            return jsonify(ok=False, error="No file provided"), 400
        if not f.content_type.startswith("image/"):
            return jsonify(ok=False, error="Only images allowed"), 400
        if len(f.read()) > 10 * 1024 * 1024:
            return jsonify(ok=False, error="File too large (max 10 MB)"), 400
        f.seek(0)
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
        blob_name = f"{timestamp}-{f.filename.replace(' ', '_')}"
        blob_client = cc.get_blob_client(blob_name)
        blob_client.upload_blob(
            f,
            overwrite=True,
            content_settings=ContentSettings(content_type=f.content_type)
        )
        return jsonify(ok=True, url=f"{STORAGE_ACCOUNT_URL}/{IMAGES_CONTAINER}/{blob_name}")
    except Exception as e:
        return jsonify(ok=False, error=str(e)), 500

@app.route("/api/v1/gallery", methods=["GET"])
def gallery():
    try:
        blobs = cc.list_blobs()
        urls = [f"{STORAGE_ACCOUNT_URL}/{IMAGES_CONTAINER}/{b.name}" for b in blobs]
        return jsonify(ok=True, gallery=urls)
    except Exception as e:
        return jsonify(ok=False, error=str(e)), 500

@app.route("/health")
def health():
    return jsonify(ok=True), 200

@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

