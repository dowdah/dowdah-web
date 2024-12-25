import {createRouter, createWebHistory} from 'vue-router';
import {h} from 'vue';
import {AppstoreOutlined, SettingOutlined, HomeOutlined} from '@ant-design/icons-vue';
import store from '../store';
import Home from '../views/Home.vue';
import NotFound from "../views/NotFound.vue";
import PermissionDenied from "../views/PermissionDenied.vue";

const routes = [
    {path: '/', name: '主页', component: Home, meta: {icon: h(HomeOutlined)}},
    {path: '/test1', name: '测试1', component: Home, meta: {groupName: "测试组1", icon: h(SettingOutlined)}},
    {path: '/test2', name: '测试2', component: Home, meta: {groupName: "测试组1", requiresPermission: ['LOGIN']}},
    {path: '/test3', name: '测试3', component: Home, meta: {groupName: "测试组2", icon: h(AppstoreOutlined)}},
    {path: '/test4', name: '测试4', component: Home, meta: {groupName: "测试组3", icon: h(AppstoreOutlined)}},
    {path: '/permission-denied', name: '别看不该看的！', component: PermissionDenied, meta: {notShownInMenu: true}},
    {path: '/:pathMatch(.*)*', name: '这是哪？', component: NotFound, meta: {notShownInMenu: true}}
];

const router = createRouter({history: createWebHistory(), routes});

router.beforeEach(async (to, from, next) => {
    await store.dispatch('init');
    console.log(`Navigating to: ${to.name}`);
    store.commit('setTopBarTitle', '主页');
    if (to.matched.some(record => record.meta.requiresAuth) && !store.getters.isAuthenticated) {
        console.log('Not authenticated, redirecting to 403 page');
        next({name: '别看不该看的！'});
    }
    if (to.matched.some(record => record.meta.blockWhenAuthenticated) && store.getters.isAuthenticated) {
        console.log('Already authenticated, redirecting to Home');
        next({name: '主页'});
    }
    if (to.matched.some(record => record.meta.requiresPermission !== undefined)) {
        if (!store.getters.isAuthenticated) {
            console.log('Not authenticated, redirecting to 403 page');
            next({name: '别看不该看的！'});
            return;
        }
        for (let permission of to.meta.requiresPermission) {
            if (!store.getters.hasPermission(permission)) {
                console.log(`Current user can't ${permission}, redirecting to 403 page`);
                next({name: '别看不该看的！'});
                return;
            }
        }
    }
    console.log('Router guard passed, proceeding to next route');
    store.commit('setTopBarTitle', to.name);
    next();
});

export default router;
