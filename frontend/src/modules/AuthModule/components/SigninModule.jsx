import React, { useState } from "react";
import { useAuth } from "../useAuth/useAuth";
import { useNavigate } from "react-router-dom";
import { Typography } from "../../../ui/Typography/Typography";
import { Button } from "../../../ui/Buttons/Button";
import Swal from "sweetalert2";
import styles from "./AuthModule.module.scss";
import { PATH } from "../../../utils/Constants/Constants";

export const SigninModule = () => {
    const [form, setForm] = useState({ username: "", password: "" });
    const { loading, error, actions } = useAuth();
    const navigate = useNavigate();

    const handleChange = (e) => {
        const { name, value } = e.target;
        setForm((prev) => ({ ...prev, [name]: value }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        // Пытаемся выполнить вход
        const result = await actions.login(form);

        // 1. Проверяем, успешен ли вход (наличие токена)
        if (localStorage.getItem("token")) {
            Swal.fire({
                title: "Ийгиликтүү!",
                text: "Сиз системага кирдиңиз",
                icon: "success",
                confirmButtonColor: "#000",
                timer: 2000,
            });
            navigate("/");
            return;
        }

        if (!localStorage.getItem("token")) {
            Swal.fire({
                title: "Аккаунт табылган жок",
                text: "Мындай колдонуучу катталган эмес. Катталууну каалайсызбы?",
                icon: "question",
                showCancelButton: true,
                confirmButtonText: "Катталуу",
                cancelButtonText: "Кайра аракет кылуу",
                confirmButtonColor: "#000",
                cancelButtonColor: "#d33",
            }).then((result) => {
                if (result.isConfirmed) {
                    navigate(PATH.signup);
                }
            });
        }
    };

    return (
        <div className={styles.authWrapper}>
            <div className={styles.authContainer}>
                <Typography variant="h3">Кирүү</Typography>

                <form className={styles.form} onSubmit={handleSubmit}>
                    <div className={styles.inputGroup}>
                        <input
                            type="text"
                            name="username"
                            placeholder="Колдонуучу аты"
                            required
                            value={form.username}
                            onChange={handleChange}
                            autoComplete="username"
                        />
                    </div>

                    <div className={styles.inputGroup}>
                        <input
                            type="password"
                            name="password"
                            placeholder="Пароль"
                            required
                            value={form.password}
                            onChange={handleChange}
                            autoComplete="current-password"
                        />
                    </div>

                    {error && <div className={styles.error}>{error}</div>}

                    <Button
                        variant="blackButton"
                        type="submit"
                        disabled={loading}
                        text={loading ? "Жүктөлүүдө..." : "Кирүү"}
                        width="100%"
                    />
                </form>
            </div>
        </div>
    );
};
