import {createApp} from 'vue';
import App from './App.vue';
import store from './store';
import router from './router';

const app = createApp(App);

// 使用 Vuex store 和 Vue Router
app.use(store);
app.use(router);
app.mount('#app');
