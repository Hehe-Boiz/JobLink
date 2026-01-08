import { useContext } from "react";
import EmployerContext from "../utils/contexts/EmployerContext";

export const useEmployer = () => {
    return useContext(EmployerContext);
};