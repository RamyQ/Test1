import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
class SentimentAnalyzer:
  def __init__(self):
      # uploaded the model on hugging face
      model_name = "ramyj/bert-finetuned-emotion10"
      self.tokenizer = AutoTokenizer.from_pretrained(model_name)
      self.model = AutoModelForSequenceClassification.from_pretrained(
          model_name,
          problem_type="multi_label_classification"
      )

  def predict_emotions(self, text, threshold=0.5):
      # tokenizer parameters
      inputs = self.tokenizer(
          text,
          return_tensors="pt",
          padding=True,
          truncation=True,
          max_length=128
      )

      # predictions
      with torch.no_grad():
          outputs = self.model(**inputs) # return logits
          probs = torch.sigmoid(outputs.logits)

      emotions = ["joy", "excitement", "love", "contentment", "amusement", "curiosity", "surprise", "anger", "fear", "sadness"]

      predictions = probs > threshold # threshold should be 0.5
      predicted_emotions = {
          label: float(prob)
          for label, prob, pred in zip(emotions, probs[0], predictions[0])
          if pred
      }

      return predicted_emotions
