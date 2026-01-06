import axios from "axios";

const BASE_URL = 'http://192.168.1.16:8000/';

export const endpoints = {
    'register_candidate': '/register/candidate/',
    'register_employer': '/register/employer/',
    'login': '/o/token/',
    'current_user': '/users/current-user/',
    'logout': '/o/revoke_token/',
    'employer_jobs': '/employer/jobs/',
    'categories': '/categories/',
    'locations': '/locations/',
    'applications_by_employer_jobs': (jobId) => `employer/jobs/${jobId}/applications/`,
    'candidate_by_applications_in_employer_jobs': (applicationId) => `employer/applications/${applicationId}/candidate-profile/`
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