import React, { useState } from "react";
import axios from "axios";
import styles from "./QuestionaryModule.module.scss";

const QuestionaryModule = ({ onComplete }) => {
    const [step, setStep] = useState(0);
    const [answers, setAnswers] = useState({
        gender: "",
        occasion: "",
        body_type: "",
        preferred_colors: [],
        budget: "",
    });

    const questions = [
        {
            id: "gender",
            question: "Сиздин жынысыңыз кандай?",
            type: "single",
            options: ["Аялдар", "Эркек"],
        },
        {
            id: "occasion",
            question:
                "Сиз кандай иш-чарага (майрамга) карата соода кылып жатасыз?",
            type: "single",
            options: ["Күнүмдүк", "Расмий", "Кечки", "Жумуш"],
        },
        {
            id: "body_type",
            question: "Сиздин дене түрүңүз кандай?",
            type: "single",
            options: ["Арык", "Спорттук", "Толукча", "Чоң өлчөмдөгү"],
        },
        {
            id: "preferred_colors",
            question:
                "Сиздин предпочиттелген түстериниз кандай? (Көбүркө санап коюнуз)",
            type: "multiple",
            options: [
                "Кара",
                "Ак",
                "Көк",
                "Кызыл",
                "Жашыл",
                "Сары",
                "Кызгылт",
                "Сыя",
                "Күрөң",
                "Боз",
            ],
        },
        {
            id: "budget",
            question: "Сиздин бюджет диапазоныңыз кандай?",
            type: "single",
            options: [
                "Кичине (2000 дан аз)",
                "Орточо (2000-5000)",
                "Жогору (5000 дан ашык)",
            ],
        },
    ];

    const handleAnswer = (questionId, answer) => {
        if (questions[step].type === "multiple") {
            const currentAnswers = answers[questionId] || [];
            const newAnswers = currentAnswers.includes(answer)
                ? currentAnswers.filter((a) => a !== answer)
                : [...currentAnswers, answer];

            setAnswers((prev) => ({
                ...prev,
                [questionId]: newAnswers,
            }));
        } else {
            setAnswers((prev) => ({
                ...prev,
                [questionId]: answer,
            }));
        }
    };

    const handleNext = () => {
        if (step < questions.length - 1) {
            setStep(step + 1);
        } else {
            submitQuestionnaire();
        }
    };

    const handlePrev = () => {
        if (step > 0) {
            setStep(step - 1);
        }
    };

    const submitQuestionnaire = async () => {
        try {
            const response = await axios.post("/api/questionnaire/", {
                gender: answers.gender,
                occasion: answers.occasion.toLowerCase(),
                body_type: answers.body_type.toLowerCase().replace(" ", "_"),
                preferred_colors: answers.preferred_colors,
                budget:
                    answers.budget === "Кичине (2000 дан аз)"
                        ? "low"
                        : answers.budget === "Орточо (2000-5000)"
                          ? "medium"
                          : "high",
            });

            onComplete(response.data);
        } catch (error) {
            console.error("Error submitting questionnaire:", error);
            alert("Error processing your answers. Please try again.");
        }
    };

    const currentQuestion = questions[step];
    const isAnswered =
        questions[step].type === "multiple"
            ? (answers[currentQuestion.id] || []).length > 0
            : answers[currentQuestion.id] !== "";

    return (
        <div className={styles.questionnaire}>
            <div className={styles.header}>
                <h2>Find Your Perfect Style</h2>
                <div className={styles.progressBar}>
                    <div
                        className={styles.progressFill}
                        style={{
                            width: `${((step + 1) / questions.length) * 100}%`,
                        }}
                    ></div>
                </div>
                <span className={styles.stepCounter}>
                    Question {step + 1} of {questions.length}
                </span>
            </div>

            <div className={styles.questionContainer}>
                <h3>{currentQuestion.question}</h3>

                <div className={styles.optionsContainer}>
                    {currentQuestion.options.map((option, index) => {
                        const isSelected =
                            currentQuestion.type === "multiple"
                                ? (answers[currentQuestion.id] || []).includes(
                                      option
                                  )
                                : answers[currentQuestion.id] === option;

                        return (
                            <button
                                key={index}
                                className={`${styles.optionButton} ${isSelected ? styles.selected : ""}`}
                                onClick={() =>
                                    handleAnswer(currentQuestion.id, option)
                                }
                            >
                                {option}
                                {currentQuestion.type === "multiple" &&
                                    isSelected && (
                                        <span className={styles.checkmark}>
                                            ✓
                                        </span>
                                    )}
                            </button>
                        );
                    })}
                </div>
            </div>

            <div className={styles.navigationButtons}>
                {step > 0 && (
                    <button
                        className={`${styles.navButton} ${styles.prev}`}
                        onClick={handlePrev}
                    >
                        Previous
                    </button>
                )}
                <button
                    className={`${styles.navButton} ${styles.next}`}
                    onClick={handleNext}
                    disabled={!isAnswered}
                >
                    {step === questions.length - 1
                        ? "Get Recommendations"
                        : "Next"}
                </button>
            </div>
        </div>
    );
};

export default QuestionaryModule;
