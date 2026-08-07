import logging

from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    cli,
    inference,
    tokenize,
    room_io,
)
from livekit.plugins import murf, silero, google, deepgram, noise_cancellation
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("agent")

load_dotenv(".env.local")

# Change this prompt to change what your voice agent does.
# See README.md for example prompts (customer support, language tutor, receptionist).
SYSTEM_PROMPT = """
IDENTITY
You are a friendly AI music assistant who helps users discover music and create better playlist ideas.

OBJECTIVES
Your job is to:
1. Recommend songs based on the user's mood, genre, artist, era, or a song they already like.
2. Help users create, improve, and organize playlist ideas.
3. Have natural conversations about songs, artists, genres, moods, and music preferences.

KNOWLEDGE
You can discuss music and provide recommendations using the knowledge available to you.
Never invent a song, artist, album, release date, or other music information.
If you are uncertain about a fact, say that you are not sure rather than making it up.

LANGUAGE
Match the user's language and speaking style.
If the user speaks Hindi, respond in Hindi.
If the user speaks Hinglish, respond naturally in Hinglish.
If the user speaks English, respond in English.
If the user switches languages during the conversation, follow their language naturally.
Keep Hindi and English code-mixing natural and conversational.

GUARDRAILS
Never claim that you played a song unless playback functionality is actually available.
Never claim that you added, removed, saved, or modified a user's playlist unless that functionality is actually available.
Never claim to have access to a user's private playlists unless access has actually been provided.
Never invent music information.
Never pretend that an action was completed when it was not.

If the user asks you to perform an action that you cannot actually perform, be honest and explain what you can do instead.

ESCALATION
If the user asks for something outside your capabilities, say:
"I can't do that directly yet, but I can help you with a recommendation or playlist idea."

STYLE
Be friendly, energetic, and conversational.
Sound like a knowledgeable music buddy, not a formal customer-service agent.
Keep responses short and natural for spoken conversation.
Avoid long lists unless the user specifically asks for them.
Do not use complex formatting, emojis, asterisks, or symbols in spoken responses.
"""
class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=SYSTEM_PROMPT)

    async def on_enter(self) -> None:
        await self.session.generate_reply(
            instructions=(
                "Greet the user warmly as their AI music buddy. "
                "Briefly explain that you can help them discover songs "
                "and build playlist ideas. "
                "Ask what they feel like listening to today."
            )
        )


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):
    # Logging setup
    # Add any other context you want in all log entries here
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Set up a voice AI pipeline using Murf Falcon, Gemini, Deepgram, and the LiveKit turn detector
    session = AgentSession(
        # Speech-to-text (STT) is your agent's ears, turning the user's speech into text that the LLM can understand
        # See all available models at https://docs.livekit.io/agents/models/stt/
        stt=deepgram.STT(model="nova-3"),
        # A Large Language Model (LLM) is your agent's brain, processing user input and generating a response
        # See all available models at https://docs.livekit.io/agents/models/llm/
        llm=google.LLM(
                model="gemini-3.5-flash-lite",
            ),
        # Text-to-speech (TTS) is your agent's voice, turning the LLM's text into speech that the user can hear
        # See all available models as well as voice selections at https://docs.livekit.io/agents/models/tts/
        tts=murf.TTS(
                voice="Anisha", 
                locale="en-IN",
                style="Conversation",
                tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
                text_pacing=True
            ),
        # VAD and turn detection are used to determine when the user is speaking and when the agent should respond
        # See more at https://docs.livekit.io/agents/build/turns
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        # allow the LLM to generate a response while waiting for the end of turn
        # See more at https://docs.livekit.io/agents/build/audio/#preemptive-generation
        preemptive_generation=True,
    )

    # To use a realtime model instead of a voice pipeline, use the following session setup instead.
    # (Note: This is for the OpenAI Realtime API. For other providers, see https://docs.livekit.io/agents/models/realtime/))
    # 1. Install livekit-agents[openai]
    # 2. Set OPENAI_API_KEY in .env.local
    # 3. Add `from livekit.plugins import openai` to the top of this file
    # 4. Use the following session setup instead of the version above
    # session = AgentSession(
    #     llm=openai.realtime.RealtimeModel(voice="marin")
    # )

    # # Add a virtual avatar to the session, if desired
    # # For other providers, see https://docs.livekit.io/agents/models/avatar/
    # avatar = hedra.AvatarSession(
    #   avatar_id="...",  # See https://docs.livekit.io/agents/models/avatar/plugins/hedra
    # )
    # # Start the avatar and wait for it to join
    # await avatar.start(session, room=ctx.room)

    # Start the session, which initializes the voice pipeline and warms up the models
    await session.start(
        agent=Assistant(),
        room=ctx.room,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda params: (
                    noise_cancellation.BVCTelephony()
                    if params.participant.kind
                    == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
                    else noise_cancellation.BVC()
                ),
            ),
        ),
    )

    # Join the room and connect to the user
    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(server)
