import { useEffect, useState, useCallback } from "react";
import { useSearchParams, Link } from "react-router-dom";
import styles from "./CatalogModule.module.scss";
import { Pagination } from "../../ui/Pagination/Pagination";

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

        let url = `http://127.0.0.1:8000/api/products/?page=${currentPage}&`;
        if (gender) url += `gender=${encodeURIComponent(gender)}&`;
        if (sub) url += `sub=${encodeURIComponent(sub)}&`;
        if (type) url += `type=${encodeURIComponent(type)}&`;
        if (search) url += `search=${encodeURIComponent(search)}`;

        try {
            const response = await fetch(url);

            if (response.status === 404) {
                setProducts([]);
                setTotalCount(0);
                return;
            }

            if (!response.ok) throw new Error("Server error");

            const data = await response.json();
            setProducts(data.results || []);
            setTotalCount(data.count || 0);
        } catch (error) {
            console.error("Fetch error:", error);
            setProducts([]);
            setTotalCount(0);
        } finally {
            setLoading(false);
        }
    }, [currentPage, gender, sub, type, search]);

    useEffect(() => {
        fetchFilteredProducts();
    }, [fetchFilteredProducts]);

    const getImageUrl = (product) => {
        if (product.link && product.link.startsWith("http")) {
            return product.link.replace("http://", "https://");
        }
        if (product.filename) {
            return `http://127.0.0.1:8000/media/products/${product.filename}`;
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
                                    to={`/product/${product.product_id}`}
                                    key={product.product_id}
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
        </main>
    );
};
