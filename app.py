from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
import os

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

    # חילוץ video_id מה-URL
    if "v=" in youtube_url:
        video_id = youtube_url.split("v=")[-1]
        if "&" in video_id:
            video_id = video_id.split("&")[0]
    else:
        return jsonify({"error": "invalid YouTube URL"}), 400

    try:
        # ניסיון להביא תמלול במספר שפות
        transcript_list = YouTubeTranscriptApi.get_transcript(
            video_id,
            languages=['he', 'en', 'en-US', 'en-GB']
        )

        transcript_text = " ".join(
            [entry['text'] for entry in transcript_list if entry['text'].strip() != '']
        )

        return jsonify({
            "video_id": video_id,
            "transcript": transcript_text
        })

    except TranscriptsDisabled:
        return jsonify({"error": "Transcripts are disabled for this video"}), 400
    except NoTranscriptFound:
        return jsonify({"error": "No transcript found for this video"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
