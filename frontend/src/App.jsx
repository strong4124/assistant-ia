import { useState, useRef, useEffect } from "react";

const API_BASE = "http://localhost:8000/api/v1";

function generateId() {
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === "x" ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

export default function App() {
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  // Cree une session au premier chargement du widget
  useEffect(() => {
    fetch(`${API_BASE}/sessions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        channel: "web",
        external_user_id: `web-${generateId()}`,
      }),
    })
      .then((r) => r.json())
      .then((data) => setSessionId(data.id))
      .catch(() => {
        setMessages([
          {
            role: "system",
            content: "Impossible de contacter l'assistant. Reessayez plus tard.",
          },
        ]);
      });
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function sendMessage() {
    const question = input.trim();
    if (!question || !sessionId || loading) return;

    setMessages((prev) => [...prev, { role: "user", content: question }]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE}/messages`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, content: question }),
      });
      const data = await res.json();
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          id: data.id,
          content: data.refused
            ? "Je n'ai pas trouve cette information dans ma base de connaissances. Souhaitez-vous etre mis en relation avec un agent ?"
            : data.content,
          sources: data.sources,
          refused: data.refused,
        },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "system", content: "Erreur reseau, reessayez." },
      ]);
    } finally {
      setLoading(false);
    }
  }

  async function sendFeedback(messageId, isPositive) {
    await fetch(`${API_BASE}/feedback`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message_id: messageId, is_positive: isPositive }),
    });
    setMessages((prev) =>
      prev.map((m) => (m.id === messageId ? { ...m, feedbackGiven: isPositive } : m))
    );
  }

  return (
    <div style={styles.container}>
      <div style={styles.header}>Assistant Teranga Telecom</div>

      <div style={styles.messages}>
        {messages.map((m, i) => (
          <div
            key={i}
            style={{
              ...styles.bubble,
              ...(m.role === "user" ? styles.bubbleUser : styles.bubbleAssistant),
            }}
          >
            <div>{m.content}</div>

            {m.sources?.length > 0 && (
              <div style={styles.sources}>
                Source{m.sources.length > 1 ? "s" : ""} : {m.sources.join(", ")}
              </div>
            )}

            {m.role === "assistant" && m.id && (
              <div style={styles.feedback}>
                <button
                  onClick={() => sendFeedback(m.id, true)}
                  style={{
                    ...styles.feedbackBtn,
                    opacity: m.feedbackGiven === false ? 0.3 : 1,
                  }}
                  disabled={m.feedbackGiven !== undefined}
                >
                  👍
                </button>
                <button
                  onClick={() => sendFeedback(m.id, false)}
                  style={{
                    ...styles.feedbackBtn,
                    opacity: m.feedbackGiven === true ? 0.3 : 1,
                  }}
                  disabled={m.feedbackGiven !== undefined}
                >
                  👎
                </button>
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div style={{ ...styles.bubble, ...styles.bubbleAssistant }}>
            L'assistant reflechit...
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div style={styles.inputRow}>
        <input
          style={styles.input}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && sendMessage()}
          placeholder={sessionId ? "Posez votre question..." : "Connexion..."}
          disabled={!sessionId}
        />
        <button style={styles.sendBtn} onClick={sendMessage} disabled={!sessionId || loading}>
          Envoyer
        </button>
      </div>
    </div>
  );
}

const styles = {
  container: {
    maxWidth: 420,
    height: "80vh",
    margin: "40px auto",
    border: "1px solid #ddd",
    borderRadius: 12,
    display: "flex",
    flexDirection: "column",
    fontFamily: "system-ui, sans-serif",
    overflow: "hidden",
    boxShadow: "0 2px 12px rgba(0,0,0,0.08)",
  },
  header: {
    background: "#1a3c6e",
    color: "white",
    padding: "14px 16px",
    fontWeight: 600,
  },
  messages: {
    flex: 1,
    overflowY: "auto",
    padding: 16,
    display: "flex",
    flexDirection: "column",
    gap: 10,
    background: "#f7f8fa",
  },
  bubble: {
    maxWidth: "80%",
    padding: "10px 14px",
    borderRadius: 14,
    fontSize: 14,
    lineHeight: 1.4,
  },
  bubbleUser: {
    alignSelf: "flex-end",
    background: "#1a3c6e",
    color: "white",
    borderBottomRightRadius: 4,
  },
  bubbleAssistant: {
    alignSelf: "flex-start",
    background: "white",
    border: "1px solid #e2e2e2",
    borderBottomLeftRadius: 4,
  },
  sources: {
    marginTop: 6,
    fontSize: 11,
    color: "#666",
    fontStyle: "italic",
  },
  feedback: {
    marginTop: 6,
    display: "flex",
    gap: 6,
  },
  feedbackBtn: {
    border: "none",
    background: "none",
    cursor: "pointer",
    fontSize: 14,
  },
  inputRow: {
    display: "flex",
    padding: 12,
    borderTop: "1px solid #eee",
    gap: 8,
  },
  input: {
    flex: 1,
    padding: "10px 12px",
    borderRadius: 8,
    border: "1px solid #ccc",
    fontSize: 14,
  },
  sendBtn: {
    background: "#1a3c6e",
    color: "white",
    border: "none",
    borderRadius: 8,
    padding: "10px 16px",
    cursor: "pointer",
  },
};
