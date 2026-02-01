import React, { useState } from "react";
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
        firstName: "",
        lastName: "",
    });
    const { loading, error, actions } = useAuth();
    const navigate = useNavigate();

    const handleSignup = async (e) => {
        e.preventDefault();
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
                background: "#fff",
                color: "#333",
            });
            setTimeout(() => {
                navigate("/signin");
            }, 1500);
        }
    };

    return (
        <div className={styles.authWrapper}>
            <div className={styles.authContainer}>
                <Typography variant="h2">Аккаунтту түзүү</Typography>

                <form className={styles.form} onSubmit={handleSignup}>
                    <input
                        type="text"
                        placeholder="Колдонуучу аты"
                        required
                        onChange={(e) =>
                            setForm({ ...form, username: e.target.value })
                        }
                    />
                    <input
                        type="text"
                        placeholder="Аты"
                        onChange={(e) =>
                            setForm({ ...form, firstName: e.target.value })
                        }
                    />
                    <input
                        type="text"
                        placeholder="Фамилия"
                        onChange={(e) =>
                            setForm({ ...form, lastName: e.target.value })
                        }
                    />
                    <input
                        type="email"
                        placeholder="Email"
                        required
                        onChange={(e) =>
                            setForm({ ...form, email: e.target.value })
                        }
                    />
                    <input
                        type="password"
                        placeholder="Пароль"
                        required
                        onChange={(e) =>
                            setForm({ ...form, password: e.target.value })
                        }
                    />

                    {error && (
                        <Typography variant="psmall" className={styles.error}>
                            {error}
                        </Typography>
                    )}

                    <Button
                        variant="blackButton"
                        disabled={loading}
                        text={loading ? "Жүктөлүүдө..." : "Катталуу"}
                        width="100%"
                    />
                </form>
            </div>
        </div>
    );
};
