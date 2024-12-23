import {createApp} from 'vue';
import App from './App.vue';
import store from './store';
import router from './router';
import Antd from 'ant-design-vue';
import 'ant-design-vue/dist/reset.css';

const app = createApp(App);

// 使用 Vuex store 和 Vue Router
app.use(store);
app.use(router);
app.use(Antd);
app.mount('#app');
