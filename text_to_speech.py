import os
from google.cloud import texttospeech
# from pydub import AudioSegment
# from pydub.playback import play
# import io
import pyaudio


def speak_text(text):
    """Uses Google Cloud Text-to-Speech to speak the provided text."""

    # Set the path to your Google Cloud credentials
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "key.json"

    # Instantiates a client
    client = texttospeech.TextToSpeechClient()

    # Set the text input to be synthesized
    synthesis_input = texttospeech.SynthesisInput(text=text)

    # Build the voice request, select the language code ("en-US") and the ssml voice gender ("neutral")
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        name="en-US-Journey-F"
    )
    # Select the type of audio file you want returned
    # audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.LINEAR16,
        effects_profile_id=["small-bluetooth-speaker-class-device"],
        pitch=2,
        speaking_rate=1
    )

    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config
    )

    py_audio = pyaudio.PyAudio()
    audio_stream = pyaudio.PyAudio().open(
        format=pyaudio.paInt16,
        channels=1,
        rate=24000,  # This is a typical rate for LINEAR16 audio, adjust as needed
        output=True
    )

    # Play the stream directly
    audio_stream.write(response.audio_content)
    audio_stream.stop_stream()
    audio_stream.close()
    py_audio.terminate()


# Example usage:
speak_text("Hello, how can I assist you today?")



# Perform the text-to-speech request on the text input with the selected voice parameters and audio file type
# response = client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)
#
# # The response's audio_content is binary.
# with open("output.mp3", "wb") as out:
#     # Write the response to the output file.
#     out.write(response.audio_content)
#     print('Audio content written to file "output.mp3"')

# audio_byte_stream = io.BytesIO(response.audio_content)
# audio = AudioSegment.from_file(audio_byte_stream, format="mp3")
# play(audio)

# python c:/Users/vince/OneDrive/Desktop/web-agent/text_to_speech.py
# python3 /Users/minhdang/Documents/school/4th year/genai_hack/web-agent/text_to_speech.py
# /Users/minhdang/Documents/school/4th year/genai_hack/web-agent/text_to_speech.py
