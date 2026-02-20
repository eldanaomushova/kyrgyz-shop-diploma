import { useCart } from "../../modules/CartProvider/CartProvider";
import { Typography } from "../../ui/Typography/Typography";
import styles from "./CartModule.module.scss";
import trash from "../../assets/Icons/trash.png";
import visa from "../../assets/Icons/visa.png";
import { Button } from "../../ui/Buttons/Button";
import { useState } from "react";
import { PaymentModule } from "../../modules/PaymentModule/PaymentModule";

export const CartModule = () => {
    const { cart, removeFromCart, updateQuantity } = useCart();
    const [isPaymentOpen, setIsPaymentOpen] = useState(false);

    const subtotal = cart.reduce(
        (acc, item) => acc + item.price * item.quantity,
        0
    );
    const deliveryFee = subtotal > 5000 ? 0 : 200;
    const total = subtotal + deliveryFee;

    if (cart.length === 0) {
        return (
            <div className={styles.emptyCart}>
                <Typography variant="h1">Себетиңиз бош</Typography>
                <button
                    className={styles.checkoutBtn}
                    onClick={() => (window.location.href = "/")}
                >
                    Шопингди баштоо
                </button>
            </div>
        );
    }
    const handlePayment = () => {
        setIsPaymentOpen(true);
    };

    if (cart.length === 0) {
        return (
            <div className={styles.emptyCart}>
                <Typography variant="h1">Себетиңиз бош</Typography>
                <button
                    className={styles.checkoutBtn}
                    onClick={() => (window.location.href = "/")}
                >
                    Шопингди баштоо
                </button>
            </div>
        );
    }

    return (
        <div className={styles.cartWrapper}>
            <h1>Себет</h1>

            <div className={styles.cartContent}>
                <div className={styles.itemsList}>
                    {cart.map((item) => (
                        <div key={item.product_id} className={styles.cartItem}>
                            <img
                                src={item.link}
                                alt={item.productDisplayName}
                            />
                            <div className={styles.itemInfo}>
                                <h5>H&M</h5>
                                <Typography
                                    variant="p"
                                    className={styles.title}
                                >
                                    {item.productDisplayName}
                                </Typography>
                                <div className={styles.price}>
                                    {item.price} сом
                                </div>

                                <div className={styles.itemDetails}>
                                    Артикул: {item.product_id}
                                    <br />
                                    Түсү: {item.color || "Стандарттык"}
                                    <br />
                                    Өлчөмү: M
                                </div>

                                <div className={styles.quantityControls}>
                                    <button
                                        onClick={() =>
                                            updateQuantity(
                                                item.product_id,
                                                item.quantity - 1
                                            )
                                        }
                                        disabled={item.quantity <= 1}
                                    >
                                        -
                                    </button>
                                    <span>{item.quantity}</span>
                                    <button
                                        onClick={() =>
                                            updateQuantity(
                                                item.product_id,
                                                item.quantity + 1
                                            )
                                        }
                                    >
                                        +
                                    </button>
                                </div>
                            </div>
                            <button
                                className={styles.removeBtn}
                                onClick={() => removeFromCart(item.product_id)}
                            >
                                <img src={trash} alt="Өчүрүү" width="16" />
                            </button>
                        </div>
                    ))}
                </div>

                <div className={styles.summaryCard}>
                    <div className={styles.summaryRow}>
                        <span>Заказдын баасы</span>
                        <span>{subtotal} сом</span>
                    </div>
                    <div className={styles.summaryRow}>
                        <span>Жеткирүү</span>
                        <span>
                            {deliveryFee === 0
                                ? "Акысыз"
                                : `${deliveryFee} сом`}
                        </span>
                    </div>
                    <div className={`${styles.summaryRow} ${styles.total}`}>
                        <span>Жалпы сумма</span>
                        <span>{total} сом</span>
                    </div>
                    <Button
                        variant="blackButton"
                        text="Төлөмгө өтүү"
                        onClick={handlePayment}
                    />
                    <div className={styles.paymentIcons}>
                        <img src={visa} alt="Visa" />
                    </div>
                    <Typography variant="psmall">
                        Баалар жана жеткирүү акысы төлөмдү ырастоо учурунда
                        такталат.
                    </Typography>
                </div>
                <PaymentModule
                    isOpen={isPaymentOpen}
                    onClose={() => setIsPaymentOpen(false)}
                    total={total}
                />
            </div>
        </div>
    );
};
