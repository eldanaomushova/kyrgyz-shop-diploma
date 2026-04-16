import React, { useState, useRef } from "react";
import QuestionaryModule from "../../modules/QuestionaryModule/QuestionaryModule";
import styles from "./VirtualTryOnModule.module.scss";
import { Typography } from "../../ui/Typography/Typography";
import { Button } from "../../ui/Buttons/Button";
import { useCart } from "../../modules/CartProvider/CartProvider";
import Swal from "sweetalert2";
import { useNavigate } from "react-router-dom";
import { requester } from "../../utils/Requester/Requester";

const getProductImageUrl = (product) => {
    if (!product) return null;
    if (product.link && product.link.startsWith("http://")) {
        return product.link.replace("http://", "https://");
    }
    if (product.link) return product.link;
    if (product.filename) {
        return `/media/products/${product.filename}`;
    }
    return null;
};

const VirtualTryOnModule = () => {
    const [stage, setStage] = useState("questionnaire");
    const [recommendations, setRecommendations] = useState([]);
    const [selectedProduct, setSelectedProduct] = useState(null);
    const [userImage, setUserImage] = useState(null);
    const [loading, setLoading] = useState(false);
    const [generatedImageUrl, setGeneratedImageUrl] = useState(null);
    const fileInputRef = useRef(null);
    const { addToCart } = useCart();
    const navigate = useNavigate();

    const getCookie = (name) => {
        let cookieValue = null;
        if (document.cookie && document.cookie !== "") {
            const cookies = document.cookie.split(";");
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === name + "=") {
                    cookieValue = decodeURIComponent(
                        cookie.substring(name.length + 1)
                    );
                    break;
                }
            }
        }
        return cookieValue;
    };

    const handleQuestionnaireComplete = (data) => {
        setRecommendations(data.recommendations);
        setStage("recommendations");
    };

    const handleProductSelect = (product) => {
        setSelectedProduct(product);
        setStage("try-on");
        setGeneratedImageUrl(null);
        setUserImage(null);
    };

    const handleImageUpload = (event) => {
        const file = event.target.files[0];
        if (file) {
            setUserImage(file);
            setGeneratedImageUrl(null);
        }
    };

    const handleAddToCart = () => {
        if (selectedProduct) {
            addToCart(selectedProduct);
            Swal.fire({
                title: "Кошулду!",
                text: `${selectedProduct.productDisplayName} себетке ийгиликтүү кошулду.`,
                icon: "success",
                toast: true,
                position: "top-end",
                showConfirmButton: false,
                timer: 2000,
                timerProgressBar: true,
                background: "#fff",
                color: "#333",
            });
        } else {
            console.error("No product selected to add to cart");
        }
    };

    const fetchProductImageAsBlob = async (imageUrl) => {
        try {
            const response = await requester.get(imageUrl, {
                responseType: "blob",
            });
            return response.data;
        } catch (error) {
            return null;
        }
    };

    const handleTryOn = async () => {
        if (!userImage || !selectedProduct) return;

        setLoading(true);
        try {
            const formData = new FormData();
            formData.append("person_image", userImage);

            const productImageUrl = getProductImageUrl(selectedProduct);
            if (productImageUrl) {
                const productBlob =
                    await fetchProductImageAsBlob(productImageUrl);
                if (productBlob) {
                    formData.append(
                        "garment_image",
                        productBlob,
                        "garment.jpg"
                    );
                }
            }
            console.log(formData);

            const response = await requester.post(
                "/api/virtual-try-on/image-try-on/",
                formData,
                {
                    headers: {
                        "X-CSRFToken": getCookie("csrftoken"),
                        "Content-Type": "multipart/form-data",
                    },
                }
            );

            if (response.data.result_url) {
                setGeneratedImageUrl(response.data.result_url);
            } else if (response.data.generated_image_url) {
                setGeneratedImageUrl(response.data.generated_image_url);
            } else if (response.data.generated_image_base64) {
                setGeneratedImageUrl(
                    `data:image/jpeg;base64,${response.data.generated_image_base64}`
                );
            } else if (response.data.image) {
                setGeneratedImageUrl(response.data.image);
            } else {
                throw new Error("No image returned from server");
            }
        } catch (error) {
            Swal.fire({
                title: "Ката!",
                text:
                    error.response?.data?.error ||
                    "Виртуалдык сынап көрүүдө ката кетти. Кайра аракет кылыңыз.",
                icon: "error",
                confirmButtonText: "Түшүндүм",
            });
        } finally {
            setLoading(false);
        }
    };

    const resetProcess = () => {
        setStage("questionnaire");
        setRecommendations([]);
        setSelectedProduct(null);
        setUserImage(null);
        setGeneratedImageUrl(null);
    };

    if (stage === "questionnaire") {
        return (
            <div
                className={`${styles.virtualTryOnPage} ${styles.questionnaireStage}`}
            >
                <div className={styles.container}>
                    <QuestionaryModule
                        onComplete={handleQuestionnaireComplete}
                    />
                </div>
            </div>
        );
    }

    if (stage === "recommendations") {
        return (
            <div className={styles.virtualTryOnPage}>
                <div className={styles.container}>
                    <Typography
                        variant="h1"
                        className={styles.headerVirtualTryOn}
                    >
                        Жекелештирилген сунуштарыңыз
                    </Typography>
                    <Button
                        className={styles.backButton}
                        onClick={() => setStage("questionnaire")}
                    >
                        ← Сурамжылоого кайтуу
                    </Button>

                    <div className={styles.recommendationsGrid}>
                        {recommendations.map((product) => (
                            <div
                                key={product.id}
                                className={styles.productCard}
                                onClick={() => handleProductSelect(product)}
                            >
                                <img
                                    src={getProductImageUrl(product)}
                                    alt={product.productDisplayName}
                                    className={styles.productImage}
                                    onError={(e) => {
                                        e.target.src = "/placeholder.jpg";
                                    }}
                                />
                                <div className={styles.productInfo}>
                                    <Typography variant="h3">
                                        {product.productDisplayName}
                                    </Typography>
                                    <Typography
                                        variant="h4"
                                        className={styles.price}
                                    >
                                        {product.price} сом
                                    </Typography>
                                    <Typography
                                        variant="body2"
                                        className={styles.category}
                                    >
                                        {product.articleType} -{" "}
                                        {product.subCategory}
                                    </Typography>
                                    <Button
                                        className={styles.tryOnButton}
                                        onClick={() =>
                                            handleProductSelect(product)
                                        }
                                    >
                                        Виртуалдык сынап көрүү
                                    </Button>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        );
    }

    if (stage === "try-on") {
        return (
            <div className={styles.virtualTryOnPage}>
                <div className={styles.container}>
                    <Typography
                        variant="h1"
                        className={styles.headerVirtualTryOn}
                    >
                        Виртуалдык сынап көрүү
                    </Typography>

                    <input
                        type="file"
                        ref={fileInputRef}
                        onChange={handleImageUpload}
                        accept="image/*"
                        style={{ display: "none" }}
                    />

                    <button
                        className={styles.backButton}
                        onClick={() => setStage("recommendations")}
                    >
                        ← Сунуштарга кайтуу
                    </button>

                    <div className={styles.tryOnContainer}>
                        <div className={styles.selectedProduct}>
                            <Typography variant="h3">Тандалган буюм</Typography>
                            <div className={styles.selectedProductImageWrapper}>
                                <img
                                    src={getProductImageUrl(selectedProduct)}
                                    className={styles.selectedProductImage}
                                    alt="Product"
                                    onError={(e) => {
                                        e.target.src = "/placeholder.jpg";
                                    }}
                                />
                            </div>
                            <div className={styles.productDetails}>
                                <Typography variant="h3">
                                    {selectedProduct?.productDisplayName}
                                </Typography>
                                <Typography variant="h4">
                                    {selectedProduct?.price} сом
                                </Typography>
                            </div>
                        </div>

                        <div className={styles.uploadSection}>
                            <Typography variant="h3">
                                Сиздин сүрөтүңүз
                            </Typography>
                            <div className={styles.imagePreview}>
                                {userImage ? (
                                    <img
                                        src={URL.createObjectURL(userImage)}
                                        alt="Preview"
                                    />
                                ) : (
                                    <div
                                        style={{
                                            color: "#999",
                                            cursor: "pointer",
                                        }}
                                        onClick={() =>
                                            fileInputRef.current.click()
                                        }
                                    >
                                        Сүрөт тандоо үчүн басыңыз
                                    </div>
                                )}
                            </div>
                            <div className={styles.resultActions}>
                                <button
                                    className={styles.changeButton}
                                    onClick={() => fileInputRef.current.click()}
                                >
                                    {userImage
                                        ? "Сүрөттү өзгөртүү"
                                        : "Сүрөт жүктөө"}
                                </button>
                                <button
                                    className={styles.tryOnActionButton}
                                    onClick={handleTryOn}
                                    disabled={!userImage || loading}
                                >
                                    {loading
                                        ? "Иштеп жатат..."
                                        : "Виртуалдык сынап көрүү"}
                                </button>
                                <button
                                    className={styles.arLiveButton}
                                    onClick={() =>
                                        navigate(
                                            `/ar-tryon/${selectedProduct?.id}`,
                                            {
                                                state: {
                                                    productImageUrl:
                                                        getProductImageUrl(
                                                            selectedProduct
                                                        ),
                                                },
                                            }
                                        )
                                    }
                                    disabled={!selectedProduct}
                                >
                                    <span className={styles.arPulse} />
                                    <span className={styles.arIcon}>
                                        <svg
                                            width="20"
                                            height="20"
                                            viewBox="0 0 24 24"
                                            fill="none"
                                            stroke="currentColor"
                                            strokeWidth="2"
                                            strokeLinecap="round"
                                            strokeLinejoin="round"
                                        >
                                            <path
                                                d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8
                 a2 2 0 0 1 2-2h4l2-3h6l2 3h4
                 a2 2 0 0 1 2 2z"
                                            />
                                            <circle cx="12" cy="13" r="4" />
                                        </svg>
                                    </span>
                                    AR Live Fit
                                </button>
                            </div>
                        </div>

                        <div className={styles.resultSection}>
                            <Typography variant="h3">
                                Виртуалдык сынап көрүү натыйжаңыз
                            </Typography>
                            <div className={styles.generatedImageContainer}>
                                {loading && (
                                    <div className={styles.aiOverlay}>
                                        <div className={styles.shimmer}></div>
                                        <div className={styles.statusText}>
                                            AI иштеп жатат...
                                        </div>
                                    </div>
                                )}
                                {generatedImageUrl && !loading && (
                                    <img src={generatedImageUrl} alt="Result" />
                                )}
                                {!generatedImageUrl && !loading && (
                                    <div style={{ color: "#999" }}>
                                        Натыйжа бул жерде болот
                                    </div>
                                )}
                            </div>
                            {generatedImageUrl && (
                                <div className={styles.resultActions}>
                                    <button
                                        className={styles.addToCartButton}
                                        onClick={handleAddToCart}
                                    >
                                        Себетке кошуу
                                    </button>
                                    <button
                                        className={styles.tryAnotherButton}
                                        onClick={resetProcess}
                                    >
                                        Башкасын көрүү
                                    </button>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    return null;
};

export default VirtualTryOnModule;
