import styles from "./MainBlock.module.scss";
// import { Typography } from "../../../ui/Typography/Typography";

export const MainBlock = () => {
    return (
        <div className={styles.main}>
            <div className={styles.wrapper}>
                <div className={styles.slogan}>
                    {/* <Typography
                        variant="h6"
                        weight="semi-bold"
                        className={styles.text}
                    >
                        Бесплатная консультация от ИИ ассистента! Получите
                        профессиональную оценку состояния вашей кожи
                        и&nbsp;рекомендации от&nbsp;эксперта.
                    </Typography> */}
                </div>
            </div>
        </div>
    );
};
