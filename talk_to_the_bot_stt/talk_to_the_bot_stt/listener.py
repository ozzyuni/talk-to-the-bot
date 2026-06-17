#!/usr/bin/env python3
import os
import pyaudio
import pickle
import json
import math
import struct
import wave
import time
from pathlib import Path

try:
    from ament_index_python.packages import get_package_share_directory

    config_path = os.path.join(
        get_package_share_directory('talk_to_the_bot_stt'),
        'listener_config.json'
    )
except:
    config_path = Path(__file__).with_name('listener_config.json')

config = {}

with open(config_path, 'r') as config_file:
    config = json.load(config_file)

if config['asr_engine'] == 'wav2vec':
    from talk_to_the_bot_stt.wav2vec import SpeechRecognition
elif config['asr_engine'] =='whisper':
    from talk_to_the_bot_stt.whisper import SpeechRecognition
elif config['asr_engine'] !='remote' and config['asr_engine'] !='tcp':
    print("Invalid parameter 'asr_engine', defaulting to wav2vec!")
    from talk_to_the_bot_stt.wav2vec import SpeechRecognition

class Listener:
    """Records audio clips and uses SpeechRecognition to transcribe them"""
    @staticmethod
    def rms(frame):
        """Given a frame of audio data, calculates an RMS (loudness) value"""
        count = len(frame) / 2
        format = "%dh" % (count)
        shorts = struct.unpack(format, frame)

        sum_squares = 0.0
        for sample in shorts:
            n = sample * 1.0/32768.0
            sum_squares += n * n
        rms = math.pow(sum_squares / count, 0.5)

        return rms * 1000

    def __init__(self):
        #config_path = Path(__file__).with_name('listener_config.json')
        config = {}

        with open(config_path, 'r') as config_file:
            config = json.load(config_file)
        
        self.asr_engine = config['asr_engine']
        self.rms_threshold = config['rms_threshold']
        self.timeout_length = config['timeout_length']
        self.buffer_size = config['buffer_size']

        self._format = pyaudio.paInt16
        self._channels = 1
        self._rate = 16000
        
        if config['asr_engine'] !='remote' and config['asr_engine'] !='tcp':
            self.asr = SpeechRecognition()
        else:
            self.asr = None

        self.audio = pyaudio.PyAudio()
        self.stream = self.audio.open(format=self._format,
                                  channels=self._channels,
                                  rate=self._rate,
                                  input=True,
                                  output=True,
                                  frames_per_buffer=self.buffer_size,
                                  start=False)

    def generate_audio_data(self, recording):
        """Writes recorded audio to a wav file and reads it back into binary format for ROS2 transmission"""
        filename = Path(__file__).with_name('temp.wav')

        wf = wave.open(str(filename), 'wb')
        wf.setnchannels(self._channels)
        wf.setsampwidth(self.audio.get_sample_size(self._format))
        wf.setframerate(self._rate)
        wf.writeframes(recording)
        wf.close()

        data = b''
        with open(str(filename), 'rb') as audiofile:
            data = audiofile.read()
        
        filename.unlink()

        return data

    def transcribe(self, recording):
        """Writes recorded audio to a wav file and uses SpeechRecognition to generate a transcript"""
        filename = Path(__file__).with_name('temp.wav')

        wf = wave.open(str(filename), 'wb')
        wf.setnchannels(self._channels)
        wf.setsampwidth(self.audio.get_sample_size(self._format))
        wf.setframerate(self._rate)
        wf.writeframes(recording)
        wf.close()
        
        transcript = self.asr.generate_transcript(str(filename))
        
        filename.unlink()

        return transcript
    
    def record(self):

        rec = []
        current = time.time()
        end = time.time() + self.timeout_length

        while current <= end:
            data = self.stream.read(self.buffer_size)

            # If speech continues, reset timeout
            if self.rms(data) >= self.rms_threshold:
                end = time.time() + self.timeout_length

            current = time.time()
            rec.append(data)
        
        return b''.join(rec)

    def wait(self, timeout=30.0):
        """Listens to incoming audio and returns a buffer when recording threshold is met"""
        speech_detected = False
        current = time.time()
        end = time.time() + timeout

        while current <= end:
            input = self.stream.read(self.buffer_size)
            current = time.time()
            # Once the rms threshold is met, begin the recording sequence
            if self.rms(input) > self.rms_threshold:
                speech_detected = True
                break

        return speech_detected
    
    def listen(self):
        """Local implementation of the entire listening loop"""
        self.stream.start_stream()
        print('\nListening...')
        speech_detected = self.wait()
        if speech_detected:
            print("Recording...")
            recording = self.record()
            self.stream.stop_stream()
            print("Generating transcript...")
            transcript = self.transcribe(recording)
            print("Done!")
        else:
            print("Timeout!")
            self.stream.stop_stream()
            transcript = 'timeout'

        return transcript


def main():
    asr = Listener()
    
    while(True):
        input('Press Enter to start listening!')
        transcript = asr.listen()
        print('Transcript:', transcript)
        


if __name__ == '__main__':
    main()