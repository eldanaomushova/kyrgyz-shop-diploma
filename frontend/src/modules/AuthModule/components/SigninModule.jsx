import React, { useState } from "react";
import { useAuth } from "../useAuth/useAuth";

export const SigninModule = () => {
    const [form, setForm] = useState({ username: "", password: "" });
    const { loading, error, actions } = useAuth();

    const handleSubmit = (e) => {
        e.preventDefault();
        actions.login(form);
    };

    return (
        <div className="auth-container">
            <h2>Sign In</h2>
            <form onSubmit={handleSubmit}>
                <input
                    type="text"
                    placeholder="Username"
                    onChange={(e) =>
                        setForm({ ...form, username: e.target.value })
                    }
                />
                <input
                    type="password"
                    placeholder="Password"
                    onChange={(e) =>
                        setForm({ ...form, password: e.target.value })
                    }
                />
                <button disabled={loading}>
                    {loading ? "Loading..." : "Login"}
                </button>
            </form>
            {error && <p style={{ color: "red" }}>{error}</p>}
        </div>
    );
};
