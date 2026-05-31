// Demo response used only by the design tweak/state-jump controls.
window.MOCK_RESPONSE = {
  transcript: "Full raw transcript would appear here.",
  language: "en",
  formatted_transcript: "",
  diarized_turns: [
    { speaker: "Counselor", start: 0.0,  end: 4.2,
      text: "Hey, thanks for coming in today. How have you been doing since we last spoke?",
      emotion: { primary_emotion: "neutral", confidence: 0.83 } },
    { speaker: "Student", start: 5.1, end: 14.6,
      text: "Honestly, not great. The exams are in three weeks and I just — I can't sleep, my chest feels tight all the time. I keep opening my notes and then closing them again because nothing sticks.",
      emotion: { primary_emotion: "fear", confidence: 0.79 } },
    { speaker: "Counselor", start: 15.4, end: 19.8,
      text: "That sounds really overwhelming. When you say nothing sticks — can you walk me through what that looks like for you?",
      emotion: { primary_emotion: "neutral", confidence: 0.72 } },
    { speaker: "Student", start: 20.7, end: 33.2,
      text: "I'll read a paragraph and then realize I haven't taken any of it in. I have to read it again. And again. After an hour I've covered maybe two pages and I'm exhausted. Then I feel guilty for being so slow, which makes it worse.",
      emotion: { primary_emotion: "sadness", confidence: 0.81 } },
    { speaker: "Counselor", start: 34.1, end: 41.3,
      text: "That cycle is really common when anxiety gets high — your brain has less bandwidth, so each read costs more. It isn't laziness. It's a load issue.",
      emotion: { primary_emotion: "neutral", confidence: 0.88 } },
    { speaker: "Student", start: 42.0, end: 47.8,
      text: "Yeah. My mom keeps saying I should just try harder and I — I don't know how to explain to her that I am.",
      emotion: { primary_emotion: "sadness", confidence: 0.77 } },
    { speaker: "Counselor", start: 48.9, end: 58.1,
      text: "That's painful. Feeling unseen by the people closest to you when you're already struggling. We can think about how to have that conversation with her too if you'd like.",
      emotion: { primary_emotion: "neutral", confidence: 0.69 } },
    { speaker: "Student", start: 59.0, end: 63.4,
      text: "Maybe. I think first I just need to find a way to actually study.",
      emotion: { primary_emotion: "neutral", confidence: 0.64 } },
    { speaker: "Counselor", start: 64.5, end: 76.0,
      text: "Okay. Let's try one small thing for this week. Twenty-minute blocks — one chapter, twenty minutes, then a five-minute walk. No phone during the block. Could that work?",
      emotion: { primary_emotion: "neutral", confidence: 0.82 } },
    { speaker: "Student", start: 77.1, end: 82.4,
      text: "Twenty minutes feels doable. I keep trying to do three hour blocks and just collapsing.",
      emotion: { primary_emotion: "joy", confidence: 0.58 } },
    { speaker: "Counselor", start: 83.0, end: 89.5,
      text: "Right — and that collapse is your nervous system tapping out. Short and consistent beats long and miserable. Let's also do a four-seven-eight breath together right now.",
      emotion: { primary_emotion: "joy", confidence: 0.67 } },
    { speaker: "Student", start: 90.2, end: 94.8,
      text: "Okay. That actually — yeah. I feel a bit lighter. Thank you.",
      emotion: { primary_emotion: "joy", confidence: 0.84 } },
    { speaker: "Counselor", start: 95.7, end: 104.3,
      text: "Of course. Same time next week? I want to hear how the twenty-minute blocks felt, and we can adjust from there.",
      emotion: { primary_emotion: "joy", confidence: 0.71 } },
    { speaker: "Student", start: 105.1, end: 108.0,
      text: "Yeah. I'll see you then.",
      emotion: { primary_emotion: "neutral", confidence: 0.74 } }
  ],
  summary: "The student presented with significant exam-related anxiety, manifesting in sleep difficulty, physical tension, and impaired concentration. They expressed feelings of inadequacy and a perceived lack of support from family. The counselor validated the student's experience by reframing study difficulty as a cognitive-load issue rather than effort, then collaboratively proposed a structured twenty-minute Pomodoro routine and a brief in-session breathing exercise. The student responded positively to both interventions and agreed to a follow-up session in one week.",
  sentiment: {
    gemini_analysis: "The student's affect shifted noticeably across the session. Early turns were marked by frustration and shame — described pressure from family, self-criticism around study performance, and somatic anxiety symptoms. The counselor's reframing of cognitive load and the introduction of a concrete, low-friction intervention (twenty-minute blocks, paced breathing) coincided with an observable lift in tone. By the closing turns, the student expressed felt relief and committed to follow-up.",
    detailed_scores: {
      vader_scores: { positive: 0.221, negative: 0.142, neutral: 0.637, compound: 0.382 },
      sentiment_label: "positive",
      confidence: "medium",
      emotional_indicators: ["difficulty", "disappointment_or_worry", "agreement", "gratitude"],
      text_stats: { word_count: 412, char_count: 2341 },
      summary: "Positive sentiment detected (compound score: 0.382)."
    }
  },
  emotions: {
    dominant_emotion: "neutral",
    emotion_distribution: {
      neutral: 0.4286,
      sadness: 0.1429,
      fear: 0.0714,
      joy: 0.3571,
      anger: 0.0,
      surprise: 0.0,
      disgust: 0.0
    },
    emotion_timeline: [] // populated from diarized_turns in app.js
  },
  keywords: {
    method: "keybert",
    keywords: [
      { keyword: "exam anxiety", score: 0.8921 },
      { keyword: "sleep difficulty", score: 0.8104 },
      { keyword: "cognitive load", score: 0.7710 },
      { keyword: "study blocks", score: 0.7411 },
      { keyword: "family pressure", score: 0.7102 },
      { keyword: "breathing exercise", score: 0.6655 },
      { keyword: "focus", score: 0.6312 },
      { keyword: "self-criticism", score: 0.5891 },
      { keyword: "follow-up session", score: 0.5544 },
      { keyword: "pomodoro routine", score: 0.5210 },
      { keyword: "nervous system", score: 0.4881 },
      { keyword: "validation", score: 0.4502 }
    ],
    top_keywords: ["exam anxiety", "sleep difficulty", "cognitive load", "study blocks", "family pressure"]
  },
  suggestion: "1. When the student described physical anxiety symptoms (\"chest feels tight\"), pause briefly to acknowledge the body sensation before pivoting to cognitive content — somatic reflection deepens rapport.\n2. The reframing of study difficulty as a *load issue* was excellent. Consider naming the cognitive science explicitly (\"working memory under stress\") to give the student a vocabulary they can use with their mother.\n3. Before proposing the twenty-minute block intervention, briefly ask what the student has already tried — this validates their effort and surfaces any prior attempts that informed your suggestion.\n4. The four-seven-eight breath was well-placed and effective. Consider sending a short follow-up resource so they can practice it between sessions.\n5. Closing felt slightly abrupt. A brief summary of agreed actions (\"so this week: twenty-minute blocks, the breath, and we'll talk on Thursday\") would reinforce commitment and clarity."
};
