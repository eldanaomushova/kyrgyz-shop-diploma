import { createBrowserRouter } from "react-router-dom";
import { PATH } from "../../utils/Constants/Constants";
import { HomePage } from "../../pages/HomePage/HomePage";
import { Layout } from "../../app/Layout/Layout";
import { CatalogPage } from "../../pages/CatalogPage/CatalogPage";
import { ProductDetailPage } from "../../pages/ProductDetailPage/ProductDetailPage";
import { CartPage } from "../../pages/CartPage/CartPage";

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
        ],
    },
]);
