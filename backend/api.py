from fastapi import FastAPI
from pydantic import BaseModel
import pickle
import numpy as np
from datetime import datetime
import pandas as pd
import os

app = FastAPI()

with open("toxicity_model.pkl", "rb") as f:
    model = pickle.load(f)

with open("tfidf_vectorizer.pkl", "rb") as f:
    tfidf = pickle.load(f)

labels = [
    'toxic',
    'severe_toxic',
    'obscene',
    'threat',
    'insult',
    'identity_hate'
]

class TextInput(BaseModel):
    text: str

def log_prediction(text, probabilities, score, action):
    log = {
        "timestamp": datetime.now(),
        "text": text,
        "score": score,
        "action": action
    }

    for label, prob in zip(labels, probabilities):
        log[label] = prob

    df = pd.DataFrame([log])

    if os.path.exists("moderation_log.csv"):
        df.to_csv("moderation_log.csv", mode='a', header=False, index=False)
    else:
        df.to_csv("moderation_log.csv", index=False)


@app.get("/")
def home():
    return {"message": "API running"}


@app.post("/moderate")
def moderate(input: TextInput):

    text_vec = tfidf.transform([input.text])
    probs = model.predict_proba(text_vec)[0]

    score = float(np.mean(probs) * 100)

    if score > 60:
        risk = "High"
        action = "Block"
    elif score > 30:
        risk = "Moderate"
        action = "Warn"
    else:
        risk = "Safe"
        action = "Allow"

    log_prediction(input.text, probs, score, action)

    return {
        "text": input.text,
        "labels": dict(zip(labels, probs)),
        "overall_score": score,
        "risk_level": risk,
        "action": action
    }
