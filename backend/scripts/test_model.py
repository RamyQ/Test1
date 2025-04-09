from SentimentAnalysis import SentimentAnalyzer
import pandas as pd
from IPython.display import display

def main():
    examples = [
        "I had the worst day at work today!",
        "I'm so excited and nervous for my exam.",
        "I finally got my dream job!"
    ]
    results = pd.DataFrame(columns=["Text", "Emotions Detected", "Scores"])

    for text in examples:
        emotions = SentimentAnalyzer().predict_emotions(text, threshold=0)
        print(f"Text: {text}\nInput emotions:")
        for emotion, score in emotions.items():
            if score > 0:
                print(f"- {emotion}: {score:.2f}")
        sorted_emotions = sorted(emotions.items(), key=lambda x: x[1], reverse=True)
        top_emotions = [(emotion, score) for emotion, score in sorted_emotions if score >= 0.3][:3]
        new_row = {
            "Text": text,
            "Emotions Detected": [emotion for emotion, _ in top_emotions],
            "Scores": [round(score, 2) for _, score in top_emotions]
        }
        
        results = pd.concat([results, pd.DataFrame([new_row])], ignore_index=True)

    display(results)

if __name__ == "__main__":
    main()
