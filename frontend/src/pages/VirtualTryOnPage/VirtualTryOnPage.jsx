import React, { useState, useRef } from "react";
import axios from "axios";
import Questionnaire from "./Questionnaire";
import "./VirtualTryOn.css";

const VirtualTryOnPage = () => {
    const [stage, setStage] = useState("questionnaire");
    const [recommendations, setRecommendations] = useState([]);
    const [selectedProduct, setSelectedProduct] = useState(null);
    const [userImage, setUserImage] = useState(null);
    const [tryOnResult, setTryOnResult] = useState(null);
    const [loading, setLoading] = useState(false);
    const fileInputRef = useRef(null);

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

    if (stage === "questionnaire") {
        return (
            <div className="virtual-try-on-page">
                <div className="container">
                    <h1>Virtual Try-On Experience</h1>
                    <p>
                        Answer a few questions to get personalized clothing
                        recommendations, then try them on virtually!
                    </p>
                    <Questionnaire onComplete={handleQuestionnaireComplete} />
                </div>
            </div>
        );
    }

    if (stage === "recommendations") {
        return (
            <div className="virtual-try-on-page">
                <div className="container">
                    <h1>Your Personalized Recommendations</h1>
                    <button
                        className="back-button"
                        onClick={() => setStage("questionnaire")}
                    >
                        ← Back to Questionnaire
                    </button>

                    <div className="recommendations-grid">
                        {recommendations.map((product) => (
                            <div key={product.id} className="product-card">
                                <img
                                    src={product.link}
                                    alt={product.productDisplayName}
                                    className="product-image"
                                />
                                <div className="product-info">
                                    <h3>{product.productDisplayName}</h3>
                                    <p className="price">${product.price}</p>
                                    <p className="category">
                                        {product.articleType} -{" "}
                                        {product.subCategory}
                                    </p>
                                    <button
                                        className="try-on-button"
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

    if (stage === "try-on") {
        return (
            <div className="virtual-try-on-page">
                <div className="container">
                    <h1>Virtual Try-On</h1>
                    <button
                        className="back-button"
                        onClick={() => setStage("recommendations")}
                    >
                        ← Back to Recommendations
                    </button>

                    <div className="try-on-container">
                        <div className="selected-product">
                            <h3>Selected Item</h3>
                            <img
                                src={selectedProduct.link}
                                alt={selectedProduct.productDisplayName}
                                className="selected-product-image"
                            />
                            <div className="product-details">
                                <h4>{selectedProduct.productDisplayName}</h4>
                                <p>${selectedProduct.price}</p>
                            </div>
                        </div>

                        <div className="upload-section">
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
                                    className="upload-button"
                                    onClick={() => fileInputRef.current.click()}
                                >
                                    Choose Photo
                                </button>
                            ) : (
                                <div className="image-preview">
                                    <img
                                        src={URL.createObjectURL(userImage)}
                                        alt="Your photo"
                                        className="preview-image"
                                    />
                                    <button
                                        className="change-photo-button"
                                        onClick={() =>
                                            fileInputRef.current.click()
                                        }
                                    >
                                        Change Photo
                                    </button>
                                </div>
                            )}

                            <button
                                className="try-on-action-button"
                                onClick={handleTryOn}
                                disabled={!userImage || loading}
                            >
                                {loading ? "Processing..." : "Try On Now"}
                            </button>
                        </div>
                    </div>

                    {tryOnResult && (
                        <div className="result-section">
                            <h3>Your Virtual Try-On Result</h3>
                            <div className="result-card">
                                <p>{tryOnResult.message}</p>
                                <p className="note">{tryOnResult.note}</p>
                                <div className="result-actions">
                                    <button className="add-to-cart-button">
                                        Add to Cart - ${selectedProduct.price}
                                    </button>
                                    <button
                                        className="try-another-button"
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

export default VirtualTryOnPage;
