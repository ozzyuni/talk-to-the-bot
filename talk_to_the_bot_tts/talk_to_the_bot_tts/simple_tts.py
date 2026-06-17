#!/usr/bin/env python
import pyttsx3

class Talker:
    def __init__(self):
        # text to speech engine for talking to the user
        self.model = pyttsx3.init()
        
        try:
            self.model.setProperty('voice', 'en')
            self.model.setProperty('rate', 160)
        except:
            # this is just for platform compatibility, available settings may vary
            pass
    
    def say(self, utterance):
        try:
            self.model.say(utterance)
            self.model.runAndWait()
            self.model.stop()
            return True
        
        except Exception as e:
            print(e)
            return False

if __name__ == '__main__':
    voice = Talker()
    
    while True:
        cmd = input("Write something to say (q to quit): ")
        if cmd == 'q':
            break
        voice.say(cmd)