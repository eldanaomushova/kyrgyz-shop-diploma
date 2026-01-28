import React, { useState, useEffect } from "react";
import styles from "./SidebarMenu.module.scss";
import { X } from "lucide-react";
import { Typography } from "../../ui/Typography/Typography";

export const SidebarMenu = ({ isOpen, onClose, gender }) => {
    const [categoriesTree, setCategoriesTree] = useState(null);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        const fetchCategories = async () => {
            setLoading(true);
            try {
                const response = await fetch(
                    "http://127.0.0.1:8000/api/categories-tree/"
                );
                const data = await response.json();
                setCategoriesTree(data);
            } catch (error) {
                console.error("Ошибка при загрузке дерева категорий:", error);
            } finally {
                setLoading(false);
            }
        };

        if (isOpen) {
            fetchCategories();
        }
    }, [isOpen]);

    if (!isOpen) return null;

    const genderData = categoriesTree ? categoriesTree[gender] : null;

    return (
        <>
            <div className={`${styles.sidebar} ${isOpen ? styles.open : ""}`}>
                <div className={styles.sidebarHeader}>
                    <Typography variant="h3">{gender || "Меню"}</Typography>
                    <button onClick={onClose} className={styles.closeBtn}>
                        <X size={24} />
                    </button>
                </div>

                <div className={styles.sidebarContent}>
                    {loading && <p>Жүктөлүүдө...</p>}

                    {genderData &&
                        Object.entries(genderData).map(([master, subs]) => (
                            <div key={master} className={styles.categoryBlock}>
                                <Typography
                                    variant="h5"
                                    className={styles.masterCategory}
                                >
                                    {master}
                                </Typography>
                                <ul className={styles.subList}>
                                    {subs.map((sub) => (
                                        <li key={sub}>
                                            <a
                                                href={`/catalog?gender=${gender}&sub=${sub}`}
                                                onClick={onClose}
                                            >
                                                {sub}
                                            </a>
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        ))}
                </div>
            </div>
            {/* Затемнение фона */}
            <div className={styles.overlay} onClick={onClose} />
        </>
    );
};
