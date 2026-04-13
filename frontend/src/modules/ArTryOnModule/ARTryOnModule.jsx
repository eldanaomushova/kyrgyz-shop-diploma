import React, { useEffect, useRef, useState, useCallback } from "react";
import { useLocation } from "react-router-dom";

async function extractGarmentWithVertexAI(imageFile, onLog) {
    try {
        onLog("🤖 Sending image to Vertex AI for garment extraction...");
        const formData = new FormData();
        formData.append("product_image", imageFile);
        const response = await fetch("/api/virtual-try-on/extract-garment/", {
            method: "POST",
            body: formData,
            headers: {
                ...(fetch.defaults?.headers?.common && {
                    "Content-Type": undefined,
                }),
            },
        });
        if (!response.ok) {
            const errorText = await response.text();
            onLog(`⚠️ Vertex AI error (${response.status}): ${errorText}`);
            return null;
        }

        const data = await response.json();

        if (data.success && data.image_url) {
            onLog("✅ Garment extracted by Vertex AI");
            return data.image_url;
        } else {
            onLog(`⚠️ Unexpected response format: ${JSON.stringify(data)}`);
            return null;
        }
    } catch (error) {
        onLog(`⚠️ Vertex AI error: ${error.message}`);
        console.error("Extraction error:", error);
        return null;
    }
}

function drawGarmentOnBody(ctx, garmentImg, landmarks, W, H) {
    if (!garmentImg || !landmarks) return;

    const getLandmark = (idx) => {
        const lm = landmarks[idx];
        return {
            x: (1 - lm.x) * W,
            y: lm.y * H,
            z: lm.z,
            visibility: lm.visibility || 1,
        };
    };

    const leftShoulder = getLandmark(11);
    const rightShoulder = getLandmark(12);
    const leftHip = getLandmark(23);
    const rightHip = getLandmark(24);
    const leftElbow = getLandmark(13);
    const rightElbow = getLandmark(14);
    const nose = getLandmark(0);

    if (leftShoulder.visibility < 0.5 || rightShoulder.visibility < 0.5) {
        console.warn("Poor landmark visibility");
        return;
    }

    const shoulderCenter = {
        x: (leftShoulder.x + rightShoulder.x) / 2,
        y: (leftShoulder.y + rightShoulder.y) / 2,
    };

    const shoulderWidth = Math.hypot(
        rightShoulder.x - leftShoulder.x,
        rightShoulder.y - leftShoulder.y
    );

    const torsoHeight = Math.abs(
        (leftHip.y + rightHip.y) / 2 - shoulderCenter.y
    );

    const shoulderAngle = Math.atan2(
        rightShoulder.y - leftShoulder.y,
        rightShoulder.x - leftShoulder.x
    );

    const shoulderZDiff = Math.abs(leftShoulder.z - rightShoulder.z);
    const isSideView = shoulderZDiff > 0.05;

    let garmentWidth = shoulderWidth * 1.4;
    let garmentHeight = garmentWidth * (garmentImg.height / garmentImg.width);

    const desiredHeight = torsoHeight * 0.9;
    if (garmentHeight > desiredHeight) {
        const ratio = desiredHeight / garmentHeight;
        garmentWidth *= ratio;
        garmentHeight = desiredHeight;
    }

    const perspectiveScale = isSideView ? 0.85 : 1.0;
    garmentWidth *= perspectiveScale;

    ctx.save();
    ctx.translate(shoulderCenter.x, shoulderCenter.y);
    ctx.rotate(shoulderAngle);
    const armRaised =
        leftElbow.y < leftShoulder.y - 50 ||
        rightElbow.y < rightShoulder.y - 50;
    if (armRaised) {
        ctx.transform(1, 0, 0.1, 1, 0, 0);
    }
    ctx.globalCompositeOperation = "source-over";
    ctx.globalAlpha = 0.95;

    ctx.shadowColor = "rgba(0, 0, 0, 0.3)";
    ctx.shadowBlur = 5;

    ctx.drawImage(
        garmentImg,
        -garmentWidth / 2,
        -garmentHeight * 0.1,
        garmentWidth,
        garmentHeight
    );

    ctx.shadowColor = "transparent";

    ctx.restore();
    if (window.DEBUG_MODE) {
        ctx.save();
        ctx.strokeStyle = "#00ff88";
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(leftShoulder.x, leftShoulder.y);
        ctx.lineTo(rightShoulder.x, rightShoulder.y);
        ctx.stroke();
        ctx.beginPath();
        ctx.moveTo(leftHip.x, leftHip.y);
        ctx.lineTo(rightHip.x, rightHip.y);
        ctx.stroke();

        ctx.restore();
    }
}

export default function ARTryOnPage({ productImageUrl: productImageUrlProp }) {
    const location = useLocation();
    const productImageUrl =
        productImageUrlProp || location.state?.productImageUrl || null;
    const videoRef = useRef(null);
    const canvasRef = useRef(null);
    const poseRef = useRef(null);
    const animRef = useRef(null);
    const frameCountRef = useRef(0);

    const [poseOk, setPoseOk] = useState(false);
    const [garmentImage, setGarmentImage] = useState(null);
    const [logs, setLogs] = useState([]);
    const [flash, setFlash] = useState(false);
    const [isExtractingGarment, setIsExtractingGarment] = useState(false);
    const [detectionQuality, setDetectionQuality] = useState(0);

    const log = useCallback((msg) => {
        console.log(msg);
        setLogs((prev) => [...prev.slice(-49), msg]);
    }, []);

    useEffect(() => {
        if (!productImageUrl) return;

        setIsExtractingGarment(true);
        fetch(productImageUrl)
            .then((res) => res.blob())
            .then(async (blob) => {
                const extracted = await extractGarmentWithVertexAI(blob, log);
                if (extracted) {
                    const img = new Image();
                    img.onload = () => {
                        setGarmentImage(img);
                        setIsExtractingGarment(false);
                        log("✅ Using Vertex AI extracted garment");
                    };
                    img.onerror = () => {
                        log("⚠️ Failed to load extracted garment image");
                        setIsExtractingGarment(false);
                    };
                    img.src = extracted;
                } else {
                    setIsExtractingGarment(false);
                    log("⚠️ Garment extraction returned nothing");
                }
            });
    }, [productImageUrl, log]);

    useEffect(() => {
        let destroyed = false;
        let stream = null;

        const init = async () => {
            try {
                const pose = new window.Pose({
                    locateFile: (file) =>
                        `https://cdn.jsdelivr.net/npm/@mediapipe/pose@0.5.1675469404/${file}`,
                });

                pose.setOptions({
                    modelComplexity: 1,
                    smoothLandmarks: true,
                    enableSegmentation: false,
                    smoothSegmentation: false,
                    minDetectionConfidence: 0.3,
                    minTrackingConfidence: 0.3,
                });

                pose.onResults((results) => {
                    if (destroyed) return;

                    const canvas = canvasRef.current;
                    const video = videoRef.current;
                    if (!canvas || !video || !video.videoWidth) return;

                    canvas.width = video.videoWidth;
                    canvas.height = video.videoHeight;

                    const ctx = canvas.getContext("2d");

                    ctx.clearRect(0, 0, canvas.width, canvas.height);
                    ctx.drawImage(
                        results.image,
                        0,
                        0,
                        canvas.width,
                        canvas.height
                    );

                    if (results.poseLandmarks && garmentImage) {
                        const shoulders = [
                            results.poseLandmarks[11],
                            results.poseLandmarks[12],
                        ];
                        const avgVisibility =
                            (shoulders[0].visibility +
                                shoulders[1].visibility) /
                            2;

                        setDetectionQuality(avgVisibility);
                        setPoseOk(avgVisibility > 0.6);

                        drawGarmentOnBody(
                            ctx,
                            garmentImage,
                            results.poseLandmarks,
                            canvas.width,
                            canvas.height
                        );
                    } else {
                        setPoseOk(false);
                        setDetectionQuality(0);

                        ctx.fillStyle = "rgba(0,0,0,0.7)";
                        ctx.fillRect(0, 0, canvas.width, canvas.height);
                        ctx.fillStyle = "#00ff88";
                        ctx.font = "20px monospace";
                        ctx.textAlign = "center";
                        ctx.fillText(
                            "Position your full body in frame",
                            canvas.width / 2,
                            canvas.height / 2
                        );
                    }
                });

                poseRef.current = pose;

                stream = await navigator.mediaDevices.getUserMedia({
                    video: {
                        facingMode: "user",
                        width: { ideal: 1280 },
                        height: { ideal: 720 },
                    },
                });

                videoRef.current.srcObject = stream;
                await videoRef.current.play();

                log("✅ Camera started successfully");

                const process = async () => {
                    if (destroyed) return;

                    frameCountRef.current++;
                    if (
                        frameCountRef.current % 2 === 0 &&
                        videoRef.current?.readyState >= 2
                    ) {
                        await pose.send({ image: videoRef.current });
                    }

                    animRef.current = requestAnimationFrame(process);
                };

                process();
            } catch (error) {
                log(`⚠️ Camera error: ${error.message}`);
                console.error("Camera initialization error:", error);
            }
        };

        init();

        return () => {
            destroyed = true;
            if (animRef.current) cancelAnimationFrame(animRef.current);
            if (poseRef.current) poseRef.current.close();
            if (stream) stream.getTracks().forEach((track) => track.stop());
            if (videoRef.current?.srcObject) {
                videoRef.current.srcObject
                    .getTracks()
                    .forEach((track) => track.stop());
            }
        };
    }, [garmentImage, log]);

    const takeScreenshot = () => {
        if (!canvasRef.current) return;
        setFlash(true);
        setTimeout(() => setFlash(false), 300);

        const link = document.createElement("a");
        link.download = `virtual-tryon-${Date.now()}.png`;
        link.href = canvasRef.current.toDataURL("image/png");
        link.click();

        log("📸 Screenshot saved");
    };

    const badgeColor = poseOk
        ? "#00ff88"
        : detectionQuality > 0.3
          ? "#ffaa00"
          : "#555";
    const statusText = poseOk
        ? "POSE DETECTED ✓"
        : detectionQuality > 0.3
          ? "POOR POSE QUALITY"
          : "NO POSE DETECTED";

    return (
        <div
            style={{
                minHeight: "100vh",
                background: "#09090d",
                color: "#ddd",
                fontFamily: "monospace",
                padding: 20,
            }}
        >
            {isExtractingGarment && (
                <div
                    style={{
                        position: "fixed",
                        inset: 0,
                        background: "#09090d",
                        zIndex: 100,
                        display: "flex",
                        flexDirection: "column",
                        alignItems: "center",
                        justifyContent: "center",
                    }}
                >
                    <div style={{ textAlign: "center" }}>
                        <h2 style={{ color: "#00ff88", marginBottom: 20 }}>
                            🤖 PROCESSING GARMENT...
                        </h2>
                        <div style={{ color: "#888" }}>
                            Using AI to extract clothing
                        </div>
                    </div>
                </div>
            )}

            <div
                style={{
                    display: "flex",
                    gap: 20,
                    flexWrap: "wrap",
                    maxWidth: 1400,
                    margin: "0 auto",
                }}
            >
                <div style={{ position: "relative", flex: 2, minWidth: 300 }}>
                    <video
                        ref={videoRef}
                        style={{ display: "none" }}
                        playsInline
                        muted
                        autoPlay
                    />
                    <canvas
                        ref={canvasRef}
                        style={{
                            width: "100%",
                            borderRadius: 10,
                            border: `2px solid ${badgeColor}`,
                            transform: "scaleX(-1)",
                            boxShadow: "0 4px 20px rgba(0,0,0,0.5)",
                        }}
                    />
                    {flash && (
                        <div
                            style={{
                                position: "absolute",
                                inset: 0,
                                background: "white",
                                opacity: 0.7,
                                borderRadius: 10,
                                pointerEvents: "none",
                            }}
                        />
                    )}

                    <div
                        style={{
                            position: "absolute",
                            bottom: 10,
                            left: 10,
                            background: "rgba(0,0,0,0.7)",
                            padding: "5px 10px",
                            borderRadius: 5,
                            fontSize: 12,
                            color: badgeColor,
                            fontFamily: "monospace",
                        }}
                    >
                        {statusText}
                    </div>
                </div>

                <div
                    style={{
                        flex: 1,
                        minWidth: 250,
                        display: "flex",
                        flexDirection: "column",
                        gap: 15,
                    }}
                >
                    <button
                        onClick={takeScreenshot}
                        style={{
                            background: "#00ff88",
                            color: "#09090d",
                            padding: "15px 20px",
                            borderRadius: 8,
                            fontWeight: "bold",
                            border: "none",
                            cursor: "pointer",
                            fontSize: 16,
                            transition: "transform 0.2s",
                        }}
                        onMouseEnter={(e) =>
                            (e.target.style.transform = "scale(1.02)")
                        }
                        onMouseLeave={(e) =>
                            (e.target.style.transform = "scale(1)")
                        }
                    >
                        📸 TAKE SCREENSHOT
                    </button>

                    <div
                        style={{
                            background: "#1a1a1a",
                            padding: 15,
                            borderRadius: 8,
                        }}
                    >
                        <h4 style={{ margin: "0 0 10px 0", color: "#00ff88" }}>
                            Tips for best results:
                        </h4>
                        <ul
                            style={{
                                margin: 0,
                                paddingLeft: 20,
                                fontSize: 12,
                                color: "#aaa",
                            }}
                        >
                            <li>Stand facing the camera directly</li>
                            <li>Keep arms slightly away from body</li>
                            <li>Ensure good lighting</li>
                            <li>Show full upper body in frame</li>
                            <li>Stand against plain background</li>
                        </ul>
                    </div>

                    {logs.length > 0 && (
                        <div
                            style={{
                                background: "#000",
                                padding: 10,
                                fontSize: 10,
                                maxHeight: 200,
                                overflow: "auto",
                                borderRadius: 5,
                                fontFamily: "monospace",
                            }}
                        >
                            {logs.map((msg, i) => (
                                <div key={i} style={{ marginBottom: 4 }}>
                                    › {msg}
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
