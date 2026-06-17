#!/usr/bin/env python3
import sys
import pickle
import argparse
import threading
from talk_to_the_bot_stt.whisper import SpeechRecognition
from pathlib import Path
from talk_to_the_bot_stt.comms import Server, Client
import rclpy
from rclpy.executors import SingleThreadedExecutor
from rclpy.node import Node

class TranscriberWebServer:
    """Provides access to CodeGen over a tcp connection. Mostly useful for prototyping with a 
    remote GPU machine. NOT SECURE, so use e.g. SSH tunneling for access outside LAN.
    """

    def __init__(self, node=None, ip = '127.0.0.1', logging=False):
        """Networking provided by comms.py, ports and server ip (to whcih client connects)
        can be changed here
        """
        # Used for most communication
        self.node = node
        self.server = Server(5003, logging=logging, logger_function=self.log_debug)
        self.asr = SpeechRecognition()

        if logging and node is not None:
            node.get_logger().set_level(rclpy.logging.LoggingSeverity.DEBUG)
    
    def log_info(self, msg):
        if self.node is not None:
            self.node.get_logger().info(msg)
        else:
            print("INFO: " + msg)

    def log_debug(self, msg):
        if self.node is not None:
            self.node.get_logger().debug(msg)
        else:
            print("DEBUG: " + msg)

    def log_error(self, msg):
        if self.node is not None:
            self.node.get_logger().error(msg)
        else:
            print("ERROR: " + msg)

    def run(self):
        """Listens to messages formatted as [instruction, data] and implements appropriate behaviour"""

        try:

            while True:
                (resp, success) = self.server.receive(timeout=True, timeout_in_seconds=3)
            
                if success:
                    self.log_info("Received request to transcribe")
                    msg = pickle.loads(resp)
                
                    filename = Path(__file__).with_name('temp.wav')

                    with open(filename, 'wb') as audiofile:
                        audiofile.write(b''.join(msg))
                    
                    transcript = self.asr.generate_transcript(str(filename))
                    self.log_info("Finished transcribing: " + transcript)
                    filename.unlink()

                    self.server.respond(transcript.encode('utf-8'))

        except KeyboardInterrupt:
            self.log_error("Keyboard interrupt")

def main():
    rclpy.init()

    node = Node('transcriber_web_server')

    parser = argparse.ArgumentParser()
    parser.add_argument('-ip', help="set ip address for the other end of the bridge (default = 127.0.0.1)")
    args, unknown = parser.parse_known_args()

    ip = args.ip
    if ip is None:
        ip = '127.0.0.1'
        print("Using default IP.")
    print("Connecting to", ip)

    executor = SingleThreadedExecutor()
    executor.add_node(node)
    et = threading.Thread(target=executor.spin)

    bridge = TranscriberWebServer(node=node, ip=ip)
    bridge.log_info("Connecting to " + ip)
    bridge.run()

    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()