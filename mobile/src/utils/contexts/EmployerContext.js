import React, { createContext, useReducer, useContext } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import EmployerReducer from '../reducers/EmployerReducer';
import { authApis, endpoints } from '../Apis';

const EmployerContext = createContext();

export const EmployerProvider = ({ children }) => {
    const [profile, dispatch] = useReducer(EmployerReducer, null);
    const loadEmployerProfile = async (token) => {
        try {
            let res = await authApis(token).get(endpoints['current_employer']); 
            
            dispatch({
                type: "SET_PROFILE",
                payload: res.data
            });
            return res.data;
        } catch (err) {
            console.error("Lỗi tải Employer Profile:", err);
            return null;
        }
    };

    const clearEmployerProfile = () => {
        dispatch({ type: "CLEAR_PROFILE" });
    };

    return (
        <EmployerContext.Provider value={{ profile, dispatch, loadEmployerProfile, clearEmployerProfile }}>
            {children}
        </EmployerContext.Provider>
    );
};

export default EmployerContext;