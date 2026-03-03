import Swal from "sweetalert2";
import { useCart } from "../../modules/CartProvider/CartProvider";
import { useState, useEffect, useRef } from "react";
import styles from "./ChabotModule.module.scss";

export const ChatbotModule = () => {
    const [open, setOpen] = useState(false);
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const chatEndRef = useRef(null);
    const { addToCart } = useCart();

    useEffect(() => {
        chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    useEffect(() => {
        const handleChatAdd = async (event) => {
            const productId = event.detail.productId;

            try {
                const response = await fetch(
                    `http://127.0.0.1:8000/api/products/detail/${productId}/`
                );
                if (!response.ok) throw new Error("Product not found");

                const productData = await response.json();

                addToCart(productData);

                Swal.fire({
                    title: "Кошулду!",
                    text: `${productData.productDisplayName} себетке кошулду.`,
                    icon: "success",
                    toast: true,
                    position: "top-end",
                    showConfirmButton: false,
                    timer: 2000,
                });
            } catch (error) {
                console.error("Error adding from chat:", error);
            }
        };

        window.addEventListener("addToCartFromChat", handleChatAdd);

        return () => {
            window.removeEventListener("addToCartFromChat", handleChatAdd);
        };
    }, [addToCart]);
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
                        "Дүкөндүн маалымат базасына туташууда көйгөй жаралууда. Кечириңиз, азыр жооп бере албайм.",
                },
            ]);
        } catch (error) {
            console.error("Chat Error:", error);
            setMessages((prev) => [
                ...prev,
                {
                    role: "bot",
                    text: "❌ Көйгөй: сервер жумушта эмес. Кечириңиз, азыр жооп бере албайм.",
                },
            ]);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className={styles.chatbotContainer}>
            {!open && (
                <button
                    onClick={() => setOpen(true)}
                    className={styles.openButton}
                >
                    💬 Соода кылууга жардам
                </button>
            )}

            {open && (
                <div className={styles.chatWindow}>
                    <div className={styles.header}>
                        <strong>🛍️ Дүкөн кызматкери</strong>
                        <button
                            onClick={() => setOpen(false)}
                            className={styles.closeButton}
                        >
                            ✕
                        </button>
                    </div>

                    <div className={styles.messageArea}>
                        {messages.length === 0 && (
                            <p className={styles.welcomeText}>
                                Салам! Кыргыз, Орус же Англис тилинде дүкөндөгү
                                товарлар жөнүндө суроо бериңиз!
                            </p>
                        )}
                        {messages.map((m, i) => (
                            <div
                                key={i}
                                className={`${styles.messageRow} ${m.role === "user" ? styles.user : styles.bot}`}
                            >
                                {m.role === "bot" ? (
                                    <span
                                        className={styles.botBubble}
                                        dangerouslySetInnerHTML={{
                                            __html: m.text,
                                        }}
                                    />
                                ) : (
                                    <span className={styles.userBubble}>
                                        {m.text}
                                    </span>
                                )}
                            </div>
                        ))}

                        {isLoading && (
                            <p className={styles.loadingText}>Typing...</p>
                        )}
                        <div ref={chatEndRef} />
                    </div>

                    <div className={styles.inputArea}>
                        <input
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyPress={(e) =>
                                e.key === "Enter" && sendMessage()
                            }
                            placeholder="Билдирүү жазыңыз..."
                        />
                        <button
                            onClick={sendMessage}
                            className={styles.sendButton}
                        >
                            Жөнөтүү
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
};
