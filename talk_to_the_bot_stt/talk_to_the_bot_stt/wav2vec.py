#!/usr/bin/env python
import torch
import torchaudio

class GreedyCTCDecoder(torch.nn.Module):
    def __init__(self, labels, blank=0):
        super().__init__()
        self.labels = labels
        self.blank = blank

    def forward(self, emission: torch.Tensor) -> str:
        """Given a sequence emission over labels, get the best path string
        Args:
            emission (Tensor): Logit tensors. Shape `[num_seq, num_label]`.

        Returns:
            str: The resulting transcript
        """
        indices = torch.argmax(emission, dim=-1)  # [num_seq,]
        indices = torch.unique_consecutive(indices, dim=-1)
        indices = [i for i in indices if i != self.blank]
        return "".join([self.labels[i] for i in indices])

class SpeechRecognition:
    """Transcribes wav files using Wav2Vec2"""
    def __init__(self):

        torch.random.manual_seed(0)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.bundle = torchaudio.pipelines.WAV2VEC2_ASR_LARGE_LV60K_960H
        self.model = self.bundle.get_model().to(self.device)
        self.decoder = GreedyCTCDecoder(labels=self.bundle.get_labels())

        print('Wav2Vec2 loaded on device:', self.device)
    
    def generate_transcript(self, speech_path):
        """ Given a path to a wav file containing speech, returns a transcript of the contents
        Args:
            speech_path: str containing the path to a wav file
        Returns:
            str: transcript of (english) speech contained in the audio
        """
        waveform, sample_rate = torchaudio.load(speech_path)
        waveform = waveform.to(self.device)

        if sample_rate != self.bundle.sample_rate:
            waveform = torchaudio.functional.resample(waveform, sample_rate, self.bundle.sample_rate)
        
        with torch.inference_mode():
            emission, _ = self.model(waveform)
        
        transcript = self.decoder(emission[0])

        transcript = transcript.lower()
        transcript = transcript.split('|')
        transcript = ' '.join(transcript)

        return transcript