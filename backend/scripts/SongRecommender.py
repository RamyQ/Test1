import requests
import spotipy
import time
import concurrent.futures
from spotipy.oauth2 import SpotifyClientCredentials

from EnglishChecker import EnglishChecker
from SongChecker import SongChecker
from ratelimit import limits, sleep_and_retry

class EmotionBasedRecommender:
    def __init__(self, spotify_client_id, spotify_client_secret):
        # Api setup
        self.sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(
            client_id=spotify_client_id, client_secret=spotify_client_secret))
        
        # Initialize checkers
        self.english_checker = EnglishChecker(self.sp)
        self.song_checker = SongChecker("bd8b93e02d32fd1f06edcde5e8e26a0a")

        self.recco_url = "https://api.reccobeats.com/v1/track/recommendation"
        self.recco_headers = {'Accept': 'application/json'}
        self.cache = {}

        # Emotion mapping
        self.emotion_map = {"joy": "happy",
                            "excitement": "energetic",
                            "love": "love",
                            "contentment": "relaxing",
                            "amusement": "playful",
                            "curiosity": "indie",
                            "surprise": "eclectic",
                            "anger": "angry",
                            "fear": "intense",
                            "sadness": "sad"}

        # Emotion to audio features mapping
        self.emotion_audio_features = {
            "joy": {'valence': 0.95, 'energy': 0.82, 'danceability': 0.80, 'acousticness': 0.10, 'instrumentalness': 0.05, 'liveness': 0.40, 'speechiness': 0.10, 'loudness': -4.0},
            "excitement": {'valence': 0.85, 'energy': 0.90, 'danceability': 0.75, 'acousticness': 0.08, 'instrumentalness': 0.10, 'liveness': 0.65, 'speechiness': 0.15, 'loudness': -3.5},
            "love": {'valence': 0.70, 'energy': 0.40, 'danceability': 0.50, 'acousticness': 0.60, 'instrumentalness': 0.20, 'liveness': 0.25, 'speechiness': 0.10, 'loudness': -10.0},
            "contentment": {'valence': 0.65, 'energy': 0.35, 'danceability': 0.45, 'acousticness': 0.70, 'instrumentalness': 0.30, 'liveness': 0.20, 'speechiness': 0.08, 'loudness': -12.0},
            "amusement": {'valence': 0.75, 'energy': 0.45, 'danceability': 0.65, 'acousticness': 0.50, 'instrumentalness': 0.15, 'liveness': 0.30, 'speechiness': 0.20, 'loudness': -8.0},
            "curiosity": {'valence': 0.55, 'energy': 0.60, 'danceability': 0.50, 'acousticness': 0.45, 'instrumentalness': 0.50, 'liveness': 0.40, 'speechiness': 0.20, 'loudness': -9.0},
            "surprise": {'valence': 0.60, 'energy': 0.70, 'danceability': 0.60, 'acousticness': 0.35, 'instrumentalness': 0.25, 'liveness': 0.55, 'speechiness': 0.25, 'loudness': -7.0},
            "anger": {'valence': 0.15, 'energy': 0.90, 'danceability': 0.55, 'acousticness': 0.20, 'instrumentalness': 0.25, 'liveness': 0.70, 'speechiness': 0.40, 'loudness': -4.0},
            "fear": {'valence': 0.10, 'energy': 0.75, 'danceability': 0.40, 'acousticness': 0.25, 'instrumentalness': 0.60, 'liveness': 0.45, 'speechiness': 0.15, 'loudness': -6.0},
            "sadness": {'valence': 0.15, 'energy': 0.25, 'danceability': 0.30, 'acousticness': 0.80, 'instrumentalness': 0.35, 'liveness': 0.15, 'speechiness': 0.10, 'loudness': -14.0}
        }

    @sleep_and_retry
    @limits(calls=50, period=60)
    def search_spotify(self, search_term, genre="", limit=10):
        query = f"{search_term} #{genre}".strip() if genre else search_term.strip()
        print(query)
        try:
            results = self.sp.search(q=query, type='track', limit=40)
            tracks = []

            if 'tracks' in results and 'items' in results['tracks']:
                for track in results['tracks']['items']:
                    # If the tracks doesn't return artist, skip to next
                    if not track.get('artists'):
                        continue

                    title = track.get('name', '')
                    artist = track['artists'][0]['name']
                    artist_id = track['artists'][0]['id']
                    track_id = track.get('id')

                    non_english_genres = ['reggae', 'electronic', 'indie', 'folk']
                    if genre != '' or genre not in non_english_genres or ('en' not in track['languages']):
                        audience_check = self.english_checker.artist_has_english_audience(artist_id)
                        if audience_check is False:
                            continue

                    popularity = track.get('popularity', 0)
                    min_popularity = 25 if genre else 20  # Higher popularity if looking with genre
                    if popularity < min_popularity:
                        continue

                    tracks.append({
                        'name': title,
                        'artist': artist,
                        'artist_id': artist_id,
                        'popularity': popularity,
                        'id': track_id,
                        'url': track.get('external_urls', {}).get('spotify', '')
                    })

            # Sort by popularity
            tracks.sort(key=lambda x: x['popularity'], reverse=True)
            return tracks[:limit]
        except Exception as e:
            print(f"Spotify search error: {e}")
            return []

    def get_weighted_audio_features(self, emotions):
        score_sum = sum(score for _, score in emotions)
        normalized_emotions = [(emotion, score/score_sum) for emotion, score in emotions]
        weighted_audio_features = {}

        for emotion, score_normalized in normalized_emotions:
            if emotion not in self.emotion_audio_features:
                continue
            emotion_features = self.emotion_audio_features[emotion].items()
            for feature, value in emotion_features:
                weighted_audio_features[feature] = weighted_audio_features.get(feature, 0) + score_normalized * value
        
        return weighted_audio_features
    
    @sleep_and_retry
    @limits(calls=50, period=60)
    def get_recco_recommendations(self, seed_track, emotions):
        audio_features = None
        if len(emotions) > 1:
            audio_features = self.get_weighted_audio_features(emotions)
        else:
            emotion, _ = emotions[0]
            audio_features = self.emotion_audio_features.get(emotion, {})
        params = {'size': 15, 'seeds': seed_track['id'], **audio_features}

        try:
            time.sleep(1)
            response = requests.get(self.recco_url, headers=self.recco_headers, params=params)

            if response.status_code == 200:
                return response.json().get('content', [])
            elif response.status_code == 429:
                # If rate limited, wait and retry
                print("Reccobeat API")
                time.sleep(20)
                params['size'] = 10 # Make size smaller incase reason why API failed
                retry_response = requests.get(self.recco_url, headers=self.recco_headers, params=params)
                if retry_response.status_code == 200:
                    return retry_response.json().get('content', [])
                else:
                    return []
            return []
        except:
            return []

    def process_seed_track(self, seed_track, top_emotions, genre, seen_artists_set):
        if seed_track['artist'].lower() in seen_artists_set:
            return []

        seen_artists = set(seen_artists_set)
        print(f"Getting recommendations for seed (spotify) track: {seed_track['name']} by {seed_track['artist']}")
        time.sleep(1)
        recco_tracks = self.get_recco_recommendations(seed_track, top_emotions)
        valid_matches = []
        # Process recommendations in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            recco_from_future = {}
            for recco_track in recco_tracks:
                future = executor.submit(
                    self.process_single_recommendation,
                    recco_track,
                    seed_track,
                    genre,
                    seen_artists
                )
                recco_from_future[future] = recco_track
                
            for future in concurrent.futures.as_completed(recco_from_future):
                track = future.result()
                if track:
                    valid_matches.append(track)
                    seen_artists.add(track['artist'].lower())
        
        # Sort by popularity and take top 5
        valid_matches.sort(key=lambda x: x.get('popularity', 0), reverse=True)
        
        formatted_results = []
        for match in valid_matches[:5]:
            print(f"Added recommendation: {match['title']} by {match['artist']} with popularity of {match['popularity']}, from spotify seed track of {match['seed_track']}")
            formatted_results.append({
                "title": match["title"],
                "artist": match["artist"],
                "link": match["link"],
                "id": match["spotify_id"],
                "genre": match["genre"],
                "artist_id": match["artist_id"],
                "popularity": match.get("popularity", 0),
                "seed_track": match["seed_track"],
                "seed_artist": match["seed_artist"],
                "emotion": top_emotions[0][0],
                "score": top_emotions[0][1]
            })

        return formatted_results

    def process_single_recommendation(self, recco, seed_track, genre, seen_artists):
        track_id = recco.get("id")
        if not track_id:
            print(f"Rejected: No track ID")
            return None

        # Get track details, if already same artist, skip
        track = {
            "title": recco.get("trackTitle", ""),
            "artist": recco.get("artists", [{}])[0].get("name", "Unknown"),
            "artist_id": recco.get("artists", [{}])[0].get("id", ""),
            "popularity": recco.get("popularity", 0),
            "link": recco.get("href", ""),
            "id": track_id
        }
        if not track:
            return None
        
        if track['artist'].lower() in seen_artists:
            return None
        
        # If recommended track same as seed track, skip
        if self.song_checker.is_same_song(track, seed_track):
            return None

        spotify_id = track['link'].split("/")[-1]
        # If the track is not english, skip
        if self.english_checker.is_non_english_track(track['title'], spotify_id):
            return None
        
        # Make sure the recommended song from recco API is in lastfm database
        if not self.song_checker.check_lastfm(track['artist'], track['title'], 'exists'):
            return None
        
        # These are genres not to do english checks on
        non_english_genres = ['reggae', 'electronic', 'indie', 'folk']
        if (genre and genre.lower() not in non_english_genres) or genre == '':
            if self.song_checker.has_non_english_tags(track['artist'], track['title'], self.english_checker.non_english_tags):
                return None

        # Make sure there are similar genre tags (like genre of rap in both seed and recommended song)
        if not self.song_checker.check_genre_match(track['artist'], track['title'], genre):
            return None

        genre_name = self.song_checker.get_genre(track['artist'], track['title'])

        # Add seed info
        track['seed_track'] = seed_track['name']
        track['seed_artist'] = seed_track['artist']
        track['genre'] = genre_name
        track['spotify_id'] = spotify_id
        
        return track

    def get_recommendations(self, emotions, genre="", limit=5):
        for emotion, score in emotions.items():
            if score > 0:
                print(f"- {emotion}: {score:.2f}")
        primary_emotion = max(emotions.items(), key=lambda x: x[1])

        sorted_emotions = sorted(emotions.items(), key=lambda x: x[1], reverse=True)
        top_emotions = [(emotion, score) for emotion, score in sorted_emotions if score >= 0.3][:3]
        
        if not top_emotions:
            top_emotions = [primary_emotion]
        print_emotion = [emotion for emotion, _ in top_emotions]
        if genre:
            print_emotion.append("and genre of "+ genre)
        print(f"Finding recommended tracks/songs for the main emotion: {', '.join(print_emotion)}")

        top_emotions = [primary_emotion]
        emotion_name = primary_emotion[0]
        search_term = self.emotion_map.get(emotion_name, emotion_name)
        spotify_tracks = self.search_spotify(search_term, genre, limit=40)
        print(f"Found {len(spotify_tracks)} initial tracks on Spotify")

        available_tracks = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = []
            for track in spotify_tracks[:20]:
                if 'artists' in track and track['artists'] and len(track['artists']) > 0:
                    artist_id = track['artists'][0]['id']
                    if ':' in artist_id:
                        artist_id = artist_id.split(':')[-1]
                    track['artist_id'] = artist_id
                futures.append(executor.submit(self.check_track_availability, track))
            # Select up to 12 songs, and check for non english tags
            for future in concurrent.futures.as_completed(futures):
                track = future.result()
                if track and len(available_tracks) < 15:
                    if not self.song_checker.has_non_english_tags(track['artist'], track['name'], self.english_checker.non_english_tags):
                        available_tracks.append(track)

        if not available_tracks:
            print("No tracks were found on last.fm, using Spotify Tracks instead.")
            available_tracks = spotify_tracks[:limit]

        print(f"{len(available_tracks)} tracks from Spotify were found on last.fm (strict checking)")

        seen_artists = set()
        all_recommendations = []

        # Now we know that song is available on last.fm, get ReccoBeats recommendations using futures for parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = []
            for seed_track in available_tracks:
                if seed_track['artist'].lower() not in seen_artists:
                    futures.append(executor.submit(
                        self.process_seed_track, seed_track, top_emotions, genre, seen_artists
                    ))

            # Get all recommendation from the spotify seed track
            for future in concurrent.futures.as_completed(futures):
                results = future.result()
                if results:
                    for result in results:
                        artist = result['artist']
                        artist = artist[0] if isinstance(artist, list) else artist
                        if artist.lower() not in seen_artists:
                            all_recommendations.append(result)
                            seen_artists.update(artist.lower())
                            print("added successfully for ", artist)


        # Sort all recommendations by popularity and take the top ones
        all_recommendations.sort(key=lambda x: x.get('popularity', 0), reverse=True)
        final_recommendations = all_recommendations[:5] # Pick the upmost 5
        api_rec_count = len(final_recommendations)
        remaining_needed_tracks = limit - len(final_recommendations)

        for seed_track in available_tracks:
            if remaining_needed_tracks <= 0:
                break
            if (seed_track['name'] not in seen_artists):
                genre_name = self.song_checker.get_genre(seed_track['artist'], seed_track['name'])
                final_recommendations.append({
                    "title": seed_track["name"],
                    "artist": seed_track["artist"],
                    "link": seed_track["url"],
                    "id": seed_track["id"],
                    "popularity": seed_track.get("popularity", 0),
                    "genre": genre_name,
                    "emotion": max(emotions.items(), key=lambda x: x[1])[0],
                    "score": max(emotions.items(), key=lambda x: x[1])[1]
                })
                remaining_needed_tracks -= 1
        print(f"Final recommendations count: {len(final_recommendations)} (Number of recommendations from ReccoBeats: {api_rec_count})")
        emotion_print = ' '.join([f"{emotion} (Score: {score:.2f})" for emotion, score in top_emotions])
        print(f"\nMoodLifter Song Recommendations for {emotion_print}")
        for i, song in enumerate(final_recommendations, 1):
            print(f"{i}. \"{song['title']}\" by {song['artist']}")
            print(f"   Spotify Link: {song['link']}")
            print(f"   Popularity: {song['popularity']}\n")
        return final_recommendations

    def check_track_availability(self, track):
        # API call to check if track is on last.fm
        is_available = self.song_checker.check_lastfm(track['artist'], track['name'], 'exists')
        return track if is_available else None
