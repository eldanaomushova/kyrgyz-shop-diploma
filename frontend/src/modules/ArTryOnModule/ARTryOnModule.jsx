import React, { useEffect, useRef, useState, useCallback } from "react";
import { useLocation } from "react-router-dom";
import styles from "./ARTryOnModule.module.scss";
import { Typography } from "../../ui/Typography/Typography";

const extractGarmentWithVertexAI = async (imageFile) => {
    try {
        const formData = new FormData();
        formData.append("product_image", imageFile);

        const response = await fetch("/api/virtual-try-on/extract-garment/", {
            method: "POST",
            body: formData,
        });

        if (!response.ok) {
            return null;
        }

        const data = await response.json();

        if (data.success && data.image_url) {
            return new Promise((resolve) => {
                const img = new Image();
                img.crossOrigin = "Anonymous";
                img.onload = () => {
                    resolve(img);
                };
                img.onerror = () => {
                    resolve(null);
                };
                img.src = data.image_url;
            });
        }
        return null;
    } catch (error) {
        return null;
    }
};

const createMaskedGarment = async (img) => {
    const canvas = document.createElement("canvas");
    canvas.width = img.width;
    canvas.height = img.height;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(img, 0, 0);
    const gradient = ctx.createLinearGradient(0, 0, 0, img.height * 0.3);
    gradient.addColorStop(0, "rgba(0, 0, 0, 0.95)");
    gradient.addColorStop(0.5, "rgba(0, 0, 0, 0.5)");
    gradient.addColorStop(1, "rgba(0, 0, 0, 0)");
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, img.width, img.height * 0.3);
    const maskedImg = new Image();
    maskedImg.src = canvas.toDataURL("image/png");
    return maskedImg;
};

const drawGarmentOnBody = (
    ctx,
    garmentImg,
    landmarks,
    W,
    H,
    sizeMultiplier = 2.0,
    verticalOffset = 0.29
) => {
    if (!garmentImg || !landmarks) return false;

    const getLandmark = (idx) => {
        const lm = landmarks[idx];
        if (!lm) return null;
        return {
            x: (1 - lm.x) * W,
            y: lm.y * H,
            z: lm.z || 0,
            visibility: lm.visibility || 0,
        };
    };

    const leftShoulder = getLandmark(11);
    const rightShoulder = getLandmark(12);
    const leftHip = getLandmark(23);
    const rightHip = getLandmark(24);

    if (
        !leftShoulder ||
        !rightShoulder ||
        leftShoulder.visibility < 0.5 ||
        rightShoulder.visibility < 0.5
    ) {
        return false;
    }

    const shoulderCenter = {
        x: (leftShoulder.x + rightShoulder.x) / 2,
        y: (leftShoulder.y + rightShoulder.y) / 2,
    };

    const shoulderWidth = Math.hypot(
        rightShoulder.x - leftShoulder.x,
        rightShoulder.y - leftShoulder.y
    );

    let torsoHeight = shoulderWidth * 1.3;
    if (
        leftHip &&
        rightHip &&
        leftHip.visibility > 0.3 &&
        rightHip.visibility > 0.3
    ) {
        const hipCenterY = (leftHip.y + rightHip.y) / 2;
        torsoHeight = Math.abs(hipCenterY - shoulderCenter.y);
    }

    const shoulderAngle = Math.atan2(
        rightShoulder.y - leftShoulder.y,
        rightShoulder.x - leftShoulder.x
    );

    let garmentWidth = shoulderWidth * sizeMultiplier;
    let garmentHeight = garmentWidth * (garmentImg.height / garmentImg.width);

    ctx.save();
    ctx.translate(shoulderCenter.x, shoulderCenter.y);
    ctx.rotate(shoulderAngle);
    ctx.globalAlpha = 0.95;
    ctx.drawImage(
        garmentImg,
        -garmentWidth / 2,
        -garmentHeight * verticalOffset,
        garmentWidth,
        garmentHeight
    );
    ctx.restore();

    return true;
};

export default function ARTryOnPage({ productImageUrl: productImageUrlProp }) {
    const location = useLocation();
    const productImageUrl =
        productImageUrlProp || location.state?.productImageUrl || null;

    const videoRef = useRef(null);
    const canvasRef = useRef(null);
    const containerRef = useRef(null);
    const animRef = useRef(null);
    const poseRef = useRef(null);
    const lastPoseRef = useRef(null);

    const [poseOk, setPoseOk] = useState(false);
    const [garmentImage, setGarmentImage] = useState(null);
    const [logs, setLogs] = useState([]);
    const [flash, setFlash] = useState(false);
    const [isExtractingGarment, setIsExtractingGarment] = useState(false);
    const [cameraActive, setCameraActive] = useState(false);
    const [garmentSize, setGarmentSize] = useState(2.5);
    const [verticalPosition, setVerticalPosition] = useState(0.12);

    const log = useCallback((msg) => {
        console.log(msg);
        setLogs((prev) => [...prev.slice(-49), msg]);
    }, []);

    useEffect(() => {
        if (!productImageUrl) {
            log("⚠️ Продукт сүрөтү жок");
            return;
        }

        setIsExtractingGarment(true);
        const loadFallback = () => {
            log("📦 Кийим сүрөтү түздөн-түз жүктөлүүдө...");
            const img = new Image();
            img.crossOrigin = "Anonymous";
            img.onload = () => {
                log(`✅ Кийим жүктөлдү: ${img.width}x${img.height}`);
                createMaskedGarment(img).then((maskedImg) => {
                    setGarmentImage(maskedImg);
                    setIsExtractingGarment(false);
                    log("✅ Кийим кийип көрүүгө даяр");
                });
            };
            img.onerror = (err) => {
                log(`⚠️ Кийим жүктөлбөй калды: ${err}`);
                setIsExtractingGarment(false);
            };
            img.src = productImageUrl;
        };

        fetch(productImageUrl)
            .then((res) => {
                if (!res.ok) throw new Error(`HTTP ${res.status}`);
                return res.blob();
            })
            .then(async (blob) => {
                log("🔍 Vertex AIге жиберилүүдө...");
                const extracted = await extractGarmentWithVertexAI(blob);
                if (extracted) {
                    log("✅ Vertex AI кийимди ийгиликтүү алып чыкты");
                    setGarmentImage(extracted);
                    setIsExtractingGarment(false);
                } else {
                    log(
                        "⚠️ Vertex AI иштебей калды, резервдик вариант колдонулууда"
                    );
                    loadFallback();
                }
            })
            .catch((err) => {
                log(`⚠️ Ката: ${err.message}, резервдик вариант колдонулууда`);
                loadFallback();
            });
    }, [productImageUrl, log]);

    useEffect(() => {
        let destroyed = false;
        let stream = null;

        const init = async () => {
            try {
                log("🎥 Камерага уруксат суралууда...");

                stream = await navigator.mediaDevices.getUserMedia({
                    video: {
                        facingMode: "user",
                        width: { ideal: 1280 },
                        height: { ideal: 720 },
                    },
                });

                log("✅ Камерага уруксат берилди");

                if (videoRef.current) {
                    videoRef.current.srcObject = stream;
                    videoRef.current.onloadedmetadata = () => {
                        videoRef.current.play();
                        setCameraActive(true);
                    };
                }

                log("📥 MediaPipe Pose жүктөлүүдө...");
                if (!window.Pose) {
                    await new Promise((resolve, reject) => {
                        const script = document.createElement("script");
                        script.src =
                            "https://cdn.jsdelivr.net/npm/@mediapipe/pose/pose.js";
                        script.crossOrigin = "anonymous";
                        script.onload = resolve;
                        script.onerror = reject;
                        document.head.appendChild(script);
                    });
                }
                log("✅ MediaPipe жүктөлдү");

                const pose = new window.Pose({
                    locateFile: (file) =>
                        `https://cdn.jsdelivr.net/npm/@mediapipe/pose/${file}`,
                });

                pose.setOptions({
                    modelComplexity: 1,
                    smoothLandmarks: true,
                    enableSegmentation: false,
                    minDetectionConfidence: 0.5,
                    minTrackingConfidence: 0.5,
                });

                pose.onResults((results) => {
                    if (!destroyed) {
                        lastPoseRef.current = results;
                    }
                });

                await pose.initialize();
                poseRef.current = pose;

                const drawLoop = () => {
                    if (destroyed) return;

                    const canvas = canvasRef.current;
                    const video = videoRef.current;
                    const poseResults = lastPoseRef.current;

                    if (canvas && video && video.videoWidth > 0) {
                        canvas.width = video.videoWidth;
                        canvas.height = video.videoHeight;

                        const ctx = canvas.getContext("2d");

                        ctx.save();
                        ctx.scale(-1, 1);
                        ctx.drawImage(
                            video,
                            -canvas.width,
                            0,
                            canvas.width,
                            canvas.height
                        );
                        ctx.restore();

                        if (
                            poseResults &&
                            poseResults.poseLandmarks &&
                            garmentImage
                        ) {
                            const drawn = drawGarmentOnBody(
                                ctx,
                                garmentImage,
                                poseResults.poseLandmarks,
                                canvas.width,
                                canvas.height,
                                garmentSize,
                                verticalPosition
                            );
                            setPoseOk(drawn);
                        } else if (garmentImage) {
                            setPoseOk(false);
                            ctx.fillStyle = "rgba(0, 0, 0, 0.5)";
                            ctx.fillRect(0, 0, canvas.width, canvas.height);
                            ctx.fillStyle = "#63aaca";
                            ctx.font =
                                "20px 'Golos Text', 'Montserrat', monospace";
                            ctx.textAlign = "center";
                            ctx.fillText(
                                "🎯 Денеңизди кадрга коюңуз",
                                canvas.width / 2,
                                canvas.height / 2
                            );
                            ctx.font =
                                "14px 'Golos Text', 'Montserrat', monospace";
                            ctx.fillStyle = "#aaa";
                            ctx.fillText(
                                "Ийиндериңиз көрүнүп турганын текшериңиз",
                                canvas.width / 2,
                                canvas.height / 2 + 40
                            );
                        }
                    }

                    animRef.current = requestAnimationFrame(drawLoop);
                };

                drawLoop();

                const detectLoop = async () => {
                    if (destroyed) return;

                    if (
                        videoRef.current &&
                        videoRef.current.readyState >= 2 &&
                        poseRef.current
                    ) {
                        try {
                            await poseRef.current.send({
                                image: videoRef.current,
                            });
                        } catch (err) {}
                    }

                    requestAnimationFrame(detectLoop);
                };

                detectLoop();
            } catch (error) {
                console.error("Camera error:", error);
            }
        };

        init();

        return () => {
            destroyed = true;
            if (animRef.current) cancelAnimationFrame(animRef.current);
            if (poseRef.current) {
                try {
                    poseRef.current.close();
                } catch (err) {}
            }
            if (stream) {
                stream.getTracks().forEach((track) => track.stop());
            }
        };
    }, [garmentImage, garmentSize, verticalPosition, log]);

    const takeScreenshot = () => {
        if (!canvasRef.current) return;
        setFlash(true);
        setTimeout(() => setFlash(false), 300);

        const link = document.createElement("a");
        link.download = `virtual-tryon-${Date.now()}.png`;
        link.href = canvasRef.current.toDataURL("image/png");
        link.click();
        log("📸 Сүрөт сакталды");
    };

    const formatSizeValue = (value) => {
        return value.toFixed(1);
    };

    const formatVerticalValue = (value) => {
        return value.toFixed(2);
    };

    const badgeColor = poseOk
        ? "#63aaca"
        : cameraActive
          ? "#e2b93b"
          : "#6c757d";
    const statusText = poseOk
        ? "✓ КИЙИМ КИЙИЛДИ"
        : cameraActive
          ? "⚠️ ДЕНЕҢИЗДИ КОЮҢУЗ"
          : "⏳ КАМЕРА КОШУЛУУДА...";

    return (
        <div className={styles.container}>
            {isExtractingGarment && (
                <div className={styles.loadingOverlay}>
                    <div className={styles.loadingContent}>
                        <div className={styles.kyrgyzPattern} />
                        <Typography
                            variant="h2"
                            className={styles.loadingTitle}
                        >
                            🎨 КИЙИМ ДАЯРДАЛУУДА...
                        </Typography>
                        <Typography
                            variant="h6"
                            className={styles.loadingSubtitle}
                        >
                            AI кийимди иштеп жатат
                        </Typography>
                    </div>
                </div>
            )}

            <div className={styles.mainLayout}>
                <div ref={containerRef} className={styles.videoContainer}>
                    <video
                        ref={videoRef}
                        className={styles.hiddenVideo}
                        playsInline
                        muted
                        autoPlay
                    />
                    <canvas
                        ref={canvasRef}
                        className={styles.canvas}
                        style={{ borderColor: badgeColor }}
                        onClick={takeScreenshot}
                    />
                    {flash && <div className={styles.flashOverlay} />}
                    <Typography
                        variant="h5"
                        className={styles.statusBadge}
                        style={{ color: badgeColor }}
                    >
                        {statusText}
                    </Typography>
                    <Typography variant="h5" className={styles.screenshotHint}>
                        Сүрөткө тартуу үчүн басыңыз
                    </Typography>
                </div>

                <div className={styles.controlsPanel}>
                    <button
                        onClick={takeScreenshot}
                        className={styles.screenshotButton}
                    >
                        <Typography variant="h6" component="span">
                            📸 СҮРӨТКӨ ТАРТУУ
                        </Typography>
                    </button>

                    <div className={styles.controlCard}>
                        <div className={styles.cardHeader}>
                            <span className={styles.cardIcon}>📏</span>
                            <Typography
                                variant="h4"
                                className={styles.cardTitle}
                            >
                                Кийимдин өлчөмү
                            </Typography>
                        </div>
                        <div className={styles.sliderContainer}>
                            <Typography
                                variant="h6"
                                className={styles.sliderLabel}
                            >
                                Кичине
                            </Typography>
                            <input
                                type="range"
                                min="1.0"
                                max="5.0"
                                step="0.05"
                                value={garmentSize}
                                onChange={(e) =>
                                    setGarmentSize(parseFloat(e.target.value))
                                }
                                className={styles.slider}
                            />
                            <Typography
                                variant="h6"
                                className={styles.sliderLabel}
                            >
                                Чоң
                            </Typography>
                        </div>
                        <Typography variant="h4" className={styles.sliderValue}>
                            {formatSizeValue(garmentSize)}
                        </Typography>
                        <Typography variant="h6" className={styles.sliderHint}>
                            Ийин кеңдигинин өлчөмү
                        </Typography>
                    </div>

                    <div className={styles.controlCard}>
                        <div className={styles.cardHeader}>
                            <span className={styles.cardIcon}>📐</span>
                            <Typography
                                variant="h4"
                                className={styles.cardTitle}
                            >
                                Тик абал
                            </Typography>
                        </div>
                        <div className={styles.sliderContainer}>
                            <Typography
                                variant="h6"
                                className={styles.sliderLabel}
                            >
                                Төмөн
                            </Typography>
                            <input
                                type="range"
                                min="0"
                                max="0.4"
                                step="0.01"
                                value={verticalPosition}
                                onChange={(e) =>
                                    setVerticalPosition(
                                        parseFloat(e.target.value)
                                    )
                                }
                                className={styles.slider}
                            />
                            <Typography
                                variant="h6"
                                className={styles.sliderLabel}
                            >
                                Жогору
                            </Typography>
                        </div>
                        <Typography variant="h4" className={styles.sliderValue}>
                            {formatVerticalValue(verticalPosition)}
                        </Typography>
                        <Typography variant="h6" className={styles.sliderHint}>
                            Кийимдин бийиктигин тууралаңыз
                        </Typography>
                    </div>
                </div>
            </div>
        </div>
    );
}
