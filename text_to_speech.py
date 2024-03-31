import os
from google.cloud import texttospeech
from pydub import AudioSegment
from pydub.playback import play
import io

# Set the path to your Google Cloud credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "key.json"

# Instantiates a client
client = texttospeech.TextToSpeechClient()

# Set the text input to be synthesized
synthesis_input = texttospeech.SynthesisInput(text="Hello, World!")

# Build the voice request, select the language code ("en-US") and the ssml voice gender ("neutral")
voice = texttospeech.VoiceSelectionParams(language_code="en-US", ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL)

# Select the type of audio file you want returned
audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)

# Perform the text-to-speech request on the text input with the selected voice parameters and audio file type
response = client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)

audio_byte_stream = io.BytesIO(response.audio_content)
audio = AudioSegment.from_file(audio_byte_stream, format="mp3")
play(audio)

# python c:/Users/vince/OneDrive/Desktop/web-agent/text_to_speech.py