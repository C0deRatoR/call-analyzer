"""
report_generator.py
PDF report generation for Call Analyzer using fpdf2.
Produces a clean, structured PDF with all analysis results.
"""

from __future__ import annotations
import logging
from datetime import datetime
from typing import Any, Dict

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Colour palette (RGB tuples)
# ──────────────────────────────────────────────
C_BRAND      = (99,  102, 241)   # indigo-500
C_BRAND_DARK = (67,  56,  202)   # indigo-700
C_ACCENT     = (139, 92,  246)   # violet-500
C_BG_LIGHT   = (248, 249, 252)   # near-white
C_BG_CARD    = (241, 245, 249)   # slate-100
C_TEXT_DARK  = (30,  41,  59)    # slate-800
C_TEXT_MID   = (100, 116, 139)   # slate-500
C_TEXT_LIGHT = (148, 163, 184)   # slate-400

EMOTION_COLOURS: Dict[str, tuple] = {
    "joy":      (34,  197, 94),
    "anger":    (239, 68,  68),
    "sadness":  (59,  130, 246),
    "fear":     (168, 85,  247),
    "surprise": (245, 158, 11),
    "disgust":  (132, 204, 22),
    "neutral":  (107, 114, 128),
}

SENTIMENT_COLOURS: Dict[str, tuple] = {
    "very_positive": (16,  185, 129),
    "positive":      (34,  197, 94),
    "neutral":       (107, 114, 128),
    "negative":      (245, 158, 11),
    "very_negative": (239, 68,  68),
}


def generate_pdf_report(data: Dict[str, Any]) -> bytes:
    """
    Generate a styled PDF report from analysis data.

    Parameters
    ----------
    data : dict
        Full JSON response from /process_audio

    Returns
    -------
    bytes
        Raw PDF bytes ready to return as a Flask response.
    """
    try:
        from fpdf import FPDF
    except ImportError:
        raise ImportError("fpdf2 is not installed. Run: pip install fpdf2")

    class PDF(FPDF):
        def header(self):
            # Gradient top-bar (simulated with two rects)
            self.set_fill_color(*C_BRAND)
            self.rect(0, 0, 210, 14, "F")
            self.set_fill_color(*C_ACCENT)
            self.rect(140, 0, 70, 14, "F")

            # Logo text
            self.set_y(3)
            self.set_font("Helvetica", "B", 11)
            self.set_text_color(255, 255, 255)
            self.cell(0, 8, "  CallAnalyzer", align="L", new_x="LMARGIN", new_y="NEXT")
            self.ln(4)

        def footer(self):
            self.set_y(-14)
            self.set_fill_color(*C_BG_CARD)
            self.rect(0, self.get_y(), 210, 14, "F")
            self.set_font("Helvetica", "", 8)
            self.set_text_color(*C_TEXT_MID)
            ts = datetime.now().strftime("%Y-%m-%d %H:%M")
            self.cell(0, 8, f"  Generated {ts}  |  CallAnalyzer AI Report  |  Page {self.page_no()}", align="C")

    pdf = PDF()
    pdf.set_margins(18, 22, 18)
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    # ── Title block ──────────────────────────────────────────────
    _section_title(pdf, "Call Analysis Report", is_main=True)

    ts = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    _sub_text(pdf, f"Generated on {ts}")
    pdf.ln(6)

    # ── Summary ──────────────────────────────────────────────────
    summary = data.get("summary", "No summary available.")
    _card_header(pdf, "\u2665  Summary")
    _body_text(pdf, summary)
    pdf.ln(5)

    # ── Sentiment ─────────────────────────────────────────────────
    sentiment = data.get("sentiment", {})
    if sentiment:
        _card_header(pdf, "\u2764  Sentiment Analysis")

        detailed = sentiment.get("detailed_scores", {})
        label = detailed.get("sentiment_label", "neutral")
        confidence = detailed.get("confidence", "—")
        vader = detailed.get("vader_scores", {})

        # Sentiment label pill
        colour = SENTIMENT_COLOURS.get(label, C_TEXT_MID)
        _label_pill(pdf, label.replace("_", " ").title(), colour)
        _sub_text(pdf, f"Confidence: {confidence}")

        # VADER score bars
        if vader:
            pdf.ln(3)
            _score_bar(pdf, "Positive", vader.get("positive", 0), (34, 197, 94))
            _score_bar(pdf, "Negative", vader.get("negative", 0), (239, 68, 68))
            _score_bar(pdf, "Neutral",  vader.get("neutral",  0), (107, 114, 128))
            compound = vader.get("compound", 0)
            _sub_text(pdf, f"Compound score: {compound:+.3f}")

        # Gemini analysis
        gemini = sentiment.get("gemini_analysis", "")
        if gemini:
            pdf.ln(3)
            _mini_header(pdf, "AI Analysis")
            _body_text(pdf, gemini)

        pdf.ln(5)

    # ── Emotions ─────────────────────────────────────────────────
    emotions = data.get("emotions", {})
    if emotions and not emotions.get("error"):
        _card_header(pdf, "\ud83c\udfad  Emotion Analysis")

        dominant = emotions.get("dominant_emotion", "unknown")
        dom_colour = EMOTION_COLOURS.get(dominant, C_TEXT_MID)
        _label_pill(pdf, f"Dominant: {dominant.title()}", dom_colour)
        pdf.ln(3)

        distribution = emotions.get("emotion_distribution", {})
        if distribution:
            _mini_header(pdf, "Emotion Distribution")
            for emotion, ratio in sorted(distribution.items(), key=lambda x: -x[1]):
                colour = EMOTION_COLOURS.get(emotion, C_TEXT_MID)
                _score_bar(pdf, emotion.title(), ratio, colour)

        pdf.ln(5)

    # ── Keywords ─────────────────────────────────────────────────
    keywords_data = data.get("keywords", {})
    keywords = keywords_data.get("keywords", [])
    if keywords:
        _card_header(pdf, "\ud83c\udfb7  Keywords & Topics")
        method = keywords_data.get("method", "unknown").upper()
        _sub_text(pdf, f"Extraction method: {method}")
        pdf.ln(3)

        # Render as a wrapped list of pills (simulated)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*C_TEXT_DARK)
        kw_texts = [f"{kw['keyword']} ({round(kw['score']*100)}%)" for kw in keywords]
        _body_text(pdf, "  •  ".join(kw_texts))
        pdf.ln(5)

    # ── Suggestions ───────────────────────────────────────────────
    suggestions = data.get("suggestion", "")
    if suggestions:
        _card_header(pdf, "\ud83d\udca1  AI Suggestions")
        lines = [
            ln.strip() for ln in suggestions.split("\n")
            if ln.strip() and not ln.strip().startswith("#")
        ]
        for line in lines:
            # Strip leading numbering / bullets
            import re
            clean = re.sub(r"^[\d\.\*\•\-]+\s*", "", line).strip()
            if clean:
                _bullet_item(pdf, clean)
        pdf.ln(4)

    # ── Transcript ────────────────────────────────────────────────
    turns = data.get("diarized_turns", [])
    if turns:
        pdf.add_page()
        _card_header(pdf, "\ud83d\udcac  Transcript")

        SPEAKER_COLOURS = {
            "counselor": C_BRAND,
            "student":   C_ACCENT,
            "speaker a": C_BRAND,
            "speaker b": C_ACCENT,
        }

        for turn in turns:
            speaker = turn.get("speaker", "Speaker")
            text    = turn.get("text", "")
            start   = turn.get("start", 0)
            emotion = turn.get("emotion", {})

            mins = int(start // 60)
            secs = int(start % 60)
            ts_str = f"{mins:02d}:{secs:02d}"

            colour = SPEAKER_COLOURS.get(speaker.lower(), C_TEXT_MID)

            # Speaker label
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_text_color(*colour)
            pdf.cell(0, 5, f"{speaker.upper()}  {ts_str}", new_x="LMARGIN", new_y="NEXT")

            # Emotion badge (if present)
            if emotion and emotion.get("primary_emotion"):
                em = emotion["primary_emotion"]
                em_colour = EMOTION_COLOURS.get(em, C_TEXT_MID)
                pdf.set_font("Helvetica", "I", 7.5)
                pdf.set_text_color(*em_colour)
                pdf.cell(0, 4, f"  [{em}]", new_x="LMARGIN", new_y="NEXT")

            # Turn text
            pdf.set_font("Helvetica", "", 9.5)
            pdf.set_text_color(*C_TEXT_DARK)
            pdf.multi_cell(0, 5.5, text)
            pdf.ln(2)

    return bytes(pdf.output())


# ─────────────────────────────────────
# Helper draw functions
# ─────────────────────────────────────

def _section_title(pdf, text: str, is_main: bool = False):
    size = 20 if is_main else 14
    pdf.set_font("Helvetica", "B", size)
    pdf.set_text_color(*C_TEXT_DARK)
    pdf.cell(0, 10, text, new_x="LMARGIN", new_y="NEXT")


def _card_header(pdf, text: str):
    pdf.set_fill_color(*C_BG_CARD)
    pdf.set_draw_color(*C_BRAND)
    # Accent left bar
    pdf.set_fill_color(*C_BRAND)
    pdf.rect(pdf.get_x(), pdf.get_y(), 3, 7, "F")
    pdf.set_x(pdf.get_x() + 5)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*C_TEXT_DARK)
    pdf.cell(0, 7, text, new_x="LMARGIN", new_y="NEXT")
    # Underline
    y = pdf.get_y()
    pdf.set_draw_color(*C_BG_CARD)
    pdf.line(pdf.l_margin, y, 210 - pdf.r_margin, y)
    pdf.ln(3)


def _mini_header(pdf, text: str):
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*C_TEXT_MID)
    pdf.cell(0, 5, text.upper(), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)


def _body_text(pdf, text: str):
    pdf.set_font("Helvetica", "", 9.5)
    pdf.set_text_color(*C_TEXT_DARK)
    pdf.multi_cell(0, 5.5, text)


def _sub_text(pdf, text: str):
    pdf.set_font("Helvetica", "I", 8.5)
    pdf.set_text_color(*C_TEXT_MID)
    pdf.cell(0, 5, text, new_x="LMARGIN", new_y="NEXT")


def _bullet_item(pdf, text: str):
    pdf.set_font("Helvetica", "", 9.5)
    pdf.set_text_color(*C_TEXT_DARK)
    # Bullet
    pdf.cell(5, 5.5, "\u2022")
    pdf.multi_cell(0, 5.5, text)


def _label_pill(pdf, label: str, colour: tuple):
    r, g, b = colour
    pdf.set_fill_color(r, g, b)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.cell(
        pdf.get_string_width(label) + 8, 6,
        label, fill=True,
        new_x="LMARGIN", new_y="NEXT"
    )
    pdf.set_text_color(*C_TEXT_DARK)
    pdf.ln(2)


def _score_bar(pdf, label: str, value: float, colour: tuple):
    """Draw a labelled horizontal progress bar."""
    bar_w = 120
    bar_h = 4
    fill_w = int(bar_w * min(max(value, 0), 1))
    pct_str = f"{round(value * 100)}%"

    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(*C_TEXT_DARK)
    pdf.cell(30, 6, label)

    x = pdf.get_x()
    y = pdf.get_y() + 1

    # Background track
    pdf.set_fill_color(226, 232, 240)
    pdf.rect(x, y, bar_w, bar_h, "F")

    # Fill
    if fill_w > 0:
        r, g, b = colour
        pdf.set_fill_color(r, g, b)
        pdf.rect(x, y, fill_w, bar_h, "F")

    # Pct label
    pdf.set_xy(x + bar_w + 3, pdf.get_y())
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(*C_TEXT_MID)
    pdf.cell(14, 6, pct_str, new_x="LMARGIN", new_y="NEXT")
