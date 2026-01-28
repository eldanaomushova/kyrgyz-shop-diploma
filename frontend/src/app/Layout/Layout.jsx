import { Outlet, useLocation } from "react-router-dom";
import { Header } from "../../modules/Header/components/Header";
import { Footer } from "../../modules/Footer/components/Footer";
import { useEffect } from "react";

export const Layout = () => {
    const location = useLocation();

    useEffect(() => {
        window.scrollTo(0, 0);
    }, [location]);
    return (
        <div>
            <Header />
            <main>
                <Outlet />
            </main>
            <Footer />
        </div>
    );
};
