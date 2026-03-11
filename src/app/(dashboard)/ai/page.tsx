"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Bot, User, Loader2 } from "lucide-react";

interface Message {
  role: "user" | "assistant";
  content: string;
  metadata?: {
    sources?: string[];
    periode?: string;
  };
}

const defaultSuggestions = [
  "Komoditas apa yang paling naik minggu ini?",
  "Wilayah mana yang perlu diwaspadai?",
  "Bagaimana tren harga beras bulan ini?",
  "Jelaskan alert yang sedang aktif",
];

export default function AIPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [suggestions, setSuggestions] = useState(defaultSuggestions);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSend(text?: string) {
    const message = text || input;
    if (!message.trim() || isLoading) return;

    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: message }]);
    setIsLoading(true);

    try {
      const res = await fetch("/api/ai/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message }),
      });

      const data = await res.json();

      if (res.ok) {
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: data.message,
            metadata: data.metadata,
          },
        ]);
        if (data.suggestedQuestions?.length) {
          setSuggestions(data.suggestedQuestions);
        }
      } else {
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content:
              data.error ||
              "Maaf, terjadi kesalahan. Silakan coba lagi.",
          },
        ]);
      }
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            "Maaf, tidak dapat terhubung ke server. Pastikan server berjalan dan coba lagi.",
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      <div className="mb-4">
        <h2 className="text-lg font-bold text-gray-900">AI Assistant</h2>
        <p className="text-sm text-gray-500 mt-0.5">
          Tanya apa saja tentang inflasi pangan Indonesia
        </p>
      </div>

      <div className="flex-1 bg-white rounded-xl border overflow-hidden flex flex-col">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <Bot className="h-12 w-12 text-gray-300 mb-3" />
              <p className="text-sm text-gray-500 mb-1">
                Halo! Saya asisten analisis inflasi pangan.
              </p>
              <p className="text-xs text-gray-400 mb-5">
                Saya dapat menjawab pertanyaan berdasarkan data harga komoditas, inflasi, dan alert yang tersedia.
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-w-lg">
                {suggestions.map((q) => (
                  <button
                    key={q}
                    onClick={() => handleSend(q)}
                    className="text-left text-sm px-3 py-2.5 border rounded-lg text-gray-600 hover:bg-blue-50 hover:border-blue-300 hover:text-blue-700 transition-colors"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex gap-3 ${msg.role === "user" ? "justify-end" : ""}`}
            >
              {msg.role === "assistant" && (
                <div className="h-7 w-7 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <Bot className="h-4 w-4 text-blue-600" />
                </div>
              )}
              <div
                className={`max-w-[80%] rounded-xl px-4 py-3 ${
                  msg.role === "user"
                    ? "bg-blue-600 text-white"
                    : "bg-gray-50 text-gray-800"
                }`}
              >
                <p className="text-sm whitespace-pre-line leading-relaxed">
                  {msg.content}
                </p>
                {msg.metadata?.sources?.length ? (
                  <p className="text-xs mt-2 opacity-60">
                    Sumber: {msg.metadata.sources.join(", ")} | Periode:{" "}
                    {msg.metadata.periode}
                  </p>
                ) : null}
              </div>
              {msg.role === "user" && (
                <div className="h-7 w-7 rounded-full bg-gray-200 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <User className="h-4 w-4 text-gray-600" />
                </div>
              )}
            </div>
          ))}

          {isLoading && (
            <div className="flex gap-3">
              <div className="h-7 w-7 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
                <Bot className="h-4 w-4 text-blue-600" />
              </div>
              <div className="bg-gray-50 rounded-xl px-4 py-3">
                <Loader2 className="h-4 w-4 text-gray-400 animate-spin" />
              </div>
            </div>
          )}

          <div ref={chatEndRef} />
        </div>

        {/* Suggested follow-ups after conversation started */}
        {messages.length > 0 && !isLoading && (
          <div className="px-4 py-2 border-t bg-gray-50">
            <div className="flex gap-2 overflow-x-auto">
              {suggestions.slice(0, 3).map((q) => (
                <button
                  key={q}
                  onClick={() => handleSend(q)}
                  className="text-xs px-3 py-1.5 border rounded-full text-gray-500 hover:text-blue-600 hover:border-blue-300 bg-white whitespace-nowrap transition-colors"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Input */}
        <div className="border-t p-3">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSend();
            }}
            className="flex gap-2"
          >
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ketik pertanyaan tentang inflasi pangan..."
              className="flex-1 text-sm border rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={isLoading}
            />
            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              className="px-4 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <Send className="h-4 w-4" />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
