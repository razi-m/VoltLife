import React, { useState, useRef, useEffect } from 'react';
import { api } from '../lib/api';
import { Button } from '../components/ui/Button';
import './AI.css';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  intent?: string;
}

const AI: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    { role: 'assistant', content: "Hello! I'm Volt AI, your intelligent assistant for battery lifecycle management. Ask me about fleet health, deployment strategies, sustainability impact, or the Battery Aadhaar identity system." },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api.ai.suggestions().then((res) => setSuggestions(res.suggestions)).catch(() => {});
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async (text: string) => {
    if (!text.trim() || loading) return;

    const userMsg: Message = { role: 'user', content: text };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const res = await api.ai.chat(text);
      setMessages((prev) => [...prev, { role: 'assistant', content: res.response, intent: res.intent }]);
      if (res.suggestions) setSuggestions(res.suggestions);
    } catch {
      setMessages((prev) => [...prev, { role: 'assistant', content: 'Sorry, I encountered an error. Please try again.' }]);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendMessage(input);
  };

  return (
    <div className="page-content ai-page">
      <div className="page-header">
        <h1 className="page-title">Volt AI — Neural Chat Interface</h1>
        <div className="ai__status">
          <span className="ai__status-dot" />
          <span className="text-label-caps">ONLINE</span>
        </div>
      </div>

      <div className="ai__container">
        {/* Chat messages */}
        <div className="ai__messages">
          {messages.map((msg, i) => (
            <div key={i} className={`ai__message ai__message--${msg.role}`}>
              <div className="ai__message-avatar">
                {msg.role === 'assistant' ? '◆' : '●'}
              </div>
              <div className="ai__message-content">
                <div className="ai__message-label text-label-caps">
                  {msg.role === 'assistant' ? 'VOLT AI' : 'YOU'}
                  {msg.intent && <span className="ai__intent-tag">{msg.intent}</span>}
                </div>
                <div className="ai__message-text text-body-sm">{msg.content}</div>
              </div>
            </div>
          ))}

          {loading && (
            <div className="ai__message ai__message--assistant">
              <div className="ai__message-avatar">◆</div>
              <div className="ai__message-content">
                <div className="ai__typing">
                  <span className="ai__typing-dot" />
                  <span className="ai__typing-dot" />
                  <span className="ai__typing-dot" />
                </div>
              </div>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        {/* Suggestions */}
        {suggestions.length > 0 && messages.length <= 2 && (
          <div className="ai__suggestions">
            {suggestions.map((s, i) => (
              <button key={i} className="ai__suggestion-chip" onClick={() => sendMessage(s)}>
                {s}
              </button>
            ))}
          </div>
        )}

        {/* Input */}
        <form className="ai__input-bar" onSubmit={handleSubmit}>
          <input
            type="text"
            className="ai__input"
            placeholder="Ask about fleet health, deployments, impact..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={loading}
          />
          <Button type="submit" variant="solid" size="md" loading={loading} disabled={!input.trim()}>
            Send
          </Button>
        </form>
      </div>
    </div>
  );
};

export default AI;
