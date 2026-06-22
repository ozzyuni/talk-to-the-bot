#!/usr/bin/env python
import rclpy
import json
import os
from rclpy.node import Node
from pathlib import Path

import talk_to_the_bot_msgs.srv

talker_config_path = ""
try:
    from ament_index_python.packages import get_package_share_directory

    talker_config_path = os.path.join(
        get_package_share_directory('talk_to_the_bot_tts'),
        'talker_config.json'
    )
except:
    talker_config_path = Path(__file__).with_name('talker_config.json')

talker_config = {}
with open(talker_config_path, 'r') as config_file:
    talker_config = json.load(config_file)

if talker_config['engine'] == 'simple':
    from talk_to_the_bot_tts.simple_tts import Talker

elif talker_config['engine'] == 'piper':
    from talk_to_the_bot_tts.piper_tts import Talker

class TalkerService(Node):
    
    def __init__(self):
        super().__init__('talker_service')
        self.voice = Talker()
        self.srv = self.create_service(talk_to_the_bot_msgs.srv.Talker, 'talker', self.code_gen_cb)
        self.get_logger().info("Service ready!")
    
    def code_gen_cb(self, request, response):
        self.get_logger().info("Request received!")
        
        result = self.voice.say(request.utterance)

        if result:
            self.get_logger().info("Speech successful!")
        else:
            self.get_logger().info("Speech failed!")

        response.success = result

        self.get_logger().info("Returning result.")
        return response

def main():
    rclpy.init()
    code_gen_service = TalkerService()
    rclpy.spin(code_gen_service)
    rclpy.shutdown()

if __name__ == '__main__':
    main()