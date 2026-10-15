"""Daily Encouragement preview content; no subscriber or delivery data.

The first six reflections adapt Study Hub's notes/week-1.meta.json.
The seventh completes the collection with a reflection on rest. Each reading is
included in full (KJV), followed by an expanded devotional.
Dates form a finite preview schedule;
the future delivery service must send only content explicitly approved to send.
"""

from datetime import date, datetime, timezone
import html
from urllib.parse import urlencode
from zoneinfo import ZoneInfo


SITE_URL = "https://angel.beyondthemessage.org/"
GOOGLE_PLAY_URL = "https://play.google.com/store/apps/details?id=org.beyondthemessage.angel"
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
        "encouragement": "God's faithfulness gives us a place to begin while the way ahead is still unfolding.",
        "devotional": (
            "It is easier to begin when we can picture how everything will turn out. Before a difficult conversation, we would like to know how the other person will respond. Before making a change, we want assurance that we will not regret it. Sometimes the desire to understand the whole journey keeps us standing still at its beginning.\n\n"
            "At the burning bush, Moses received a clear assignment: go to Pharaoh and bring Israel out of Egypt. He could understand the words and still feel overwhelmed by what they meant. A king would have to be confronted. An enslaved people would have to be freed. Moses had questions about his own place in that work.\n\n"
            "God's answer included a promise that reached beyond the immediate obstacle. The people would one day worship Him on that mountain. Pharaoh still stood between Moses and that day, but God was already speaking about the purpose of their deliverance. Israel's freedom would lead them into worship and relationship with Him.\n\n"
            "This scene continues a journey that began generations earlier. Hebrews 11:8 recalls Abraham leaving in response to God's call without knowing his destination. Abraham's descendants would become the people Moses was sent to lead out of Egypt. The promises of God were moving through lives whose understanding was always smaller than the story itself.\n\n"
            "There is something deeply human about wanting more information. We can ask questions, seek counsel, and take time to understand Scripture. Moses' conversation shows that our questions can be brought into God's presence. His clear commission also gives us a reason to listen carefully to what God has actually said.\n\n"
            "Jesus gives that trust a personal center. In John 14:6, He identifies Himself as the way to the Father. As we read the larger biblical story, its direction leads us toward Him. Through His death and resurrection, we are invited into the relationship with God that our own effort could never secure.\n\n"
            "Our daily decisions will usually look much smaller than a departure from Egypt. Scripture gives us things we can return to: truthfulness, mercy, love, forgiveness. We may find an opportunity to practice one of those while other questions remain open. Both the unfinished questions and the next ordinary act of faithfulness can become part of our conversation with Him."
        ),
        "context": "God names Moses' task: go to Pharaoh and bring Israel out of Egypt. The story does not ask Moses to follow an undefined feeling. His response is to a clear commission from God.",
        "connection": "Hebrews 11:8 recalls Abraham responding to God's call before knowing his destination; Moses later leads Abraham's descendants toward the land of promise. John 14:6 centers access to the Father in Jesus. These passages trace God's faithfulness without making our uncertainty itself proof of a divine assignment.",
        "reflection": "What part of your life are you trying to understand all at once, and what becomes clearer as you bring it before God?",
        "prayer": "Father, I bring You the questions I cannot answer yet. Help me listen to Your Word, welcome wise counsel, and recognize what faithfulness might look like today. Amen.",
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
        "encouragement": "God's promise of His presence gives us language for trust in the middle of difficulty.",
        "devotional": (
            "A hard day can leave us wondering whether we have misunderstood something. We prayed. We tried to act with care. Yet the conversation became more difficult, the burden grew heavier, or the answer we hoped for still has not come. In that place, even familiar words about God's presence can feel difficult to hold.\n\n"
            "Moses heard God's promise before he returned to Egypt: Certainly I will be with thee. What followed included real resistance. In Exodus 5, Pharaoh responded to the request for Israel's release by making the people's work harder. Moses returned to God with painful questions about what was happening. His experience of difficulty became part of his conversation with the One who had sent him.\n\n"
            "That detail matters. Scripture gives us both the promise at the bush and the distress that came afterward. We are allowed to read them together. Moses' story makes room for a faith that speaks honestly about suffering while continuing to look toward God for help.\n\n"
            "Psalm 23 gives us another way to hear this. David speaks of green pastures and still waters, then of the valley of the shadow of death. In the valley, his words become direct: Thou art with me. The Shepherd who restores his soul is also the One he addresses when the path grows dark. His trust has someone to speak to.\n\n"
            "The same concern for His people's companionship appears in Jesus' words before the cross. In John 14:16-18, He promises the Holy Spirit and tells His disciples that He will not leave them comfortless. They were approaching events that would shake them deeply. Jesus was preparing them to understand their life with Him beyond what they could presently see.\n\n"
            "Through Christ's death and resurrection, His people are brought into lasting fellowship with God. The Holy Spirit's presence belongs to that gift. Our prayers can include grief, confusion, and a request for help without pretending that we have already found an explanation for everything.\n\n"
            "Perhaps the prayer available to you today is very simple: Lord, this is hard. You may need time, practical help, or the company of someone who will listen. Bringing those needs before God can be part of learning to trust Him in the place you actually are."
        ),
        "context": "Exodus 3:12 promises God's presence for Moses' commission. Exodus 5:6-23 records Pharaoh increasing Israel's burdens and Moses returning to God with questions. Read the promise alongside the later resistance, without making hardship evidence that God is absent.",
        "connection": "Psalm 23:4 addresses God directly in the valley. In John 14:16-18, Jesus promises the Holy Spirit and assures His disciples that He will not leave them comfortless. These passages develop the theme of God's presence with His people through different circumstances and covenants.",
        "reflection": "What would you want to say to God about a hard place in your life if you did not feel you had to make your prayer sound strong?",
        "prayer": "Lord, You know what this day feels like. Help me bring my questions to You honestly and receive the care and support I need. Teach me to trust Your presence while the way remains difficult. Amen.",
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
        "encouragement": "We can bring the words we struggle to find before the God who knows us.",
        "devotional": (
            "Some conversations begin long before we speak. We rehearse them while driving, imagine several possible responses, and search for a sentence that will make everything come out right. The more a conversation matters, the more aware we may become of our limits. We want to be understood. We are afraid of making things worse.\n\n"
            "Moses brought his concern about speaking directly to God. He described himself as slow of speech and of a slow tongue. The prospect of standing before Pharaoh was tied to a deeply personal concern: he did not feel able to speak for the task God had given him.\n\n"
            "God answered by reminding Moses who made the human mouth. Then He promised to help him speak and teach him what to say. The commission to Pharaoh remained enormous, but Moses' difficulty was fully known to the One who was sending him. God would also provide Aaron to share in the work.\n\n"
            "There is a larger story of God making Himself known through words. He speaks to Moses and sends him with a message for Israel. Later, John 1:14 brings us to Jesus, the Word made flesh, full of grace and truth. God comes near in the person of His Son. Through Jesus, we see His character and hear His invitation to life with Him.\n\n"
            "Grace and truth give us something to consider when we bring our own conversations to God. We may need courage to speak honestly, humility to admit what we do not know, or tenderness toward someone whose pain we have not understood. Prayer can begin before we have found a polished sentence.\n\n"
            "James 1:19 adds another part of faithful communication: being quick to listen and slow to speak. Sometimes the words we need become clearer as we listen. We may discover that we have been preparing a defense when the other person needs to be heard, or rushing toward an answer before we understand the question.\n\n"
            "Our words will still need care. We can ask for wisdom, prepare thoughtfully, and seek help from someone trustworthy. We can also return to a conversation when we need to apologize or clarify. The God who heard Moses' concern can hear ours as we learn to speak with honesty and love."
        ),
        "context": "Moses names his difficulty speaking in Exodus 4:10-12. God reminds him of His creative authority and promises help for the commission; Aaron's supporting role follows in verses 14-16. The text does not identify a medical diagnosis or make our everyday speech infallible.",
        "connection": "John 1:14 presents Jesus as the Word made flesh, full of grace and truth, within God's larger work of making Himself known. James 1:19 calls believers to be quick to listen and slow to speak. Together these passages invite thoughtful, humble reflection on communication.",
        "reflection": "When you think about a conversation you are carrying, what do you need to bring to God before you try to find the right words?",
        "prayer": "God, You know the words I struggle to find. Help me listen with care, speak truthfully, and remain willing to learn. Give me humility to ask for help and make things right when I need to. Amen.",
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
        "verse": "I will be with thy mouth, and with his mouth.",
        "verse_reference": "Exodus 4:15",
        "encouragement": "God's correction and His provision both belong in Moses' story of reluctance.",
        "devotional": (
            "There is a difference between having a question and hoping the responsibility will go away. Sometimes we recognize that difference in ourselves before we are willing to say it aloud. We may have several sensible explanations ready, while underneath them sits a simpler thought: I wish someone else would do this.\n\n"
            "By this point in the conversation at the burning bush, Moses has raised concern after concern. Now he asks God to send someone else. Scripture records the moment plainly. It also tells us that God's anger was kindled against him. The conversation includes a correction that we should allow ourselves to hear.\n\n"
            "Yet the next words also describe provision. Aaron will come to meet Moses and help him speak. God will teach them what to do. Moses still has a part in the work, and he will receive help within it. God's response takes his resistance seriously while making a way for him to move forward.\n\n"
            "Jonah's story gives us another account of reluctance. He receives a clear call to Nineveh and boards a ship headed elsewhere (Jonah 1:1-3). Later, the word of the Lord comes to him a second time, and he goes (Jonah 3:1-3). These stories show God's servants as real people whose responses sometimes need to change. God's purpose and mercy extend beyond their first response.\n\n"
            "That honesty can help us look at our own hearts without rushing to a conclusion about every hesitation. Some situations call for patience, more information, or wise counsel. There are also moments when Scripture has made something clear and we are resisting what it asks of us. God knows the difference, including the motives we struggle to untangle.\n\n"
            "Hebrews 4:14-16 brings us to Jesus, our great High Priest. Because of Him, we are invited to approach God's throne of grace for mercy and help. We can come with our need fully acknowledged. His grace gives us a place to bring the parts of ourselves that still need correction.\n\n"
            "Perhaps there is a conversation, an apology, or an act of care you have been avoiding. Perhaps you need help understanding what faithfulness would involve. You can bring the hesitation itself into prayer. There is room to listen, receive help, and allow God to work on what lies beneath your first response."
        ),
        "context": "Moses asks God to send someone else in Exodus 4:13. Verses 14-17 describe God's anger, Aaron's provision as spokesman, and continued instruction for their task. This specific commission includes correction and help; it does not make every hesitation in ordinary decision-making disobedience.",
        "connection": "Jonah 1:1-3 and 3:1-3 show resistance followed by a renewed call. Hebrews 4:14-16 invites believers to seek mercy and help through Jesus, their great High Priest. These passages make room for honest self-examination without hiding the need for a changed response.",
        "reflection": "What hesitation might you name honestly before God if you trusted that you could come to Him for both mercy and correction?",
        "prayer": "Lord, help me understand what is beneath my hesitation. Give me discernment where I need patience, humility where I need correction, and willingness to receive the help You provide. Amen.",
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
        "encouragement": "An ordinary staff becomes part of a story that draws attention to God's power and faithfulness.",
        "devotional": (
            "It is easy to look at someone else's resources and decide we have very little to offer. They seem to have the experience, the confidence, or the opportunity we lack. Meanwhile, our own life can look too ordinary to matter much: familiar work, limited time, a few relationships, and responsibilities that rarely attract attention.\n\n"
            "When Moses wondered whether Israel would believe that God had appeared to him, God asked about the object already in his hand. It was a staff. In God's instructions, that familiar object became part of a sign confirming the message Moses would carry. The authority behind the sign belonged to God.\n\n"
            "Verse 5 tells us the purpose: the people would believe that the God of Abraham, Isaac, and Jacob had appeared to Moses. That places the staff inside a much larger story. Generations of promise and a suffering people's need for deliverance meet in this conversation. God is making Himself known as faithful to His covenant.\n\n"
            "The scene also includes a moment of fear: when the staff becomes a serpent, Moses runs from it. He then follows God's instruction to take it by the tail, and it becomes a staff again. We see a person learning to respond while the signs themselves point Israel toward God.\n\n"
            "Paul develops a related theme in 2 Corinthians 4:5-7. He describes the gospel as a treasure carried in earthen vessels. Those fragile containers draw attention to the power of God. The treasure is the knowledge of His glory in the face of Jesus Christ, the Lord whom Paul proclaims. Human weakness can remain visible as the good news is shared.\n\n"
            "Moses' staff and Paul's image of clay vessels belong to different settings. Together they help us consider a life of dependence on God. Our limitations do not have to be hidden before we bring our lives to Him. Christ's death and resurrection give us a hope far larger than an impressive account of our own abilities.\n\n"
            "The ordinary things around us may offer real opportunities for love: time to listen, a meal to share, a skill that helps someone, or a few words of encouragement. We can ask God to help us notice those possibilities and use what is available with care. Even what feels small can become something we bring before Him as we consider the needs of the people around us."
        ),
        "context": "Exodus 4:1-5 gives Moses a sign confirming God's appearance and commission to Israel. Verse 5 explicitly names the God of Abraham, Isaac, and Jacob. The staff's role depends on God's command and action, rather than a general promise that everyday possessions become miraculous.",
        "connection": "Second Corinthians 4:5-7 describes the knowledge of God's glory in Christ as treasure in fragile earthen vessels. Verses 13-14 connect Paul's ministry to faith in the God who raised Jesus. These themes invite reflection on dependence, service, and the gospel amid human limitations.",
        "reflection": "What ordinary part of your life have you been overlooking as you consider how you might love and serve the people around you?",
        "prayer": "Father, I bring You my real life, with its resources and its limits. Help me notice opportunities to love others and use what I have with care. Keep my attention on Your faithfulness as I learn to serve. Amen.",
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
        "encouragement": "Stillness begins with remembering who God is while much around us remains unsettled.",
        "devotional": (
            "Our bodies can stop while our minds keep working. We sit down with a cup of coffee and begin rehearsing the conversation ahead, reviewing yesterday's decisions, or making a list of things we might have missed. A quiet room can make us more aware of how much we are carrying.\n\n"
            "Psalm 46 meets us with a world far more unsettled than that room. The earth moves. Mountains shake. Waters roar. Nations rage, and kingdoms are disturbed. In the middle of those images, the psalm names God as refuge and strength, a very present help in trouble. Its confidence has room for an honest description of upheaval.\n\n"
            "The call to be still comes within that larger picture. God is the One who brings wars to an end and will be exalted among the nations. Stillness involves recognizing His authority over a world we cannot hold together ourselves. The psalm directs our attention toward Him and repeats its assurance that the Lord of hosts is with His people.\n\n"
            "Notice the name used beside that assurance: the God of Jacob. This is the God whose faithfulness runs through the story of His people. The worshippers are remembering who He has shown Himself to be as they face what they cannot control. Their refuge has a history of covenant faithfulness.\n\n"
            "Later in Moses' journey, Exodus 33:14 connects God's presence with rest. Moses responds that he does not want to go forward without that presence. Even the prospect of reaching a destination could not take the place of life with God. His prayer turns our attention toward the relationship at the center of the journey.\n\n"
            "Jesus brings that invitation close in Matthew 11:28-30. He calls the weary to come to Him, take His yoke, and learn from His gentle and humble heart. The rest He offers reaches the soul. Following Him includes a new way of carrying life in relationship with the One who welcomes us.\n\n"
            "A pause in your day may leave many things unfinished. You can name them before God without trying to settle them all in that moment. There may be grief to acknowledge, help to ask for, or a responsibility to return to afterward. For now, there is room to remember the God who is present and let that truth accompany your next breath."
        ),
        "context": "Psalm 46 describes upheaval in creation, the nations, and warfare, while proclaiming God as refuge and sovereign over the earth. Its repeated assurance names the Lord of hosts and the God of Jacob. The call to stillness belongs to that proclamation of His authority and presence.",
        "connection": "Exodus 33:14-15 joins God's presence with rest and records Moses' desire to travel only with Him. In Matthew 11:28-30, Jesus invites the weary to come to Him, learn from Him, and find rest for their souls. Each passage connects rest to relationship with God in its own setting.",
        "reflection": "What would it mean to place what remains unresolved in God's care as you spend a quiet moment with Him today?",
        "prayer": "Lord, I bring You what is unfinished and unsettled. Help me remember who You are, receive the rest You offer, and return to this day with my attention turned toward You. Amen.",
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


def exploration_links(message):
    """Public browser context and the verified Android download listing."""
    return (
        ("Open Angel Chat in your browser", SITE_URL + "?" + urlencode({"v": "angel", "message": message["id"]})),
        ("Get Angel Chat for Android", GOOGLE_PLAY_URL),
    )


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
    links = "\n\n".join(f"{label}:\n{url}" for label, url in exploration_links(message))
    return (
        f"Angel Chat — {message['title']}\n\n"
        f"{opening}"
        f"Today's reading — {message['reference']} (KJV)\n\n"
        f"{message['reading']}\n\n"
        f"{message.get('devotional', message['encouragement'])}\n\n"
        f"A question to carry: {message['reflection']}\n\n"
        f"A prayer: {message['prayer']}\n\n"
        f"Explore this message and ask questions in Angel Chat:\n\n{links}\n\n"
        "Use the browser link on iPhone, iPad, or computer.\n"
    )


def email_preview_html(message):
    """Use the same complete content and named links in preview and delivery."""
    links = {f"{label}:\n{url}": (label, url) for label, url in exploration_links(message)}
    paragraphs = []
    for paragraph in email_preview(message).strip().split("\n\n"):
        if paragraph in links:
            label, url = links[paragraph]
            paragraphs.append(
                f'<p><a href="{html.escape(url, quote=True)}" target="_blank" rel="noopener noreferrer">{html.escape(label)}</a></p>'
            )
        else:
            paragraphs.append(f'<p>{html.escape(paragraph).replace(chr(10), "<br>")}</p>')
    return "".join(paragraphs)
