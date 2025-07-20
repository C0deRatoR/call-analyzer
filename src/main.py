from gemini_module import summarize_transcript, analyze_sentiment, suggest_counsellor_response
from whisper_module import transcribe_audio


def process_audio(filepath):
    
    # Step 1: Transcribe audio using Whisper
    transcript = transcribe_audio(filepath)
    # print("Transcript:\n", transcript)
    
    # Step 2: Summarize the transcript
    summary = summarize_transcript(transcript)
    print("\nSummary:\n", summary)
    
    # Step 3: Analyze the sentiment of the transcript
    sentiment = analyze_sentiment(transcript)
    print("\nSentiment Analysis:\n", sentiment)
    
    # Step 4: Get suggestions for alternative counsellor responses
    suggestions = suggest_counsellor_response(transcript)
    print("\nCounsellor Response Suggestions:\n", suggestions)

    response = {
        "summary": summary,
        "sentiment": sentiment,
        "suggestion": suggestions
    }

    return response

if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="Process an audio file and output the summary, sentiment, and response suggestions"
    )
    parser.add_argument("audio_file", help="Path to the audio file to analyze")
    args = parser.parse_args()

    result = process_audio(args.audio_file)
    print(json.dumps(result, indent=2))