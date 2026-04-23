import React, { useEffect, useRef, useState } from "react";
import axios from "axios";
import { motion, AnimatePresence } from "framer-motion";
import { Send, Terminal, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { useI18n } from "@/i18n/I18nProvider";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function ProphetChat() {
  const { t, lang } = useI18n();
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    // reset convo when language changes — keeps persona clean
    setMessages([]);
    setSessionId(null);
  }, [lang]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, sending]);

  const send = async (textOverride) => {
    const text = (textOverride ?? input).trim();
    if (!text || sending) return;
    setInput("");
    const userMsgId = `u-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
    setMessages((m) => [...m, { id: userMsgId, role: "user", content: text }]);
    setSending(true);
    try {
      const res = await axios.post(`${API}/chat`, {
        session_id: sessionId,
        message: text,
        lang,
      });
      if (!sessionId) setSessionId(res.data.session_id);
      setMessages((m) => [
        ...m,
        {
          id: `p-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
          role: "prophet",
          content: res.data.reply,
        },
      ]);
    } catch (e) {
      toast.error(t("chat.errorToast"));
      setMessages((m) => [
        ...m,
        {
          id: `e-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
          role: "prophet",
          content:
            lang === "fr"
              ? "[Signal perdu. Le Deep State rétablit la ligne…]"
              : "[Signal lost. The Deep State is restoring the line…]",
          error: true,
        },
      ]);
    } finally {
      setSending(false);
    }
  };

  const onKey = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  const examples = t("chat.exampleQuestions") || [];

  return (
    <section
      id="chat"
      data-testid="prophet-chat"
      className="py-14 sm:py-18 lg:py-24 border-t border-border"
    >
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center gap-2 mb-2">
          <span className="font-mono text-[11px] uppercase tracking-[0.25em] text-muted-foreground">
            {t("chat.kicker")}
          </span>
        </div>
        <h2 className="font-display text-3xl md:text-4xl lg:text-5xl font-semibold leading-tight text-foreground">
          {t("chat.title")}
        </h2>
        <p className="mt-3 text-foreground/80 max-w-2xl">{t("chat.subtitle")}</p>

        <div className="mt-8 grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Rules column */}
          <div className="lg:col-span-4">
            <div className="rounded-xl border border-border p-5 bg-card">
              <div className="flex items-center gap-2 text-foreground/90 mb-3">
                <Terminal size={16} />
                <span className="font-display font-semibold">
                  {lang === "fr" ? "Règles du Prophète" : "Prophet Rules"}
                </span>
              </div>
              <ul className="space-y-2 text-sm text-foreground/80">
                {(t("chat.rules") || []).map((r, i) => (
                  <li key={`rule-${i}-${(r || "").slice(0, 12)}`} className="flex gap-2">
                    <span className="text-[--terminal-green-dim] font-mono">
                      &gt;
                    </span>
                    <span>{r}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="mt-5">
              <div className="text-[11px] font-mono uppercase tracking-widest text-muted-foreground mb-2 flex items-center gap-1">
                <Sparkles size={12} />
                {lang === "fr" ? "Essayez ces questions" : "Try these questions"}
              </div>
              <div className="flex flex-wrap gap-2">
                {examples.map((q, i) => (
                  <button
                    key={`example-${i}-${(q || "").slice(0, 12)}`}
                    onClick={() => send(q)}
                    className="px-3 py-1.5 rounded-full text-xs border border-border bg-background hover:bg-secondary transition-colors text-foreground/80"
                    data-testid={`chat-example-${i}`}
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Terminal */}
          <div className="lg:col-span-8">
            <div className="terminal-panel rounded-xl p-0 scanlines">
              <div className="flex items-center justify-between px-4 py-2.5 border-b border-[#1f2937] bg-[#0b1117]">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-[#E11D48]" />
                  <span className="w-2.5 h-2.5 rounded-full bg-[#F59E0B]" />
                  <span className="w-2.5 h-2.5 rounded-full bg-[#33FF33]" />
                  <span className="ml-3 font-mono text-[11px] uppercase tracking-widest text-zinc-400">
                    deepotus@deepstate ~ prophecy_channel
                  </span>
                </div>
                <Badge
                  variant="outline"
                  className="bg-transparent border-zinc-700 text-[#33ff33] font-mono text-[10px] uppercase tracking-widest"
                >
                  {lang === "fr" ? "LIGNE OUVERTE" : "LINE OPEN"}
                </Badge>
              </div>

              <div
                ref={scrollRef}
                data-testid="prophet-chat-messages"
                className="p-5 h-[360px] overflow-y-auto font-mono text-[13.5px] leading-relaxed"
                aria-live="polite"
              >
                {messages.length === 0 && !sending && (
                  <div className="text-zinc-500">
                    <span className="prompt">&gt;</span> {t("chat.empty")}
                  </div>
                )}
                <AnimatePresence initial={false}>
                  {messages.map((m, i) => (
                    <motion.div
                      key={m.id || `msg-${i}`}
                      initial={{ opacity: 0, y: 4 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.25 }}
                      className="mb-3"
                    >
                      {m.role === "user" ? (
                        <div>
                          <span className="text-[#F59E0B]">you@deepstate</span>
                          <span className="text-zinc-500"> :~$ </span>
                          <span className="text-zinc-200">{m.content}</span>
                        </div>
                      ) : (
                        <div>
                          <span className="text-[#33ff33]">
                            DEEPOTUS@prophet
                          </span>
                          <span className="text-zinc-500"> :~&gt; </span>
                          <span
                            className={
                              m.error ? "text-[#E11D48]" : "text-zinc-100"
                            }
                          >
                            {m.content}
                          </span>
                        </div>
                      )}
                    </motion.div>
                  ))}
                </AnimatePresence>
                {sending && (
                  <div className="mb-3">
                    <span className="text-[#33ff33]">DEEPOTUS@prophet</span>
                    <span className="text-zinc-500"> :~&gt; </span>
                    <span className="text-zinc-300 caret">
                      {t("chat.sending")}
                    </span>
                  </div>
                )}
              </div>

              <div className="border-t border-[#1f2937] p-3 bg-[#0b1117]">
                <div className="flex items-start gap-2">
                  <Textarea
                    data-testid="prophet-chat-input"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={onKey}
                    placeholder={t("chat.placeholder")}
                    className="min-h-[48px] max-h-36 resize-none bg-[#0e141b] border-[#1f2937] text-zinc-100 font-mono text-[13.5px] focus-visible:ring-[var(--ring)]"
                  />
                  <Button
                    size="lg"
                    onClick={() => send()}
                    disabled={sending || !input.trim()}
                    data-testid="prophet-chat-send-button"
                    className="rounded-[var(--btn-radius)] btn-press"
                  >
                    <Send size={16} className="mr-1" />
                    {sending ? t("chat.sending") : t("chat.send")}
                  </Button>
                </div>
                <div className="mt-2 text-[11px] font-mono text-zinc-500">
                  {t("chat.hint")}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
