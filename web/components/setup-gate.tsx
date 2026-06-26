"use client";

import { Check, ExternalLink, Loader2, Lock, Sparkles } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { CommandBlock } from "@/components/command-block";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export type PrerequisiteStep = {
  id: string;
  title: string;
  command: string | null;
  succeeded: boolean;
  nextAction: string;
};

const API_KEY_URL = "https://platform.relai.ai/settings/workspace/api-keys";

export function SetupGate({
  steps,
  ready,
  projectRoot,
  onContinue,
  continueLabel = "Get started"
}: {
  steps: PrerequisiteStep[];
  ready: boolean;
  projectRoot?: string;
  onContinue: () => void;
  continueLabel?: string;
}) {
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const activeIndex = steps.findIndex((step) => !step.succeeded);

  async function copy(step: PrerequisiteStep) {
    if (!step.command) {
      return;
    }
    await navigator.clipboard.writeText(step.command);
    setCopiedId(step.id);
    toast.success("Command copied", {
      description: "Run it in your terminal — we'll detect it automatically."
    });
    window.setTimeout(() => setCopiedId((current) => (current === step.id ? null : current)), 1600);
  }

  return (
    <div
      className="fixed inset-0 z-[90] flex items-center justify-center p-4"
      style={{ background: "rgba(0,0,0,0.7)" }}
      aria-modal="true"
      role="dialog"
    >
      <div className="w-full max-w-md rounded-xl border border-border bg-popover p-6 text-popover-foreground shadow-2xl">
        {ready ? (
          <div className="flex flex-col items-center text-center">
            <div className="flex size-11 items-center justify-center rounded-full border border-border bg-muted text-[color:var(--success)]">
              <Sparkles className="size-5" />
            </div>
            <h2 className="mt-4 text-base font-semibold">You&apos;re all set</h2>
            <p className="mt-1.5 text-sm text-muted-foreground">
              RELAI is configured and your project is initialized. Let&apos;s take a quick look around.
            </p>
            <Button className="mt-5 w-full" onClick={onContinue}>
              {continueLabel}
            </Button>
          </div>
        ) : (
          <>
            <h2 className="text-base font-semibold">Welcome to RELAI</h2>
            <p className="mt-1.5 text-sm leading-relaxed text-muted-foreground">
              This is a guided tour of the{" "}
              <code className="rounded bg-muted px-1 py-0.5 font-mono text-xs text-foreground">relai</code> CLI
              and platform. Before we start, complete these two steps — run each command in your terminal and
              we&apos;ll detect when it&apos;s done.
            </p>

            <div className="mt-5 flex flex-col gap-3">
              {steps.map((step, index) => {
                const isActive = index === activeIndex;
                const isLocked = activeIndex >= 0 && index > activeIndex;
                return (
                  <div
                    key={step.id}
                    className={cn(
                      "rounded-lg border p-3 transition-opacity",
                      isActive ? "border-border bg-card" : "border-border/70",
                      isLocked && "opacity-55"
                    )}
                  >
                    <div className="flex items-start gap-3">
                      <StepIndicator number={index + 1} succeeded={step.succeeded} active={isActive} locked={isLocked} />
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-medium">{step.title}</p>
                        <p className="mt-0.5 text-[13px] leading-relaxed text-muted-foreground">
                          {step.nextAction}
                        </p>

                        {isActive && step.command ? (
                          <div className="mt-3 grid gap-2.5">
                            <CommandBlock
                              command={step.command}
                              projectRoot={projectRoot}
                              copied={copiedId === step.id}
                              onCopy={() => void copy(step)}
                            />

                            <div className="flex items-center gap-2 px-0.5 text-sm text-muted-foreground">
                              <Loader2 className="size-4 shrink-0 spin" />
                              <span>Watching for the command to run…</span>
                            </div>

                            {step.id === "setup" ? (
                              <a
                                href={API_KEY_URL}
                                target="_blank"
                                rel="noreferrer"
                                className="inline-flex items-center gap-1 px-0.5 text-xs text-primary hover:underline"
                              >
                                Get your API key
                                <ExternalLink className="size-3" />
                              </a>
                            ) : null}
                          </div>
                        ) : null}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function StepIndicator({
  number,
  succeeded,
  active,
  locked
}: {
  number: number;
  succeeded: boolean;
  active: boolean;
  locked: boolean;
}) {
  return (
    <span
      className={cn(
        "flex size-6 shrink-0 items-center justify-center rounded-md border text-xs font-semibold",
        succeeded
          ? "border-transparent bg-[color:var(--success)] text-background"
          : active
            ? "border-transparent bg-primary text-primary-foreground"
            : "border-border bg-muted text-muted-foreground"
      )}
    >
      {succeeded ? <Check className="size-3.5" /> : locked ? <Lock className="size-3" /> : number}
    </span>
  );
}
