#!/usr/bin/env python3
import rclpy

from pathlib import Path
from rclpy.node import Node

import talk_to_the_bot_msg.srv
import talk_to_the_bot_stt.whisper

class TranscriberService(Node):
    """Implements OpenAI Whisper as a service to allow running it on a separate PC"""
    def __init__(self):
        super().__init__('transcriber_service')
        self.srv = self.create_service(talk_to_the_bot_msg.srv.ListenerTranscribe, 'transcriber', self.transcribe_cb)
        self.asr = talk_to_the_bot_stt.whisper.SpeechRecognition()

        self.get_logger().info("Service ready!")
    
    def transcribe_cb(self, request, response):
        """Writes recorded audio to a wav file and uses SpeechRecognition to generate a transcript"""
        filename = Path(__file__).with_name('temp.wav')

        with open(filename, 'wb') as audiofile:
            audiofile.write(b''.join(request.recording))
        
        response.transcript = self.asr.generate_transcript(str(filename))
        print("Finished transcribing:")
        filename.unlink()
        print(response.transcript)

        return response

def main():
    rclpy.init()
    transcriber_service = TranscriberService()
    rclpy.spin(transcriber_service)
    transcriber_service.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()