import React, { useState } from "react";
import { useAuth } from "../useAuth/useAuth";
import { useNavigate } from "react-router-dom";
import { Typography } from "../../../ui/Typography/Typography";
import { Button } from "../../../ui/Buttons/Button";
import Swal from "sweetalert2";
import styles from "./AuthModule.module.scss";

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

        // Use the credentials from local state
        await actions.login(form);

        // Check if login was successful (Zustand will have set the user)
        if (localStorage.getItem("token")) {
            Swal.fire({
                title: "Ийгиликтүү!",
                text: "Сиз системага кирдиңиз",
                icon: "success",
                confirmButtonColor: "#000",
                timer: 2000,
            });
            navigate("/");
        }
    };

    return (
        <div className={styles.authWrapper}>
            <div className={styles.authContainer}>
                <Typography variant="h2">Кирүү</Typography>

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
