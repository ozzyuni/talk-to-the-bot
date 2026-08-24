from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
  
  return LaunchDescription([
    Node(
      package='talk_to_the_bot_tts',
      executable='tts',
    ),
    Node(
      package='talk_to_the_bot_stt',
      executable='stt',
    ),
  ])
