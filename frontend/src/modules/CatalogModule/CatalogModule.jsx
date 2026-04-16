import { useEffect, useState, useCallback } from "react";
import { useSearchParams, Link } from "react-router-dom";
import styles from "./CatalogModule.module.scss";
import { Pagination } from "../../ui/Pagination/Pagination";
import { Footer } from "../../modules/Footer/components/Footer";
import { requester } from "../../utils/Requester/Requester";

export const CatalogModule = () => {
    const [products, setProducts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [totalCount, setTotalCount] = useState(0);
    const [searchParams, setSearchParams] = useSearchParams();

    const currentPage = parseInt(searchParams.get("page")) || 1;
    const pageSize = 12;

    const gender = searchParams.get("gender");
    const sub = searchParams.get("sub");
    const type = searchParams.get("type");
    const search = searchParams.get("search");

    const fetchFilteredProducts = useCallback(async () => {
        setLoading(true);

        const params = new URLSearchParams();
        params.append("page", currentPage);
        params.append("page_size", pageSize);

        if (gender) params.append("gender", gender);
        if (sub) params.append("sub", sub);
        if (type) params.append("type", type);
        if (search) params.append("search", search);

        try {
            const response = await requester.get(`/api/products/`, {
                params: params,
            });

            setProducts(response.data.results || []);
            setTotalCount(response.data.count || 0);
        } catch (error) {
            if (error.response && error.response.status === 404) {
                setProducts([]);
                setTotalCount(0);
            } else {
                setProducts([]);
                setTotalCount(0);
            }
        } finally {
            setLoading(false);
        }
    }, [currentPage, gender, sub, type, search, pageSize]);

    useEffect(() => {
        fetchFilteredProducts();
    }, [fetchFilteredProducts]);

    const getImageUrl = (product) => {
        if (product.link && product.link.startsWith("http")) {
            return product.link.replace("http://", "https://");
        }
        if (product.filename) {
            return `/media/products/${product.filename}`;
        }
        return "/placeholder.jpg";
    };

    const handlePageChange = (newPage) => {
        const newParams = new URLSearchParams(searchParams);
        newParams.set("page", newPage);
        setSearchParams(newParams);
        window.scrollTo({ top: 0, behavior: "smooth" });
    };

    const totalPages = Math.ceil(totalCount / pageSize);

    return (
        <main className={styles.catalogContainer}>
            <header className={styles.catalogHeader}>
                <nav className={styles.breadcrumb}>
                    <span>{gender}</span> {sub && ` / ${sub}`}
                </nav>
                <h1 className={styles.title}>{type || sub || "Каталог"}</h1>
            </header>

            {loading ? (
                <div className={styles.loader}>Загрузка...</div>
            ) : (
                <>
                    <div className={styles.productGrid}>
                        {products?.length > 0 ? (
                            products.map((product) => (
                                <Link
                                    to={`/product/${product.id}`}
                                    key={product.id}
                                    className={styles.productCard}
                                >
                                    <div className={styles.imageWrapper}>
                                        <img
                                            src={getImageUrl(product)}
                                            alt={product.productDisplayName}
                                            onError={(e) => {
                                                e.target.src =
                                                    "/placeholder.jpg";
                                            }}
                                        />
                                    </div>
                                    <div className={styles.productInfo}>
                                        <h3 className={styles.productName}>
                                            {product.productDisplayName}
                                        </h3>
                                        <p className={styles.price}>
                                            {product.price} сом
                                        </p>
                                        <p className={styles.articleType}>
                                            {product.articleType}
                                        </p>
                                    </div>
                                </Link>
                            ))
                        ) : (
                            <p className={styles.empty}>Товары не найдены</p>
                        )}
                    </div>

                    <Pagination
                        currentPage={currentPage}
                        totalPages={totalPages}
                        onPageChange={handlePageChange}
                    />
                </>
            )}
            <Footer />
        </main>
    );
};
