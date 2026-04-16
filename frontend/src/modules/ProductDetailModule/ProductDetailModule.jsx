import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import styles from "./ProductDetailModule.module.scss";
import { Typography } from "../../ui/Typography/Typography";
import { useCart } from "../../modules/CartProvider/CartProvider";
import Swal from "sweetalert2";
import { Button } from "../../ui/Buttons/Button";
import { requester } from "../../utils/Requester/Requester";

export const ProductDetailModule = () => {
    const { id } = useParams();
    const navigate = useNavigate();
    const [product, setProduct] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const { addToCart } = useCart();

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

    const getImageUrl = () => {
        if (product?.link && product.link.startsWith("http")) {
            return product.link.replace("http://", "https://");
        }
        if (product?.filename) {
            return `/media/products/${product.filename}`;
        }
        return "/placeholder.jpg";
    };

    useEffect(() => {
        const fetchProduct = async () => {
            if (
                !id ||
                id === "undefined" ||
                id === "null" ||
                isNaN(parseInt(id))
            ) {
                setError("Неверный ID товара");
                setLoading(false);
                return;
            }

            setLoading(true);
            setError(null);

            try {
                const response = await requester.get(
                    `/api/products/detail/${id}/`
                );
                setProduct(response.data);
            } catch (error) {
                console.error("Error fetching product:", error);

                if (error.response) {
                    // Server responded with error status
                    if (error.response.status === 404) {
                        setError("Товар не найден");
                    } else if (error.response.status === 400) {
                        setError("Неверный формат ID товара");
                    } else {
                        setError("Ошибка при загрузке товара");
                    }
                } else if (error.request) {
                    // Request was made but no response
                    setError(
                        "Ошибка соединения с сервером. Проверьте интернет-соединение."
                    );
                } else {
                    // Something else happened
                    setError("Произошла ошибка при загрузке данных");
                }
            } finally {
                setLoading(false);
            }
        };

        fetchProduct();
    }, [id]);

    // Redirect to home if no valid id
    useEffect(() => {
        if (!id || id === "undefined" || id === "null" || isNaN(parseInt(id))) {
            const timer = setTimeout(() => {
                navigate("/");
            }, 3000);
            return () => clearTimeout(timer);
        }
    }, [id, navigate]);

    if (loading) {
        return (
            <div className={styles.loaderContainer}>
                <div className={styles.loader}>Загрузка...</div>
            </div>
        );
    }

    if (error) {
        return (
            <div className={styles.errorContainer}>
                <div className={styles.error}>
                    <Typography variant="h2">Ошибка</Typography>
                    <Typography variant="p" className={styles.errorMessage}>
                        {error}
                    </Typography>
                    <Button
                        variant="blackButton"
                        text="Вернуться на главную"
                        onClick={() => navigate("/")}
                    />
                </div>
            </div>
        );
    }

    if (!product) return null;

    return (
        <div className={styles.wrapper}>
            <div className={styles.container}>
                <div className={styles.imageGallery}>
                    <img
                        src={getImageUrl()}
                        alt={product.productDisplayName || "Product image"}
                        className={styles.mainImage}
                        onError={(e) => {
                            e.target.src = "/placeholder.jpg";
                        }}
                    />
                </div>

                <div className={styles.infoSidebar}>
                    <div className={styles.header}>
                        <Typography variant="h1" className={styles.title}>
                            {product.productDisplayName || "Без названия"}
                        </Typography>
                        <Typography variant="h5" className={styles.price}>
                            {product.price
                                ? `${product.price} сом`
                                : "Цена не указана"}
                        </Typography>
                    </div>

                    <div className={styles.colorSection}>
                        <Typography variant="h3" className={styles.label}>
                            Цвет: <span>{product.color || "Не указан"}</span>
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
                                {product.brand || "Не указан"}
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
                                {product.season || "Не указан"}
                            </Typography>
                        </div>
                        {product.gender && (
                            <div className={styles.detailItem}>
                                <Typography
                                    variant="h5"
                                    className={styles.detailLabel}
                                >
                                    Пол:
                                </Typography>
                                <Typography className={styles.detailValue}>
                                    {product.gender === "Men"
                                        ? "Мужской"
                                        : product.gender === "Women"
                                          ? "Женский"
                                          : product.gender}
                                </Typography>
                            </div>
                        )}
                    </div>

                    <Button
                        variant="blackButton"
                        text="Себетке кошуу"
                        onClick={handleAddToCart}
                        disabled={!product}
                    />

                    <div className={styles.description}>
                        <Typography variant="h4" className={styles.h4text}>
                            Сүрөттөмө жана курамы
                        </Typography>
                        <Typography variant="p" className={styles.ptext}>
                            Бул {product.brand || "бренд"} брендинин товары "
                            {product.usage || "универсальный"}" категориясында
                            колдонуу үчүн эң сонун ийкемдүү келет.
                        </Typography>
                        <ul>
                            <li>Түрү: {product.articleType || "Не указан"}</li>
                            <li>
                                Силуэт: {product.silhouette || "Классикалык"}
                            </li>
                            <li>
                                Коллекция жылы: {product.year || "Не указан"}
                            </li>
                            {product.fabric && (
                                <li>Курамы: {product.fabric}</li>
                            )}
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    );
};
