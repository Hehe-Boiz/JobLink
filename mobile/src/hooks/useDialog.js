import { useContext } from "react";
import DialogContext from "../utils/contexts/DialogContext";

export const useDialog = () => {
    return useContext(DialogContext);
};