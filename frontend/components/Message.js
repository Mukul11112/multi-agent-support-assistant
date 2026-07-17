import { useState } from 'react';
import RoutingTrace from './RoutingTrace';

function SourceChips({ sources = [] }) {
  const [open, setOpen] = useState(false);
  if (!sources.length) return null;

  // Sources are the evidence that the answer came from the knowledge base and
  // not from the model's imagination. Shown by default, collapsed if there are
  // many, with the similarity score in mono because it is data, not prose.
  const shown = open ? sources : sources.slice(0, 3);

  return (
    <div className="mt-3 flex flex-wrap items-center gap-1.5 border-t border-line pt-2.5">
      <span className="font-mono text-[10px] uppercase tracking-widest text-ink-mute">
        sources
      </span>
      {shown.map((s, i) => (
        <span
          key={`${s.source}-${s.page}-${i}`}
          className="inline-flex items-center gap-1.5 rounded border border-line bg-paper
                     px-2 py-0.5 font-mono text-[10px] text-ink-soft"
          title={`Similarity ${s.score} — higher means a closer match to your question`}
        >
          {s.source}
          <span className="text-ink-mute">p{s.page}</span>
          <span className="text-ink-mute">{s.score?.toFixed(2)}</span>
        </span>
      ))}
      {sources.length > 3 && (
        <button
          onClick={() => setOpen(!open)}
          className="font-mono text-[10px] text-ink-mute underline underline-offset-2
                     hover:text-ink"
        >
          {open ? 'show fewer' : `+${sources.length - 3} more`}
        </button>
      )}
    </div>
  );
}

export function TypingIndicator({ agents = [] }) {
  return (
    <div className="animate-rise">
      <div className="mb-2 font-mono text-[10px] uppercase tracking-widest text-ink-mute">
        {agents.length > 1 ? 'two specialists are answering' : 'routing your question'}
      </div>
      <div className="inline-flex items-center gap-1.5 rounded-2xl rounded-tl-sm border
                      border-line bg-paper-raised px-4 py-3">
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            className="h-1.5 w-1.5 animate-blink rounded-full bg-ink-mute"
            style={{ animationDelay: `${i * 160}ms` }}
          />
        ))}
      </div>
    </div>
  );
}

export default function Message({ message }) {
  const isUser = message.role === 'user';

  if (isUser) {
    return (
      <div className="flex animate-rise justify-end">
        <div className="max-w-[78%] rounded-2xl rounded-br-sm bg-ink px-4 py-2.5
                        text-[15px] leading-relaxed text-paper">
          {message.content}
        </div>
      </div>
    );
  }

  return (
    <div className="animate-rise">
      <RoutingTrace
        agents={message.agents}
        routing={message.routing}
        escalated={message.escalated}
      />
      <div className="max-w-[88%] rounded-2xl rounded-tl-sm border border-line
                      bg-paper-raised px-4 py-3">
        <div className="whitespace-pre-wrap text-[15px] leading-relaxed text-ink">
          {message.content}
        </div>
        <SourceChips sources={message.sources} />
        {message.latency_ms > 0 && (
          <div className="mt-2 font-mono text-[10px] text-ink-mute">
            {(message.latency_ms / 1000).toFixed(1)}s
          </div>
        )}
      </div>
    </div>
  );
}
