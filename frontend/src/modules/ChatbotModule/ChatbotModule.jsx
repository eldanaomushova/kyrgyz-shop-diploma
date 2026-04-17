import Swal from "sweetalert2";
import { useCart } from "../../modules/CartProvider/CartProvider";
import { useState, useEffect, useRef } from "react";
import styles from "./ChabotModule.module.scss";
import { requester } from "../../utils/Requester/Requester";

export const ChatbotModule = () => {
    const [open, setOpen] = useState(false);
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [isListening, setIsListening] = useState(false);

    const chatEndRef = useRef(null);
    const { addToCart } = useCart();

    useEffect(() => {
        chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    useEffect(() => {
        const handleChatAdd = async (event) => {
            const productId = event.detail.productId;
            try {
                const response = await requester.get(
                    `/products/detail/${productId}/`
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
        return () =>
            window.removeEventListener("addToCartFromChat", handleChatAdd);
    }, [addToCart]);

    const playKyrgyzVoice = (text) => {
        window.speechSynthesis.cancel();

        let cleanText = text.replace(/<\/?[^>]+(>|$)/g, "");
        cleanText = cleanText.replace(/ID:?\s?\d+/gi, "");
        cleanText = cleanText.replace(
            /([\u2700-\u27BF]|[\uE000-\uF8FF]|\uD83C[\uDC00-\uDFFF]|\uD83D[\uDC00-\uDFFF]|[\u2011-\u26FF]|\uD83E[\uDD10-\uDDFF])/g,
            ""
        );
        cleanText = cleanText.replace(/[#*_]/g, "");

        const kgNumbers = {
            0: "нөл",
            1: "бир",
            2: "эки",
            3: "үч",
            4: "төрт",
            5: "беш",
            6: "алты",
            7: "жети",
            8: "сегиз",
            9: "тогуз",
            10: "он",
            20: "жыйырма",
            30: "отуз",
            40: "кырк",
            50: "элүү",
            60: "алтымыш",
            70: "жетимиш",
            80: "сексен",
            90: "токсон",
            100: "жуз",
            1000: "миң",
        };

        const toKyrgyzNumber = (num) => {
            let n = parseInt(num);
            if (isNaN(n)) return "";
            if (n === 0) return kgNumbers[0];

            let parts = [];

            if (n >= 1000) {
                let thousands = Math.floor(n / 1000);
                if (thousands > 1) parts.push(toKyrgyzNumber(thousands));
                parts.push(kgNumbers[1000]);
                n %= 1000;
            }

            if (n >= 100) {
                let hundreds = Math.floor(n / 100);
                if (hundreds > 1) parts.push(toKyrgyzNumber(hundreds));
                parts.push(kgNumbers[100]);
                n %= 100;
            }

            if (n >= 10) {
                let tens = Math.floor(n / 10) * 10;
                parts.push(kgNumbers[tens]);
                n %= 10;
            }

            if (n > 0) {
                parts.push(kgNumbers[n]);
            }

            return parts.join(" ");
        };

        cleanText = cleanText.replace(/\d+/g, (match) => toKyrgyzNumber(match));

        if (cleanText.trim().length > 0) {
            const utterance = new SpeechSynthesisUtterance(cleanText);
            utterance.lang = "ru-RU";
            utterance.rate = 0.8;
            utterance.pitch = 1.0;
            window.speechSynthesis.speak(utterance);
        }
    };

    const sendMessage = async () => {
        if (!input.trim()) return;
        const userMessage = input;
        setInput("");
        setMessages((prev) => [...prev, { role: "user", text: userMessage }]);
        setIsLoading(true);

        try {
            const response = await requester.post("/chatbot/api/chat/", {
                message: userMessage,
            });
            const botText =
                response.data?.response ||
                response.response ||
                "Кечириңиз, ката кетти.";
            setMessages((prev) => [
                ...prev,
                {
                    role: "bot",
                    text: botText,
                    audio: botText,
                },
            ]);
            if (botText) {
                playKyrgyzVoice(botText);
            }
        } catch (error) {
            setMessages((prev) => [
                ...prev,
                { role: "bot", text: "❌ Сервер иштебей жатат." },
            ]);
        } finally {
            setIsLoading(false);
        }
    };

    const startListening = () => {
        const SpeechRecognition =
            window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            alert("Бул браузер үндү колдобойт. Chrome колдонуңуз.");
            return;
        }
        const recognition = new SpeechRecognition();
        recognition.lang = "ru-RU";
        recognition.continuous = false;
        recognition.interimResults = false;

        recognition.onstart = () => setIsListening(true);

        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            setInput(transcript);
        };

        recognition.onerror = (event) => {
            console.error("STT Error:", event.error);
            setIsListening(false);
        };

        recognition.onend = () => setIsListening(false);
        recognition.start();
    };

    return (
        <div className={styles.chatbotContainer}>
            {!open && (
                <button
                    onClick={() => setOpen(true)}
                    className={styles.openButton}
                >
                    💬 Жардам
                </button>
            )}

            {open && (
                <div className={styles.chatWindow}>
                    <div className={styles.header}>
                        <strong>🛍️ Ассистент</strong>
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
                                Кандай жардам бере алам?
                            </p>
                        )}
                        {messages.map((m, i) => (
                            <div
                                key={i}
                                className={`${styles.messageRow} ${m.role === "user" ? styles.user : styles.bot}`}
                            >
                                <div
                                    className={
                                        m.role === "user"
                                            ? styles.userBubble
                                            : styles.botBubble
                                    }
                                >
                                    <span
                                        dangerouslySetInnerHTML={
                                            m.role === "bot"
                                                ? { __html: m.text }
                                                : null
                                        }
                                    >
                                        {m.role === "user" ? m.text : null}
                                    </span>

                                    {m.role === "bot" && (
                                        <button
                                            onClick={() =>
                                                playKyrgyzVoice(m.text)
                                            }
                                            className={styles.inlineTtsButton}
                                            title="Угуу"
                                        >
                                            🔊
                                        </button>
                                    )}
                                </div>
                            </div>
                        ))}
                        {isLoading && (
                            <p className={styles.loadingText}>
                                Ойлонуп жатат...
                            </p>
                        )}
                        <div ref={chatEndRef} />
                    </div>

                    <div className={styles.inputArea}>
                        <button
                            onClick={startListening}
                            className={`${styles.micButton} ${isListening ? styles.active : ""}`}
                        >
                            {isListening ? "🛑" : "🎤"}
                        </button>
                        <input
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyPress={(e) =>
                                e.key === "Enter" && sendMessage()
                            }
                            placeholder="Жазуу же сүйлөө..."
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
