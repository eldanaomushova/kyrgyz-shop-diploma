import React, { useState, useEffect } from "react";
import styles from "./SearchPanel.module.scss";
import { Search, X, ShoppingBag } from "lucide-react";
import { requester } from "../../utils/Requester/Requester";
import { Typography } from "../Typography/Typography";

export const SearchPanel = ({ isOpen, onClose }) => {
    const [query, setQuery] = useState("");
    const [results, setResults] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        const searchProducts = async () => {
            if (query.trim().length < 2) {
                setResults([]);
                setError(null);
                return;
            }

            setLoading(true);
            setError(null);

            try {
                const response = await requester.get("/api/products/search/", {
                    params: { search: query.trim() },
                });

                const products = response.data.results || response.data;
                setResults(products);
            } catch (error) {
                console.error("Search error:", error);
                setError("Search failed. Please try again.");
                setResults([]);
            } finally {
                setLoading(false);
            }
        };

        const timer = setTimeout(() => {
            searchProducts();
        }, 300);

        return () => clearTimeout(timer);
    }, [query]);

    const getHighlightedText = (text, highlight) => {
        if (!highlight.trim() || !text) return text?.toUpperCase() || "";

        const displayName = text.toUpperCase();
        const searchTerm = highlight.toUpperCase();

        const escapedSearchTerm = searchTerm.replace(
            /[.*+?^${}()|[\]\\]/g,
            "\\$&"
        );
        const parts = displayName.split(
            new RegExp(`(${escapedSearchTerm})`, "gi")
        );

        return (
            <>
                {parts.map((part, i) => (
                    <span
                        key={i}
                        className={
                            part.toUpperCase() === searchTerm
                                ? styles.highlightedText
                                : styles.normalText
                        }
                    >
                        {part}
                    </span>
                ))}
            </>
        );
    };

    const handleResultClick = (item) => {
        let url = `/catalog?`;
        const params = [];

        if (item.gender)
            params.push(`gender=${encodeURIComponent(item.gender)}`);
        if (item.subCategory)
            params.push(`sub=${encodeURIComponent(item.subCategory)}`);
        if (item.articleType)
            params.push(`type=${encodeURIComponent(item.articleType)}`);
        if (item.id) params.push(`id=${item.id}`);

        if (params.length === 0) {
            url = `/catalog?search=${encodeURIComponent(query)}`;
        } else {
            url += params.join("&");
        }

        window.location.href = url;
        onClose();
    };

    if (!isOpen) return null;

    return (
        <>
            <div className={styles.overlay} onClick={onClose} />
            <div className={styles.searchPanel}>
                <div className={styles.searchHeader}>
                    <div className={styles.inputWrapper}>
                        <Search size={20} className={styles.searchIcon} />
                        <input
                            type="text"
                            placeholder="Search products..."
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            autoFocus
                        />
                        {query && (
                            <button
                                className={styles.clearBtn}
                                onClick={() => setQuery("")}
                            >
                                Тазалоо
                            </button>
                        )}
                        <button className={styles.closeBtn} onClick={onClose}>
                            <X size={24} />
                        </button>
                    </div>
                </div>

                <div className={styles.resultsContainer}>
                    {loading && (
                        <div className={styles.loading}>
                            <div className={styles.spinner}></div>
                            <span>Searching...</span>
                        </div>
                    )}

                    {error && (
                        <div className={styles.error}>
                            <span>{error}</span>
                        </div>
                    )}

                    {!loading &&
                        !error &&
                        results.length === 0 &&
                        query.length >= 2 && (
                            <div className={styles.noResults}>
                                <Search size={48} strokeWidth={1} />
                                <Typography variant="h3">
                                    No products found
                                </Typography>
                                <Typography variant="p">
                                    We couldn't find any products matching "
                                    {query}"
                                </Typography>
                                <Typography
                                    variant="p"
                                    className={styles.suggestion}
                                >
                                    Try different keywords or browse our
                                    categories
                                </Typography>
                            </div>
                        )}

                    {!loading && !error && results.length > 0 && (
                        <>
                            <div className={styles.resultsHeader}>
                                <span className={styles.resultsCount}>
                                    {results.length} Товар табылды
                                </span>
                            </div>
                            <div className={styles.resultsList}>
                                {results.map((item) => (
                                    <button
                                        key={item.id}
                                        className={styles.resultItem}
                                        onClick={() => handleResultClick(item)}
                                    >
                                        <div className={styles.resultContent}>
                                            <div className={styles.resultIcon}>
                                                <ShoppingBag size={20} />
                                            </div>
                                            <div
                                                className={styles.resultDetails}
                                            >
                                                <div
                                                    className={
                                                        styles.productName
                                                    }
                                                >
                                                    {getHighlightedText(
                                                        item.productDisplayName,
                                                        query
                                                    )}
                                                </div>
                                                <div
                                                    className={
                                                        styles.productMeta
                                                    }
                                                >
                                                    {item.brand && (
                                                        <span
                                                            className={
                                                                styles.brand
                                                            }
                                                        >
                                                            {item.brand}
                                                        </span>
                                                    )}
                                                    {item.subCategory && (
                                                        <span
                                                            className={
                                                                styles.category
                                                            }
                                                        >
                                                            {item.subCategory}
                                                        </span>
                                                    )}
                                                </div>
                                            </div>
                                            {item.price && (
                                                <div className={styles.price}>
                                                    {typeof item.price ===
                                                    "number"
                                                        ? Math.floor(item.price)
                                                        : Math.floor(
                                                              parseFloat(
                                                                  item.price
                                                              )
                                                          )}{" "}
                                                    сом
                                                </div>
                                            )}
                                        </div>
                                    </button>
                                ))}
                            </div>
                        </>
                    )}
                </div>
            </div>
        </>
    );
};
