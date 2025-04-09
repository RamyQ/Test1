import requests
import time
import re

class SongChecker:
    def __init__(self, lastfm_api_key):
        self.lastfm_url = "http://ws.audioscrobbler.com/2.0/"
        self.lastfm_api_key = lastfm_api_key
        self.cache = {}

        # Genre mapping
        self.genre_tags = {
            "rap": ["rap", "hip-hop", "hip hop", "hiphop", "trap", "conscious hip hop", "underground rap", "neo", "retro"],
            "rock": ["rock", "alternative rock", "hard rock", "indie rock", "garage rock", "punk rock", "folk rock"],
            "pop": ["pop", "pop rock", "dance pop", "synth pop", "electropop"],
            "electronic": ["electronic", "edm", "techno", "house", "trance", "dubstep", "drum and bass"],
            "r&b": ["r&b", "rnb", "soul", "neo soul", "contemporary r&b"],
            "country": ["country", "country rock", "americana", "outlaw country", "country pop"],
            "jazz": ["jazz", "smooth jazz", "bebop", "fusion", "cool jazz", "modal jazz"],
            "classical": ["classical", "orchestra", "symphony", "chamber music", "baroque"],
            "metal": ["metal", "heavy metal", "thrash metal", "death metal", "black metal", "doom metal"],
            "indie": ["indie", "indie pop", "indie folk", "indie electronic", "alternative"],
            "folk": ["folk", "acoustic", "singer-songwriter", "traditional folk"],
            "latin": ["latin", "latin pop", "reggaeton", "salsa", "bachata", "cumbia"],
            "blues": ["blues", "rhythm and blues", "electric blues", "chicago blues", "delta blues"],
            "reggae": ["reggae", "dancehall", "ska", "dub", "roots reggae"]
        }

    def check_lastfm(self, artist, track_name, check_type='exists'):
        # Use lastfm api to check track tags and if it matches with genre
        cache_key = f"{artist}:{track_name}:{check_type}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        # Defining parameters to use for last.fm API
        method = {'exists': 'track.getInfo', 'track_tags': 'track.getTopTags',
                 'artist_tags': 'artist.getTopTags'}.get(check_type)

        params = {'method': method, 'artist': artist, 'api_key': self.lastfm_api_key,
                 'format': 'json', 'autocorrect': 1}

        # If we are not checking only for artist tag, also include the track name
        if check_type != 'artist_tags':
            params['track'] = track_name

        try:
            time.sleep(0.1)
            response = requests.get(self.lastfm_url, params=params, timeout=5)

            # Return false if track doesn't exist in last.fm
            if response.status_code != 200:
                result = False if check_type == 'exists' else []
            else:
                data = response.json()
                if check_type == 'exists':
                    result = 'track' in data and not 'error' in data
                else:  # tags
                    tags = []
                    if 'toptags' in data and 'tag' in data['toptags']:
                        tag_data = data['toptags']['tag']
                        if isinstance(tag_data, list):
                            tags = [tag['name'].lower() for tag in tag_data if 'name' in tag]
                        elif isinstance(tag_data, dict) and 'name' in tag_data:
                            tags = [tag_data['name'].lower()]
                    result = tags

            self.cache[cache_key] = result
            return result
        except:
            return False if check_type == 'exists' else []

    def has_non_english_tags(self, artist, track, non_english_tags):
        # Check if the tags for both track and artist in last.fm database contains any non-english characters
        all_tags = self.check_lastfm(artist, track, 'track_tags')
        all_tags.extend(self.check_lastfm(artist, track, 'artist_tags'))
        return any(tag in non_english_tags for tag in all_tags)

    def get_genre(self, artist, track):
        # Get genre from the last.fm database
        all_tags = self.check_lastfm(artist, track, 'track_tags')
        all_tags.extend(self.check_lastfm(artist, track, 'artist_tags'))

        all_tags = [tag.lower() for tag in all_tags]

        # Look for known genres in tags
        for genre, variations in self.genre_tags.items():
            for tag in all_tags:
                if tag in variations:
                    return genre

        return all_tags[0] if all_tags else "unknown"
    
    def normalize(self, text):
        # Anything that is not alpha letter is split
        return re.split(r'\W+', text.lower())

    def check_genre_match(self, artist, track, genre):
        if not genre:
            return True

        variations = self.genre_tags.get(genre.lower(), [genre.lower()])
        all_tags = self.check_lastfm(artist, track, 'track_tags')
        all_tags.extend(self.check_lastfm(artist, track, 'artist_tags'))

        all_tags = [tag.lower() for tag in all_tags]
        variations = [tag.lower() for tag in variations]

        for tag in all_tags:
            if tag in variations:
                return True
        
        for tag in all_tags:
            tag = self.normalize(tag)
            for genre_var in variations:
                return any(item in genre_var for item in tag)

        return False

    def is_same_song(self, track1, track2):
        # Extract title and artist
        title1 = track1.get('title', '').lower() if 'title' in track1 else track1.get('name', '').lower()
        title2 = track2.get('title', '').lower() if 'title' in track2 else track2.get('name', '').lower()

        # Strip featuring parts
        title1 = title1.split('(feat')[0].split('ft.')[0].strip()
        title2 = title2.split('(feat')[0].split('ft.')[0].strip()

        artist1 = track1.get('artist', '').lower()
        artist2 = track2.get('artist', '').lower()

        return (title1 == title2) or (artist1 == artist2 and (title1 in title2 or title2 in title1))
