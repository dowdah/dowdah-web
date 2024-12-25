import {createApp} from 'vue';
import App from './App.vue';
import store from './store';
import router from './router';
import Antd, { message } from 'ant-design-vue';
import 'ant-design-vue/dist/reset.css';

const app = createApp(App);

app.config.globalProperties.$message = message;

// 使用 Vuex store 和 Vue Router
app.use(store);
app.use(router);
app.use(Antd);
app.mount('#app');

window.matchMedia('(prefers-color-scheme: light)').addEventListener('change', (e) => {
    const newTheme = e.matches ? 'light' : 'dark';
    store.commit('setTheme', newTheme); // 直接调用 mutation
});
