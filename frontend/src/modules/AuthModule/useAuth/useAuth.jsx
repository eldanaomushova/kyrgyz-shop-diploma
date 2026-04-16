import { create } from "zustand";
import { requester } from "../../../utils/Requester/Requester";

export const useAuth = create((set) => ({
    user: null,
    loading: false,
    error: null,

    actions: {
        login: async (credentials) => {
            set({ loading: true, error: null });
            try {
                const response = await requester.post(
                    "/api/login/",
                    credentials
                );
                localStorage.setItem("token", response.data.access);
                set({ user: response.data.user, loading: false });
            } catch (err) {
                set({ error: "Invalid credentials", loading: false });
            }
        },
        register: async (userData) => {
            set({ loading: true, error: null });
            try {
                await requester.post("/api/register/", userData);
                set({ loading: false });
                return { success: true };
            } catch (err) {
                set({ error: "Registration failed", loading: false });
            }
        },
        clearError: () => set({ error: null }),
    },
}));
