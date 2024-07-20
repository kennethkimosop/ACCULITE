import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
from faster_whisper import WhisperModel
from openai import OpenAI
import time
from pynput import keyboard
from TTS.api import TTS
import simpleaudio as sa

# capture audio from the microphone
def record_audio(duration, fs):
    print("Recording...")
    audio = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype=np.int16)
    sd.wait()  # Wait until recording is finished
    print("Recording complete.")
    return audio

# Transcribe the captured audio
def transcribe_audio(audio, fs, model):
    # Save the audio to a temporary file
    temp_wav_file = 'audio.wav'
    write(temp_wav_file, fs, audio)
    
    # Transcribe the audio file
    segments, info = model.transcribe(temp_wav_file, beam_size=5)
    
    print("Detected language '%s' with probability %f" % (info.language, info.language_probability))
    
    transcribed_text = ""
    for segment in segments:
        transcribed_text += segment.text + " "
        print("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text))
    
    return transcribed_text.strip()

# get response
def get_response(transcribed_text, client):
    completion = client.chat.completions.create(
        model="lmstudio-community/Meta-Llama-3-8B-Instruct-GGUF",
        messages=[
            {"role": "system", "content":  "You are a medical assistant that interfaces between the doctor and the patient you give insight of ehat the illness might be you help to the best of your knowledge"},
            {"role": "user", "content": transcribed_text}
        ],
        temperature=0.7,
    )
    return completion.choices[0].message.content

# Convert text to speech and play it
def text_to_speech(text, tts, speaker_wav, language="en"):
    output_wav_file = "output.wav"
    tts.tts_to_file(text=text, file_path=output_wav_file, speaker_wav=speaker_wav, language=language)
    
    # Play the generated audio file
    wave_obj = sa.WaveObject.from_wave_file(output_wav_file)
    play_obj = wave_obj.play()
    play_obj.wait_done()

if __name__ == "__main__":
    # Model configuration for Whisper
    model_size = "large-v3"
    model = WhisperModel(model_size, device="cuda", compute_type="float16")
    
    # OpenAI client configuration for Llama 3 using lm_studio
    client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")
    
    # TTS configuration
    tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
    tts.to("cuda")  # Move the TTS model to GPU
    
    speaker_wav = "X:/Friday/Voices/melina.wav"  # Path to the sample speaker WAV file
    
    # Recording configuration
    duration = 10  # seconds
    fs = 16000  # Sample rate
    
    # Capture audio from the microphone
    audio = record_audio(duration, fs)
        
    # Transcribe the captured audio
    transcribed_text = transcribe_audio(audio, fs, model)
    print(f"Transcribed text: {transcribed_text}")
        
    # Get response from Llama 3 with simulated streamingk
    response = get_response(transcribed_text, client)
    print(f"Llama 3 response: {response}")
        
    # Convert response to speech
    text_to_speech(response, tts, speaker_wav)
