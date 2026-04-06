import React, { useState, useRef } from "react";
import axios from "axios";
import QuestionaryModule from "../../modules/QuestionaryModule/QuestionaryModule";
import styles from "./VirtualTryOnModule.module.scss";
import { Typography } from "../../ui/Typography/Typography";
import { Button } from "../../ui/Buttons/Button";

const VirtualTryOnModule = () => {
    const [stage, setStage] = useState("questionnaire");
    const [recommendations, setRecommendations] = useState([]);
    const [selectedProduct, setSelectedProduct] = useState(null);
    const [userImage, setUserImage] = useState(null);
    const [tryOnResult, setTryOnResult] = useState(null);
    const [loading, setLoading] = useState(false);
    const [generatedImageUrl, setGeneratedImageUrl] = useState(null);
    const fileInputRef = useRef(null);

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
        setUserImage(null); // Reset user image when new product selected
    };

    const handleImageUpload = (event) => {
        const file = event.target.files[0];
        if (file) {
            setUserImage(file);
            setTryOnResult(null);
            setGeneratedImageUrl(null);
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
                    <button
                        className={styles.backButton}
                        onClick={() => setStage("recommendations")}
                    >
                        ← Сунуштарга кайтуу
                    </button>

                    <div className={styles.tryOnContainer}>
                        <div className={styles.selectedProduct}>
                            <Typography variant="h3">Тандалган буюм</Typography>
                            <img
                                src={selectedProduct.link}
                                alt={selectedProduct.productDisplayName}
                                className={styles.selectedProductImage}
                            />
                            <div className={styles.productDetails}>
                                <Typography variant="h4">
                                    {selectedProduct.productDisplayName}
                                </Typography>
                                <Typography variant="h5">
                                    ${selectedProduct.price}
                                </Typography>
                            </div>
                        </div>

                        <div className={styles.uploadSection}>
                            <Typography variant="h3">
                                Сүрөтүңүздү жүктөңүз
                            </Typography>
                            <Typography variant="body2">
                                Эң жакшы натыйжа алуу үчүн толук дене сүрөтүн
                                жүктөңүз
                            </Typography>

                            <input
                                type="file"
                                ref={fileInputRef}
                                onChange={handleImageUpload}
                                accept="image/*"
                                style={{ display: "none" }}
                            />

                            {!userImage ? (
                                <button
                                    className={styles.uploadButton}
                                    onClick={() => fileInputRef.current.click()}
                                >
                                    Менин сүрөтүмдү жүктөө
                                </button>
                            ) : (
                                <div className={styles.imagePreview}>
                                    <img
                                        src={URL.createObjectURL(userImage)}
                                        alt="Your photo"
                                        className={styles.previewImage}
                                    />
                                    <button
                                        className={styles.changePhotoButton}
                                        onClick={() =>
                                            fileInputRef.current.click()
                                        }
                                    >
                                        Сүрөттү өзгөртүү
                                    </button>
                                </div>
                            )}

                            <button
                                className={styles.tryOnActionButton}
                                onClick={handleTryOn}
                                disabled={!userImage || loading}
                            >
                                {loading
                                    ? "Иштетүүдө..."
                                    : "Кийимди сынап көрүү"}
                            </button>
                        </div>
                    </div>

                    {(tryOnResult || generatedImageUrl) && (
                        <div className={styles.resultSection}>
                            <Typography variant="h3">
                                Виртуалдык сынап көрүү натыйжаңыз
                            </Typography>

                            {generatedImageUrl && (
                                <div className={styles.generatedImageContainer}>
                                    <img
                                        src={generatedImageUrl}
                                        alt="Virtual try-on result"
                                        className={styles.generatedImage}
                                        onError={(e) => {
                                            console.error(
                                                "Image failed to load:",
                                                generatedImageUrl
                                            );
                                            e.target.src =
                                                "https://via.placeholder.com/800x1000/ff0000/ffffff?text=Image+Load+Error";
                                        }}
                                    />
                                </div>
                            )}

                            <div className={styles.resultCard}>
                                {tryOnResult?.message && (
                                    <Typography variant="body1">
                                        {tryOnResult.message}
                                    </Typography>
                                )}
                                {tryOnResult?.note && (
                                    <Typography
                                        variant="body2"
                                        className={styles.note}
                                    >
                                        {tryOnResult.note}
                                    </Typography>
                                )}
                                <div className={styles.resultActions}>
                                    <Button
                                        className={styles.addToCartButton}
                                        variant="secondary"
                                        onClick={() => {
                                            alert(
                                                `Себетке кошулду: ${selectedProduct.productDisplayName} - $${selectedProduct.price}`
                                            );
                                        }}
                                    >
                                        Себетке кошуу - ${selectedProduct.price}
                                    </Button>
                                    <Button
                                        variant="secondary"
                                        className={styles.tryAnotherButton}
                                        onClick={resetProcess}
                                    >
                                        Башка буюмду сынап көрүү
                                    </Button>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        );
    }

    return null;
};

export default VirtualTryOnModule;
