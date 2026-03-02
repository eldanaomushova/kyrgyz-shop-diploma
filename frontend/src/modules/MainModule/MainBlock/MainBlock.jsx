import styles from "./MainBlock.module.scss";
import { Typography } from "../../../ui/Typography/Typography";
import { Button } from "../../../ui/Buttons/Button";
import { useNavigate } from "react-router-dom";
import { PATH } from "../../../utils/Constants/Constants";
import { Footer } from "modules/Footer/components/Footer";
import heroVideo from "../../../assets/Videos/video.mp4";
import { ChatbotModule } from "../../../modules/ChatbotModule/ChatbotModule";

export const MainBlock = () => {
    const navigate = useNavigate();

    const categories = [
        {
            id: 1,
            name: "АЯЛДАР",
            image: "https://images.unsplash.com/photo-1581044777550-4cfa60707c03?auto=format&fit=crop&w=600&q=80",
            path: "/catalog?gender=Аялдар",
        },
        {
            id: 2,
            name: "ЭРКЕКТЕР",
            image: "https://i.pinimg.com/736x/b7/e6/3f/b7e63fe079f4c2b470e223ccad0c334f.jpg",
            path: "/catalog?gender=Эркек",
        },
        {
            id: 3,
            name: "БАЛДАР",
            image: "https://sunjimise.com/cdn/shop/files/O1CN01bXhhj31ez1jFZBv6F__2583103941-0-cib.jpg",
            path: "/catalog?gender=Балдар",
        },
    ];

    return (
        <div className={styles.main}>
            <section className={styles.hero}>
                <video
                    autoPlay
                    muted
                    loop
                    playsInline
                    className={styles.videoBg}
                >
                    <source src={heroVideo} type="video/mp4" />
                </video>
                <div className={styles.heroOverlay}>
                    <div className={styles.heroContent}>
                        <Typography
                            variant="h1"
                            weight="bold"
                            className={styles.heroTitle}
                        >
                            ЖАҢЫ КОЛЛЕКЦИЯ
                        </Typography>
                        <Typography
                            variant="h4"
                            weight="regular"
                            className={styles.heroSubtitle}
                        >
                            Мезгилдин башкы тренддери ушул жерде
                        </Typography>
                        <div className={styles.heroActions}>
                            <Button
                                text="Азыр сатып алуу"
                                variant="primary"
                                onClick={() => navigate(PATH.catalog)}
                                className={styles.heroButton}
                            />
                        </div>
                    </div>
                </div>
            </section>
            <ChatbotModule />
            <section className={styles.categories}>
                <div className={styles.container}>
                    <Typography variant="h2" className={styles.sectionTitle}>
                        КАТЕГОРИЯЛАР БОЮНЧА
                    </Typography>
                    <div className={styles.categoryGrid}>
                        {categories.map((cat) => (
                            <div
                                key={cat.id}
                                className={styles.categoryCard}
                                onClick={() => navigate(cat.path)}
                            >
                                <div className={styles.imageWrapper}>
                                    <img src={cat.image} alt={cat.name} />
                                </div>
                                <div className={styles.categoryInfo}>
                                    <Typography
                                        variant="h3"
                                        className={styles.categoryName}
                                    >
                                        {cat.name}
                                    </Typography>
                                    <span className={styles.shopLink}>
                                        Каталогго өтүү
                                    </span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </section>
            <Footer />
        </div>
    );
};
