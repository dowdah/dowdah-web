import {createRouter, createWebHistory} from 'vue-router';
import store from '../store';
import Home from '../views/Home.vue';

const routes = [
    {path: '/', name: '主页', component: Home},
    {path: '/test1', name: '测试1', component: Home, meta: {groupName: "测试组1"}},
    {path: '/test2', name: '测试2', component: Home, meta: {groupName: "测试组1"}},
    {path: '/test3', name: '测试3', component: Home, meta: {groupName: "测试组2"}},
    {path: '/test4', name: '测试4', component: Home, meta: {groupName: "测试组3"}}
];

const router = createRouter({history: createWebHistory(), routes});

router.beforeEach(async (to, from, next) => {
    await store.dispatch('init');
    console.log(`Navigating to: ${to.name}`);
    store.commit('setTopBarTitle', '主页');
    if (to.matched.some(record => record.meta.requiresAuth) && !store.getters.isAuthenticated) {
        console.log('Not authenticated, redirecting to Home');
        next({name: '主页'});
    }
    if (to.matched.some(record => record.meta.blockWhenAuthenticated) && store.getters.isAuthenticated) {
        console.log('Already authenticated, redirecting to Home');
        next({name: '主页'});
    }
    if (to.matched.some(record => record.meta.requiresPermission !== undefined)) {
        for (let permission of to.meta.requiresPermission) {
            if (!store.getters.hasPermission(permission)) {
                console.log(`Current user can't ${permission}, redirecting to Home`);
                next({name: '主页'});
                return;
            }
        }
    }
    console.log('Router guard passed, proceeding to next route');
    store.commit('setTopBarTitle', to.name);
    next();
});

export default router;
