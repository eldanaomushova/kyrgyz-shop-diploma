import ReactDOM from "react-dom/client";
import { RouterProvider } from "react-router-dom";
import { AppRouter } from "./app/Routes/AppRoutes";
import "./app/Style/index.scss";

const root = ReactDOM.createRoot(document.getElementById("root"));

root.render(<RouterProvider router={AppRouter} />);
