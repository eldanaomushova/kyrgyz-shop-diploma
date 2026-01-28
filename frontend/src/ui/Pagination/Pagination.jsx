import React from "react";
import styles from "./Pagination.module.scss";

export const Pagination = ({ currentPage, totalPages, onPageChange }) => {
    if (totalPages <= 1) return null;

    const getVisiblePages = () => {
        const delta = 2;
        const range = [];
        const rangeWithDots = [];
        let l;

        for (let i = 1; i <= totalPages; i++) {
            if (
                i === 1 ||
                i === totalPages ||
                (i >= currentPage - delta && i <= currentPage + delta)
            ) {
                range.push(i);
            }
        }

        for (let i of range) {
            if (l) {
                if (i - l === 2) {
                    rangeWithDots.push(l + 1);
                } else if (i - l !== 1) {
                    rangeWithDots.push("...");
                }
            }
            rangeWithDots.push(i);
            l = i;
        }
        return rangeWithDots;
    };

    return (
        <nav className={styles.paginationContainer}>
            <button
                onClick={() => onPageChange(currentPage - 1)}
                disabled={currentPage === 1}
                className={styles.arrow}
            >
                &lsaquo;
            </button>

            <div className={styles.pages}>
                {getVisiblePages().map((page, index) => (
                    <button
                        key={index}
                        onClick={() =>
                            typeof page === "number" && onPageChange(page)
                        }
                        className={`${styles.pageItem} ${currentPage === page ? styles.active : ""} ${typeof page !== "number" ? styles.dots : ""}`}
                    >
                        {page}
                    </button>
                ))}
            </div>

            <button
                onClick={() => onPageChange(currentPage + 1)}
                disabled={currentPage === totalPages}
                className={styles.arrow}
            >
                &rsaquo;
            </button>
        </nav>
    );
};
