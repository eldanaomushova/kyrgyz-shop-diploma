import React, { useState, useEffect } from "react";
import { useAuth } from "../useAuth/useAuth";
import { Typography } from "../../../ui/Typography/Typography";
import { Button } from "../../../ui/Buttons/Button";
import styles from "./AuthModule.module.scss";
import Swal from "sweetalert2";
import { useNavigate } from "react-router-dom";
import { PATH } from "../../../utils/Constants/Constants";

export const SignupModule = () => {
    const [form, setForm] = useState({
        username: "",
        email: "",
        password: "",
        confirmPassword: "",
        firstName: "",
        lastName: "",
    });

    const [validationError, setValidationError] = useState("");
    const { loading, error, actions } = useAuth();
    const navigate = useNavigate();
    const handleChange = (e) => {
        const { name, value } = e.target;
        setForm((prev) => ({ ...prev, [name]: value }));
        if (validationError) setValidationError("");
    };

    const validatePassword = (pass) => {
        const regex = /^[A-Za-z0-9]{8,}$/;
        return regex.test(pass);
    };

    const handleSignup = async (e) => {
        e.preventDefault();
        setValidationError("");

        if (form.password !== form.confirmPassword) {
            setValidationError("Паролдор бири-бирине дал келбейт!");
            return;
        }

        if (!validatePassword(form.password)) {
            setValidationError(
                "Пароль кеминде 8 белгиден туруп, тамга жана сан камтышы керек!"
            );
            return;
        }

        const result = await actions.register(form);

        if (result?.success) {
            Swal.fire({
                title: "Кошулду!",
                text: "Каттоо ийгиликтүү болду",
                icon: "success",
                toast: true,
                position: "top-end",
                showConfirmButton: false,
                timer: 2000,
                timerProgressBar: true,
            });
            setTimeout(() => navigate("/signin"), 1500);
        }
    };
    useEffect(() => {
        if (actions.clearError) {
            actions.clearError();
        } else {
        }
    }, [actions]);

    return (
        <div className={styles.authWrapper}>
            <div className={styles.authContainer}>
                <Typography variant="h3">Аккаунтту түзүү</Typography>

                <form className={styles.form} onSubmit={handleSignup}>
                    <input
                        type="text"
                        name="username"
                        placeholder="Колдонуучу аты"
                        required
                        value={form.username}
                        onChange={handleChange}
                    />
                    <input
                        type="text"
                        name="firstName"
                        placeholder="Аты"
                        value={form.firstName}
                        onChange={handleChange}
                    />
                    <input
                        type="text"
                        name="lastName"
                        placeholder="Фамилия"
                        value={form.lastName}
                        onChange={handleChange}
                    />
                    <input
                        type="email"
                        name="email"
                        placeholder="Email"
                        required
                        value={form.email}
                        onChange={handleChange}
                    />
                    <input
                        type="password"
                        name="password"
                        placeholder="Пароль"
                        required
                        value={form.password}
                        onChange={handleChange}
                    />
                    <input
                        type="password"
                        name="confirmPassword"
                        placeholder="Паролду кайталаңыз"
                        required
                        value={form.confirmPassword}
                        onChange={handleChange}
                    />

                    {(validationError || error) && (
                        <Typography
                            variant="psmall"
                            className={styles.error}
                            style={{ color: "red" }}
                        >
                            {validationError || error}
                        </Typography>
                    )}

                    <Button
                        variant="blackButton"
                        disabled={loading}
                        text={loading ? "Жүктөлүүдө..." : "Катталуу"}
                        width="100%"
                        type="submit"
                    />
                    <div
                        className={styles.redirectLink}
                        style={{ marginTop: "20px", textAlign: "center" }}
                    >
                        <Typography variant="psmall">
                            Аккаунтуңуз барбы?{" "}
                            <span
                                onClick={() => navigate(PATH.signin)}
                                style={{
                                    fontWeight: "bold",
                                    cursor: "pointer",
                                    textDecoration: "underline",
                                }}
                            >
                                Кирүү
                            </span>
                        </Typography>
                    </div>
                </form>
            </div>
        </div>
    );
};
