#!/usr/bin/env python
import torch
import json
import os
from pathlib import Path
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, BitsAndBytesConfig, pipeline

class SpeechRecognition:
    """Transcribes wav files using OpenAI Whisper"""
    def __init__(self):
        try:
            from ament_index_python.packages import get_package_share_directory

            config_path = os.path.join(
                get_package_share_directory('lmpvc_listener'),
                'listener_config.json'
                )
        except:
            config_path = Path(__file__).with_name('listener_config.json')
        
        config = {}
        with open(config_path, 'r') as config_file:
            config = json.load(config_file)
        
        self.translate = config['whisper']['translate']
        self.language = config['whisper']['input_language']
        self.format = config['whisper']['format']
        self.multilingual = config['whisper']['multilingual']
        quantization_config = None

        model_id = config['whisper']['hf_url']

        if config['whisper']['device'] == 'cpu':
            attn_implementation = "sdpa"
            torch_dtype = torch.float32
            self.device = 'cpu'
            
        elif config['whisper']['device'] == 'cuda':
            if torch.cuda.is_available():
                attn_implementation = "flash_attention_2"
                torch_dtype = torch.float16
                self.device = 'cuda:0'

                if config['whisper']['quantization'] == '4bit':
                    quantization_config = BitsAndBytesConfig(load_in_4bit=True,
                                                                bnb_4bit_use_double_quant=True,
                                                                bnb_4bit_quant_type='nf4',
                                                                bnb_4bit_compute_dtype=torch.bfloat16,
                                                                )
                    
                elif config['whisper']['quantization'] == '8bit':
                    print("WARNING: 8bit quantization is currently broken, using fp16!")
                    #quantization_config = BitsAndBytesConfig(load_in_8bit=True)

            else:
                attn_implementation = "sdpa"
                torch_dtype = torch.float32
                self.device = 'cpu'
                print("WARNING: Could not find a valid cuda device, using cpu!")
        
        
        self.model = AutoModelForSpeechSeq2Seq.from_pretrained(model_id,
                                                                device_map='auto',
                                                                torch_dtype=torch_dtype,
                                                                low_cpu_mem_usage=True,
                                                                use_safetensors=True,
                                                                attn_implementation=attn_implementation,
                                                                quantization_config=quantization_config
                                                                )
        if self.device == 'cpu': 
            self.model.to(self.device)

        self.processor = AutoProcessor.from_pretrained(model_id)

        self.pipe = pipeline("automatic-speech-recognition",
                            model=self.model,
                            tokenizer=self.processor.tokenizer,
                            feature_extractor=self.processor.feature_extractor,
                            max_new_tokens=128,
                            chunk_length_s=30,
                            batch_size=16,
                            return_timestamps=True,
                            torch_dtype=torch_dtype)

        print('Whisper loaded on device:', self.device)
    
    def format_transcript(self, transcript):
        """Removes puncutation and sets the string to lowercase.
            - Does not remove periods or commas, except at the end of the string
        """
        
        remove_punctuation = str.maketrans('', '', """!()-[]{};:'"\<>/?@#$%^&*_~""")
        formatted_transcript = transcript.translate(remove_punctuation).lower()

        if formatted_transcript[-1] == '.':
            formatted_transcript = formatted_transcript[:-1]
        
        return formatted_transcript

    def generate_transcript(self, filename):
        """Uses the Whisper pipeline initiated by the class to transcribe
            or translate audio files.
        """

        transcript = ''

        if not self.multilingual:
            data = self.pipe(filename)
            transcript = data['text']

        elif self.translate:
            data = self.pipe(filename, generate_kwargs={'task': 'translate'})
            transcript = data['text']
        else:
            data = self.pipe(filename, generate_kwargs={'task': 'transcribe', 
                                                        'language': self.language})
            transcript = data['text']

        if self.format:
            transcript = self.format_transcript(transcript)

        return transcript