import {createStore} from 'vuex';
import {SITE_NAME} from '@/config/constants';
import apiClient from "@/api";

const store = createStore({
    state: {
        user: null,
        isLoading: false,
        permissions: null,
        isInitialized: false,
        topBarTitle: null,
        title: SITE_NAME,
        theme: window.matchMedia('(prefers-color-scheme: light)').matches ? "light" : "dark",
        fingerprint: null,
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
            state.theme = state.theme === 'light' ? 'dark' : 'light';
        },
        setTheme(state, theme) {
            state.theme = theme;
        },
        setFingerprint(state, fingerprint) {
            state.fingerprint = fingerprint;
        }
    },
    actions: {
        async login({commit}, credentials) {
            console.log('Login action called with credentials:', credentials);
            commit('setLoading', true);
            try {
                const response = await apiClient.post('/auth/login', credentials);
                if (response.data.success) {
                    console.log('Login response:', response.data);
                    localStorage.setItem('access_token', response.data.access_token);
                    localStorage.setItem('refresh_token', response.data.refresh_token);
                    commit('setUser', response.data.user);
                    if (store.state.permissions === null) {
                        await store.dispatch('fetchPermissions');
                    }
                } else {
                    console.error('Login failed:', response.data.msg);
                    throw new Error('Login failed: ' + response.data.msg);
                }
            } catch (error) {
                console.error('Login error:', error);
                throw error;
            } finally {
                commit('setLoading', false);
            }
        },
        async register({commit}, payload) {
            console.log('Register called with payload:', payload);
            commit('setLoading', true);
            let response;
            try {
                response = await apiClient.post('/auth/register', payload);
            } catch (error) {
                console.error('Register error:', error);
                commit('setLoading', false);
                return error.response.data;
            }
            if (response.data.success) {
                console.log('Registration successful');
                commit('setUser', response.data.user);
                localStorage.setItem('access_token', response.data.access_token);
                localStorage.setItem('refresh_token', response.data.refresh_token);
                if (store.state.permissions === null) {
                    await store.dispatch('fetchPermissions');
                }
            }
            commit('setLoading', false);
            return response.data;
        },
        async logout({commit}) {
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            commit('clearUser');
        },
        async init({commit, state}) {
            commit('setLoading', true);
            const access_token = localStorage.getItem('access_token');
            console.log('Init action called with token:', access_token)
            if (access_token) {
                try {
                    const response = await apiClient.get('/auth/me');
                    commit('setUser', response.data.user);
                    if (state.permissions === null) {
                        await store.dispatch('fetchPermissions');
                    }
                    console.log('User set:', response.data.user);
                } catch (error) {
                    console.error('Init unknown error:', error);
                    store.dispatch('logout');
                }
            }
            commit('setLoading', false);
            commit('setInitialized', true);
        },
        setLoading({commit}, isLoading) {
            commit('setLoading', isLoading);
        },
        async fetchPermissions({commit}) {
            try {
                const response = await apiClient.get('/permissions');
                commit('setPermissions', response.data.permissions);
            } catch (error) {
                console.error('Fetch permissions error:', error);
                throw error;
            }
        },
        async webauthnLoginComplete({commit}, assertionResponse) {
            try {
                const response = await apiClient.post('/webauthn/login/complete', assertionResponse);
                if (response.data.success) {
                    commit('setUser', response.data.user);
                    localStorage.setItem('access_token', response.data.access_token);
                    localStorage.setItem('refresh_token', response.data.refresh_token);
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
