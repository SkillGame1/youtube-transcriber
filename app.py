from flask import Flask, request, jsonify
import os
import re
import sys
from urllib.parse import urlparse, parse_qs

# youtube-transcript-api
from youtube_transcript_api import (
    YouTubeTranscriptApi,
    TranscriptsDisabled,
    NoTranscriptFound,
)
# יוצרים אפליקציה
app = Flask(__name__)

ALLOWED_LANGS = ['he', 'iw', 'en', 'en-US', 'en-GB']

@app.route('/')
def home():
    return jsonify({"message": "YouTube Transcriber API is running"})

@app.route('/healthz')
def health():
    return jsonify({"ok": True})

def extract_video_id(url_or_id: str) -> str:
    """
    מקבל URL של יוטיוב או Video ID גולמי ומחזיר את ה-ID (11 תווים).
    תומך ב: watch?v=, youtu.be/, /embed/, /shorts/ וגם אם שולחים רק ID.
    """
    s = (url_or_id or '').strip()
    if not s:
        raise ValueError("youtube_url (or id) is required")

    # אם קיבלנו כבר ID תקין
    if re.fullmatch(r'[A-Za-z0-9_-]{11}', s):
        return s

    parsed = urlparse(s)
    qs = parse_qs(parsed.query or '')

    # watch?v=VIDEO_ID
    if 'v' in qs and qs['v']:
        vid = qs['v'][0]
        if re.fullmatch(r'[A-Za-z0-9_-]{11}', vid):
            return vid

    # youtu.be/VIDEO_ID
    if parsed.netloc.lower().endswith('youtu.be'):
        m = re.match(r'^/([A-Za-z0-9_-]{11})', parsed.path or '')
        if m:
            return m.group(1)

    # /embed/VIDEO_ID או /shorts/VIDEO_ID
    m = re.match(r'^/(?:embed|shorts)/([A-Za-z0-9_-]{11})', parsed.path or '')
    if m:
        return m.group(1)

    raise ValueError("Invalid YouTube URL or video ID")

def fetch_transcript(video_id: str, languages=None):
    """
    ניסיון ראשון: get_transcript (גרסאות חדשות).
    אם (נדיר) אין מתודה כזו – נופלים ל-list_transcripts ואז .fetch()
    """
    languages = languages or ALLOWED_LANGS
    try:
        # הנתיב "הרגיל"
        return YouTubeTranscriptApi.get_transcript(video_id, languages=languages)
    except AttributeError:
        # גרסה ישנה/שונה של הספרייה – ננסה דרך list_transcripts
        transcripts = YouTubeTranscriptApi.list_transcripts(video_id)
        try:
            t = transcripts.find_transcript(languages)
            return t.fetch()
        except NoTranscriptFound:
            # ננסה גם תרגום אוטומטי אם קיים
            try:
                t = transcripts.find_generated_transcript(languages)
                return t.fetch()
            except NoTranscriptFound:
                raise

@app.route("/transcribe", methods=["POST"])
def transcribe():
    data = request.get_json(silent=True) or {}
    youtube_url = data.get("youtube_url") or data.get("video_id")
    if not youtube_url:
        return jsonify({"error": "youtube_url (or video_id) is required"}), 400

    try:
        video_id = extract_video_id(youtube_url)
        transcript_list = fetch_transcript(video_id, ALLOWED_LANGS)
        transcript_text = " ".join(
            [entry['text'] for entry in transcript_list if entry.get('text', '').strip()]
        )
        return jsonify({"video_id": video_id, "transcript": transcript_text})

    except TranscriptsDisabled:
        return jsonify({"error": "Transcripts are disabled for this video"}), 400
    except NoTranscriptFound:
        return jsonify({"error": "No transcript found for this video"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# מסלול דיאגנוסטי שמדווח איזו גרסה של הספרייה נטענה ומה נתיב הקובץ שלה
@app.route("/_debug")
def debug():
    info = {
        "python_version": sys.version,
        "youtube_transcript_api_version": None,
        "youtube_transcript_api_location": None,
    }
    try:
        # Python 3.8+
        try:
            from importlib.metadata import version, packages_distributions
        except ImportError:
            # Python <3.8 (לא צפוי ברנדר מודרני)
            from importlib_metadata import version, packages_distributions  # type: ignore

        info["youtube_transcript_api_version"] = version("youtube-transcript-api")
    except Exception:
        info["youtube_transcript_api_version"] = "unknown"

    try:
        import youtube_transcript_api as yta
        info["youtube_transcript_api_location"] = getattr(yta, "__file__", "unknown")
    except Exception:
        pass

    return jsonify(info)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
