import { useLocation } from "react-router-dom";
import ARTryOnModule from "../../modules/ArTryOnModule/ARTryOnModule";

const ARTryOnPage = () => {
    const location = useLocation();
    const productImageUrl = location.state?.productImageUrl;

    return <ARTryOnModule productImageUrl={productImageUrl} />;
};
export default ARTryOnPage;
