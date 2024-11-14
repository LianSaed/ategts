import cv2
import numpy as np
import mediapipe as mp
from collections import Counter
from keras.models import load_model
from setup import connect_db  # Ensure setup has add_face_emotion or similar function
from setup import add_face_emotion

# Load the emotion detection model
model = load_model('../models/face_emotions_try2.h5')

# Define emotion labels
emotions = ["Angry", "Disgust", "Fear", "Happy", "Sad", "Surprise", "Neutral"]

# Initialize Mediapipe Holistic for face landmarks detection
mp_holistic = mp.solutions.holistic
holistic = mp_holistic.Holistic()

def process_video_emotions(answer_id, video_path):
    print(f"Processing video for answer_id: {answer_id}")

    # Open the video file
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Cannot open video file at {video_path}")
        return

    # Variables for processing frames
    fps = cap.get(cv2.CAP_PROP_FPS)
    resize_width, resize_height = 640, 480
    emotion_list = []

    while True:
        ret, frame = cap.read()
        if not ret:
            break  # End of video

        # Resize frame for consistent processing
        frame = cv2.resize(frame, (resize_width, resize_height))
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process the frame with the model
        face_region = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        face_region = cv2.resize(face_region, (48, 48))
        face_region = face_region.astype('float32') / 255.0
        face_region = np.expand_dims(face_region, axis=-1)
        face_region = np.expand_dims(face_region, axis=0)
        
        # Predict emotion
        predictions = model.predict(face_region)
        emotion_index = np.argmax(predictions)
        emotion_label = emotions[emotion_index]
        emotion_list.append(emotion_label)

    # Close video file
    cap.release()

    # Count the detected emotions
    emotion_counts = Counter(emotion_list)

    # Check if any emotions were detected
    if emotion_counts:
        # Insert emotion counts into the database
        for emotion, count in emotion_counts.items():
            add_face_emotion(answer_id, emotion, count)
    else:
        print("No emotions detected, nothing to insert into the database.")
    # Release video capture
    cap.release()

    # Count occurrences of each emotion
    emotion_counts = Counter(emotion_list)

    # Only insert into database if there are detected emotions
    if emotion_counts:
        for emotion, count in emotion_counts.items():
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO face_emotions (answer_id, emotion, count)
                VALUES (?, ?, ?)
            ''', (answer_id, emotion, count))
            conn.commit()
            conn.close()
        print("Inserted face emotions into the database.")
    else:
        print("No emotions detected, nothing to insert into the database.")


def save_emotion_results(answer_id, emotion_counts):
    """
    Saves emotion counts for a video to the face_emotions table in the database.

    Parameters:
    - answer_id (int): ID of the answer in the database.
    - emotion_counts (Counter): Dictionary with emotion labels as keys and counts as values.
    """
    conn = connect_db()
    cursor = conn.cursor()
    
    for emotion, count in emotion_counts.items():
        cursor.execute('''
            INSERT INTO face_emotions (answer_id, emotion, count)
            VALUES (?, ?, ?)
        ''', (answer_id, emotion, count))
    
    conn.commit()
    conn.close()
