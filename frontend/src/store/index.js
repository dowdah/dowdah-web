import {createStore} from 'vuex';
import {BASE_API_URL} from '@/config/constants';
import axios from 'axios';

const store = createStore({
    state: {
        user: null,
        isLoading: false,
        permissions: null,
        isInitialized: false,
        topBarTitle: null,
        title: process.env.VUE_APP_TITLE,
        theme: window.matchMedia('(prefers-color-scheme: light)').matches ? "light":"dark"
    },
    mutations: {
        setUser(state, user) {
            state.user = user;
        },
        clearUser(state) {
            state.user = null;
        },
        setLoading(state, isLoading) {
            state.isLoading = isLoading;
        },
        setPermissions(state, permissions) {
            state.permissions = permissions;
        },
        setInitialized(state, isInitialized) {
            state.isInitialized = isInitialized;
        },
        setTopBarTitle(state, title) {
            state.topBarTitle = title;
        },
        changeTheme(state) {
            state.theme = state.theme==='light' ? 'dark' : 'light';
        },
        setTheme(state, theme) {
            state.theme = theme;
        }
    },
    actions: {
        async login({commit}, credentials) {
            console.log('Login action called with credentials:', credentials);
            commit('setLoading', true);
            try {
                const response = await axios.post(`${BASE_API_URL}/auth/login`, credentials);
                if (response.data.success) {
                    console.log('Login response:', response.data);
                    localStorage.setItem('access_token', response.data.access_token);
                    localStorage.setItem('refresh_token', response.data.refresh_token);
                    axios.defaults.headers.common['Authorization'] = 'Bearer ' + response.data.access_token;
                    commit('setUser', response.data.user);
                    if (store.state.permissions === null) {
                        await store.dispatch('fetchPermissions');
                    }
                } else {
                    alert('登录失败：' + response.data.msg)
                }
            } catch (error) {
                console.error('Login error:', error);
                throw error;
            } finally {
                commit('setLoading', false);
            }
        },
        async logout({commit}) {
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            delete axios.defaults.headers.common['Authorization'];
            commit('clearUser');
        },
        async init({commit, state}) {
            // 当加载时间超过 500ms 时，显式加载。
            let setLoadingCalled = false;
            const timer = setTimeout(() => {
                setLoadingCalled = true;
                commit('setLoading', true);
            }, 500);
            const access_token = localStorage.getItem('access_token');
            console.log('Init action called with token:', access_token)
            if (access_token) {
                axios.defaults.headers.common['Authorization'] = 'Bearer ' + access_token;
                try {
                    const response = await axios.get(`${BASE_API_URL}/auth/me`);
                    commit('setUser', response.data.user);
                    if (state.permissions === null) {
                        await store.dispatch('fetchPermissions');
                    }
                    console.log('User set:', response.data.user);
                } catch (error) {
                    if (error.response && error.response.status === 401 && error.response.data.msg === 'Token has expired') {
                        console.log('Token expired, refreshing...');
                        if (await store.dispatch('refreshAccessToken')) {
                            console.log('Token refreshed, retrying...');
                            await store.dispatch('init');
                        } else {
                            console.log('Refresh token expired, user has been logged out.');
                        }
                    } else {
                        console.error('Init unknown error:', error);
                        store.dispatch('logout');
                    }
                }
            }
            // 如果加载时间未超过 500ms，取消计时器。若计时器已触发，取消加载状态。
            if (!setLoadingCalled) {
                clearTimeout(timer);
            } else {
                commit('setLoading', false);
            }
            commit('setInitialized', true);
        },
        setLoading({commit}, isLoading) {
            commit('setLoading', isLoading);
        },
        async fetchPermissions({commit}) {
            try {
                const response = await axios.get(`${BASE_API_URL}/permissions`);
                commit('setPermissions', response.data.permissions);
            } catch (error) {
                console.error('Fetch permissions error:', error);
                throw error;
            }
        },
        async refreshAccessToken({commit}) {
            const refresh_token = localStorage.getItem('refresh_token');
            if (!refresh_token) {
                return false;
            }
            try {
                const refresh_token = localStorage.getItem('refresh_token');
                axios.defaults.headers.common['Authorization'] = 'Bearer ' + refresh_token;
                const response = await axios.get(`${BASE_API_URL}/auth/refresh`)
                localStorage.setItem('access_token', response.data.access_token);
                axios.defaults.headers.common['Authorization'] = 'Bearer ' + response.data.access_token;
                return true;
            } catch (error) {
                if (error.response && error.response.status === 401) {
                    localStorage.removeItem('access_token');
                    localStorage.removeItem('refresh_token');
                    delete axios.defaults.headers.common['Authorization'];
                    commit('clearUser');
                } else {
                    console.error('Refresh token unknown error:', error);
                }
                return false;
            }
        },
        async webauthnLoginComplete({commit}, assertionResponse) {
            try {
                const response = await axios.post(`${BASE_API_URL}/webauthn/login/complete`, assertionResponse);
                if (response.data.success) {
                    commit('setUser', response.data.user);
                    localStorage.setItem('access_token', response.data.access_token);
                    localStorage.setItem('refresh_token', response.data.refresh_token);
                    axios.defaults.headers.common['Authorization'] = 'Bearer ' + response.data.access_token;
                    if (store.state.permissions === null) {
                        await store.dispatch('fetchPermissions');
                    }
                }
                return response.data;
            } catch (error) {
                console.error('WebAuthn Login Complete error:', error);
                throw error;
            } finally {
                commit('setLoading', false);
            }
        }
    },
    getters: {
        isAuthenticated: state => !!state.user,
        cards: state => state.user ? state.user.cards : [],
        hasPermission: function (state) {
            return function (permission) {
                const permissionNumber = state.permissions[permission];
                if (permissionNumber === undefined || !store.getters.isAuthenticated) {
                    return false;
                } else {
                    return (state.user.role.permissions & state.permissions['ADMIN']) === state.permissions['ADMIN'] ||
                        (state.user.role.permissions & permissionNumber) === permissionNumber;
                }
            }
        }
    }
});

export default store;
