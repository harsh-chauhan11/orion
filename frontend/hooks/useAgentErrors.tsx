import { ReactNode, useEffect } from 'react';
import { toast as sonnerToast } from 'sonner';
import { useAgent, useSessionContext } from '@livekit/components-react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';

interface ToastProps {
  title: ReactNode;
  description: ReactNode;
}

function toastAlert(toast: ToastProps) {
  const { title, description } = toast;

  return sonnerToast.custom(
    (id) => (
      <Alert
        onClick={() => sonnerToast.dismiss(id)}
        className="w-full border-destructive/20 bg-background md:w-[364px]"
      >
        <AlertTitle className="flex items-center gap-2">
          ⚠️ {title}
        </AlertTitle>

        <AlertDescription className="mt-2">
          {description && description}
        </AlertDescription>
      </Alert>
    ),
    {
      duration: 10_000,
    }
  );
}

export function useAgentErrors() {
  const agent = useAgent();
  const { isConnected, end } = useSessionContext();

  useEffect(() => {
    if (isConnected && agent.state === 'failed') {
      const reasons = agent.failureReasons;

      toastAlert({
        title: 'Orioncouldn’t connect',
        description: (
          <>
            <p className="mb-3">
              Something went wrong while connecting to your music
              companion. Please try starting the conversation again.
            </p>

            {reasons.length > 0 && (
              <div className="rounded-md bg-muted/50 p-2 text-xs">
                {reasons.length > 1 ? (
                  <ul className="list-inside list-disc">
                    {reasons.map((reason) => (
                      <li key={reason}>{reason}</li>
                    ))}
                  </ul>
                ) : (
                  <p>{reasons[0]}</p>
                )}
              </div>
            )}
          </>
        ),
      });

      end();
    }
  }, [agent, isConnected, end]);
}


