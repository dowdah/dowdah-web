import {createRouter, createWebHistory} from 'vue-router';
import store from '../store';
import Home from '../views/Home.vue';

const routes = [
    {path: '/', name: 'Home', component: Home}
];

const router = createRouter({history: createWebHistory(), routes});

router.beforeEach(async (to, from, next) => {
    await store.dispatch('init');
    console.log(`Navigating to: ${to.name}`);
    if (to.matched.some(record => record.meta.requiresAuth) && !store.getters.isAuthenticated) {
        console.log('Not authenticated, redirecting to Home');
        next({name: 'Home'});
    }
    if (to.matched.some(record => record.meta.blockWhenAuthenticated) && store.getters.isAuthenticated) {
        console.log('Already authenticated, redirecting to Home');
        next({name: 'Home'});
    }
    if (to.matched.some(record => record.meta.requiresPermission !== undefined)) {
        for (let permission of to.meta.requiresPermission) {
            if (!store.getters.hasPermission(permission)) {
                console.log(`Current user can't ${permission}, redirecting to Home`);
                next({name: 'Home'});
                return;
            }
        }
    }
    console.log('Router guard passed, proceeding to next route');
    next();
});

export default router;
