"""Daily Encouragement preview content; no subscriber or delivery data.

The first six reflections adapt Study Hub's notes/week-1.meta.json.
The seventh completes the collection with a reflection on rest. Dates form a finite preview schedule;
the future delivery service must send only content explicitly approved to send.
"""

from datetime import date, datetime, timezone
from urllib.parse import urlencode
from zoneinfo import ZoneInfo


SITE_URL = "https://angel.beyondthemessage.org/"
PREVIEW_TIMEZONE = "America/Denver"
SOURCE_URL = (
    "https://github.com/jLvRjay-coder/btm-study-hub-streamlit/"
    "blob/main/notes/week-1.meta.json"
)

DAILY_MESSAGES = (
    {
        "id": "compass-w01-god-sends",
        "date": "2026-10-14",
        "title": "God Sends the Reluctant",
        "reference": "Exodus 3:10-12",
        "verse": "Certainly I will be with thee.",
        "verse_reference": "Exodus 3:12",
        "encouragement": "Moses felt unqualified. God's answer was a promise of His presence. You can bring your uncertainty to God without pretending you have everything figured out.",
        "context": "At the burning bush, God calls Moses to lead Israel out of Egypt. Moses asks who he is to take on that task. God answers by promising to be with him. This is a specific call in Israel's story, not a guarantee that every difficult plan we choose will succeed.",
        "connection": "In Matthew 28:18-20, Jesus sends His disciples and promises His presence. The missions are different, but both passages direct attention toward the One who sends His people.",
        "reflection": "Where do you feel inadequate, and what would it mean to bring that honestly to God?",
        "prayer": "Lord, You know where I feel unsure. Help me trust Your presence and listen carefully for Your direction.",
        "source": SOURCE_URL,
        "approved_for_delivery": False,
    },
    {
        "id": "compass-w01-obedience",
        "date": "2026-10-15",
        "title": "Before You See the Whole Picture",
        "reference": "Exodus 3:10-12",
        "verse": "Certainly I will be with thee.",
        "verse_reference": "Exodus 3:12",
        "encouragement": "Moses did not receive a map of every obstacle ahead. He received God's call and a promise of His presence. Faith can make room for questions while listening for what God has already made clear.",
        "context": "God names Moses' task: go to Pharaoh and bring Israel out of Egypt. The story does not ask Moses to follow an undefined feeling. His response is to a clear commission from God.",
        "connection": "Hebrews 11:8 recalls Abraham obeying God's call before knowing his destination. These stories invite us to consider trust without treating uncertainty itself as proof of God's direction.",
        "reflection": "What is clear in Scripture that you can pray about today, even while other questions remain unanswered?",
        "prayer": "Father, help me listen to Your Word. Give me patience with unanswered questions and wisdom about my next step.",
        "source": SOURCE_URL,
        "approved_for_delivery": False,
    },
    {
        "id": "compass-w01-presence",
        "date": "2026-10-16",
        "title": "God's Presence in the Hard Place",
        "reference": "Exodus 3:12",
        "verse": "Certainly I will be with thee.",
        "verse_reference": "Exodus 3:12",
        "encouragement": "God's promise did not make Moses' journey easy. It placed God's presence at the center of it. Difficulty does not have to be hidden from your prayers.",
        "context": "Moses will face Pharaoh, resistance, and setbacks. Exodus 3:12 reassures him of God's presence; it does not promise a trouble-free path.",
        "connection": "Psalm 23:4 speaks of God's presence in the valley. The psalm does not erase the valley; it gives language for trust within it.",
        "reflection": "What hard part of your day would you like to bring into conversation with God?",
        "prayer": "Lord, meet me in the places I find difficult. Help me notice Your care and receive support from the people around me.",
        "source": SOURCE_URL,
        "approved_for_delivery": False,
    },
    {
        "id": "compass-w01-words",
        "date": "2026-10-17",
        "title": "When the Words Feel Difficult",
        "reference": "Exodus 4:10-12",
        "verse": "I will be with thy mouth, and teach thee what thou shalt say.",
        "verse_reference": "Exodus 4:12",
        "encouragement": "Moses spoke honestly about his difficulty with words. God did not dismiss his concern. You can bring a difficult conversation to God and ask for wisdom before you speak.",
        "context": "Moses objects to speaking on God's behalf. God reminds him who made the human mouth and promises help for this commission. The passage does not make every word we say a message from God.",
        "connection": "James 1:19 calls believers to be quick to listen and slow to speak. Courage and careful listening belong together.",
        "reflection": "Where might you need both courage to speak and patience to listen today?",
        "prayer": "God, guide my words. Help me listen well and speak with honesty, kindness, and care.",
        "source": SOURCE_URL,
        "approved_for_delivery": False,
    },
    {
        "id": "compass-w01-hesitation",
        "date": "2026-10-18",
        "title": "Bring Your Hesitation to God",
        "reference": "Exodus 4:13-17",
        "verse": "Now therefore go, and I will be with thy mouth.",
        "verse_reference": "Exodus 4:12",
        "encouragement": "Moses' hesitation did not disappear after one conversation. God addressed his resistance and provided Aaron's help. Honest prayer can include the places where we are still reluctant.",
        "context": "Moses asks God to send someone else. The text describes God's anger and His provision of Aaron as a spokesman. God's response includes correction as well as practical help.",
        "connection": "Jonah 1:1-3 presents another response to a specific call: flight. Together these accounts give us room to examine reluctance honestly, rather than assume every hesitation is the same.",
        "reflection": "Is there a hesitation you want to name honestly before God, without defending it or rushing past it?",
        "prayer": "Lord, help me be honest about what holds me back. Give me discernment, humility, and willingness to receive help.",
        "source": SOURCE_URL,
        "approved_for_delivery": False,
    },
    {
        "id": "compass-w01-willingness",
        "date": "2026-10-19",
        "title": "You Can Begin with What You Have",
        "reference": "Exodus 4:1-5",
        "verse": "What is that in thine hand?",
        "verse_reference": "Exodus 4:2",
        "encouragement": "God began with the staff already in Moses' hand. You do not have to present a polished version of yourself in prayer. Bring your real life, with its limits and possibilities, before God.",
        "context": "God gives Moses signs to confirm his commission to Israel. The staff is part of those signs. This scene is not a promise that any object or talent we possess will become miraculous.",
        "connection": "In 2 Corinthians 4:7, Paul describes the treasure of the gospel in fragile human vessels. The emphasis is on God's power, not human self-sufficiency.",
        "reflection": "What ordinary part of your life could you bring to God with a willing heart?",
        "prayer": "Father, here is my real life. Help me recognize opportunities to love others and trust You with my limitations.",
        "source": SOURCE_URL,
        "approved_for_delivery": False,
    },
    {
        "id": "angel-w01-rest",
        "date": "2026-10-20",
        "title": "Make Room to Be Still",
        "reference": "Psalm 46:1-11",
        "verse": "Be still, and know that I am God.",
        "verse_reference": "Psalm 46:10",
        "encouragement": "Psalm 46 describes upheaval before it speaks of stillness. You do not need a perfectly quiet life to pause before God. There can be room for prayer in the middle of what remains unresolved.",
        "context": "The psalm celebrates God as refuge amid shaking earth, troubled nations, and war. Its call to stillness rests on God's authority, rather than a technique for making every anxious feeling disappear.",
        "connection": "Exodus 33:14 joins God's presence with rest. Matthew 11:28-30 invites the weary to come to Jesus. Read each passage in its own setting as you consider where you turn for rest.",
        "reflection": "What are you carrying that you would like to lay before God for a moment today?",
        "prayer": "Lord, I bring You what is unfinished and unresolved. Help me pause, listen, and remember that I do not carry this day alone.",
        "source": "Original reflection to complete the seven-day preview collection.",
        "approved_for_delivery": False,
    },
)


def local_today(now=None):
    """Keep daily selection consistent around UTC midnight without GPS data."""
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("now must include a timezone")
    return now.astimezone(ZoneInfo(PREVIEW_TIMEZONE)).date()


def message_by_key(key):
    """Resolve an immutable ID or scheduled ISO date; invalid links fail closed."""
    return next(
        (dict(m) for m in DAILY_MESSAGES if key in (m["id"], m["date"])),
        None,
    )


def default_message(today=None):
    today = today or local_today()
    dated = sorted(DAILY_MESSAGES, key=lambda m: m["date"])
    published = [m for m in dated if date.fromisoformat(m["date"]) <= today]
    return dict(published[-1] if published else dated[0])


def message_url(message):
    """Public links never include the private session ID or chat content."""
    return SITE_URL + "?" + urlencode({"v": "daily", "message": message["id"]})


def chat_context(message):
    return "\n".join(
        f"{label}: {message[field]}"
        for label, field in (
            ("Title", "title"), ("Passage", "reference"),
            ("Encouragement", "encouragement"), ("Passage context", "context"),
            ("Connection across Scripture", "connection"),
            ("Reflection question", "reflection"),
        )
    )


def email_preview(message):
    """Content-only preview for a future sender; this function sends nothing."""
    return (
        f"Angel Chat — {message['title']}\n\n"
        f"{message['verse']} ({message['verse_reference']}, KJV)\n\n"
        f"{message['encouragement']}\n\n"
        f"A question to carry: {message['reflection']}\n\n"
        f"A prayer: {message['prayer']}\n\n"
        f"Explore this message and ask questions in Angel Chat:\n{message_url(message)}\n"
    )
