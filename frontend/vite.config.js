import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
    plugins: [react()],
    resolve: {
        alias: {
            "@assets": path.resolve(__dirname, "./src/assets"),
            "@pages": path.resolve(__dirname, "./src/pages"),
            "@utils": path.resolve(__dirname, "./src/utils"),
            "@modules": path.resolve(__dirname, "./src/modules"),
            "@ui": path.resolve(__dirname, "./src/ui"),
            "@app": path.resolve(__dirname, "./src"),
            "@Mixins": path.resolve(
                __dirname,
                "./src/Assets/Styles/Mixins.scss"
            ),
        },
    },
});
