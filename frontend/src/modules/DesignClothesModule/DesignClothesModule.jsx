import React, { useRef, useState, useEffect, useCallback } from "react";
import styles from "./DesignClothesModule.module.scss";
import { Typography } from "../../ui/Typography/Typography";
import {
    Pencil,
    Eraser,
    Trash2,
    Download,
    Send,
    Wand2,
    Palette,
    Minus,
    Plus,
    RotateCcw,
} from "lucide-react";
import { requester } from "../../utils/Requester/Requester";

const TOOLS = [
    { id: "pen", icon: Pencil, label: "Калем" },
    { id: "eraser", icon: Eraser, label: "Өчүргүч" },
];

const COLORS = [
    "#1a1a2e",
    "#16213e",
    "#0f3460",
    "#533483",
    "#e94560",
    "#f5a623",
    "#7ed321",
    "#4a90d9",
    "#ffffff",
    "#b0b0b0",
    "#8b4513",
    "#ff69b4",
];

const BRUSH_SIZES = [2, 4, 8, 14, 22];

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

async function analyzeSketchWithGemini(canvasElement) {
    const blob = await new Promise((resolve) =>
        canvasElement.toBlob(resolve, "image/png")
    );
    if (!blob) throw new Error("Canvas rendering failed");
    const formData = new FormData();
    formData.append("cloth_image", blob, "sketch.png");
    const response = await requester.post("/api/generate-design/", formData, {
        headers: {
            "X-CSRFToken": getCookie("csrftoken"),
            "Content-Type": "multipart/form-data",
        },
    });
    return response.data;
}

export const DesignClothesModule = () => {
    const canvasRef = useRef(null);
    const lastPos = useRef(null);

    const [isDrawing, setIsDrawing] = useState(false);
    const [tool, setTool] = useState("pen");
    const [color, setColor] = useState("#1a1a2e");
    const [brushIndex, setBrushIndex] = useState(1);
    const [history, setHistory] = useState([]);
    const [analysisResult, setAnalysisResult] = useState(null);
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [submitStatus, setSubmitStatus] = useState(null);

    useEffect(() => {
        const canvas = canvasRef.current;
        const ctx = canvas.getContext("2d");
        ctx.fillStyle = "#fafaf8";
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        setHistory([canvas.toDataURL()]);
    }, []);

    const saveHistory = useCallback(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;
        setHistory((h) => [...h.slice(-20), canvas.toDataURL()]);
    }, []);

    const getPos = (e, canvas) => {
        const rect = canvas.getBoundingClientRect();
        const scaleX = canvas.width / rect.width;
        const scaleY = canvas.height / rect.height;
        const src = e.touches ? e.touches[0] : e;
        return {
            x: (src.clientX - rect.left) * scaleX,
            y: (src.clientY - rect.top) * scaleY,
        };
    };

    const startDraw = (e) => {
        e.preventDefault();
        const canvas = canvasRef.current;
        const ctx = canvas.getContext("2d");
        const pos = getPos(e, canvas);
        lastPos.current = pos;
        setIsDrawing(true);
        ctx.globalCompositeOperation =
            tool === "eraser" ? "destination-out" : "source-over";
        ctx.beginPath();
        ctx.arc(pos.x, pos.y, BRUSH_SIZES[brushIndex] / 2, 0, Math.PI * 2);
        ctx.fillStyle = color;
        ctx.fill();
    };

    const draw = (e) => {
        if (!isDrawing) return;
        e.preventDefault();
        const canvas = canvasRef.current;
        const ctx = canvas.getContext("2d");
        const pos = getPos(e, canvas);
        ctx.globalCompositeOperation =
            tool === "eraser" ? "destination-out" : "source-over";
        ctx.lineWidth = BRUSH_SIZES[brushIndex];
        ctx.lineCap = "round";
        ctx.lineJoin = "round";
        ctx.strokeStyle = color;
        ctx.beginPath();
        ctx.moveTo(lastPos.current.x, lastPos.current.y);
        ctx.lineTo(pos.x, pos.y);
        ctx.stroke();
        lastPos.current = pos;
    };

    const endDraw = () => {
        if (isDrawing) {
            setIsDrawing(false);
            saveHistory();
        }
    };

    const undo = () => {
        if (history.length < 2) return;
        const prev = history[history.length - 2];
        const canvas = canvasRef.current;
        const ctx = canvas.getContext("2d");
        const img = new Image();
        img.onload = () => {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.drawImage(img, 0, 0);
        };
        img.src = prev;
        setHistory((h) => h.slice(0, -1));
    };

    const clearCanvas = () => {
        const canvas = canvasRef.current;
        const ctx = canvas.getContext("2d");
        ctx.fillStyle = "#fafaf8";
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        setAnalysisResult(null);
        setSubmitStatus(null);
        saveHistory();
    };

    const downloadSketch = () => {
        const canvas = canvasRef.current;
        const link = document.createElement("a");
        link.download = "my-cloth-design.png";
        link.href = canvas.toDataURL();
        link.click();
    };

    const analyzeWithAI = async () => {
        setIsAnalyzing(true);
        setAnalysisResult(null);
        setSubmitStatus(null);
        try {
            const result = await analyzeSketchWithGemini(canvasRef.current);
            setAnalysisResult(result);
        } catch (error) {
            setAnalysisResult({
                error: "AI анализинде ката кетти. Кайра аракет кылыңыз.",
            });
        } finally {
            setIsAnalyzing(false);
        }
    };

    const submitToBackend = async () => {
        setIsSubmitting(true);
        setSubmitStatus(null);
        const abortController = new AbortController();
        try {
            const canvas = canvasRef.current;
            const blob = await new Promise((res) =>
                canvas.toBlob(res, "image/png")
            );
            const formData = new FormData();
            formData.append("cloth_image", blob, "design.png");
            if (analysisResult?.imagePrompt) {
                formData.append("prompt", analysisResult.imagePrompt);
            }
            await requester.post(
                "/api/virtual-try-on/image-try-on/",
                formData,
                {
                    headers: {
                        "X-CSRFToken": getCookie("csrftoken"),
                        "Content-Type": "multipart/form-data",
                    },
                    timeout: 55000,
                    signal: abortController.signal,
                }
            );
            setSubmitStatus("success");
        } catch {
            setSubmitStatus("error");
        } finally {
            setIsSubmitting(false);
        }
    };

    const canSubmit =
        analysisResult &&
        !analysisResult.error &&
        !isAnalyzing &&
        !isSubmitting;

    return (
        <main className={styles.wrapper}>
            <section className={styles.container}>
                <header className={styles.pageHeader}>
                    <div className={styles.iconCircle}>
                        <Pencil size={24} />
                    </div>
                    <div>
                        <Typography variant="h1" className={styles.title}>
                            Кийимди дизайндоо
                        </Typography>
                        <Typography variant="p" className={styles.subtitle}>
                            Өзүңүздүн уникалдуу стилиңизди жаратыңыз
                        </Typography>
                    </div>
                </header>

                <div className={styles.editorLayout}>
                    {/* Toolbar */}
                    <aside className={styles.toolbar}>
                        <div className={styles.toolGroup}>
                            <span className={styles.toolLabel}>Куралдар</span>
                            {TOOLS.map(({ id, icon: Icon, label }) => (
                                <button
                                    key={id}
                                    title={label}
                                    onClick={() => setTool(id)}
                                    className={`${styles.toolBtn} ${tool === id ? styles.toolBtnActive : ""}`}
                                >
                                    <Icon size={17} />
                                    <span>{label}</span>
                                </button>
                            ))}
                        </div>

                        <div className={styles.toolGroup}>
                            <span className={styles.toolLabel}>Өлчөм</span>
                            <div className={styles.sizeRow}>
                                <button
                                    className={styles.sizeBtn}
                                    onClick={() =>
                                        setBrushIndex((i) => Math.max(0, i - 1))
                                    }
                                >
                                    <Minus size={13} />
                                </button>
                                <span className={styles.sizeDisplay}>
                                    {BRUSH_SIZES[brushIndex]}px
                                </span>
                                <button
                                    className={styles.sizeBtn}
                                    onClick={() =>
                                        setBrushIndex((i) =>
                                            Math.min(
                                                BRUSH_SIZES.length - 1,
                                                i + 1
                                            )
                                        )
                                    }
                                >
                                    <Plus size={13} />
                                </button>
                            </div>
                            {/* sizeDot uses inline style only for dynamic width/height/color — this is valid */}
                            <div className={styles.sizePreview}>
                                <div
                                    className={styles.sizeDot}
                                    style={{
                                        width: BRUSH_SIZES[brushIndex],
                                        height: BRUSH_SIZES[brushIndex],
                                        background: color,
                                    }}
                                />
                            </div>
                        </div>

                        <div className={styles.toolGroup}>
                            <span className={styles.toolLabel}>Түс</span>
                            <div className={styles.colorGrid}>
                                {COLORS.map((c) => (
                                    <button
                                        key={c}
                                        onClick={() => setColor(c)}
                                        className={`${styles.colorBtn} ${color === c ? styles.colorBtnActive : ""}`}
                                        style={{ background: c }}
                                        title={c}
                                    />
                                ))}
                            </div>
                            <div className={styles.customColorRow}>
                                <Palette size={13} />
                                <input
                                    type="color"
                                    value={color}
                                    onChange={(e) => setColor(e.target.value)}
                                    className={styles.colorPicker}
                                    title="Өзгөчө түс"
                                />
                                <span className={styles.colorHex}>{color}</span>
                            </div>
                        </div>

                        <div className={styles.toolGroup}>
                            <span className={styles.toolLabel}>Аракеттер</span>
                            <button className={styles.actionBtn} onClick={undo}>
                                <RotateCcw size={14} /> Артка
                            </button>
                            <button
                                className={styles.actionBtn}
                                onClick={clearCanvas}
                            >
                                <Trash2 size={14} /> Тазалоо
                            </button>
                            <button
                                className={styles.actionBtn}
                                onClick={downloadSketch}
                            >
                                <Download size={14} /> Жүктөө
                            </button>
                        </div>
                    </aside>

                    {/* Canvas area */}
                    <div className={styles.canvasArea}>
                        <canvas
                            ref={canvasRef}
                            width={700}
                            height={520}
                            className={`${styles.canvas} ${tool === "eraser" ? styles.cursorEraser : styles.cursorPen}`}
                            onMouseDown={startDraw}
                            onMouseMove={draw}
                            onMouseUp={endDraw}
                            onMouseLeave={endDraw}
                            onTouchStart={startDraw}
                            onTouchMove={draw}
                            onTouchEnd={endDraw}
                        />

                        <div className={styles.submitRow}>
                            <button
                                className={`${styles.primaryBtn} ${styles.btnAI}`}
                                onClick={analyzeWithAI}
                                disabled={isAnalyzing || isSubmitting}
                            >
                                <Wand2 size={15} />
                                {isAnalyzing
                                    ? "Анализдөө..."
                                    : "AI менен анализдөө"}
                            </button>
                            <button
                                className={`${styles.primaryBtn} ${styles.btnSend}`}
                                onClick={submitToBackend}
                                disabled={!canSubmit}
                            >
                                <Send size={15} />
                                {isSubmitting
                                    ? "Жөнөтүлүүдө..."
                                    : "Серверге жөнөтүү"}
                            </button>
                        </div>

                        {submitStatus === "success" && (
                            <div
                                className={`${styles.statusBanner} ${styles.statusSuccess}`}
                            >
                                ✅ Дизайн ийгиликтүү жөнөтүлдү!
                            </div>
                        )}
                        {submitStatus === "error" && (
                            <div
                                className={`${styles.statusBanner} ${styles.statusError}`}
                            >
                                ❌ Жөнөтүүдө ката кетти. Кайра аракет кылыңыз.
                            </div>
                        )}
                    </div>

                    {/* AI result panel */}
                    {(isAnalyzing || analysisResult) && (
                        <aside className={styles.resultPanel}>
                            <h3 className={styles.resultTitle}>
                                <Wand2 size={14} /> AI Анализи
                            </h3>
                            {isAnalyzing && (
                                <div className={styles.loadingDots}>
                                    <span />
                                    <span />
                                    <span />
                                </div>
                            )}
                            {!isAnalyzing && analysisResult?.error && (
                                <p className={styles.resultError}>
                                    {analysisResult.error}
                                </p>
                            )}
                            {!isAnalyzing &&
                                analysisResult &&
                                !analysisResult.error && (
                                    <>
                                        <span className={styles.garmentChip}>
                                            {analysisResult.garmentType}
                                        </span>
                                        <p className={styles.resultDesc}>
                                            {analysisResult.description}
                                        </p>
                                        <div className={styles.promptBox}>
                                            <span
                                                className={styles.promptLabel}
                                            >
                                                Image Prompt
                                            </span>
                                            <p className={styles.promptText}>
                                                {analysisResult.imagePrompt}
                                            </p>
                                        </div>
                                    </>
                                )}
                        </aside>
                    )}
                </div>
            </section>
        </main>
    );
};
