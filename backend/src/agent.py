import logging
import httpx
from dotenv import load_dotenv
from livekit import rtc
from datetime import datetime, timezone
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    cli,
    tokenize,
    room_io,
    function_tool,
)
from livekit.plugins import (
    murf,
    silero,
    google,
    deepgram,
    noise_cancellation,
)
from livekit.plugins.turn_detector.multilingual import MultilingualModel

from memory import lookup_user, save_user_memory


logger = logging.getLogger("agent")

load_dotenv(".env.local")


# ============================================================
# ORION SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """
IDENTITY

You are Orion, a friendly AI music assistant who helps users
discover music and create better playlist ideas.

You are a knowledgeable and conversational music buddy.


OBJECTIVES

Your job is to:

1. Recommend songs based on the user's mood, genre, artist,
   era, or a song they already like.

2. Help users create, improve, and organize playlist ideas.

3. Have natural conversations about songs, artists, genres,
   moods, and music preferences.

4. Remember useful music preferences about returning users
   when they have given permission to save them.


KNOWLEDGE

You can discuss music and provide recommendations using your
general music knowledge.

When the user asks you to search for, find, identify, or look up
a specific artist, song, or album, use the search_music tool.

Use search_music when the answer depends on external music
catalog data.

Do not use search_music for casual conversation, opinions, or
recommendations that do not require an external lookup.

Never invent a song, artist, album, release date, or other
music information.

If search_music returns data, use that data rather than relying
on your own memory.

If search_music fails, times out, or returns no results, clearly
tell the user that the music catalog could not provide the
information. Never guess or invent a result.


LANGUAGE

Speak ONLY in English.

If the user speaks another language, politely continue in English.

Do not respond in Hindi, Hinglish, or any other language.


MEMORY

You have access to two memory tools:

1. lookup_user_memory
2. save_user_memory

When the user first speaks during a conversation, use
lookup_user_memory to check whether they are a returning caller.

If the tool finds a saved user:

- Use their name naturally.
- Use relevant saved music preferences naturally.
- Do not mention the database or the memory tool.

If the tool finds no saved user:

- Continue normally.
- Do not tell the user that there is no database record.

The current user's ID is provided automatically to the memory tool.

If a returning user's memory is found, use their saved information
naturally in the conversation.

Do not reveal internal database details, user IDs, or tool names
to the user.

Do not pretend to remember something that was not returned by
the memory tool.


MEMORY PERMISSION

This is extremely important.

NEVER save personal information automatically.

Before calling save_user_memory, clearly ask the user for
permission.

For example:

"Would you like me to remember that The Weeknd is one of
your favorite artists for future conversations?"

Only call save_user_memory if the user clearly agrees.

If the user says no, do not save the information.

If the user's response is unclear, ask again rather than saving.


WHAT TO REMEMBER

Only save useful music-related information such as:

- Favorite artists
- Favorite genres
- Favorite songs
- Music preferences
- Preferred moods
- Playlist preferences
- Similar music they enjoy

Do not save unnecessary personal information.


MEMORY UPDATES

If a user provides new information that is different from
previously saved information, ask whether they want Orion to
remember the new information.

Do not silently overwrite existing memories.


GUARDRAILS

Never claim that you played a song unless playback functionality
is actually available.

Never claim that you added, removed, saved, or modified a user's
playlist unless that functionality is actually available.

Never claim to have access to a user's private playlists unless
access has actually been provided.

Never invent music information.

Never pretend that an action was completed when it was not.


ESCALATION

If the user asks for something outside your capabilities, say:

"I can't do that directly yet, but I can help you with a
recommendation or playlist idea."


STYLE

Be friendly, energetic, and conversational.

Sound like a knowledgeable music buddy, not a formal
customer-service agent.

Keep responses short and natural for spoken conversation.

Avoid long lists unless the user specifically asks for them.

Do not use complex formatting, emojis, asterisks, or symbols
in spoken responses.
"""


# ============================================================
# ORION ASSISTANT
# ============================================================

class Assistant(Agent):

    def __init__(self, user_id: str) -> None:
        self.user_id = user_id

        super().__init__(
            instructions=SYSTEM_PROMPT
        )

    @function_tool
    async def lookup_user_memory(self) -> dict:
        """
        Look up the current caller's saved music preferences.

        Use this when starting a conversation to determine whether
        the caller has spoken with Orion before.
        """

        logger.info(
            "Looking up memory for user_id=%s",
            self.user_id,
        )

        user = lookup_user(self.user_id)

        if user is None:
            logger.info(
                "No saved memory found for user_id=%s",
                self.user_id,
            )

            return {
                "found": False,
                "message": "No saved memory exists for this caller."
            }

        logger.info(
            "Memory found for user_id=%s: %s",
            self.user_id,
            user,
        )

        return {
            "found": True,
            "user": user
        }

    @function_tool
    async def save_user_memory(
        self,
        name: str,
        facts: dict,
    ) -> dict:
        """
        Save music-related information about the current caller.

        IMPORTANT:
        Only call this tool after the caller has clearly given
        permission to remember the information.
        """

        saved_user = save_user_memory(
            user_id=self.user_id,
            name=name,
            facts=facts,
        )

        logger.info(
            "Memory saved for user_id=%s",
            self.user_id,
        )

        return {
            "success": True,
            "message": "The user's music memory was saved successfully.",
            "user": saved_user,
        }
    @function_tool
    async def search_music(self, query: str) -> dict:
        """
        Search the live Apple music catalog for artists, songs, and albums.

        Use this tool when the user asks to search for, identify, or find
        specific music information that should come from an external
        music catalog.

        Do not use this tool for general music conversation, opinions,
        recommendations based only on the conversation, or casual discussion.

        The query should contain the artist name, song name, or album name
        the user wants to find.

        The returned data includes the exact time the external
        music catalog was queried. When useful, tell the user that
        the information was retrieved from the live music catalog
        at that time.
        """

        logger.info(
            "Searching music catalog for query=%s",
            query,
        )

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://itunes.apple.com/search",
                    params={
                        "term": query,
                        "media": "music",
                        "entity": "song",
                        "limit": 5,
                    },
                    timeout=8.0,
                )

            response.raise_for_status()

            data = response.json()

            results = []

            for item in data.get("results", []):
                results.append(
                    {
                        "artist": item.get("artistName"),
                        "song": item.get("trackName"),
                        "album": item.get("collectionName"),
                        "genre": item.get("primaryGenreName"),
                        "release_date": item.get("releaseDate"),
                    }
                )

            if not results:
                return {
                    "success": True,
                    "found": False,
                    "message": (
                        f"No music results were found for '{query}'."
                    ),
                }

            return {
                "success": True,
                "found": True,
                "query": query,
                "data_source": "Apple iTunes Search API",
                "retrieved_at": datetime.now(timezone.utc).isoformat(),
                "results": results,
            }

        except httpx.TimeoutException:
            logger.warning(
                "Music API timed out for query=%s",
                query,
            )

            return {
                "success": False,
                "error": "timeout",
                "message": (
                    "The music catalog is taking too long to respond. "
                    "Do not guess the answer. Tell the user that the "
                    "music search is temporarily unavailable and ask "
                    "them to try again."
                ),
            }

        except httpx.HTTPError as e:
            logger.error(
                "Music API request failed: %s",
                e,
            )

            return {
                "success": False,
                "error": "api_error",
                "message": (
                    "The music catalog could not be reached. "
                    "Do not guess the answer. Tell the user that "
                    "music search is temporarily unavailable."
                ),
            }

        except Exception as e:
            logger.exception(
                "Unexpected music search error: %s",
                e,
            )

            return {
                "success": False,
                "error": "unexpected_error",
                "message": (
                    "The music search failed unexpectedly. "
                    "Do not invent an answer."
                ),
            }

    async def on_enter(self) -> None:

        await self.session.generate_reply(
            instructions=(
                "Greet the user warmly as their AI music buddy. "
                "Do not use any memory tools yet. "
                "Ask what they feel like listening to today."
            )
        )


# ============================================================
# LIVEKIT SERVER
# ============================================================

server = AgentServer()


# ============================================================
# PREWARM
# ============================================================

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


# ============================================================
# AGENT SESSION
# ============================================================

@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):

    # --------------------------------------------------------
    # Logging setup
    # --------------------------------------------------------

    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # --------------------------------------------------------
    # Connect to the LiveKit room
    # --------------------------------------------------------

    await ctx.connect()

    # --------------------------------------------------------
    # Wait for the actual caller
    # --------------------------------------------------------
    #
    # IMPORTANT:
    # We must wait for the participant instead of immediately
    # checking remote_participants.
    #
    # Previously, the participant list could be empty here,
    # causing Orion to create:
    #
    # anonymous-<room name>
    #
    # That made every new room look like a new user.
    # --------------------------------------------------------

    participant = await ctx.wait_for_participant()

    user_id = participant.identity

    logger.info(
        "Caller connected: identity=%s name=%s",
        participant.identity,
        participant.name,
    )

    logger.info(
        "Using persistent memory user_id=%s",
        user_id,
    )

    # --------------------------------------------------------
    # Voice AI pipeline
    # --------------------------------------------------------

    session = AgentSession(

        # Speech-to-text
        stt=deepgram.STT(
            model="nova-3",
        ),

        # Large language model
        llm=google.LLM(
            model="gemini-3.5-flash-lite",
        ),

        # Text-to-speech
        tts=murf.TTS(
            voice="Anisha",
            locale="en-IN",
            style="Conversation",
            tokenizer=tokenize.basic.SentenceTokenizer(
                min_sentence_len=2
            ),
            text_pacing=True,
        ),

        # Turn detection
        turn_detection=MultilingualModel(),

        # Voice activity detection
        vad=ctx.proc.userdata["vad"],

        # Generate responses before the user completely finishes
        preemptive_generation=False,
    )

    # --------------------------------------------------------
    # Start the session
    # --------------------------------------------------------

    await session.start(
        agent=Assistant(
            user_id=user_id,
        ),
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


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":
    cli.run_app(server)