import { Outlet, useLocation } from "react-router-dom";
import { Header } from "../../modules/Header/components/Header";
import { useEffect } from "react";
import { CartProvider } from "../../modules/CartProvider/CartProvider";
import { ChatbotModule } from "../../modules/ChatbotModule/ChatbotModule";

export const Layout = () => {
    const location = useLocation();

    useEffect(() => {
        window.scrollTo(0, 0);
    }, [location]);
    return (
        <div>
            <CartProvider>
                <Header />
                <main>
                    <Outlet />
                </main>
                <ChatbotModule />
            </CartProvider>
        </div>
    );
};
