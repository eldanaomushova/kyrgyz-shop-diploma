import { useState, useEffect } from "react";
import styles from "./Header.module.scss";
import { Button } from "../../../ui/Buttons/Button";
import { ShoppingBag, User, Search, Menu, X, Sparkles } from "lucide-react";
import { SidebarMenu } from "../../../ui/SidebarMenu/SidebarMenu";
import { SearchPanel } from "../../../ui/SearchPanel/SearchPanel";
import { useNavigate } from "react-router-dom";
import { PATH } from "../../../utils/Constants/Constants";
import { useCart } from "../../../modules/CartProvider/CartProvider";
import { Typography } from "../../../ui/Typography/Typography";
import { useAuth } from "../../../modules/AuthModule/useAuth/useAuth";

export const Header = () => {
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
    const [activeGender, setActiveGender] = useState("");
    const [isSearchOpen, setIsSearchOpen] = useState(false);
    const [isMobile, setIsMobile] = useState(false);
    const navigate = useNavigate();
    const { cart } = useCart();
    const cartCount = cart.length;
    const { actions } = useAuth();

    useEffect(() => {
        const checkMobile = () => {
            setIsMobile(window.innerWidth <= 768);
        };
        checkMobile();
        window.addEventListener("resize", checkMobile);
        return () => window.removeEventListener("resize", checkMobile);
    }, []);

    const openCategories = (gender) => {
        if (isMobile) {
            setIsMobileMenuOpen(false);
            setActiveGender(gender);
            setIsSidebarOpen(true);
        } else {
            setActiveGender(gender);
            setIsSidebarOpen(true);
        }
    };

    const isAuthenticated = !!localStorage.getItem("token");

    const handleLogout = () => {
        localStorage.removeItem("token");
        localStorage.removeItem("user");
        if (actions.logout) {
            actions.logout();
        }
        navigate(PATH.signin || "/signin");
        setIsMobileMenuOpen(false);
    };
    const handleNavigation = (path) => {
        navigate(path);
        setIsMobileMenuOpen(false);
    };

    return (
        <>
            <header className={styles.header} id="home">
                <div className={styles.mainHeader}>
                    <div className={styles.containerMain}>
                        <div className={styles.containerSecond}>
                            <div className={styles.logo}>
                                <a href="/">STIL.NО</a>
                            </div>

                            <nav className={styles.desktopNav}>
                                <ul className={styles.navList}>
                                    <li>
                                        <button
                                            onClick={() =>
                                                openCategories("Аялдар")
                                            }
                                            className={styles.navBtn}
                                        >
                                            Аял
                                        </button>
                                    </li>
                                    <li>
                                        <button
                                            onClick={() =>
                                                openCategories("Эркек")
                                            }
                                            className={styles.navBtn}
                                        >
                                            Эркек
                                        </button>
                                    </li>
                                    <li>
                                        <button
                                            onClick={() =>
                                                openCategories("Кыздар")
                                            }
                                            className={styles.navBtn}
                                        >
                                            Кыздар
                                        </button>
                                    </li>
                                    <li>
                                        <button
                                            onClick={() =>
                                                openCategories("Балдар")
                                            }
                                            className={styles.navBtn}
                                        >
                                            Балдар
                                        </button>
                                    </li>
                                    <li>
                                        <button
                                            onClick={() =>
                                                handleNavigation(
                                                    PATH.virtualTryOn
                                                )
                                            }
                                            className={
                                                styles.virtualTryOnDesktop
                                            }
                                        >
                                            <Sparkles size={18} />
                                            Virtual Try-On
                                        </button>
                                    </li>
                                </ul>
                            </nav>
                        </div>

                        <div className={styles.actions}>
                            {isAuthenticated && !isMobile && (
                                <Button
                                    variant="text"
                                    text="Чыгуу"
                                    onClick={handleLogout}
                                    width="90px"
                                    className={styles.logout}
                                />
                            )}

                            <Button
                                variant="icon"
                                onClick={() => setIsSearchOpen(true)}
                                className={styles.iconBtn}
                            >
                                <Search size={18} />
                            </Button>

                            <Button
                                variant="icon"
                                icon={<User size={18} />}
                                onClick={() => handleNavigation(PATH.signin)}
                                className={styles.iconBtn}
                            />

                            <Button
                                variant="icon"
                                onClick={() => handleNavigation(PATH.cart)}
                                className={styles.cartIconWrapper}
                            >
                                <ShoppingBag size={18} />
                                {cartCount > 0 && (
                                    <span className={styles.badge}>
                                        {cartCount}
                                    </span>
                                )}
                            </Button>

                            <Button
                                variant="icon"
                                onClick={() =>
                                    setIsMobileMenuOpen(!isMobileMenuOpen)
                                }
                                className={styles.menuBtn}
                            >
                                {isMobileMenuOpen ? (
                                    <X size={18} />
                                ) : (
                                    <Menu size={18} />
                                )}
                            </Button>
                        </div>
                    </div>
                </div>
            </header>

            <div
                className={`${styles.mobileMenu} ${isMobileMenuOpen ? styles.open : ""}`}
            >
                <div className={styles.mobileMenuHeader}>
                    <div className={styles.logo}>STIL.NО</div>
                    <button
                        onClick={() => setIsMobileMenuOpen(false)}
                        className={styles.closeMenuBtn}
                    >
                        <X size={24} />
                    </button>
                </div>

                <div className={styles.mobileMenuContent}>
                    <div className={styles.mobileNavSection}>
                        <Typography
                            variant="h4"
                            className={styles.sectionTitle}
                        >
                            Категории
                        </Typography>
                        <ul className={styles.mobileNavList}>
                            <li>
                                <button
                                    onClick={() => openCategories("Аялдар")}
                                >
                                    Аял
                                </button>
                            </li>
                            <li>
                                <button onClick={() => openCategories("Эркек")}>
                                    Эркек
                                </button>
                            </li>
                            <li>
                                <button
                                    onClick={() => openCategories("Кыздар")}
                                >
                                    Кыздар
                                </button>
                            </li>
                            <li>
                                <button
                                    onClick={() => openCategories("Балдар")}
                                >
                                    Балдар
                                </button>
                            </li>
                        </ul>
                    </div>

                    <div className={styles.mobileNavSection}>
                        <Typography
                            variant="h4"
                            className={styles.sectionTitle}
                        >
                            Сервистер
                        </Typography>
                        <ul className={styles.mobileNavList}>
                            <li>
                                <button
                                    onClick={() =>
                                        handleNavigation(PATH.virtualTryOn)
                                    }
                                    className={styles.virtualTryOnBtn}
                                >
                                    <Sparkles size={18} />
                                    Virtual Try-On
                                </button>
                            </li>
                        </ul>
                    </div>

                    {isAuthenticated && (
                        <div className={styles.mobileNavSection}>
                            <Typography
                                variant="h4"
                                className={styles.sectionTitle}
                            >
                                Аккаунт
                            </Typography>
                            <ul className={styles.mobileNavList}>
                                <li>
                                    <button onClick={handleLogout}>
                                        Чыгуу
                                    </button>
                                </li>
                            </ul>
                        </div>
                    )}
                </div>
            </div>
            {isMobileMenuOpen && (
                <div
                    className={styles.mobileOverlay}
                    onClick={() => setIsMobileMenuOpen(false)}
                />
            )}

            <SidebarMenu
                isOpen={isSidebarOpen}
                onClose={() => setIsSidebarOpen(false)}
                gender={activeGender}
            />
            <SearchPanel
                isOpen={isSearchOpen}
                onClose={() => setIsSearchOpen(false)}
            />
        </>
    );
};
