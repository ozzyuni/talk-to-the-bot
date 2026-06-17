#!/usr/bin/env python
import pickle
import copy
import argparse
import threading
import geometry_msgs.msg
from pathlib import Path
import rclpy
from rclpy.node import Node
from rclpy.executors import MultiThreadedExecutor
from talk_to_the_bot_stt.comms import Server, Client
from talk_to_the_bot_stt.listener import Listener

class TranscriberWebClient:
    """Provides access to Whisper over a tcp connection. Mostly useful for prototyping with a 
    remote GPU machine. NOT SECURE, so use e.g. SSH tunneling for access outside LAN.
    """

    def __init__(self, node=None, ip='127.0.0.1'):
        
        # Used for most communication
        self.node = node
        self.client = Client(ip, 5003)
    
    def log_info(self, msg):
        if self.node is not None:
            self.node.get_logger().info(msg)
        else:
            print("INFO: " + msg)

    def log_error(self, msg):
        if self.node is not None:
            self.node.get_logger().error(msg)
        else:
            print("ERROR: " + msg)
    
    def transcribe(self, data):
        self.log_info("Web client: Requesting inference")
        # Send instruction
        msg = pickle.dumps(data)
        (resp, success) = self.client.send(msg)
            
        if success:
            self.log_info("Response received")
            return resp.decode('utf-8')
        else:
            self.log_error("Did not receive a response from transcriber")
            return ""


def main():
    from lmpvc_listener.listener import Listener

    parser = argparse.ArgumentParser()
    parser.add_argument('-ip', help="set ip address for the other end of the bridge (default = 127.0.0.1)")
    args = parser.parse_args()

    ip = args.ip
    if ip is None:
        ip = '127.0.0.1'
        print("Using default IP.")
    print("Connecting to", ip)

    rclpy.init()
    executor = MultiThreadedExecutor()
    node = Node('transcriber_client')

    bridge = TranscriberWebClient(node=node, ip=ip)

    executor.add_node(node)
    et = threading.Thread(target=executor.spin)
    et.start()

    bridge.log_info("Connecting to " + ip)

    listener = Listener()

    listener.stream.start_stream()

    data = None

    bridge.log_info("Listening")
    if(listener.wait()):
        bridge.log_info("Recording")
        recording = listener.record()
        # Get a binary representation of a wav file
        data = listener.generate_audio_data(recording)
        # Split into bytes for transmission
        data = [data[i:i+1] for i in range(0, len(data))]
    else:
        bridge.log_error("Did not detect speech")

    listener.stream.stop_stream()
    
    transcript = ""

    if data is not None:
        bridge.log_info("Transcribing")
        transcript = bridge.transcribe(data)
    else:
        bridge.log_error("No audio data to transcribe")

    bridge.log_info("[TRANSCRIPT]: " + transcript)

    executor.shutdown()
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()

