import axios from 'axios';

const API = axios.create({
  baseURL: process.env.REACT_APP_BACKEND_URL,
});

export const chatMessage = (session_id, message) =>
  API.post('/api/chat/message', { session_id, message });

export const extractProfile = (session_id) =>
  API.post('/api/chat/extract-profile', { session_id });

export const getPolicies = (params) =>
  API.get('/api/policies', { params });

export const getPolicy = (policy_id) =>
  API.get(`/api/policies/${policy_id}`);

export const recommendPolicies = (session_id, category) =>
  API.post('/api/policies/recommend', { session_id, category });

export const comparePolicies = (policy_ids) =>
  API.post('/api/policies/compare', { policy_ids });

export const createApplication = (session_id, policy_id, user_profile) =>
  API.post('/api/applications', { session_id, policy_id, user_profile });

export const getApplications = (session_id) =>
  API.get(`/api/applications/${session_id}`);

export const getNews = (category) =>
  API.get('/api/news', { params: category ? { category } : {} });

export const openChat = (session_id, message) =>
  API.post('/api/chat/open', { session_id, message });

export default API;
