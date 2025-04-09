from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from SentimentAnalysis import SentimentAnalyzer
from SongRecommender import EmotionBasedRecommender
import re
from flask_cors import CORS  # To handle Cross-Origin Resource Sharing (CORS)

server = Flask(__name__)
CORS(server)

@server.route("/")
def home():
    return "Vercel"

@server.route("/api"):
def home():
    return "Vercel here"

limiter = Limiter(
    get_remote_address,
    server=server,
    default_limits=["1 per minute"],
    storage_uri="memory://",
)

CLIENT_ID = "9c0bb1d40bd84e6588f3841126fe3d4d"
CLIENT_SECRET = "ebdfecacff5445bfbf132010e9b47237"
    
sentiment = SentimentAnalyzer()
matcher = EmotionBasedRecommender(CLIENT_ID, CLIENT_SECRET)

# Example function to preprocess the text (cleaning)
def preprocess_text(text):
    text = re.sub(r'[^a-zA-Z\s]', '', text)  # Finds anything NOT a letter or whitespace and replaces it with a blank space.
    text = re.sub(r'\s+', ' ', text)  # Removes any extra spaces.
    text = text.lower()  # Converts to lowercase
    text = text.strip()  # Removes trailing and leading white spaces.
    return text

# Function that checks to ensure text is preprocessed.
def is_preprocessed(text):
    return bool(re.fullmatch(r'^[a-z\s]*$', text))  # Checks that text contains only lower case letters and spaces.

def song_recommendation(text, genre):
    if is_preprocessed(text):    
        emotions = sentiment.predict_emotions(text)
        songs = matcher.get_recommendations(emotions, genre)
        return songs
    else:
        print("Song Recommendation failed. Text input is not preprocessed.")
        return []  # Return an empty list instead of None

@server.route('/process_input', methods=['POST'])
@limiter.limit("1 per minute")  # Apply rate limit of 1 request per minute
def process_input():
    try:
        data = request.get_json()
        user_text = data.get('user_text')
        genre = data.get('genre')

        if not user_text:
            return jsonify({"error": "No text provided"}), 400

        user_text = preprocess_text(user_text)
        song_list = song_recommendation(user_text, genre)

        if not song_list:
            return jsonify({"error": "No song recommendations available"}), 400

        # Build structured response
        response = {
            "song_recommendations": [
                {
                    "name": song['title'],
                    "artist": song['artist'],
                    "emotion": song['emotion'],
                    "score": round(song['score'], 3),
                    "url": song['link']
                }
                for song in song_list
            ]
        }

        return jsonify(response), 200

    except Exception as e:
        import traceback
        traceback.print_exc()  # This will print the full error to your terminal
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    server.run()
