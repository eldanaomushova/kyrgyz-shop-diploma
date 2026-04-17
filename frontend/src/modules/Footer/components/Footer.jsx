import styles from "./Footer.module.scss";
import { Instagram, Youtube, Facebook, Music2 } from "lucide-react";

const FOOTER_DATA = [
    {
        title: "Дүкөн",
        links: ["Аялдар", "Эркектер", "Балдар", "H&M Home"],
    },
    {
        title: "Корпоративдик маалымат",
        links: [
            "H&Mдеги карьера",
            "H&M Group жөнүндө",
            "Туруктуулук",
            "Пресс",
            "Инвесторлор менен байланыш",
        ],
    },
    {
        title: "Жардам",
        links: [
            "Кардарларды тейлөө",
            "Менин аккаунтум",
            "Дүкөндү табуу",
            "Юридикалык жана купуялык",
            "Байланышуу",
        ],
    },
];

export const Footer = () => {
    return (
        <footer className={styles.footer}>
            <div className={styles.container}>
                <div className={styles.topSection}>
                    {FOOTER_DATA.map((section) => (
                        <div key={section.title} className={styles.column}>
                            <h3 className={styles.title}>{section.title}</h3>
                            <ul className={styles.list}>
                                {section.links.map((link) => (
                                    <li key={link}>
                                        <a href="/">{link}</a>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    ))}

                    <div className={styles.column}>
                        <h3 className={styles.title}>Мүчө эмессизби?</h3>
                        <p className={styles.text}>
                            Азыр кошулуңуз жана биринчи сатып алууңузга 10%
                            жеңилдик алыңыз!
                        </p>
                        <a href="/" className={styles.readMore}>
                            КЕНИРЭЭК
                        </a>
                    </div>
                </div>

                <div className={styles.middleSection}>
                    <h2 className={styles.footerLogo}>STIL.NO</h2>
                </div>

                <div className={styles.bottomSection}>
                    <div className={styles.socialIcons}>
                        <Instagram size={20} />
                        <Music2 size={20} />
                        <Youtube size={20} />
                        <Facebook size={20} />
                    </div>
                    <p className={styles.copyright}>
                        Бул сайттын мазмуну автордук укук менен корголгон жана
                        STIL.NO компаниясынын менчиги болуп саналат.
                    </p>
                </div>
            </div>
        </footer>
    );
};
