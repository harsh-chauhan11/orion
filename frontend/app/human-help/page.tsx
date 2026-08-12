"use client";

import { useEffect, useState } from "react";

type Escalation = {
  request_id: string;
  user_id: string;
  name: string;
  issue: string;
  agent_checked: string;
  urgency: string;
  language: string;
  preferred_follow_up: string;
  status: string;
  created_at: string;
};

export default function HumanHelpPage() {
  const [escalations, setEscalations] = useState<Escalation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadEscalations() {
      try {
        const response = await fetch("/api/escalations");

        if (!response.ok) {
          throw new Error("Failed to load escalation requests.");
        }

        const data = await response.json();

        setEscalations(data.escalations ?? []);
      } catch (err) {
        console.error(err);
        setError("Unable to load human-help requests.");
      } finally {
        setLoading(false);
      }
    }

    loadEscalations();
  }, []);

  return (
    <main className="min-h-screen bg-black px-6 py-10 text-white">
      <div className="mx-auto max-w-6xl">
        <div className="mb-10">
          <p className="text-sm uppercase tracking-[0.3em] text-white/50">
            Orion
          </p>

          <h1 className="mt-2 text-4xl font-semibold">
            Human Help
          </h1>

          <p className="mt-3 text-white/60">
            Review support requests created by Orion.
          </p>
        </div>

        {loading && (
          <div className="rounded-2xl border border-white/10 bg-white/5 p-8">
            Loading requests...
          </div>
        )}

        {error && (
          <div className="rounded-2xl border border-red-400/20 bg-red-400/10 p-6 text-red-200">
            {error}
          </div>
        )}

        {!loading && !error && escalations.length === 0 && (
          <div className="rounded-2xl border border-white/10 bg-white/5 p-8 text-white/60">
            No human-help requests yet.
          </div>
        )}

        <div className="space-y-6">
          {escalations.map((request) => (
            <section
              key={request.request_id}
              className="rounded-3xl border border-white/10 bg-white/[0.04] p-6 shadow-xl"
            >
              <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                <div>
                  <p className="text-sm text-white/50">
                    Request ID
                  </p>

                  <h2 className="mt-1 text-xl font-medium">
                    {request.request_id}
                  </h2>
                </div>

                <div className="flex gap-3">
                  <span className="rounded-full border border-white/10 bg-white/10 px-3 py-1 text-xs uppercase tracking-wide">
                    {request.status}
                  </span>

                  <span className="rounded-full border border-white/10 bg-white/10 px-3 py-1 text-xs uppercase tracking-wide">
                    {request.urgency}
                  </span>
                </div>
              </div>

              <div className="mt-8 grid gap-6 md:grid-cols-2">
                <div>
                  <p className="text-sm text-white/40">
                    User
                  </p>
                  <p className="mt-1">
                    {request.name}
                  </p>
                </div>

                <div>
                  <p className="text-sm text-white/40">
                    Language
                  </p>
                  <p className="mt-1">
                    {request.language}
                  </p>
                </div>

                <div>
                  <p className="text-sm text-white/40">
                    Preferred follow-up
                  </p>
                  <p className="mt-1">
                    {request.preferred_follow_up}
                  </p>
                </div>

                <div>
                  <p className="text-sm text-white/40">
                    Created
                  </p>
                  <p className="mt-1">
                    {new Date(request.created_at).toLocaleString()}
                  </p>
                </div>
              </div>

              <div className="mt-8">
                <p className="text-sm text-white/40">
                  What happened
                </p>

                <p className="mt-2 leading-7 text-white/80">
                  {request.issue}
                </p>
              </div>

              <div className="mt-6">
                <p className="text-sm text-white/40">
                  What Orion already checked
                </p>

                <p className="mt-2 leading-7 text-white/80">
                  {request.agent_checked}
                </p>
              </div>
            </section>
          ))}
        </div>
      </div>
    </main>
  );
}