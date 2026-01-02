import axios from "axios";

const BASE_URL = 'http://localhost:8000/';

export const endpoints = {
    'register': '/users/',
    'login': '/o/token/',
};

export const authApis = (token) => {
    return axios.create({
        baseURL: BASE_URL,
        headers: {
            'Authorization': `Bearer ${token}`
        }
    })
};

export default axios.create({
    baseURL: BASE_URL
});