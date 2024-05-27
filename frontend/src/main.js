import { createApp } from 'vue';
import App from './app.vue';
import ul from './components/UserList.vue';

createApp(App).mount('#app');
createApp(ul).mount('#user-list');
