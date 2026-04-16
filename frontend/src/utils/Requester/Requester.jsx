import axios from "axios";

export const requester = axios.create({
    baseURL: "https://diploma-project-788181191989.us-central1.run.app/",
    timeout: 60000,
    headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
    },
});

requester.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem("token");
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

requester.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response && error.response.status === 401) {
            localStorage.removeItem("token");
        }
        return Promise.reject(error);
    }
);
