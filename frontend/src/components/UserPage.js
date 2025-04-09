import React, { useState } from "react";
import "../css/UserPage.css";

const UserPage = () => {
  const [userText, setUserText] = useState(""); // To manage the state of the textarea
  const [selectedGenre, setSelectedGenre] = useState(""); // Manage state of genre area
  const [recommendations, setRecommendations] = useState([]);
  const [error, setError] = useState("");

  // List of genres
  const genres = [
    "rap",
    "rock",
    "pop",
    "electronic",
    "r&b",
    "country",
    "jazz",
    "classical",
    "metal",
    "indie",
    "folk",
    "latin",
    "blues",
    "reggae",
  ];

  const handleSubmit = (event) => {
    event.preventDefault();

    fetch("http://localhost:5000/process_input", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_text: userText,
        genre: selectedGenre,
      }),
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.error) {
          setError(data.error);
          setRecommendations([]);
        } else {
          setRecommendations(data.song_recommendations);
          setError("");
        }
      })
      .catch(() => {
        setError("Error fetching recommendations");
        setRecommendations([]);
      });
  };

  return (
    <div className="form-container" id="emotionAnalysis">
      <h2 className="contact-title">How Are You Feeling Today?</h2>

      <form id="userEmotionInput" onSubmit={handleSubmit}>
        <div>
          <textarea
            className="message-box"
            type="text"
            name="user_text"
            id="message"
            value={userText} // Bind textarea value to state
            onChange={(e) => setUserText(e.target.value)} // Update state when the user types
          />
        </div>
        <div>
          <input className="send-button" type="submit" value="Analyze" />
        </div>
      </form>

      <div className="genre-selection">
        <h3>Choose a genre (optional)</h3>
        <div className="genre-buttons">
          {genres.map((genre) => (
            <button
              key={genre}
              type="button"
              className={selectedGenre === genre ? "genre-selected" : ""}
              onClick={() => setSelectedGenre(selectedGenre === genre ? null : genre)}
            >
              {genre}
            </button>
          ))}
        </div>
      </div>

      {error && <p>{error}</p>}

      <div className="recommendations">
        {recommendations.map((song, index) => (
          <div key={index} className="song-card">
            <h3>
              {song.name} by {song.artist}
            </h3>
            <p>
              Emotion: {song.emotion} (Score: {song.score})
            </p>
            <a href={song.url} target="_blank" rel="noopener noreferrer">
              Listen on Spotify
            </a>
          </div>
        ))}
      </div>
    </div>
  );
};

export default UserPage;
