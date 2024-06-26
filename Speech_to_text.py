# code from:
# https://cloud.google.com/speech-to-text/docs/transcribe-streaming-audio?_gl=1*3m4ohq*_up*MQ..&gclid=Cj0KCQjw8J6wBhDXARIsAPo7QA_F8euqgZnju9joV5k9OUT9cKogYZd-aQzcKdujGSYm8Vz4eSju0bUaAmFUEALw_wcB&gclsrc=aw.ds#perform_streaming_speech_recognition_on_an_audio_stream
import os
import queue
import re
import sys

from google.cloud import speech

import pyaudio

# Audio recording parameters
RATE = 16000
CHUNK = int(RATE / 10)  # 100ms


class MicrophoneStream:
    """Opens a recording stream as a generator yielding the audio chunks."""

    def __init__(self: object, rate: int = RATE, chunk: int = CHUNK) -> None:
        """The audio -- and generator -- is guaranteed to be on the main thread."""
        self._rate = rate
        self._chunk = chunk

        # Create a thread-safe buffer of audio data
        self._buff = queue.Queue()
        self.closed = True

    def __enter__(self: object) -> object:
        self._audio_interface = pyaudio.PyAudio()
        self._audio_stream = self._audio_interface.open(
            format=pyaudio.paInt16,
            # The API currently only supports 1-channel (mono) audio
            # https://goo.gl/z757pE
            channels=1,
            rate=self._rate,
            input=True,
            frames_per_buffer=self._chunk,
            # Run the audio stream asynchronously to fill the buffer object.
            # This is necessary so that the input device's buffer doesn't
            # overflow while the calling thread makes network requests, etc.
            stream_callback=self._fill_buffer,
        )

        self.closed = False

        return self

    def __exit__(
            self: object,
            type: object,
            value: object,
            traceback: object,
    ) -> None:
        """Closes the stream, regardless of whether the connection was lost or not."""
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True
        # Signal the generator to terminate so that the client's
        # streaming_recognize method will not block the process termination.
        self._buff.put(None)
        self._audio_interface.terminate()

    def _fill_buffer(
            self: object,
            in_data: object,
            frame_count: int,
            time_info: object,
            status_flags: object,
    ) -> object:
        """Continuously collect data from the audio stream, into the buffer.

        Args:
            in_data: The audio data as a bytes object
            frame_count: The number of frames captured
            time_info: The time information
            status_flags: The status flags

        Returns:
            The audio data as a bytes object
        """
        self._buff.put(in_data)
        return None, pyaudio.paContinue

    def generator(self: object) -> object:
        """Generates audio chunks from the stream of audio data in chunks.

        Args:
            self: The MicrophoneStream object

        Returns:
            A generator that outputs audio chunks.
        """
        while not self.closed:
            # Use a blocking get() to ensure there's at least one chunk of
            # data, and stop iteration if the chunk is None, indicating the
            # end of the audio stream.
            chunk = self._buff.get()
            if chunk is None:
                return
            data = [chunk]

            # Now consume whatever other data's still buffered.
            while True:
                try:
                    chunk = self._buff.get(block=False)
                    if chunk is None:
                        return
                    data.append(chunk)
                except queue.Empty:
                    break

            yield b"".join(data)


# def listen_print_loop(responses: object) -> str:
#     """Iterates through server responses and prints them.
#
#     The responses passed is a generator that will block until a response
#     is provided by the server.
#
#     Each response may contain multiple results, and each result may contain
#     multiple alternatives; for details, see https://goo.gl/tjCPAU.  Here we
#     print only the transcription for the top alternative of the top result.
#
#     In this case, responses are provided for interim results as well. If the
#     response is an interim one, print a line feed at the end of it, to allow
#     the next result to overwrite it, until the response is a final one. For the
#     final one, print a newline to preserve the finalized transcription.
#
#     Args:
#         responses: List of server responses
#
#     Returns:
#         The transcribed text.
#     """
#     num_chars_printed = 0
#     for response in responses:
#         if not response.results:
#             continue
#
#         # The `results` list is consecutive. For streaming, we only care about
#         # the first result being considered, since once it's `is_final`, it
#         # moves on to considering the next utterance.
#         result = response.results[0]
#         if not result.alternatives:
#             continue
#
#         # Display the transcription of the top alternative.
#         transcript = result.alternatives[0].transcript
#
#         # Display interim results, but with a carriage return at the end of the
#         # line, so subsequent lines will overwrite them.
#         #
#         # If the previous result was longer than this one, we need to print
#         # some extra spaces to overwrite the previous result
#         overwrite_chars = " " * (num_chars_printed - len(transcript))
#
#         if not result.is_final:
#             sys.stdout.write(transcript + overwrite_chars + "\r")
#             sys.stdout.flush()
#
#             num_chars_printed = len(transcript)
#
#         else:
#             print(transcript + overwrite_chars)
#
#             # Exit recognition if any of the transcribed phrases could be
#             # one of our keywords.
#             if re.search(r"\b(exit|quit)\b", transcript, re.I):
#                 print("Exiting..")
#                 break
#
#             num_chars_printed = 0
#
#     return transcript

def listen_print_loop(responses):
    num_chars_printed = 0
    for response in responses:
        if not response.results:
            continue

        result = response.results[0]
        if not result.alternatives:
            continue

        transcript = result.alternatives[0].transcript
        overwrite_chars = " " * (num_chars_printed - len(transcript))

        if not result.is_final:
            sys.stdout.write(transcript + overwrite_chars + '\r')
            sys.stdout.flush()
            num_chars_printed = len(transcript)
        else:
            print(transcript + overwrite_chars)
            num_chars_printed = 0
            if re.search(r"\b(quit)\b", transcript, re.I):
                print("Quitting current session..")
                return transcript, False  # Continue in the main loop
            if re.search(r"\b(end)\b", transcript, re.I):
                print("Ending the session permanently..")
                return transcript, True  # Break from the main loop

    return "", False  # Continue by default


def start_streaming():
    """Transcribe speech from audio file."""
    # See http://g.co/cloud/speech/docs/languages
    # for a list of supported languages.
    language_code = "en-US"

    # Set the path to the service account key file, can change it
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "key.json"

    client = speech.SpeechClient()
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=RATE,
        language_code=language_code,
    )

    streaming_config = speech.StreamingRecognitionConfig(
        config=config, interim_results=True
    )

    with MicrophoneStream(RATE, CHUNK) as stream:
        audio_generator = stream.generator()
        requests = (
            speech.StreamingRecognizeRequest(audio_content=content)
            for content in audio_generator
        )

        responses = client.streaming_recognize(streaming_config, requests)

        # Now, put the transcription responses to use.
        return listen_print_loop(responses)
        # transcribed_text = listen_print_loop(responses)
        # print("Full Transcription:", transcribed_text)


def delete_last_word(transcript):
    words = transcript.split()  # Split the transcript into a list of words.
    if not words:  # Check if the list is empty.
        return ""  # Return an empty string if there are no words to remove.
    return ' '.join(words[:-1])


if __name__ == "__main__":
    while True:
        # Start the streaming and processing of the speech
        transcribed_text, end_session = start_streaming()
        print(transcribed_text)

        processed_text = delete_last_word(transcribed_text)
        print(processed_text)

        if end_session:
            print("Ending the program.")
            break  # Exit the while loop and end the program

        # The loop will automatically continue if "quit" was said, restarting the session
        print("Restarting the session...")

    print("Program terminated.")
