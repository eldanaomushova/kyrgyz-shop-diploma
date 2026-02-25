import styles from "./Footer.module.scss";
import { Instagram, Youtube, Facebook, Music2 } from "lucide-react";

const FOOTER_DATA = [
    {
        title: "Shop",
        links: ["Women", "Men", "Kids", "H&M Home"],
    },
    {
        title: "Corporate Info",
        links: [
            "Career at H&M",
            "About H&M Group",
            "Sustainability",
            "Press",
            "Investor Relations",
        ],
    },
    {
        title: "Help",
        links: [
            "Customer Service",
            "My Account",
            "Find a Store",
            "Legal & Privacy",
            "Contact Us",
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
                                        <a href="#">{link}</a>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    ))}

                    <div className={styles.column}>
                        <h3 className={styles.title}>Not a member yet?</h3>
                        <p className={styles.text}>
                            Join now and get 10% off your first purchase!
                        </p>
                        <a href="#" className={styles.readMore}>
                            READ MORE
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
                        The content of this site is copyright-protected and is
                        the property of STIL.NO.
                    </p>
                </div>
            </div>
        </footer>
    );
};
