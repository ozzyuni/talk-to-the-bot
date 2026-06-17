FROM nvidia/cuda:12.8.1-devel-ubuntu24.04

# User setup
RUN userdel -r ubuntu && \
    useradd -m talk_to_the_bot && \
    passwd talk_to_the_bot -d

# ROS2 Humble and a few audio requirements

RUN apt-get update && DEBIAN_FRONTEND="noninteractive" apt-get install -y \
    curl \
    software-properties-common \
    locales \
    wget \
    sudo

RUN echo "talk_to_the_bot ALL=(ALL:ALL) NOPASSWD: ALL" | tee /etc/sudoers.d/talk_to_the_bot

RUN locale-gen en_US en_US.UTF-8 && update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 

ENV LANG=en_US.UTF-8

RUN add-apt-repository universe

RUN curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg

RUN echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" | tee /etc/apt/sources.list.d/ros2.list > /dev/null

RUN apt-get update && DEBIAN_FRONTEND="noninteractive" apt-get install -y \
    pulseaudio \
    ros-jazzy-desktop \
    ros-dev-tools \
    python3-rosdep \
    alsa-utils \
    pulseaudio-utils \
    espeak-ng \
    ffmpeg \
    libespeak1 \
    portaudio19-dev \
    libasound2-plugins \
    python3-pip \
    python3-venv

# Make ALSA-only software use Pulseaudio
RUN echo "pcm.default pulse" > ~/.asoundrc
RUN echo "ctl.default pulse" >> ~/.asoundrc

# General Python requirements
RUN mkdir -p /venv && chmod 777 /venv

SHELL ["/bin/bash", "-c"]

USER talk_to_the_bot

RUN . /opt/ros/jazzy/setup.bash && \
    python3 -m venv /venv/talk_to_the_bot --system-site-packages

RUN . /opt/ros/jazzy/setup.bash && \
    . /venv/talk_to_the_bot/bin/activate && \
    pip install --no-cache-dir --default-timeout=1000 \
    "numpy<2.0" \
    pyaudio \
    pyttsx3 \
    sounddevice \
    piper-tts \
    astunparse \
    matplotlib \
    pillow \
    jupyterlab \
    ipywidgets \
    pypdf

# PyTorch
RUN . /opt/ros/jazzy/setup.bash && \
    . /venv/talk_to_the_bot/bin/activate && \
    pip install --no-cache-dir \
    torch==2.8.0 \
    torchvision==0.23.0 \
    torchaudio==2.8.0 \
    --index-url https://download.pytorch.org/whl/cu128
    
# Flash Attention
RUN . /opt/ros/jazzy/setup.bash && \
    . /venv/talk_to_the_bot/bin/activate && \
    pip install flash-attn==2.8.3 --no-cache-dir --no-build-isolation

# Hugging Face
RUN . /opt/ros/jazzy/setup.bash && \
    . /venv/talk_to_the_bot/bin/activate && \
    pip install --no-cache-dir \
    transformers==4.40.2\
    accelerate \
    bitsandbytes \
    pydub \
    "numpy<2.0"

USER root

RUN rosdep init

RUN apt-get update && apt-get install -y tzdata zstd libmagic1

# Workspace setup
RUN mkdir -p /talk_to_the_bot_ws/src

# This is intended as a temporary copy for use with rosdep.
# Typical usage is to override it with a bind mount later, as is done in docker_run.bash.
COPY . /talk_to_the_bot_ws/src

RUN chmod 777 /talk_to_the_bot_ws

USER talk_to_the_bot

WORKDIR /talk_to_the_bot_ws

RUN curl -fsSL https://ollama.com/download/ollama-linux-amd64.tar.zst \
    | sudo tar --zstd -x -C /usr

RUN . /opt/ros/jazzy/setup.bash && \
    . /venv/talk_to_the_bot/bin/activate && \
    python -m colcon build --cmake-args -DCMAKE_BUILD_TYPE=Release

RUN rosdep update && rosdep install --from-paths src -y --ignore-src --rosdistro jazzy

WORKDIR /talk_to_the_bot_ws