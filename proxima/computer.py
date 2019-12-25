import pyttsx3

def sayit(message):
    engine = pyttsx3.init()
    engine.say(message)
    engine.runAndWait()


