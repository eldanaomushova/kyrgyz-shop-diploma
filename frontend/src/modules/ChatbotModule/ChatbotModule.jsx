import { useState, useEffect, useRef } from "react";

export const ChatbotModule = () => {
    const [open, setOpen] = useState(false);
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const chatEndRef = useRef(null);

    useEffect(() => {
        chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    const sendMessage = async () => {
        if (!input.trim()) return;

        const userMessage = input;
        setInput("");
        setMessages((prev) => [...prev, { role: "user", text: userMessage }]);
        setIsLoading(true);

        try {
            const res = await fetch("http://127.0.0.1:8000/chatbot/api/chat/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ message: userMessage }),
            });

            const data = await res.json();

            setMessages((prev) => [
                ...prev,
                {
                    role: "bot",
                    text:
                        data.response ||
                        "I'm having trouble connecting to the store database.",
                },
            ]);
        } catch (error) {
            console.error("Chat Error:", error);
            setMessages((prev) => [
                ...prev,
                {
                    role: "bot",
                    text: "❌ Connection error. Please make sure the server is running.",
                },
            ]);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div
            style={{
                position: "fixed",
                bottom: "20px",
                right: "20px",
                zIndex: 1000,
            }}
        >
            {!open && (
                <button
                    onClick={() => setOpen(true)}
                    style={{
                        padding: "12px 20px",
                        borderRadius: "50px",
                        backgroundColor: "#007bff",
                        color: "white",
                        border: "none",
                        cursor: "pointer",
                        boxShadow: "0 4px 10px rgba(0,0,0,0.2)",
                    }}
                >
                    💬 Помощь по покупкам
                </button>
            )}

            {open && (
                <div
                    style={{
                        border: "1px solid #ddd",
                        padding: "15px",
                        width: "350px",
                        backgroundColor: "white",
                        borderRadius: "15px",
                        boxShadow: "0 10px 25px rgba(0,0,0,0.15)",
                        display: "flex",
                        flexDirection: "column",
                    }}
                >
                    <div
                        style={{
                            display: "flex",
                            justifyContent: "space-between",
                            marginBottom: "10px",
                            borderBottom: "1px solid #eee",
                            paddingBottom: "5px",
                        }}
                    >
                        <strong style={{ color: "#333" }}>
                            🛍️ Shop Assistant
                        </strong>
                        <button
                            onClick={() => setOpen(false)}
                            style={{
                                background: "none",
                                border: "none",
                                cursor: "pointer",
                            }}
                        >
                            ✕
                        </button>
                    </div>

                    <div
                        style={{
                            height: "300px",
                            overflowY: "auto",
                            marginBottom: "10px",
                            padding: "5px",
                        }}
                    >
                        {messages.length === 0 && (
                            <p
                                style={{
                                    color: "#888",
                                    fontSize: "0.9em",
                                    textAlign: "center",
                                }}
                            >
                                Salam! Ask me about our products in Kyrgyz,
                                Russian, or English!
                            </p>
                        )}
                        {messages.map((m, i) => (
                            <div
                                key={i}
                                style={{
                                    textAlign:
                                        m.role === "user" ? "right" : "left",
                                    margin: "10px 0",
                                }}
                            >
                                <span
                                    style={{
                                        display: "inline-block",
                                        padding: "8px 12px",
                                        borderRadius: "12px",
                                        backgroundColor:
                                            m.role === "user"
                                                ? "#007bff"
                                                : "#f1f0f0",
                                        color:
                                            m.role === "user"
                                                ? "white"
                                                : "#333",
                                        fontSize: "0.95em",
                                        maxWidth: "80%",
                                    }}
                                >
                                    {m.text}
                                </span>
                            </div>
                        ))}
                        {isLoading && (
                            <p style={{ fontSize: "0.8em", color: "#888" }}>
                                Typing...
                            </p>
                        )}
                        <div ref={chatEndRef} />
                    </div>

                    <div style={{ display: "flex", gap: "5px" }}>
                        <input
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyPress={(e) =>
                                e.key === "Enter" && sendMessage()
                            }
                            placeholder="Write a message..."
                            style={{
                                flex: 1,
                                padding: "8px",
                                borderRadius: "5px",
                                border: "1px solid #ccc",
                            }}
                        />
                        <button
                            onClick={sendMessage}
                            style={{
                                padding: "8px 15px",
                                backgroundColor: "#28a745",
                                color: "white",
                                border: "none",
                                borderRadius: "5px",
                                cursor: "pointer",
                            }}
                        >
                            Send
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
};
