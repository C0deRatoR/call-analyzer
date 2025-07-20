from gtts import gTTS

conversation = """
I'm interested in applying to your university. Could you provide some details about the admission process?
Of course. Could you let me know which program you're interested in? We have different admission requirements for undergraduate and postgraduate courses.
I'm looking to apply for the Bachelor's program in Computer Science.
Great choice! For the Computer Science program, you’ll need to submit your high school transcripts, standardized test scores, and a personal statement. We also require an entrance exam or interview in some cases.
"""

tts = gTTS(conversation, lang="en")
tts.save("university_admission.wav")

print("Audio file saved as university_admission.wav")
