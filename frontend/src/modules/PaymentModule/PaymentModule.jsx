import React, { useState } from "react";
import styles from "./PaymentModule.module.scss";
import { Typography } from "../../ui/Typography/Typography";
import { Button } from "../../ui/Buttons/Button";
import { requester } from "../../utils/Requester/Requester";
import { useCart } from "../CartProvider/CartProvider";

export const PaymentModule = ({ isOpen, onClose, total, orderId }) => {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [cardNumber, setCardNumber] = useState("");
    const [expiryMonth, setExpiryMonth] = useState("");
    const [expiryYear, setExpiryYear] = useState("");
    const [cvv, setCvv] = useState("");

    const { clearCart } = useCart();

    if (!isOpen) return null;

    const handlePayment = async () => {
        const cleaned = cardNumber.replace(/\s+/g, "");
        if (!cleaned || !expiryMonth || !expiryYear || !cvv) {
            setError("Пожалуйста, заполните все поля карты");
            return;
        }

        if (!/^\d{16}$/.test(cleaned)) {
            setError("Жараксыз карта номери");
            return;
        }

        const luhnCheck = (num) => {
            const arr = num
                .split("")
                .reverse()
                .map((d) => parseInt(d, 10));
            let sum = 0;
            for (let i = 0; i < arr.length; i++) {
                let val = arr[i];
                if (i % 2 === 1) {
                    val *= 2;
                    if (val > 9) val -= 9;
                }
                sum += val;
            }
            return sum % 10 === 0;
        };

        if (!luhnCheck(cleaned)) {
            setError("Жараксыз карта номери (тексерүү ийгиликсиз)");
            return;
        }

        const mm = parseInt(expiryMonth, 10);
        const yyyy = parseInt(expiryYear, 10);
        const now = new Date();
        const currentYear = now.getFullYear();
        const currentMonth = now.getMonth() + 1;

        if (!(mm >= 1 && mm <= 12)) {
            setError("Жараксыз мөөнөт (ай)");
            return;
        }

        if (
            isNaN(yyyy) ||
            yyyy < currentYear ||
            (yyyy === currentYear && mm < currentMonth)
        ) {
            setError("Карта мөөнөтү бүткөнгө окшойт");
            return;
        }

        if (!/^\d{3}$/.test(cvv)) {
            setError("Жараксыз CVV коду");
            return;
        }

        setLoading(true);
        setError(null);

        try {
            const response = await requester.post("/api/payment/initiate/", {
                order_id: orderId,
                amount: total,
                phone_number: "+996706225571",
                payment_method: "visa",
                card_number: cleaned,
                expiry_month: expiryMonth,
                expiry_year: expiryYear,
                cvv: cvv,
            });

            if (response.data.success) {
                try {
                    await clearCart();
                } catch (e) {
                    console.error("Clear cart failed", e);
                }
                alert("Order confirmed");
                onClose();
            } else {
                setError(response.data.error || "Төлөм жүргүзүүдө ката болду.");
            }
        } catch (err) {
            setError(
                err.response?.data?.error ||
                    "Төлөм жүргүзүүдө ката болду. Кайра аракет кылып көрүңүз."
            );
            console.error("Payment error:", err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className={styles.overlay} onClick={onClose}>
            <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
                <button className={styles.closeBtn} onClick={onClose}>
                    &times;
                </button>

                <Typography variant="h2">Visa аркылуу төлөм</Typography>
                <div className={styles.details}>
                    <p>
                        Төлөнүүчү сумма: <strong>{total} сом</strong>
                    </p>
                </div>

                {error && <div className={styles.errorMessage}>{error}</div>}

                <div className={styles.formPlaceholder}>
                    <div className={styles.visaInfo}>
                        <p>Visa картасы менен төлөм жүргүзүү:</p>
                    </div>

                    <input
                        type="text"
                        placeholder="Карта номери (16 цифр)"
                        value={cardNumber}
                        onChange={(e) => {
                            const onlyDigits = e.target.value.replace(
                                /\D/g,
                                ""
                            );
                            const trimmed = onlyDigits.slice(0, 16);
                            const parts = trimmed.match(/.{1,4}/g) || [];
                            setCardNumber(parts.join(" "));
                        }}
                        className={styles.input}
                        disabled={loading}
                        maxLength="19"
                    />

                    <div className={styles.cardDetails}>
                        <input
                            type="text"
                            placeholder="Ай (MM)"
                            value={expiryMonth}
                            onChange={(e) => {
                                const onlyDigits = e.target.value.replace(
                                    /\D/g,
                                    ""
                                );
                                setExpiryMonth(onlyDigits.slice(0, 2));
                            }}
                            className={styles.inputSmall}
                            disabled={loading}
                            maxLength="2"
                        />
                        <input
                            type="text"
                            placeholder="Жыл (YYYY)"
                            value={expiryYear}
                            onChange={(e) => {
                                const onlyDigits = e.target.value.replace(
                                    /\D/g,
                                    ""
                                );
                                setExpiryYear(onlyDigits.slice(0, 4));
                            }}
                            className={styles.inputSmall}
                            disabled={loading}
                            maxLength="4"
                        />
                        <input
                            type="text"
                            placeholder="CVV"
                            value={cvv}
                            onChange={(e) => {
                                const onlyDigits = e.target.value.replace(
                                    /\D/g,
                                    ""
                                );
                                setCvv(onlyDigits.slice(0, 3));
                            }}
                            className={styles.inputSmall}
                            disabled={loading}
                            maxLength="3"
                        />
                    </div>

                    <Button
                        variant="blackButton"
                        className={styles.paySubmitBtn}
                        onClick={handlePayment}
                        disabled={loading}
                    >
                        {loading ? "Өндүрүлүүдө..." : "Visa аркылуу төлөө"}
                    </Button>
                </div>
            </div>
        </div>
    );
};
