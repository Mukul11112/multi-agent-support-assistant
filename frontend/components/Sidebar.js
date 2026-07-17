import { AGENT_META } from './RoutingTrace';

export default function Sidebar({
  sessions, activeId, onSelect, onNew, onDelete, user, onSignOut, open, onClose,
}) {
  return (
    <>
      {/* Mobile scrim */}
      {open && (
        <div
          className="fixed inset-0 z-20 bg-ink/30 md:hidden"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      <aside
        className={`fixed inset-y-0 left-0 z-30 flex w-72 flex-col border-r border-line
                    bg-paper-sunk transition-transform md:static md:translate-x-0
                    ${open ? 'translate-x-0' : '-translate-x-full'}`}
      >
        <div className="border-b border-line px-4 py-4">
          <h1 className="font-display text-lg font-bold tracking-tight">TechMart</h1>
          <p className="mt-0.5 font-mono text-[10px] uppercase tracking-widest text-ink-mute">
            support console
          </p>
        </div>

        <div className="px-3 pt-3">
          <button
            onClick={onNew}
            className="w-full rounded-lg bg-ink px-3 py-2 text-sm font-medium text-paper
                       transition hover:bg-ink-soft"
          >
            New conversation
          </button>
        </div>

        <nav className="scrollbar-thin mt-3 flex-1 overflow-y-auto px-3 pb-3">
          {sessions.length === 0 ? (
            <p className="px-1 py-4 text-xs leading-relaxed text-ink-mute">
              Your conversations will appear here. Ask about a refund, a device
              that won&apos;t connect, or which laptop to buy.
            </p>
          ) : (
            <ul className="space-y-1">
              {sessions.map((s) => (
                <li key={s.session_id}>
                  <div
                    className={`group flex items-center gap-1 rounded-lg
                                ${s.session_id === activeId
                                  ? 'bg-paper-raised ring-1 ring-line-strong'
                                  : 'hover:bg-paper-raised/60'}`}
                  >
                    <button
                      onClick={() => onSelect(s.session_id)}
                      className="min-w-0 flex-1 px-3 py-2 text-left"
                    >
                      <span className="block truncate text-[13px] text-ink">
                        {s.title}
                      </span>
                      <span className="font-mono text-[10px] text-ink-mute">
                        {s.message_count} messages
                      </span>
                    </button>
                    <button
                      onClick={() => onDelete(s.session_id)}
                      aria-label={`Delete conversation: ${s.title}`}
                      className="px-2 py-2 text-ink-mute opacity-0 transition
                                 hover:text-complaint focus-visible:opacity-100
                                 group-hover:opacity-100"
                    >
                      <svg width="13" height="13" viewBox="0 0 24 24" fill="none"
                           stroke="currentColor" strokeWidth="2.2">
                        <path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6" />
                      </svg>
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </nav>

        {/* Agent legend: teaches the colour code once, so every badge in the
            transcript is readable without a tooltip. */}
        <div className="border-t border-line px-4 py-3">
          <p className="mb-2 font-mono text-[10px] uppercase tracking-widest text-ink-mute">
            specialists
          </p>
          <ul className="grid grid-cols-2 gap-y-1">
            {Object.entries(AGENT_META).map(([key, meta]) => (
              <li key={key} className="flex items-center gap-1.5 text-[11px] text-ink-soft">
                <span className={`h-1.5 w-1.5 rounded-full ${meta.dot}`} />
                {meta.label}
              </li>
            ))}
          </ul>
        </div>

        <div className="border-t border-line px-4 py-3">
          <div className="flex items-center justify-between gap-2">
            <div className="min-w-0">
              <p className="truncate text-[13px] font-medium">{user?.name}</p>
              <p className="truncate font-mono text-[10px] text-ink-mute">{user?.email}</p>
            </div>
            <button
              onClick={onSignOut}
              className="shrink-0 text-[11px] text-ink-mute underline underline-offset-2
                         hover:text-ink"
            >
              Sign out
            </button>
          </div>
        </div>
      </aside>
    </>
  );
}
