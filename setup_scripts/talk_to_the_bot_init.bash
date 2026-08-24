#!/usr/bin/env bash
mkdir -p ${PWD}/models/voices

if [ ! -f ${PWD}/models/voices/en_GB-northern_english_male-medium.onnx ]; then
  wget https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_GB/northern_english_male/medium/en_GB-northern_english_male-medium.onnx -P ${PWD}/models/voices/
fi

if [ ! -f ${PWD}/models/voices/en_GB-northern_english_male-medium.onnx.json ]; then
  wget https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_GB/northern_english_male/medium/en_GB-northern_english_male-medium.onnx.json -P ${PWD}/models/voices/
fi

if [ ! -f ${PWD}/models/voices/en_GB-jenny_dioco-medium.onnx ]; then
  wget https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_GB/jenny_dioco/medium/en_GB-jenny_dioco-medium.onnx -P ${PWD}/models/voices/
fi

if [ ! -f ${PWD}/models/voices/en_GB-jenny_dioco-medium.onnx.json ]; then
  wget https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_GB/jenny_dioco/medium/en_GB-jenny_dioco-medium.onnx.json -P ${PWD}/models/voices/
fi

. /venv/talk_to_the_bot_ws/bin/activate
. /opt/ros/jazzy/setup.bash && python3 -m colcon build --cmake-args -DCMAKE_BUILD_TYPE=Release --symlink-install

cp ${PWD}/src/setup_scripts/talk_to_the_bot_ws.bash ${PWD}/talk_to_the_bot_ws.bash

. ${PWD}/install/setup.bash
