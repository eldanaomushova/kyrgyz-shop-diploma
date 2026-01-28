import { useState } from "react";
import styles from "./Header.module.scss";
import { Button } from "../../../ui/Buttons/Button";
import { ShoppingBag, User, Search, X } from "lucide-react";
import { SidebarMenu } from "../../../ui/SidebarMenu/SidebarMenu";
import { SearchPanel } from "../../../ui/SearchPanel/SearchPanel";

export const Header = () => {
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);
    const [activeGender, setActiveGender] = useState("");
    const [isSearchOpen, setIsSearchOpen] = useState(false);

    const openCategories = (gender) => {
        setActiveGender(gender);
        setIsSidebarOpen(true);
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
                                </ul>
                            </nav>
                        </div>

                        <div className={styles.actions}>
                            <Button
                                variant="icon"
                                icon={<Search size={18} />}
                                onClick={() => setIsSearchOpen(true)}
                            />

                            <Button
                                variant="icon"
                                icon={<User size={18} />}
                                className={styles.iconBtn}
                            />
                            <Button
                                variant="icon"
                                icon={<ShoppingBag size={16} />}
                                className={styles.iconBtn}
                            />
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
