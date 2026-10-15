"""Daily Encouragement preview content; no subscriber or delivery data.

The first six reflections adapt Study Hub's notes/week-1.meta.json.
The seventh completes the collection with a reflection on rest. Each reading is
included in full (KJV); the first message is the expanded devotional model.
Dates form a finite preview schedule;
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
        "reference": "Exodus 3:7-12",
        "reading": (
            "7 And the LORD said, I have surely seen the affliction of my people which are in Egypt, and have heard their cry by reason of their taskmasters; for I know their sorrows;\n\n"
            "8 And I am come down to deliver them out of the hand of the Egyptians, and to bring them up out of that land unto a good land and a large, unto a land flowing with milk and honey; unto the place of the Canaanites, and the Hittites, and the Amorites, and the Perizzites, and the Hivites, and the Jebusites.\n\n"
            "9 Now therefore, behold, the cry of the children of Israel is come unto me: and I have also seen the oppression wherewith the Egyptians oppress them.\n\n"
            "10 Come now therefore, and I will send thee unto Pharaoh, that thou mayest bring forth my people the children of Israel out of Egypt.\n\n"
            "11 And Moses said unto God, Who am I, that I should go unto Pharaoh, and that I should bring forth the children of Israel out of Egypt?\n\n"
            "12 And he said, Certainly I will be with thee; and this shall be a token unto thee, that I have sent thee: When thou hast brought forth the people out of Egypt, ye shall serve God upon this mountain."
        ),
        "verse": "Certainly I will be with thee.",
        "verse_reference": "Exodus 3:12",
        "encouragement": "God meets Moses' uncertainty with a promise of His presence.",
        "devotional": (
            "There are moments when a responsibility seems to expose every weakness we would rather keep hidden. A difficult conversation. Someone who needs our help. A step of obedience we understand, but still feel afraid to take. Before we consider what faithfulness might look like, we begin making a list of reasons someone else would be better suited.\n\n"
            "Moses stood before the burning bush with a question like that: Who am I to go to Pharaoh? He had once lived in Egypt, but he had also fled it. Now God was sending him back to confront its king and bring Israel out of slavery. The task was far beyond what Moses could accomplish on his own.\n\n"
            "Notice what God says before Moses ever raises his objection. He has seen His people's suffering. He has heard their cries. He knows their sorrow, and He has come to deliver them. Moses is being invited into something that begins with God's compassion. The suffering people in Egypt have not slipped from His sight.\n\n"
            "That reaches back into the larger story. God had made promises to Abraham, and Exodus 2:24 tells us He remembered His covenant with Abraham, Isaac, and Jacob. The burning bush belongs to that unfolding faithfulness. Moses is standing inside a story God was carrying forward long before Moses understood his place in it.\n\n"
            "God's answer to his question is striking: Certainly I will be with thee. He does not give Moses a speech about discovering hidden greatness within himself. He promises His own presence. Moses will still have to go, speak, and face resistance. His confidence can rest in the One who sends him.\n\n"
            "Centuries later, after His resurrection, Jesus sends His disciples to make disciples of all nations and promises to be with them always (Matthew 28:18-20). The assignments are different, yet both scenes draw our attention to God's presence as His people participate in His work. Through Christ's death and resurrection, the story opens onto deliverance from sin and a life of belonging to Him.\n\n"
            "Our own responsibilities may look ordinary beside Moses' calling. Caring for someone. Telling the truth. Asking forgiveness. We can bring our inadequacy into prayer as we listen to Scripture and seek wise counsel. There is room to be honest about what feels difficult while learning to trust the God who knows us."
        ),
        "context": "At the burning bush, God declares that He has seen Israel's affliction and heard their cries before commissioning Moses. Exodus 2:24 connects this deliverance to His covenant with Abraham, Isaac, and Jacob. God's promise in Exodus 3:12 addresses Moses' specific commission; it does not guarantee success for every difficult plan we choose.",
        "connection": "Exodus 2:24 connects the rescue to God's covenant promises. In Matthew 28:18-20, the risen Jesus sends His disciples and promises His presence. These distinct commissions point toward God's faithful work through His people; Christ's death and resurrection bring deliverance from sin, rather than repeating Israel's political rescue from Egypt.",
        "reflection": "Where does your own sense of inadequacy enter your prayers, and what might you notice as you sit with God's promise to Moses?",
        "prayer": "Father, You know the places where I feel inadequate. Help me listen to Your Word, receive wise counsel, and trust Your presence as I learn to respond faithfully. Amen.",
        "source": SOURCE_URL,
        "approved_for_delivery": False,
    },
    {
        "id": "compass-w01-obedience",
        "date": "2026-10-15",
        "title": "Before You See the Whole Picture",
        "reference": "Exodus 3:10-12",
        "reading": (
            "10 Come now therefore, and I will send thee unto Pharaoh, that thou mayest bring forth my people the children of Israel out of Egypt.\n\n"
            "11 And Moses said unto God, Who am I, that I should go unto Pharaoh, and that I should bring forth the children of Israel out of Egypt?\n\n"
            "12 And he said, Certainly I will be with thee; and this shall be a token unto thee, that I have sent thee: When thou hast brought forth the people out of Egypt, ye shall serve God upon this mountain."
        ),
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
        "reading": "12 And he said, Certainly I will be with thee; and this shall be a token unto thee, that I have sent thee: When thou hast brought forth the people out of Egypt, ye shall serve God upon this mountain.",
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
        "reading": (
            "10 And Moses said unto the LORD, O my Lord, I am not eloquent, neither heretofore, nor since thou hast spoken unto thy servant: but I am slow of speech, and of a slow tongue.\n\n"
            "11 And the LORD said unto him, Who hath made man's mouth? or who maketh the dumb, or deaf, or the seeing, or the blind? have not I the LORD?\n\n"
            "12 Now therefore go, and I will be with thy mouth, and teach thee what thou shalt say."
        ),
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
        "reading": (
            "13 And he said, O my Lord, send, I pray thee, by the hand of him whom thou wilt send.\n\n"
            "14 And the anger of the LORD was kindled against Moses, and he said, Is not Aaron the Levite thy brother? I know that he can speak well. And also, behold, he cometh forth to meet thee: and when he seeth thee, he will be glad in his heart.\n\n"
            "15 And thou shalt speak unto him, and put words in his mouth: and I will be with thy mouth, and with his mouth, and will teach you what ye shall do.\n\n"
            "16 And he shall be thy spokesman unto the people: and he shall be, even he shall be to thee instead of a mouth, and thou shalt be to him instead of God.\n\n"
            "17 And thou shalt take this rod in thine hand, wherewith thou shalt do signs."
        ),
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
        "reading": (
            "1 And Moses answered and said, But, behold, they will not believe me, nor hearken unto my voice: for they will say, The LORD hath not appeared unto thee.\n\n"
            "2 And the LORD said unto him, What is that in thine hand? And he said, A rod.\n\n"
            "3 And he said, Cast it on the ground. And he cast it on the ground, and it became a serpent; and Moses fled from before it.\n\n"
            "4 And the LORD said unto Moses, Put forth thine hand, and take it by the tail. And he put forth his hand, and caught it, and it became a rod in his hand:\n\n"
            "5 That they may believe that the LORD God of their fathers, the God of Abraham, the God of Isaac, and the God of Jacob, hath appeared unto thee."
        ),
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
        "reading": (
            "1 God is our refuge and strength, a very present help in trouble.\n\n"
            "2 Therefore will not we fear, though the earth be removed, and though the mountains be carried into the midst of the sea;\n\n"
            "3 Though the waters thereof roar and be troubled, though the mountains shake with the swelling thereof. Selah.\n\n"
            "4 There is a river, the streams whereof shall make glad the city of God, the holy place of the tabernacles of the most High.\n\n"
            "5 God is in the midst of her; she shall not be moved: God shall help her, and that right early.\n\n"
            "6 The heathen raged, the kingdoms were moved: he uttered his voice, the earth melted.\n\n"
            "7 The LORD of hosts is with us; the God of Jacob is our refuge. Selah.\n\n"
            "8 Come, behold the works of the LORD, what desolations he hath made in the earth.\n\n"
            "9 He maketh wars to cease unto the end of the earth; he breaketh the bow, and cutteth the spear in sunder; he burneth the chariot in the fire.\n\n"
            "10 Be still, and know that I am God: I will be exalted among the heathen, I will be exalted in the earth.\n\n"
            "11 The LORD of hosts is with us; the God of Jacob is our refuge. Selah."
        ),
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
            ("Scripture reading (KJV)", "reading"),
            ("Devotional", "devotional"),
            ("Encouragement", "encouragement"), ("Passage context", "context"),
            ("Connection across Scripture", "connection"),
            ("Reflection question", "reflection"),
        )
        if field in message
    )


def email_preview(message):
    """Content-only preview for a future sender; this function sends nothing."""
    opening = f"{message['encouragement']}\n\n" if message.get("devotional") else ""
    return (
        f"Angel Chat — {message['title']}\n\n"
        f"{opening}"
        f"Today's reading — {message['reference']} (KJV)\n\n"
        f"{message['reading']}\n\n"
        f"{message.get('devotional', message['encouragement'])}\n\n"
        f"A question to carry: {message['reflection']}\n\n"
        f"A prayer: {message['prayer']}\n\n"
        f"Explore this message and ask questions in Angel Chat:\n{message_url(message)}\n"
    )
