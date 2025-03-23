import axios from 'axios';
import {BASE_API_URL} from '@/config/constants';

// 创建 axios 实例
const apiClient = axios.create({
    baseURL: BASE_API_URL, // 你的 API 地址
    timeout: 5000,
});

// 请求拦截器，添加 access token
apiClient.interceptors.request.use(config => {
    console.log("Request Interceptor is called");
    const accessToken = localStorage.getItem('access_token');
    if (accessToken) {
        config.headers.Authorization = `Bearer ${accessToken}`;
    }
    return config;
}, error => Promise.reject(error));

// 响应拦截器，自动刷新 token
apiClient.interceptors.response.use(response => response, async error => {
    console.log("Response Interceptor is called");
    if (error.response && error.response.status === 401
        && error.response.data.msg === 'Token has expired') {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
            try {
                // 使用 refresh token 获取新的 access token
                const response = await axios.get(`${BASE_API_URL}/auth/refresh`, {
                    headers: {
                        Authorization: `Bearer ${refreshToken}`
                    }
                });
                const newAccessToken = response.data.access_token;

                // 更新 token
                localStorage.setItem('access_token', newAccessToken);
                error.config.headers.Authorization = `Bearer ${newAccessToken}`;

                // 重新发送原始请求
                return apiClient(error.config);
            } catch (refreshError) {
                console.error('Refresh token failed', refreshError);
                // 清除无效 token 并跳转到登录页
                localStorage.removeItem('access_token');
                localStorage.removeItem('refresh_token');
                window.location.href = '/';
            }
        }
    }
    return Promise.reject(error);
});

export default apiClient;
