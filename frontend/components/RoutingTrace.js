// The signature element of this interface.
//
// A support chatbot normally hides its plumbing. This one shows it: every
// answer is stamped with the routing decision the orchestrator made, and when
// two specialists collaborate the trace visibly forks. The architecture is the
// point of the project, so the interface makes it legible instead of burying it
// behind a generic bubble.

export const AGENT_META = {
  billing: { label: 'Billing', dot: 'bg-billing', text: 'text-billing', ring: 'ring-billing/25' },
  technical: { label: 'Technical', dot: 'bg-technical', text: 'text-technical', ring: 'ring-technical/25' },
  product: { label: 'Product', dot: 'bg-product', text: 'text-product', ring: 'ring-product/25' },
  complaint: { label: 'Complaints', dot: 'bg-complaint', text: 'text-complaint', ring: 'ring-complaint/25' },
  faq: { label: 'General', dot: 'bg-faq', text: 'text-faq', ring: 'ring-faq/25' },
};

export function AgentBadge({ name }) {
  const meta = AGENT_META[name] || AGENT_META.faq;
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full bg-paper-raised px-2.5 py-1
                  text-[11px] font-medium ring-1 ${meta.ring} ${meta.text}`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${meta.dot}`} aria-hidden="true" />
      {meta.label}
    </span>
  );
}

export default function RoutingTrace({ agents = [], routing, escalated }) {
  if (!agents.length) return null;
  const collaborated = agents.length > 1;

  return (
    <div className="mb-2 flex flex-wrap items-center gap-x-2 gap-y-1.5">
      <span className="font-mono text-[10px] uppercase tracking-widest text-ink-mute">
        routed
      </span>

      <span className="text-line-strong" aria-hidden="true">→</span>

      {agents.map((a, i) => (
        <span key={a} className="flex items-center gap-2">
          {i > 0 && (
            // The fork: two specialists answered and their replies were merged.
            <span
              className="font-mono text-[10px] text-ink-mute"
              title="Two specialists answered and their replies were merged into one"
            >
              +
            </span>
          )}
          <AgentBadge name={a} />
        </span>
      ))}

      {collaborated && (
        <span className="font-mono text-[10px] text-ink-mute">merged</span>
      )}

      {routing?.confidence != null && (
        <span
          className="font-mono text-[10px] text-ink-mute"
          title={routing.reasoning || 'Router confidence'}
        >
          conf {routing.confidence.toFixed(2)}
          {routing.method === 'fallback' && ' (keyword fallback)'}
        </span>
      )}

      {escalated && (
        <span className="rounded-full bg-complaint/10 px-2 py-0.5 font-mono text-[10px]
                         font-medium text-complaint">
          escalated to human
        </span>
      )}
    </div>
  );
}
