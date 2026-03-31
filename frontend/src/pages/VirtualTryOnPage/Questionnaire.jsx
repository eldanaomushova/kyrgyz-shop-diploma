import React, { useState } from "react";
import axios from "axios";
import "./Questionnaire.css";

const Questionnaire = ({ onComplete }) => {
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
            question: "What is your gender?",
            type: "single",
            options: ["Аялдар", "Эркек"], // Women, Men in Kyrgyz
        },
        {
            id: "occasion",
            question: "What occasion are you shopping for?",
            type: "single",
            options: ["Casual", "Formal", "Party", "Work"],
        },
        {
            id: "body_type",
            question: "What is your body type?",
            type: "single",
            options: ["Slim", "Athletic", "Curvy", "Plus Size"],
        },
        {
            id: "preferred_colors",
            question: "What are your preferred colors? (Select multiple)",
            type: "multiple",
            options: [
                "Black",
                "White",
                "Blue",
                "Red",
                "Green",
                "Yellow",
                "Pink",
                "Purple",
                "Brown",
                "Gray",
            ],
        },
        {
            id: "budget",
            question: "What is your budget range?",
            type: "single",
            options: [
                "Low (under 2000)",
                "Medium (2000-5000)",
                "High (over 5000)",
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
            // Submit questionnaire
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
                budget: answers.budget.toLowerCase().split(" ")[0], // Extract 'low', 'medium', 'high'
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
        <div className="questionnaire">
            <div className="questionnaire-header">
                <h2>Find Your Perfect Style</h2>
                <div className="progress-bar">
                    <div
                        className="progress-fill"
                        style={{
                            width: `${((step + 1) / questions.length) * 100}%`,
                        }}
                    ></div>
                </div>
                <span className="step-counter">
                    Question {step + 1} of {questions.length}
                </span>
            </div>

            <div className="question-container">
                <h3>{currentQuestion.question}</h3>

                <div className="options-container">
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
                                className={`option-button ${isSelected ? "selected" : ""}`}
                                onClick={() =>
                                    handleAnswer(currentQuestion.id, option)
                                }
                            >
                                {option}
                                {currentQuestion.type === "multiple" &&
                                    isSelected && (
                                        <span className="checkmark">✓</span>
                                    )}
                            </button>
                        );
                    })}
                </div>
            </div>

            <div className="navigation-buttons">
                {step > 0 && (
                    <button className="nav-button prev" onClick={handlePrev}>
                        Previous
                    </button>
                )}

                <button
                    className="nav-button next"
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

export default Questionnaire;
