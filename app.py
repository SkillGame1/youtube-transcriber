from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({"message": "YouTube Transcriber API is running"})

@app.route('/transcribe', methods=['POST'])
def transcribe():
    data = request.get_json()
    youtube_url = data.get("youtube_url")

    if not youtube_url:
        return jsonify({"error": "youtube_url is required"}), 400

    # דוגמה בסיסית – מחלץ רק את ה-ID של הסרטון
    video_id = youtube_url.split("v=")[-1]

    return jsonify({
        "video_id": video_id,
        "status": "transcription feature not yet implemented"
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
