import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import styles from "./ProductDetailModule.module.scss";
import { Typography } from "../../ui/Typography/Typography";
import { useCart } from "../../modules/CartProvider/CartProvider";
import Swal from "sweetalert2";
import { Button } from "../../ui/Buttons/Button";

export const ProductDetailModule = () => {
    const { id } = useParams();
    const navigate = useNavigate();
    const [product, setProduct] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const { addToCart } = useCart();
    console.log("Product ID from params:", id);

    const handleAddToCart = () => {
        if (product) {
            addToCart(product);
            Swal.fire({
                title: "Кошулду!",
                text: `${product.productDisplayName} себетке ийгиликтүү кошулду.`,
                icon: "success",
                toast: true,
                position: "top-end",
                showConfirmButton: false,
                timer: 1000,
                timerProgressBar: true,
                background: "#fff",
                color: "#333",
            });
        }
    };

    useEffect(() => {
        const fetchProduct = async () => {
            // Проверяем наличие id
            if (!id || id === "undefined" || id === "null") {
                setError("Неверный ID товара");
                setLoading(false);
                return;
            }

            setLoading(true);
            setError(null);

            try {
                const response = await fetch(
                    `http://127.0.0.1:8000/api/products/detail/${id}/`
                );

                if (response.status === 400) {
                    setError("Неверный формат ID товара");
                    setLoading(false);
                    return;
                }

                if (!response.ok) {
                    if (response.status === 404) {
                        setError("Товар не найден");
                    } else {
                        setError("Ошибка при загрузке товара");
                    }
                    setLoading(false);
                    return;
                }

                const data = await response.json();
                setProduct(data);
            } catch (error) {
                console.error("Error:", error);
                setError("Ошибка соединения с сервером");
            } finally {
                setLoading(false);
            }
        };

        fetchProduct();
    }, [id]);

    // Редирект на главную если нет id
    useEffect(() => {
        if (!id || id === "undefined" || id === "null") {
            const timer = setTimeout(() => {
                navigate("/");
            }, 3000);
            return () => clearTimeout(timer);
        }
    }, [id, navigate]);

    if (loading) return <div className={styles.loader}>Загрузка...</div>;

    if (error) {
        return (
            <div className={styles.error}>
                <Typography variant="h2">Ошибка</Typography>
                <Typography>{error}</Typography>
                <Button
                    variant="blackButton"
                    text="Вернуться на главную"
                    onClick={() => navigate("/")}
                />
            </div>
        );
    }

    if (!product) return null;

    return (
        <div className={styles.wrapper}>
            <div className={styles.container}>
                <div className={styles.imageGallery}>
                    <img
                        src={product.link || "/placeholder.jpg"}
                        alt={product.productDisplayName}
                        className={styles.mainImage}
                    />
                </div>

                <div className={styles.infoSidebar}>
                    <div className={styles.header}>
                        <Typography variant="h1" className={styles.title}>
                            {product.productDisplayName}
                        </Typography>
                        <Typography variant="h5" className={styles.price}>
                            {product.price} сом
                        </Typography>
                    </div>

                    <div className={styles.colorSection}>
                        <Typography variant="h3" className={styles.label}>
                            Цвет: <span>{product.color}</span>
                        </Typography>
                    </div>

                    <div className={styles.details}>
                        <div className={styles.detailItem}>
                            <Typography
                                variant="h5"
                                className={styles.detailLabel}
                            >
                                Бренд:
                            </Typography>
                            <Typography className={styles.detailValue}>
                                {product.brand}
                            </Typography>
                        </div>
                        <div className={styles.detailItem}>
                            <Typography
                                variant="h5"
                                className={styles.detailLabel}
                            >
                                Артикул:
                            </Typography>
                            <Typography className={styles.detailValue}>
                                {product.id}
                            </Typography>
                        </div>
                        <div className={styles.detailItem}>
                            <Typography
                                variant="h5"
                                className={styles.detailLabel}
                            >
                                Сезон:
                            </Typography>
                            <Typography className={styles.detailValue}>
                                {product.season}
                            </Typography>
                        </div>
                    </div>

                    <Button
                        variant="blackButton"
                        text="Себетке кошуу"
                        onClick={handleAddToCart}
                    />

                    <div className={styles.description}>
                        <Typography variant="h4" className={styles.h4text}>
                            Сүрөттөмө жана курамы
                        </Typography>
                        <Typography variant="p" className={styles.ptext}>
                            Бул {product.brand} брендинин товары "
                            {product.usage}" категориясында колдонуу үчүн эң
                            сонун ийкемдүү келет.
                        </Typography>
                        <ul>
                            <li>Түрү: {product.articleType}</li>
                            <li>
                                Силуэт: {product.silhouette || "Классикалык"}
                            </li>
                            <li>Коллекция жылы: {product.year}</li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    );
};
