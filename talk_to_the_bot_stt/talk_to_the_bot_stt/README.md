# TalkToTheBot STT Module

This package implements speech to text functionality using two engines, Wav2vec 2.0 and OpenAI Whisper.

**Start the action server:**
```
ros2 run talk_to_the_bot_stt stt
```

**Use a separte transcriber service if configured to do so:**
```
ros2 run talk_to_the_bot_stt transcriber
```

## Configuration

```
"buffer_size": 128,
"timeout_length": 0.5,
"rms_threshold": 30.0,
"asr_engine": "remote",

"wav2vec":{

},
"whisper": {
    "hf_url": "JunWorks/Quantized_4bit_WhisperSmallStd_zhTW",
    "device": "cuda",
    "multilingual": true,
    "input_language": "en",
    "translate": false,
    "format": true
}
```

**General options:**

*buffer_size:* the size of the audio buffer used for processing, in frames

*timeout_length:* how long to wait for speech to continue before recording stops, in seconds

*rms_threshold:* minimum rms level for audio to be considered speech, tune to your situation

*asr_engine:* one of the options below, "remote" to use whisper through a separate service

**Whisper options:**

*hf_url:* Hugging Face model id for the specific version to use

*device:* "cuda" for compatible gpus, "cpu" for other devices

*multilingual:* set to true if the whisper model you are using is multilingual

*input_language:* set an input language for multilingual models

*translate:* multilingual models can translate from different input languages to English

*format:* set to true to format output for more consistent generation results