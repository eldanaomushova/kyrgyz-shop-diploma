import { createBrowserRouter, useLocation } from "react-router-dom";
import { PATH } from "../../utils/Constants/Constants";
import { HomePage } from "../../pages/HomePage/HomePage";
import { Layout } from "../../app/Layout/Layout";
import { CatalogPage } from "../../pages/CatalogPage/CatalogPage";
import { ProductDetailPage } from "../../pages/ProductDetailPage/ProductDetailPage";
import { CartPage } from "../../pages/CartPage/CartPage";
import { SigninPage } from "../../pages/AuthPage/SigninPage";
import { SignupPage } from "../../pages/AuthPage/SignupPage";
import VirtualTryOnPage from "../../pages/VirtualTryOnPage/VirtualTryOnPage";
import ArTryOnPage from "../../pages/ArTryOnPage/ArTryOnPage";

const ArTryOnPageWrapper = () => {
    const { state } = useLocation();
    return <ArTryOnPage productImageUrl={state?.productImageUrl} />;
};

export const AppRouter = createBrowserRouter([
    {
        path: PATH.home,
        element: <Layout />,
        children: [
            {
                path: PATH.home,
                element: <HomePage />,
            },
            {
                path: PATH.catalog,
                element: <CatalogPage />,
            },
            {
                path: "/product/:id",
                element: <ProductDetailPage />,
            },
            {
                path: "/cart",
                element: <CartPage />,
            },
            {
                path: "/signin",
                element: <SigninPage />,
            },
            {
                path: "/signup",
                element: <SignupPage />,
            },
            {
                path: PATH.virtualTryOn,
                element: <VirtualTryOnPage />,
            },
            {
                path: PATH.arTryOn,
                element: <ArTryOnPageWrapper />,
            },
        ],
    },
]);
