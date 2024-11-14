import librosa
import soundfile as sf
import whisper

# Load the Whisper model
whisper_model = whisper.load_model("large")

# Normalize audio function
def normalize_audio(input_file, output_file):
    """
    Normalize the audio file by resampling it to 16kHz and saving it in WAV format.

    Parameters:
    - input_file (str): Path to the input audio file.
    - output_file (str): Path where the normalized audio file will be saved.
    """
    y, sr = librosa.load(input_file, sr=16000)  # Resample to 16kHz
    sf.write(output_file, y, 16000, format='WAV')

# Translate audio function
def translate_audio(file_path):
    """
    Translate the audio file content to text using Whisper.

    Parameters:
    - file_path (str): Path to the audio file.

    Returns:
    - str: Translated text from the audio.
    """
    # Prepare a normalized file path
    normalized_file = file_path.rsplit('.', 1)[0] + '_normalized.wav'
    
    # Normalize and convert to the required format
    normalize_audio(file_path, normalized_file)
    
    # Perform translation
    translation_result = whisper_model.transcribe(normalized_file, task="translate")['text']
    
    return translation_result
