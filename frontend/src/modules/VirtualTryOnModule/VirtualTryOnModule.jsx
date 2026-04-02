import React, { useState, useRef } from "react";
import axios from "axios";
import QuestionaryModule from "../../modules/QuestionaryModule/QuestionaryModule";
import styles from "./VirtualTryOnModule.module.scss";

const VirtualTryOnModule = () => {
    const [stage, setStage] = useState("questionnaire");
    const [recommendations, setRecommendations] = useState([]);
    const [selectedProduct, setSelectedProduct] = useState(null);
    const [userImage, setUserImage] = useState(null);
    const [tryOnResult, setTryOnResult] = useState(null);
    const [loading, setLoading] = useState(false);
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
    };

    const handleImageUpload = (event) => {
        const file = event.target.files[0];
        if (file) {
            setUserImage(file);
        }
    };

    const handleTryOn = async () => {
        if (!userImage || !selectedProduct) return;

        setLoading(true);
        try {
            const formData = new FormData();
            formData.append("user_image", userImage);
            formData.append("id", selectedProduct.id);

            const response = await axios.post(
                "/api/virtual-try-on/",
                formData,
                {
                    headers: {
                        "X-CSRFToken": getCookie("csrftoken"),
                        "Content-Type": "multipart/form-data",
                    },
                }
            );

            setTryOnResult(response.data);
        } catch (error) {
            console.error("Error during virtual try-on:", error);
            alert("Error processing virtual try-on. Please try again.");
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
    };

    // Questionnaire Stage
    if (stage === "questionnaire") {
        return (
            <div className={styles.virtualTryOnPage}>
                <div className={styles.container}>
                    <h1>Virtual Try-On Experience</h1>
                    <p>
                        Answer a few questions to get personalized clothing
                        recommendations, then try them on virtually!
                    </p>
                    <QuestionaryModule
                        onComplete={handleQuestionnaireComplete}
                    />
                </div>
            </div>
        );
    }

    // Recommendations Stage
    if (stage === "recommendations") {
        return (
            <div className={styles.virtualTryOnPage}>
                <div className={styles.container}>
                    <h1>Your Personalized Recommendations</h1>
                    <button
                        className={styles.backButton}
                        onClick={() => setStage("questionnaire")}
                    >
                        ← Back to Questionnaire
                    </button>

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
                                    <h3>{product.productDisplayName}</h3>
                                    <p className={styles.price}>
                                        ${product.price}
                                    </p>
                                    <p className={styles.category}>
                                        {product.articleType} -{" "}
                                        {product.subCategory}
                                    </p>
                                    <button
                                        className={styles.tryOnButton}
                                        onClick={() =>
                                            handleProductSelect(product)
                                        }
                                    >
                                        Try On Virtually
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        );
    }

    // Try-On Stage
    if (stage === "try-on") {
        return (
            <div className={styles.virtualTryOnPage}>
                <div className={styles.container}>
                    <h1>Virtual Try-On</h1>
                    <button
                        className={styles.backButton}
                        onClick={() => setStage("recommendations")}
                    >
                        ← Back to Recommendations
                    </button>

                    <div className={styles.tryOnContainer}>
                        <div className={styles.selectedProduct}>
                            <h3>Selected Item</h3>
                            <img
                                src={selectedProduct.link}
                                alt={selectedProduct.productDisplayName}
                                className={styles.selectedProductImage}
                            />
                            <div className={styles.productDetails}>
                                <h4>{selectedProduct.productDisplayName}</h4>
                                <p>${selectedProduct.price}</p>
                            </div>
                        </div>

                        <div className={styles.uploadSection}>
                            <h3>Upload Your Photo</h3>
                            <p>
                                Upload a front-facing photo for the best results
                            </p>

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
                                    Choose Photo
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
                                        Change Photo
                                    </button>
                                </div>
                            )}

                            <button
                                className={styles.tryOnActionButton}
                                onClick={handleTryOn}
                                disabled={!userImage || loading}
                            >
                                {loading ? "Processing..." : "Try On Now"}
                            </button>
                        </div>
                    </div>

                    {tryOnResult && (
                        <div className={styles.resultSection}>
                            <h3>Your Virtual Try-On Result</h3>
                            <div className={styles.resultCard}>
                                <p>{tryOnResult.message}</p>
                                <p className={styles.note}>
                                    {tryOnResult.note}
                                </p>
                                <div className={styles.resultActions}>
                                    <button className={styles.addToCartButton}>
                                        Add to Cart - ${selectedProduct.price}
                                    </button>
                                    <button
                                        className={styles.tryAnotherButton}
                                        onClick={resetProcess}
                                    >
                                        Try Another Item
                                    </button>
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
