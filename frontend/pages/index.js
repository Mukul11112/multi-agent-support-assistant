import { useRouter } from 'next/router';
import { useCallback, useEffect, useRef, useState } from 'react';
import Message, { TypingIndicator } from '../components/Message';
import Sidebar from '../components/Sidebar';
import { api, auth } from '../services/api';

// Starters chosen to demo the architecture, not to look friendly. The first is
// single-agent, the last is the cross-domain case that fans out to two.
const STARTERS = [
  'How long does a credit card refund take?',
  "My smart plug won't connect to wifi",
  'Air 14 or Pro 16 for video editing?',
  "I paid for Premium yesterday but it's still locked",
];

export default function Home() {
  const router = useRouter();
  const [user, setUser] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [error, setError] = useState('');
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const endRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    if (!auth.token()) {
      router.replace('/login');
      return;
    }
    setUser(auth.user());
    refreshSessions();
  }, [router]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, sending]);

  const refreshSessions = useCallback(async () => {
    try {
      setSessions(await api.sessions());
    } catch {
      /* sidebar is non-critical; a failure here must not block chatting */
    }
  }, []);

  async function openSession(id) {
    setSidebarOpen(false);
    setError('');
    setSessionId(id);
    try {
      const rows = await api.history(id);
      setMessages(
        rows.map((m) => ({
          id: m.id,
          role: m.role,
          content: m.content,
          agents: m.agents,
          sources: m.sources,
          escalated: m.escalated,
          latency_ms: m.latency_ms,
        }))
      );
    } catch (err) {
      setError(err.message);
    }
  }

  function newConversation() {
    setSessionId(null);
    setMessages([]);
    setError('');
    setSidebarOpen(false);
    inputRef.current?.focus();
  }

  async function removeSession(id) {
    try {
      await api.deleteSession(id);
      if (id === sessionId) newConversation();
      refreshSessions();
    } catch (err) {
      setError(err.message);
    }
  }

  async function send(text) {
    const content = (text ?? input).trim();
    if (!content || sending) return;

    setInput('');
    setError('');
    setSending(true);
    setMessages((prev) => [...prev, { id: `local-${Date.now()}`, role: 'user', content }]);

    try {
      const res = await api.chat(content, sessionId);
      setSessionId(res.session_id);
      setMessages((prev) => [
        ...prev,
        {
          id: res.message_id,
          role: 'assistant',
          content: res.answer,
          agents: res.agents,
          routing: res.routing,
          sources: res.sources,
          escalated: res.escalated,
          latency_ms: res.latency_ms,
        },
      ]);
      refreshSessions();
    } catch (err) {
      setError(err.message);
      // Put the text back so a failed send does not lose what they typed.
      setInput(content);
      setMessages((prev) => prev.slice(0, -1));
    } finally {
      setSending(false);
    }
  }

  function onKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  }

  if (!user) return null;

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar
        sessions={sessions}
        activeId={sessionId}
        onSelect={openSession}
        onNew={newConversation}
        onDelete={removeSession}
        user={user}
        onSignOut={() => {
          auth.clear();
          router.push('/login');
        }}
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      <main className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center gap-3 border-b border-line bg-paper-raised
                           px-4 py-3 md:px-6">
          <button
            onClick={() => setSidebarOpen(true)}
            className="text-ink-soft md:hidden"
            aria-label="Open conversations"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none"
                 stroke="currentColor" strokeWidth="2">
              <path d="M3 6h18M3 12h18M3 18h18" />
            </svg>
          </button>
          <div>
            <h2 className="font-display text-[15px] font-bold tracking-tight">
              Customer support
            </h2>
            <p className="font-mono text-[10px] text-ink-mute">
              five specialists, one conversation
            </p>
          </div>
        </header>

        <div className="scrollbar-thin flex-1 overflow-y-auto px-4 py-6 md:px-6">
          <div className="mx-auto max-w-3xl space-y-5">
            {messages.length === 0 ? (
              <div className="pt-10">
                <h3 className="font-display text-2xl font-bold tracking-tight">
                  What can we help with?
                </h3>
                <p className="mt-2 max-w-md text-[15px] leading-relaxed text-ink-soft">
                  Every question is read, classified, and handed to the specialist who
                  owns it. Answers come from TechMart&apos;s own documentation, with the
                  sources shown.
                </p>
                <div className="mt-6 grid gap-2 sm:grid-cols-2">
                  {STARTERS.map((s) => (
                    <button
                      key={s}
                      onClick={() => send(s)}
                      className="rounded-xl border border-line bg-paper-raised px-4 py-3
                                 text-left text-[14px] text-ink-soft transition
                                 hover:border-line-strong hover:text-ink"
                    >
                      {s}
                    </button>
                  ))}
                </div>
                <p className="mt-4 font-mono text-[11px] text-ink-mute">
                  the last one needs two specialists at once
                </p>
              </div>
            ) : (
              messages.map((m) => <Message key={m.id} message={m} />)
            )}

            {sending && <TypingIndicator />}
            {error && (
              <p role="alert"
                 className="rounded-lg bg-complaint/8 px-3 py-2 text-[13px] text-complaint">
                {error}
              </p>
            )}
            <div ref={endRef} />
          </div>
        </div>

        <div className="border-t border-line bg-paper-raised px-4 py-3 md:px-6">
          <div className="mx-auto flex max-w-3xl items-end gap-2">
            <textarea
              ref={inputRef}
              rows={1}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={onKeyDown}
              placeholder="Ask about an order, a refund, or a device…"
              className="max-h-40 flex-1 resize-none rounded-xl border border-line bg-paper
                         px-4 py-2.5 text-[15px] placeholder:text-ink-mute
                         focus:border-ink focus:outline-none"
            />
            <button
              onClick={() => send()}
              disabled={sending || !input.trim()}
              className="rounded-xl bg-ink px-4 py-2.5 text-[14px] font-medium text-paper
                         transition hover:bg-ink-soft disabled:opacity-40"
            >
              Send
            </button>
          </div>
          <p className="mx-auto mt-2 max-w-3xl font-mono text-[10px] text-ink-mute">
            answers are generated from TechMart documentation and may be incomplete
          </p>
        </div>
      </main>
    </div>
  );
}
