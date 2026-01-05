import axios from "axios";

const BASE_URL = 'http://192.168.1.16:8000/';

export const endpoints = {
    'register_candidate': '/register/candidate/',
    'register_employer': '/register/employer/',
    'login': '/o/token/',
    'current_user': '/users/current-user/',
    'logout': '/o/revoke_token/'
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