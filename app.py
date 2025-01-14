from flask import Flask, request, render_template, jsonify
import requests
import os

app = Flask(__name__)

# URL of your backend service
BACKEND_URL = "http://34.59.99.37:5001/api/parseDocument?renderFormat=all"


@app.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        if "file" not in request.files:
            return "No file part in the request", 400

        file = request.files["file"]
        
        if file.filename == "":
            return "No file selected", 400

        files = {"file": (file.filename, file.stream, file.content_type)}
        response = requests.post(BACKEND_URL, files=files)

        if response.status_code == 200:
            data = response.json()  # Parse the JSON response from the backend

            # Check if blocks exist in the response
            if "return_dict" in data and "result" in data["return_dict"] and "blocks" in data["return_dict"]["result"]:
                blocks = data["return_dict"]["result"]["blocks"]
            else:
                return "Invalid response format from backend", 500

            output_lines = []

            for blk in blocks:
                sentences = blk.get('sentences', [])
                if blk['tag'] == "header" and 0 <= blk['level'] <= 6:
                    output_lines.append("#" * (blk['level'] + 1) + " " + ", ".join(sentences))
                elif blk['tag'] == "para" and 0 <= blk['level'] <= 6:
                    output_lines.append(" " * (blk['level'] + 1) + " " + ", ".join(sentences))

            formatted_output = "\n".join(output_lines) if output_lines else "No content extracted."

            return render_template("result.html", output=formatted_output)
        else:
            return f"Failed to retrieve data. Status code: {response.status_code}. Response: {response.text}", 500

    return render_template("upload.html")


if __name__ == "__main__":
    app.run(debug=True, port=8080)
