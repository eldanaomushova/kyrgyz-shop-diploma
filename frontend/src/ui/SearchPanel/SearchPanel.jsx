import React, { useState, useEffect } from "react";
import styles from "./SearchPanel.module.scss";
import { Search, X } from "lucide-react";

export const SearchPanel = ({ isOpen, onClose }) => {
    const [query, setQuery] = useState("");
    const [results, setResults] = useState([]);

    useEffect(() => {
        const searchProducts = async () => {
            if (query.trim().length < 2) {
                setResults([]);
                return;
            }

            try {
                const url = `http://127.0.0.1:8000/api/products/?search=${encodeURIComponent(query)}`;
                const response = await fetch(url);
                const data = await response.json();
                setResults(data.results || data);
            } catch (error) {
                console.error("Search error:", error);
            }
        };

        const timer = setTimeout(() => {
            searchProducts();
        }, 300);

        return () => clearTimeout(timer);
    }, [query]);
    const getHighlightedText = (text, highlight) => {
        if (!highlight.trim()) return text.toUpperCase();

        const displayName = text.toUpperCase();
        const searchTerm = highlight.toUpperCase();
        const parts = displayName.split(new RegExp(`(${searchTerm})`, "gi"));

        return (
            <>
                {parts.map((part, i) => (
                    <span
                        key={i}
                        style={
                            part.toUpperCase() === searchTerm
                                ? { fontWeight: "900", color: "#000" }
                                : { fontWeight: "400", color: "#999" }
                        }
                    >
                        {part}
                    </span>
                ))}
            </>
        );
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
                            placeholder="Search"
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

                <div className={styles.resultsList}>
                    {results.map((item) => (
                        <a
                            key={item.id || item.product_id}
                            href={`/catalog?gender=${item.gender}&sub=${item.subCategory}&type=${item.articleType}`}
                            className={styles.resultItem}
                            onClick={() => {
                                onClose();
                            }}
                        >
                            {getHighlightedText(item.productDisplayName, query)}
                        </a>
                    ))}
                </div>
            </div>
        </>
    );
};
