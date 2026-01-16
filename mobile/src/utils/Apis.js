import axios from "axios";

const BASE_URL = 'http://192.168.1.23:8000/';

export const endpoints = {
    'register_candidate': '/register/candidate/',
    'register_employer': '/register/employer/',
    'login': '/o/token/',
    'logout': '/o/revoke_token/',
    'current_user': '/users/current-user/',
    'current_employer': '/employers/me/',
    'employer_jobs': '/employer/jobs/',
    'delete_jobs': (jobId) => `/employer/jobs/${jobId}/`,
    'update_jobs': (jobId) => `/employer/jobs/${jobId}/`,
    'categories': '/categories/',
    'locations': '/locations/',
    'tags': '/tags/',
    'applications_by_employer_jobs': (jobId) => `employer/applications/?job_id=${jobId}`,
    'candidate_by_applications_in_employer_jobs': (applicationId) => `employer/applications/${applicationId}/candidate-profile/`,
    'update_application': (applicationId) => `employer/applications/${applicationId}/`,
    'jobs': '/jobs/',
    'bookmarks': '/bookmarks/',
    'candidate_applications': '/candidate/applications/',
    'candidate_profile': '/candidates/me/',
    'update_user': '/users/current-user/',
    'update_candidate_profile': '/candidates/me/',
    'update_application': (applicationId) => `employer/applications/${applicationId}/`,
    'service_packs': '/payments/service-packs/',
    'create_payment': '/payments/receipts/create-payment/',
    'confirm_payment': '/payments/receipts/confirm-payment/',
    'history_payment': '/payments/receipts/',
    'work_experience': '/work-experience/',
    'education': '/education/',
    'languages': '/languages/',
    'appreciations': '/appreciations/',
    'skills': '/skills/',
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