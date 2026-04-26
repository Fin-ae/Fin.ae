import axios from 'axios';

const API = axios.create({
  baseURL: process.env.REACT_APP_BACKEND_URL || '',
});

// Attach JWT token from localStorage on every request
API.interceptors.request.use((config) => {
  const token = localStorage.getItem('finae_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ── Auth ──────────────────────────────────────────────────
export const registerUser = (email, password, name) =>
  API.post('/api/auth/register', { email, password, name });

export const loginUser = (email, password) =>
  API.post('/api/auth/login', { email, password });

export const getMe = () =>
  API.get('/api/auth/me');

// ── Chat ──────────────────────────────────────────────────
export const chatMessage = (session_id, message) =>
  API.post('/api/chat/message', { session_id, message });

export const extractProfile = (session_id) =>
  API.post('/api/chat/extract-profile', { session_id });

// ── Policies ──────────────────────────────────────────────
export const getPolicies = (params) =>
  API.get('/api/policies', { params });

export const getPolicy = (policy_id) =>
  API.get(`/api/policies/${policy_id}`);

export const recommendPolicies = (session_id, category) =>
  API.post('/api/policies/recommend', { session_id, category });

export const comparePolicies = (policy_ids) =>
  API.post('/api/policies/compare', { policy_ids });

// ── Applications ──────────────────────────────────────────
export const createApplication = (policy_id, user_profile, session_id) =>
  API.post('/api/applications', { policy_id, user_profile, session_id });

export const getApplications = () =>
  API.get('/api/applications');

export const updateApplicationStatus = (application_number, status) =>
  API.patch(`/api/applications/${application_number}`, { status });

// ── News ──────────────────────────────────────────────────
export const getNews = (category, page = 1) =>
  API.get('/api/news', { params: { ...(category ? { category } : {}), page } });

// ── Open Chat ─────────────────────────────────────────────
export const openChat = (session_id, message) =>
  API.post('/api/chat/open', { session_id, message });

export const agentAction = (session_id, action_type, action_data) =>
  API.post('/api/chat/agent-action', { session_id, action_type, action_data });

export default API;
