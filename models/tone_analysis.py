# models/tone_analysis.py

import os
import pandas as pd
import librosa
import soundfile as sf
import tempfile
from transformers import pipeline
import matplotlib.pyplot as plt 
import sqlite3
import seaborn as sns

# Connect to the database
db_name = 'automated_interviews.db'

def connect_db():
    return sqlite3.connect(db_name)

# Initialize tone/emotion analysis model
tone_model = pipeline("audio-classification", model="superb/wav2vec2-base-superb-er")
def convert_to_wav(input_file):
    """
    Converts an audio file from any format supported by librosa to `.wav`.
    """
    y, sr = librosa.load(input_file, sr=16000)  # Resample to 16kHz if needed
    temp_wav_path = tempfile.NamedTemporaryFile(delete=False, suffix=".wav").name
    sf.write(temp_wav_path, y, sr)
    return temp_wav_path

def analyze_tone(file_path):
    """
    Analyzes the tone/emotion for each segment of the audio file.
    """
    results = tone_model(file_path)
    emotion_df = pd.DataFrame([
        {"Time (s)": i, "Tone": res["label"], "Score": res["score"]}
        for i, res in enumerate(results)
    ])
    return emotion_df

def save_tone_analysis_to_db(answer_id, emotion_df):
    """
    Saves tone analysis results to the `tone_analysis` table.
    """
    conn = connect_db()
    cursor = conn.cursor()
    for _, row in emotion_df.iterrows():
        cursor.execute('''
            INSERT INTO tone_analysis (answer_id, time, tone, score)
            VALUES (?, ?, ?, ?)
        ''', (answer_id, row["Time (s)"], row["Tone"], row["Score"]))
    conn.commit()
    conn.close()

def process_audio_for_tone_analysis(answer_id, file_path):
    """
    Processes the audio for tone analysis, saves results to the database.
    """
    wav_path = convert_to_wav(file_path)
    emotion_df = analyze_tone(wav_path)
    
    # Save results to database
    save_tone_analysis_to_db(answer_id, emotion_df)
    
    # Clean up the temporary `.wav` file
    if wav_path:
        os.remove(wav_path)
    
    print(f"Tone analysis saved for answer {answer_id}.")

# Plot waveform
def plot_waveform(file_path):
    """
    Plots the waveform of an audio file and saves it as an image.
    
    Parameters:
    - file_path (str): Path to the audio file.
    
    Returns:
    - str: Path to the saved waveform plot image.
    """
    audio_data, sampling_rate = librosa.load(file_path, sr=None)
    plt.figure(figsize=(12, 4))
    librosa.display.waveshow(audio_data, sr=sampling_rate)
    plt.title("Waveform of Audio")
    plt.xlabel("Time (s)")
    plt.ylabel("Amplitude")
    
    temp_plot_path = tempfile.NamedTemporaryFile(delete=False, suffix=".png").name
    plt.savefig(temp_plot_path)
    plt.close()
    return temp_plot_path

# Plot distribution of top emotions per second
def plot_top_emotion_distribution(emotion_df):
    """
    Plots distribution of each emotion as the top emotion per second.
    
    Parameters:
    - emotion_df (pd.DataFrame): DataFrame with tone analysis data.
    
    Returns:
    - str: Path to the saved plot image.
    """
    top_emotion_per_second = emotion_df.loc[emotion_df.groupby("Time (s)")["Score"].idxmax()]
    emotion_counts = top_emotion_per_second["Tone"].value_counts().reset_index()
    emotion_counts.columns = ["Tone", "Count"]

    plt.figure(figsize=(10, 6))
    sns.barplot(x=emotion_counts["Tone"], y=emotion_counts["Count"], palette="viridis")
    plt.xlabel("Emotion")
    plt.ylabel("Count of Top Emotion")
    plt.title("Distribution of Top Emotions per Second")
    plt.xticks(rotation=45)

    temp_plot_path = tempfile.NamedTemporaryFile(delete=False, suffix=".png").name
    plt.savefig(temp_plot_path)
    plt.close()
    return temp_plot_path
