'use client';

import { useEffect, useRef, useState } from 'react';
import { useTheme } from 'next-themes';
import { AnimatePresence, motion } from 'motion/react';
import {
  CheckCircle2,
  Loader2,
  Music2,
  RotateCcw,
} from 'lucide-react';
import { useSessionContext } from '@livekit/components-react';

import type { AppConfig } from '@/app-config';
import { AgentSessionView_01 } from '@/components/agents-ui/blocks/agent-session-view-01';
import { WelcomeView } from '@/components/app/welcome-view';
import { Button } from '@/components/ui/button';

const MotionWelcomeView = motion.create(WelcomeView);
const MotionSessionView = motion.create(AgentSessionView_01);

const VIEW_MOTION_PROPS = {
  variants: {
    visible: {
      opacity: 1,
    },
    hidden: {
      opacity: 0,
    },
  },
  initial: 'hidden',
  animate: 'visible',
  exit: 'hidden',
  transition: {
    duration: 0.5,
    ease: 'linear',
  },
};

interface ViewControllerProps {
  appConfig: AppConfig;
}

export function ViewController({ appConfig }: ViewControllerProps) {
  const { isConnected, start } = useSessionContext();
  const { resolvedTheme } = useTheme();

  const [isConnecting, setIsConnecting] = useState(false);
  const [hasEndedCall, setHasEndedCall] = useState(false);

  const wasConnected = useRef(false);

  useEffect(() => {
    if (isConnected) {
      setIsConnecting(false);
      setHasEndedCall(false);
      wasConnected.current = true;
    } else if (wasConnected.current) {
      setHasEndedCall(true);
      wasConnected.current = false;
    }
  }, [isConnected]);

  const handleStartCall = async () => {
    setIsConnecting(true);
    setHasEndedCall(false);

    try {
      await start();
    } catch (error) {
      console.error('Failed to start call:', error);
      setIsConnecting(false);
    }
  };

  return (
    <AnimatePresence mode="wait">
      {!isConnected && !isConnecting && !hasEndedCall && (
        <MotionWelcomeView
          key="welcome"
          {...VIEW_MOTION_PROPS}
          startButtonText={appConfig.startButtonText}
          onStartCall={handleStartCall}
        />
      )}

      {!isConnected && isConnecting && (
       <motion.div
          key="connecting"
          {...VIEW_MOTION_PROPS}
          className="flex min-h-svh w-full items-center justify-center bg-cover bg-center bg-no-repeat px-6"
          style={{ backgroundImage: "url('/images/orionbackground.jpg')" }}>
          <div className="flex max-w-md flex-col items-center text-center">
            <div className="mb-6 flex size-24 items-center justify-center rounded-full border border-primary/20 bg-primary/10">
              <Music2 className="size-10 text-primary" />
            </div>

            <div className="mb-4 flex items-center gap-2">
              <Loader2 className="size-5 animate-spin text-primary" />

              <span className="text-sm font-medium">
                Connecting to Orion...
              </span>
            </div>

            <h1 className="text-2xl font-bold">
              Getting your music companion ready
            </h1>

            <p className="text-muted-foreground mt-3 max-w-sm text-sm leading-6">
              Please wait while we connect you to your AI music assistant.
            </p>
          </div>
        </motion.div>
      )}

      {!isConnected && !isConnecting && hasEndedCall && (
        <motion.div
          key="call-ended"
          {...VIEW_MOTION_PROPS}
          className="flex min-h-svh w-full items-center justify-center bg-cover bg-center bg-no-repeat px-6"
          style={{ backgroundImage: "url('/images/orionbackground.jpg')" }}>
          <div className="flex max-w-md flex-col items-center text-center">
            <div className="mb-6 flex size-24 items-center justify-center rounded-full border border-primary/20 bg-primary/10">
              <CheckCircle2 className="size-10 text-primary" />
            </div>

            <h1 className="text-3xl font-bold">
              Call ended
            </h1>

            <p className="text-muted-foreground mt-3 max-w-sm text-sm leading-6">
              Thanks for listening with Orion. Ready to discover some more
              music?
            </p>

            <Button
              onClick={handleStartCall}
              className="mt-6"
            >
              <RotateCcw className="mr-2 size-4" />
              Start new conversation
            </Button>
          </div>
        </motion.div>
      )}

      {isConnected && (
        <MotionSessionView
          key="session-view"
          {...VIEW_MOTION_PROPS}
          supportsChatInput={appConfig.supportsChatInput}
          supportsVideoInput={appConfig.supportsVideoInput}
          supportsScreenShare={appConfig.supportsScreenShare}
          isPreConnectBufferEnabled={appConfig.isPreConnectBufferEnabled}
          audioVisualizerType={appConfig.audioVisualizerType}
          audioVisualizerColor={
            resolvedTheme === 'dark'
              ? appConfig.audioVisualizerColorDark
              : appConfig.audioVisualizerColor
          }
          audioVisualizerColorShift={appConfig.audioVisualizerColorShift}
          audioVisualizerBarCount={appConfig.audioVisualizerBarCount}
          audioVisualizerGridRowCount={appConfig.audioVisualizerGridRowCount}
          audioVisualizerGridColumnCount={
            appConfig.audioVisualizerGridColumnCount
          }
          audioVisualizerRadialBarCount={
            appConfig.audioVisualizerRadialBarCount
          }
          audioVisualizerRadialRadius={
            appConfig.audioVisualizerRadialRadius
          }
          audioVisualizerWaveLineWidth={
            appConfig.audioVisualizerWaveLineWidth
          }
          className="fixed inset-0"
        />
      )}
    </AnimatePresence>
  );
}


