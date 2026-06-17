#!/usr/bin/env python3
import time
from threading import Event

import rclpy
from rclpy.action import ActionServer
from rclpy.node import Node
from rclpy.callback_groups import MutuallyExclusiveCallbackGroup
from rclpy.executors import MultiThreadedExecutor

from talk_to_the_bot_msgs.action import Listen
from talk_to_the_bot_msgs.srv import ListenerTranscribe
from talk_to_the_bot_stt.listener import Listener

class ListenerActionServer(Node):
    """Implements Listener as a ROS2 ActionServer"""

    def __init__(self):
        super().__init__('listen_action_server')
        self.main_group = MutuallyExclusiveCallbackGroup()
        self.transcriber_group = MutuallyExclusiveCallbackGroup()
        self.transcriber_cli = self.create_client(ListenerTranscribe, 'transcriber', callback_group=self.transcriber_group)
        self.transcriber_req = ListenerTranscribe.Request()

        self._listener = Listener()

        self._tcp_client = None

        if self._listener.asr_engine == 'tcp':
            import talk_to_the_bot_stt.transcriber_tcp_cli
            self._tcp_client = talk_to_the_bot_stt.transcriber_tcp_cli.TranscriberWebClient(self)

        self._action_server = ActionServer(
            self,
            Listen,
            'listen_action',
            self.listen_cb,
            callback_group=self.main_group)
        self.get_logger().info("Action server ready!")

        # Making sure a new goal waits until the previous one is the microphone and gpu
        self._hardware_released = Event()
        self._hardware_released.set()
    
    def transcribe(self, recording):
        # Get a binary representation of a wav file
        data = self._listener.generate_audio_data(recording)
        # Split into bytes for transmission
        data = [data[i:i+1] for i in range(0, len(data))]
        self.transcriber_req.recording = data

        if self._listener.asr_engine == 'remote':

            while not self.transcriber_cli.wait_for_service(timeout_sec=1.0):
                self.get_logger().info("Transcription service not available, trying again...")

            # Call service to generate a transcript
            result = self.transcriber_cli.call(self.transcriber_req)
            return result.transcript
        
        elif self._listener.asr_engine == 'tcp':
            transcript = self._tcp_client.transcribe(data)
            return transcript

        else:
            self.get_logger().error("Invalid asr_engine type for remote operation")
            return ""


    def listen_cb(self, goal_handle):
        """A ROS2 enabled reimplementation of Listener.listen()"""
        self.get_logger().info('New goal received!')

        # Action feedback: Waiting for hardware access... (waiting for previous goals to release hardware)
        feedback_msg = Listen.Feedback()
        if not self._hardware_released.is_set():
            feedback_msg.state = "Waiting for hardware..."
            self.get_logger().info('Feedback: {0}'.format(feedback_msg.state))
            goal_handle.publish_feedback(feedback_msg)

        self._hardware_released.wait()
        self._hardware_released.clear()

        # Action feedback: Waiting for speech... (waiting for recording threshold to be met)
        feedback_msg.state = "Waiting for speech..."
        self.get_logger().info('Feedback: {0}'.format(feedback_msg.state))
        goal_handle.publish_feedback(feedback_msg)

        # Waiting
        self._listener.stream.start_stream()
        speech_detected = self._listener.wait(timeout=goal_handle.request.timeout)

        if speech_detected:
            # Action feedback: Recording... (recording has started)
            feedback_msg.state = "Recording..."
            self.get_logger().info('Feedback: {0}'.format(feedback_msg.state))
            goal_handle.publish_feedback(feedback_msg)

            # Recording
            start = time.time()
            recording = self._listener.record()
            self._listener.stream.stop_stream()
            end = time.time()

            # Action feedback: Recorded for x seconds (recording has stopped)
            feedback_msg.state = "Recorded for " + str(end - start) + "seconds."
            self.get_logger().info('Feedback: {0}'.format(feedback_msg.state))
            goal_handle.publish_feedback(feedback_msg)

            # Action feedback: Transcribing... (transcribing has started)
            feedback_msg.state = "Transcribing..."
            self.get_logger().info('Feedback: {0}'.format(feedback_msg.state))
            goal_handle.publish_feedback(feedback_msg)

            # Transcribing
            start = time.time()
            if self._listener.asr is not None:
                transcript = self._listener.transcribe(recording)
            else:
                transcript = self.transcribe(recording)
            end = time.time()

            # Action feedback: Transcribing took x seconds  (transcribing has stopped)
            feedback_msg.state = "Transcribing finished in " + str(end - start) + "seconds."
            self.get_logger().info('Feedback: {0}'.format(feedback_msg.state))
            goal_handle.publish_feedback(feedback_msg)
        
        else:
            self._listener.stream.stop_stream()
            # Action feedback: Timed out! (did not detect speech before timeout)
            feedback_msg.state = "Timed out!"
            self.get_logger().info('Feedback: {0}'.format(feedback_msg.state))
            goal_handle.publish_feedback(feedback_msg)
            
            transcript = 'timeout'

        # Done
        self._hardware_released.set()
        goal_handle.succeed()
        result = Listen.Result()
        result.transcript = transcript
        return result


def main(args=None):
    rclpy.init(args=args)
    executor = MultiThreadedExecutor()

    listener_action_server = ListenerActionServer()
    executor.add_node(listener_action_server)

    executor.spin()
    executor.shutdown()
    listener_action_server.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()