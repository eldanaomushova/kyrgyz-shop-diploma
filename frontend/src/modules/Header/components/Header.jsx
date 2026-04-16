import { useState } from "react";
import styles from "./Header.module.scss";
import { Button } from "../../../ui/Buttons/Button";
import { ShoppingBag, User, Search } from "lucide-react";
import { SidebarMenu } from "../../../ui/SidebarMenu/SidebarMenu";
import { SearchPanel } from "../../../ui/SearchPanel/SearchPanel";
import { useNavigate } from "react-router-dom";
import { PATH } from "../../../utils/Constants/Constants";
import { useCart } from "../../../modules/CartProvider/CartProvider";
import { useAuth } from "../../../modules/AuthModule/useAuth/useAuth";

export const Header = () => {
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);
    const [activeGender, setActiveGender] = useState("");
    const [isSearchOpen, setIsSearchOpen] = useState(false);
    const navigate = useNavigate();
    const { cart } = useCart();
    const cartCount = cart.length;
    const { actions } = useAuth();

    const openCategories = (gender) => {
        setActiveGender(gender);
        setIsSidebarOpen(true);
    };
    const isAuthenticated = !!localStorage.getItem("token");

    const handleLogout = () => {
        localStorage.removeItem("token");
        localStorage.removeItem("user");

        if (actions.logout) {
            actions.logout();
        }

        navigate(PATH.signin || "/signin");
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

                            <nav className={styles.nav}>
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
                                                navigate(PATH.virtualTryOn)
                                            }
                                            className={styles.navBtn}
                                        >
                                            Virtual Try-On
                                        </button>
                                    </li>
                                </ul>
                            </nav>
                        </div>

                        <div className={styles.actions}>
                            {isAuthenticated && (
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
                                onClick={() => navigate(PATH.signin)}
                                className={styles.iconBtn}
                            />

                            <Button
                                variant="icon"
                                onClick={() => navigate(PATH.cart)}
                                className={styles.cartIconWrapper}
                            >
                                <ShoppingBag size={18} />
                                {cartCount > 0 && (
                                    <span className={styles.badge}>
                                        {cartCount}
                                    </span>
                                )}
                            </Button>
                        </div>
                    </div>
                </div>
            </header>

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
