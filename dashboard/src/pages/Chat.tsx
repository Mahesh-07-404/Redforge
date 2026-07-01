import React, { useEffect, useRef, useState } from 'react';
import { useSession } from '../contexts/SessionContext';
import { useSettings } from '../contexts/SettingsContext';
import { RedForgeAPI } from '../services/api';
import { Send, Terminal, AlertTriangle, CheckCircle, ArrowRight } from 'lucide-react';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  isStreaming?: boolean;
}

export const Chat: React.FC = () => {
  const { activeSession } = useSession();
  const { settings } = useSettings();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const wsRef = useRef<WebSocket | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Load chat history
  useEffect(() => {
    if (!activeSession) {
      setMessages([
        {
          id: 'welcome',
          role: 'system',
          content: 'No active session. Please select or create a session in the header dropdown to start chatting with the AI assistant.',
          timestamp: new Date().toISOString(),
        },
      ]);
      return;
    }

    const loadHistory = async () => {
      setError(null);
      try {
        const history = await RedForgeAPI.getConversationHistory(
          settings.apiUrl,
          activeSession.id,
          settings.apiKey,
          settings.authToken
        );
        if (history && history.messages) {
          const formatted = history.messages.map((m: any, idx: number) => ({
            id: `hist-${idx}`,
            role: m.role,
            content: m.content,
            timestamp: m.timestamp || new Date().toISOString(),
          }));
          setMessages(formatted.length > 0 ? formatted : getDefaultMessages());
        } else {
          setMessages(getDefaultMessages());
        }
      } catch (err: any) {
        setError(err.message || 'Failed to load conversation history');
        setMessages(getDefaultMessages());
      }
    };

    loadHistory();
  }, [activeSession, settings.apiUrl, settings.apiKey, settings.authToken]);

  // Scroll to bottom on new message
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  const getDefaultMessages = (): ChatMessage[] => [
    {
      id: 'welcome-ast',
      role: 'assistant',
      content: `Hello! I am your RedForge Cybersecurity Copilot. I can help you orchestrate security tools, run workflows, perform reconnaissance, and analyze findings. Try asking me to:
      
* "scan target.com for open ports"
* "run passive reconnaissance workflow"
* "generate a security report for the active session"`,
      timestamp: new Date().toISOString(),
    },
  ];

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputMessage.trim() || !activeSession || isStreaming) return;

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: inputMessage,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputMessage('');
    setIsStreaming(true);
    setError(null);

    // Setup WebSocket for streaming chat
    try {
      const socket = RedForgeAPI.createWebSocket(settings.apiUrl, '/ws/chat', settings.authToken);
      wsRef.current = socket;

      let assistantMsgId = `ast-${Date.now()}`;
      let accumulatedResponse = '';

      socket.onopen = () => {
        // Send chat parameters
        socket.send(
          JSON.stringify({
            session_id: activeSession.id,
            message: userMsg.content,
          })
        );
      };

      socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.event_type === 'chat_start') {
            // Initialize empty response
            setMessages((prev) => [
              ...prev,
              {
                id: assistantMsgId,
                role: 'assistant',
                content: '',
                timestamp: new Date().toISOString(),
                isStreaming: true,
              },
            ]);
          } else if (data.event_type === 'token') {
            accumulatedResponse += data.token;
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMsgId
                  ? { ...msg, content: accumulatedResponse }
                  : msg
              )
            );
          } else if (data.event_type === 'done') {
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMsgId ? { ...msg, isStreaming: false } : msg
              )
            );
            socket.close();
            setIsStreaming(false);
          } else if (data.event_type === 'error') {
            setError(data.message || 'Chat stream encountered an error');
            setMessages((prev) => prev.filter((msg) => msg.id !== assistantMsgId));
            socket.close();
            setIsStreaming(false);
          }
        } catch (err) {
          console.error('Failed to parse WebSocket stream token:', err);
        }
      };

      socket.onerror = (err) => {
        console.error('WebSocket error:', err);
        setError('Connection to chat stream failed.');
        setIsStreaming(false);
      };

      socket.onclose = () => {
        setIsStreaming(false);
      };
    } catch (err: any) {
      setError(err.message || 'Failed to open chat stream');
      setIsStreaming(false);
    }
  };

  // Simple clean markdown custom renderer
  const renderMessageContent = (content: string) => {
    return (
      <div className="space-y-2 leading-relaxed text-sm">
        {content.split('\n\n').map((para, pIdx) => {
          // List Items
          if (para.startsWith('* ') || para.startsWith('- ')) {
            return (
              <ul key={pIdx} className="list-disc pl-5 space-y-1">
                {para.split('\n').map((item, itemIdx) => (
                  <li key={itemIdx}>{item.substring(2)}</li>
                ))}
              </ul>
            );
          }
          
          // Bullet list numbered
          if (/^\d+\./.test(para.trim())) {
            return (
              <ol key={pIdx} className="list-decimal pl-5 space-y-1">
                {para.split('\n').map((item, itemIdx) => (
                  <li key={itemIdx}>{item.replace(/^\d+\.\s*/, '')}</li>
                ))}
              </ol>
            );
          }

          // Code blocks or terminal commands
          if (para.startsWith('`') || para.includes('`')) {
            const parts = para.split('`');
            return (
              <p key={pIdx}>
                {parts.map((part, idx) =>
                  idx % 2 === 1 ? (
                    <code key={idx} className="bg-muted px-1.5 py-0.5 rounded font-mono text-foreground border border-border">
                      {part}
                    </code>
                  ) : (
                    part
                  )
                )}
              </p>
            );
          }

          return <p key={pIdx}>{para}</p>;
        })}
      </div>
    );
  };

  return (
    <div className="h-full flex flex-col border border-border bg-card/10 backdrop-blur-md rounded-lg overflow-hidden animate-in fade-in duration-300">
      {/* Header */}
      <div className="px-6 py-4 border-b border-border bg-card/30 flex items-center justify-between">
        <h2 className="text-sm font-bold tracking-widest text-foreground uppercase flex items-center gap-2 m-0">
          <Terminal className="h-4 w-4 text-primary" /> Operations Assistant Console
        </h2>
        {activeSession && (
          <span className="text-[10px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2 py-0.5 rounded uppercase font-semibold">
            Context: {activeSession.name}
          </span>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex flex-col max-w-[80%] ${
              msg.role === 'user'
                ? 'ml-auto items-end'
                : msg.role === 'system'
                ? 'mx-auto w-full items-center text-center'
                : 'items-start'
            }`}
          >
            {/* Sender tag */}
            <span className="text-[10px] text-muted-foreground uppercase tracking-wider mb-1 px-1">
              {msg.role === 'user' ? 'Operator' : msg.role === 'system' ? 'System alert' : 'Assistant Copilot'}
            </span>

            {/* Bubble */}
            <div
              className={`p-4 rounded-lg border text-sm ${
                msg.role === 'user'
                  ? 'bg-primary text-primary-foreground border-primary/20 shadow-[0_0_10px_rgba(170,59,255,0.15)]'
                  : msg.role === 'system'
                  ? 'bg-amber-950/20 border-amber-800/40 text-amber-300'
                  : 'bg-card border-border text-foreground'
              }`}
            >
              {msg.role === 'system' ? (
                <div className="flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4 shrink-0 text-amber-400" />
                  <span>{msg.content}</span>
                </div>
              ) : (
                renderMessageContent(msg.content)
              )}
            </div>

            {/* Time */}
            <span className="text-[9px] text-muted-foreground/60 mt-1 px-1">
              {new Date(msg.timestamp).toLocaleTimeString()}
            </span>
          </div>
        ))}

        {isStreaming && (
          <div className="flex flex-col items-start max-w-[80%] animate-pulse">
            <span className="text-[10px] text-muted-foreground uppercase tracking-wider mb-1 px-1">Assistant Copilot</span>
            <div className="p-4 rounded-lg border border-border bg-card text-muted-foreground text-xs flex items-center gap-2">
              <span className="h-1.5 w-1.5 bg-primary rounded-full animate-bounce" />
              <span className="h-1.5 w-1.5 bg-primary rounded-full animate-bounce [animation-delay:0.2s]" />
              <span className="h-1.5 w-1.5 bg-primary rounded-full animate-bounce [animation-delay:0.4s]" />
              <span>Receiving stream tokens...</span>
            </div>
          </div>
        )}

        {error && (
          <div className="p-4 rounded border border-rose-800/40 bg-rose-950/20 text-rose-300 text-xs flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 shrink-0 text-rose-500" />
            <span>Error: {error}</span>
          </div>
        )}

        <div ref={scrollRef} />
      </div>

      {/* Input panel */}
      <div className="p-4 border-t border-border bg-card/30">
        <form onSubmit={handleSendMessage} className="flex gap-2">
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            placeholder={
              activeSession
                ? `Type scan target, workflow launch, or query session details...`
                : 'Please select a session first to chat.'
            }
            disabled={!activeSession || isStreaming}
            className="flex-1 px-4 py-2.5 rounded border border-border bg-muted/40 focus:outline-none focus:border-primary text-sm placeholder:text-muted-foreground disabled:opacity-50 text-foreground"
          />
          <button
            type="submit"
            disabled={!inputMessage.trim() || !activeSession || isStreaming}
            className="px-5 py-2.5 bg-primary hover:bg-primary/95 text-primary-foreground font-semibold text-sm rounded shadow-[0_0_15px_rgba(170,59,255,0.25)] flex items-center gap-2 transition disabled:opacity-50 shrink-0"
          >
            <Send className="h-4 w-4" /> Send
          </button>
        </form>
      </div>
    </div>
  );
};
