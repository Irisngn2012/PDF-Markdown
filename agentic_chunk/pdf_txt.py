from flask import Flask, request, jsonify
import os
from werkzeug.utils import secure_filename
import requests

# Initialize Flask app
app = Flask(__name__)

# LLMSherpa backend endpoint
LLMSHERPA_URL = "http://localhost:5001/api/parseDocument?renderFormat=all"

# Define the upload folder
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["ALLOWED_EXTENSIONS"] = {"pdf"}

# Function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]

# Route for file upload form
@app.route('/')
def upload_form():
    return '''
    <!doctype html>
    <html>
    <head>
        <title>Upload PDF</title>
    </head>
    <body>
        <h1>Upload PDF File</h1>
        <form action="/upload" method="POST" enctype="multipart/form-data">
            <input type="file" name="file" accept="application/pdf">
            <br><br>
            <input type="submit" value="Upload">
        </form>
    </body>
    </html>
    '''

# Route to handle file upload and processing
@app.route('/upload', methods=['POST'])
def upload_file():
    # Validate the uploaded file
    if "file" not in request.files:
        return "No file part in the request", 400

    uploaded_file = request.files["file"]
    if uploaded_file.filename == "":
        return "No file selected", 400

    if allowed_file(uploaded_file.filename):
        # Secure the filename and save it temporarily
        filename = secure_filename(uploaded_file.filename)
        temp_file_path = os.path.join(app.config["UPLOAD_FOLDER"], f"temp_{filename}")
        uploaded_file.save(temp_file_path)

        try:
            # Send the file to LLMSherpa backend
            with open(temp_file_path, "rb") as pdf_data:
                files = {"file": (uploaded_file.filename, pdf_data, "application/pdf")}
                response = requests.post(LLMSHERPA_URL, files=files)

            # Check if the backend response is successful
            if response.status_code != 200:
                return f"LLMSherpa Error: {response.status_code}\n{response.text}", 500

            # Parse the JSON response
            sherpa_data = response.json()
            blocks = sherpa_data["return_dict"]["result"]["blocks"]
            sentences = []
            for blk in blocks:
                sentences.extend(blk.get("sentences", []))

            # Combine sentences into extracted text
            extracted_text = "\n".join(sentences)
            app.logger.info(f"Extracted text from LLMSherpa:\n{extracted_text}")

            # Save the extracted text to a .txt file
            text_file_path = os.path.join(app.config["UPLOAD_FOLDER"], f"{os.path.splitext(filename)[0]}.txt")
            with open(text_file_path, "w", encoding="utf-8") as text_file:
                text_file.write(extracted_text)

            return f"File uploaded and processed successfully! Text saved to {text_file_path}", 200
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
    else:
        return "Invalid file type. Please upload a PDF file.", 400

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080, debug=True)
