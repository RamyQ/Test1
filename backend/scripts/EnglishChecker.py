from spotipy.oauth2 import SpotifyClientCredentials
import langdetect as detect

class EnglishChecker:
    def __init__(self, sp):
        # English-speaking markets
        self.english_markets = ['US', 'GB', 'CA', 'AU', 'NZ', 'IE']
        self.non_english_words = [' otr@', ' chic@', ' con ', ' esta ', ' otro ', ' otra ', ' el ', ' la ', ' tono ']       
        self.non_english_tags = ['spanish', 'espanol', 'español', 'french', 'german', 'italian', 'japanese', 'korean', 'japanese', 'brazilian', 'portuguese','chinese']     
        self.sp = sp
        
        # Caches
        self.market_popularity_cache = {}

    def is_non_english_track(self, title, track_id=None):
        if len(title) <= 2:
            return False
        if self.is_non_english(title):
            return True
        if track_id is not None:
            try:
                track_info = self.sp.track(track_id)
                
                album_name = track_info.get('album', {}).get('name', '')
                
                if album_name and self.is_non_english(album_name):
                    return True
                    
            except Exception as e:
                print(f"Error checking album language: {e}")

        # Returning false meaning it is probably english track
        return False

    def is_non_english(self, text):
        if any(word in text.lower() for word in self.non_english_words):
            return True
        
        english_punctuation = '''!()-[]{};:'",<>./?@#$%^&*_~'''
        cleaned_text = ''.join(c for c in text if c not in english_punctuation)
        
        # Count non-ASCII characters (this will include all non-Latin scripts)
        non_ascii_chars = sum(1 for c in cleaned_text if ord(c) > 127)
        
        if non_ascii_chars > 0:
            return True
        # In case there are all ASCII characters but actually different language
        try:
            lang = detect(text)
            return lang != 'en'
        except:
            return False

    def artist_has_english_audience(self, artist_id):
        try:
            us_top_tracks = self.sp.artist_top_tracks(artist_id, country='US')['tracks']

            # If artist has at least 3 tracks popular in US
            if len(us_top_tracks) >= 3:
                # Check if any tracks have high popularity
                us_popularity = [track.get('popularity', 0) for track in us_top_tracks]
                if any(pop > 10 for pop in us_popularity):
                    return True

            return False
        except:
            return None
