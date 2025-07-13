from flask import Flask, render_template, request, jsonify
import os

from main import process_audio

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/process_audio", methods=["POST"])
def process_audio_request():
    if "audio_file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["audio_file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    file_path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
    file.save(file_path)

    response = process_audio(file_path)
    
    return jsonify(response)  # Send JSON response

# install ffmpeg from 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-full.7z' and set it as env path
# flask --app app.py run --debug
if __name__ == "__main__":
    app.run(debug=True)
