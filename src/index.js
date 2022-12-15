import { createRoot } from "react-dom/client";
import recycle from "./recycle.png";
import truck from "./truck.png";
import App from "./App";
import "./App.css";

const container = document.getElementById("root");
const root = createRoot(container);
root.render(<App />);
