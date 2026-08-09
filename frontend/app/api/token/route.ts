import { NextResponse } from 'next/server';
import {
  AccessToken,
  type AccessTokenOptions,
  type VideoGrant,
} from 'livekit-server-sdk';
import { RoomConfiguration } from '@livekit/protocol';

type ConnectionDetails = {
  serverUrl: string;
  roomName: string;
  participantName: string;
  participantToken: string;
};

// Environment variables
const API_KEY = process.env.LIVEKIT_API_KEY;
const API_SECRET = process.env.LIVEKIT_API_SECRET;
const LIVEKIT_URL = process.env.LIVEKIT_URL;
const AGENT_NAME = process.env.AGENT_NAME;

// Don't cache results
export const revalidate = 0;

export async function POST(req: Request) {
  try {
    if (LIVEKIT_URL === undefined) {
      throw new Error('LIVEKIT_URL is not defined');
    }

    if (API_KEY === undefined) {
      throw new Error('LIVEKIT_API_KEY is not defined');
    }

    if (API_SECRET === undefined) {
      throw new Error('LIVEKIT_API_SECRET is not defined');
    }

    // --------------------------------------------------------
    // Parse room configuration
    // --------------------------------------------------------

    const body = await req.json().catch(() => ({}));

    let roomConfig: RoomConfiguration | undefined;

    if (body?.room_config) {
      roomConfig = RoomConfiguration.fromJson(
        body.room_config,
        { ignoreUnknownFields: true }
      );
    } else if (AGENT_NAME) {
      roomConfig = RoomConfiguration.fromJson(
        {
          agents: [{ agentName: AGENT_NAME }],
        },
        { ignoreUnknownFields: true }
      );
    }

    // --------------------------------------------------------
    // Persistent participant identity
    // --------------------------------------------------------
    //
    // Previously we generated a random identity every time:
    //
    // voice_assistant_user_7451
    // voice_assistant_user_3821
    // voice_assistant_user_9182
    //
    // That caused Orion's memory system to treat every
    // conversation as a different person.
    //
    // Now we store the identity in a browser cookie.
    // --------------------------------------------------------

    const requestCookies = req.headers.get('cookie') ?? '';

    const existingCookie = requestCookies
      .split(';')
      .map((cookie) => cookie.trim())
      .find((cookie) => cookie.startsWith('orion_user_id='));

    let participantIdentity: string;

    if (existingCookie) {
      participantIdentity = decodeURIComponent(
        existingCookie.substring('orion_user_id='.length)
      );

      console.log(
        `[Orion] Reusing persistent user identity: ${participantIdentity}`
      );
    } else {
      participantIdentity = `voice_assistant_user_${crypto.randomUUID()}`;

      console.log(
        `[Orion] Created new persistent user identity: ${participantIdentity}`
      );
    }

    // --------------------------------------------------------
    // Room identity remains temporary
    // --------------------------------------------------------

    const roomName = `voice_assistant_room_${crypto.randomUUID()}`;

    const participantName = 'user';

    // --------------------------------------------------------
    // Generate LiveKit token
    // --------------------------------------------------------

    const participantToken = await createParticipantToken(
      {
        identity: participantIdentity,
        name: participantName,
      },
      roomName,
      roomConfig
    );

    // --------------------------------------------------------
    // Return connection details
    // --------------------------------------------------------

    const data: ConnectionDetails = {
      serverUrl: LIVEKIT_URL,
      roomName,
      participantName,
      participantToken,
    };

    const headers = new Headers({
      'Cache-Control': 'no-store',
    });

    // If this is the first connection, create the persistent
    // browser cookie.
    if (!existingCookie) {
      headers.append(
        'Set-Cookie',
        `orion_user_id=${encodeURIComponent(
          participantIdentity
        )}; Path=/; Max-Age=31536000; SameSite=Lax`
      );
    }

    return NextResponse.json(data, { headers });

  } catch (error) {
    if (error instanceof Error) {
      console.error(error);

      return new NextResponse(
        error.message,
        { status: 500 }
      );
    }

    return new NextResponse(
      'Unknown error',
      { status: 500 }
    );
  }
}


// ============================================================
// LIVEKIT PARTICIPANT TOKEN
// ============================================================

function createParticipantToken(
  userInfo: AccessTokenOptions,
  roomName: string,
  roomConfig?: RoomConfiguration
): Promise<string> {

  const at = new AccessToken(
    API_KEY!,
    API_SECRET!,
    {
      ...userInfo,
      ttl: '15m',
    }
  );

  const grant: VideoGrant = {
    room: roomName,
    roomJoin: true,
    canPublish: true,
    canPublishData: true,
    canSubscribe: true,
  };

  at.addGrant(grant);

  if (roomConfig) {
    at.roomConfig = roomConfig;
  }

  return at.toJwt();
}