"use client";

import { Check, Copy, Terminal } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";

export function CommandBlock({
  command,
  projectRoot,
  copied,
  onCopy
}: {
  command: string;
  projectRoot?: string;
  copied: boolean;
  onCopy: () => void;
}) {
  return (
    <div className="overflow-hidden rounded-lg border border-border bg-[var(--background)]">
      <div className="border-b border-border px-3 py-2">
        <p className="text-[11px] text-muted-foreground">Run this command from this folder:</p>
        <p className="mt-1 text-xs font-medium break-all text-foreground">
          {projectRoot ?? "your project directory"}
        </p>
      </div>
      <div className="flex items-center gap-2 py-2 pr-2 pl-3">
        <Terminal className="size-3.5 shrink-0 text-muted-foreground" />
        <code className="min-w-0 flex-1 overflow-x-auto whitespace-pre font-mono text-xs text-foreground">
          {command}
        </code>
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              size="icon"
              variant="ghost"
              className="size-7 shrink-0 text-muted-foreground hover:text-foreground"
              onClick={onCopy}
              aria-label="Copy command"
            >
              {copied ? <Check className="text-[color:var(--success)]" /> : <Copy />}
            </Button>
          </TooltipTrigger>
          <TooltipContent>Copy command</TooltipContent>
        </Tooltip>
      </div>
    </div>
  );
}
