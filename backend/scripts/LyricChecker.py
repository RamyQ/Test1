import lyricsgenius
import re

class LyricCheck:
    def song_is_english(self, artist, title):
        token = "GoowUN6MKxl99zqwg4cuexIkOB_vNMcMtzhkVFtrDtFWZ3WkTVFdW86nCS2fliIa"
        genius = lyricsgenius.Genius(token)
        try:
            song = genius.search_song(title, artist)
            if song and song.lyrics:
                lyrics = song.lyrics
                lyrics = re.sub(r'\[.*?\]', '', lyrics)
                
                words_only = ''.join(char for char in lyrics if char.isalpha())                
                has_non_english = any(ord(char) > 127 for char in words_only)
                
                if has_non_english:
                    return False
                else:
                    return True
            else:
                return True
        except Exception as e:
            print(f"Error checking lyrics for \"{title}\" by {artist}: {str(e)}")
            return True
