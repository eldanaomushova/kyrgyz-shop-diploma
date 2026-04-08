import React, { useState, useRef } from "react";
import axios from "axios";
import QuestionaryModule from "../../modules/QuestionaryModule/QuestionaryModule";
import styles from "./VirtualTryOnModule.module.scss";
import { Typography } from "../../ui/Typography/Typography";
import { Button } from "../../ui/Buttons/Button";
import { useParams } from "react-router-dom";
import { useCart } from "../../modules/CartProvider/CartProvider";
import Swal from "sweetalert2";

const VirtualTryOnModule = () => {
    const [stage, setStage] = useState("questionnaire");
    const [recommendations, setRecommendations] = useState([]);
    const [selectedProduct, setSelectedProduct] = useState(null);
    const [userImage, setUserImage] = useState(null);
    const [tryOnResult, setTryOnResult] = useState(null);
    const [loading, setLoading] = useState(false);
    const [generatedImageUrl, setGeneratedImageUrl] = useState(null);
    const fileInputRef = useRef(null);
    const { id } = useParams();
    const { addToCart } = useCart();
    console.log("Product ID from params:", id);

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
        setTryOnResult(null);
        setGeneratedImageUrl(null);
        setUserImage(null);
    };

    const handleImageUpload = (event) => {
        const file = event.target.files[0];
        if (file) {
            setUserImage(file);
            setTryOnResult(null);
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

    const handleTryOn = async () => {
        if (!userImage || !selectedProduct) return;

        setLoading(true);
        try {
            const formData = new FormData();
            formData.append("person_image", userImage);

            if (selectedProduct.link) {
                const productImageBlob = await fetch(selectedProduct.link).then(
                    (res) => res.blob()
                );
                formData.append(
                    "garment_image",
                    productImageBlob,
                    "garment.jpg"
                );
            }

            const response = await axios.post(
                "/api/virtual-try-on/image-try-on/",
                formData,
                {
                    headers: {
                        "X-CSRFToken": getCookie("csrftoken"),
                        "Content-Type": "multipart/form-data",
                    },
                }
            );

            setTryOnResult(response.data);

            if (response.data.result_url) {
                setGeneratedImageUrl(response.data.result_url);
            } else if (response.data.generated_image_url) {
                setGeneratedImageUrl(response.data.generated_image_url);
            } else if (response.data.generated_image_base64) {
                setGeneratedImageUrl(response.data.generated_image_base64);
            }
        } catch (error) {
            console.error("Error during virtual try-on:", error);
            alert("Виртуалдык сынап көрүүдө ката кетти. Кайра аракет кылыңыз.");
        } finally {
            setLoading(false);
        }
    };

    const resetProcess = () => {
        setStage("questionnaire");
        setRecommendations([]);
        setSelectedProduct(null);
        setUserImage(null);
        setTryOnResult(null);
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
                                    src={product.link}
                                    alt={product.productDisplayName}
                                    className={styles.productImage}
                                />
                                <div className={styles.productInfo}>
                                    <Typography variant="h3">
                                        {product.productDisplayName}
                                    </Typography>
                                    <Typography
                                        variant="h4"
                                        className={styles.price}
                                    >
                                        ${product.price}
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
                                    src={selectedProduct.link}
                                    className={styles.selectedProductImage}
                                    alt="Product"
                                />
                            </div>
                            <div className={styles.productDetails}>
                                <Typography variant="h3">
                                    {selectedProduct.productDisplayName}
                                </Typography>
                                <Typography variant="h4">
                                    ${selectedProduct.price}
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
                                    Виртуалдык сынап көрүү
                                </button>
                            </div>
                        </div>

                        {/* 3. Result Section */}
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
