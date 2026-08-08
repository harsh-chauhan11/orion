'use client';

import { Music2, Mic } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface WelcomeViewProps {
  startButtonText: string;
  onStartCall: () => void;
}

export const WelcomeView = ({
  startButtonText,
  onStartCall,
}: React.ComponentProps<'div'> & WelcomeViewProps) => {
  return (
    <div className="relative flex min-h-svh w-full items-center justify-center overflow-hidden bg-cover bg-center bg-no-repeat"
      style={{ backgroundImage: "url('/images/orionbackground.jpg')" }}>
      {/* Background glow */}
      <div className="pointer-events-none absolute left-1/2 top-1/2 h-[500px] w-[500px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-primary/10 blur-3xl" />

      <main className="relative z-10 flex w-full max-w-2xl flex-col items-center px-6 text-center">
        {/* Logo */}
        <div className="mb-8 flex items-center gap-2">
          <div className="flex size-10 items-center justify-center rounded-full bg-primary text-primary-foreground">
            <Music2 size={22} />
          </div>

          <span className="text-xl font-bold tracking-[0.25em]">
            ORION
          </span>
        </div>

        {/* Hero */}
        <div className="mb-8 flex flex-col items-center">
          <div className="mb-6 flex size-24 items-center justify-center rounded-full border border-primary/20 bg-primary/10">
            <Music2 size={42} className="text-primary" />
          </div>

          <h1 className="text-4xl font-bold tracking-tight sm:text-5xl">
            Your AI Music Companion
          </h1>

          <p className="text-muted-foreground mt-4 max-w-lg text-base leading-7 sm:text-lg">
            Discover songs, explore artists, and get personalized music
            recommendations — just ask with your voice.
          </p>
        </div>

        {/* Start button */}
        <Button
          size="lg"
          onClick={onStartCall}
          className="h-14 w-64 rounded-full text-sm font-bold tracking-wide"
        >
          <Mic className="mr-2 size-5" />
          {startButtonText || 'Start Listening'}
        </Button>

        <p className="text-muted-foreground mt-5 text-xs">
          Tap the button and start talking
        </p>
      </main>

      {/* Footer */}
      <div className="text-muted-foreground absolute bottom-5 left-0 flex w-full justify-center px-6 text-center text-xs">
        <p>
          Powered by AI voice technology
        </p>
      </div>
    </div>
  );
};


