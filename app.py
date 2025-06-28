from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound, VideoUnavailable

app = Flask(__name__)

@app.route('/transcript', methods=['POST'])
def get_transcript():
    data = request.get_json()
    video_id = data.get('videoId')

    if not video_id:
        return jsonify({'error': 'Missing videoId'}), 400

    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        full_text = " ".join([entry['text'] for entry in transcript_list])
        return jsonify({'transcript': full_text})
    except (TranscriptsDisabled, NoTranscriptFound, VideoUnavailable) as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500

if __name__ == '__main__':
    app.run()
