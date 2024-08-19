import { createApp } from "vue";
import { library } from "@fortawesome/fontawesome-svg-core";

import { faFileLines } from "@fortawesome/free-regular-svg-icons";
import { faRotate, faSignature, faTrashCan } from "@fortawesome/free-solid-svg-icons";

import App from "./App.vue";

import "./index.css";

library.add(faFileLines, faRotate, faSignature, faTrashCan)

const app = createApp(App);

app.mount("#app");
