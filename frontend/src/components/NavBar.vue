<template>
  <div class="layout-menu use-shadow">
    <h1 class="menu-logo">
      <img src="/favicon.ico" alt="menu logo">
      <span>Dowdah</span>
    </h1>
    <div class="menu-groups">
      <div class="menu-group" v-for="(routes, groupName) in groupedRoutes" :key="groupName">
        <div class="g-title" v-if="groupName !== 'ungrouped'">{{ groupName }}</div>
        <ul class="g-links">
          <template v-for="route in routes" :key="route.name">
            <router-link :to="route.path" custom v-slot="{ href, navigate, isActive, isExactActive }">
              <li :class="{ 'is-active': isExactActive }" @click="navigate">
                <span class="link">
                  <span class="tit">
                    {{ route.name }}
                  </span>
                </span>
              </li>
            </router-link>
          </template>
        </ul>
      </div>
    </div>
    <p class="version"> Dowdah 1.0.0 </p>
  </div>
</template>

<script>
import {mapGetters, mapState, mapActions} from 'vuex';
import {useRouter} from 'vue-router';

export default {
  name: 'NavBar',
  data() {
    return {
      routes: this.$router.options.routes,
      filteredRoutes: [],
      groups: []
    };
  },
  methods: {
    ...mapActions(['fetchPermissions']),
    filterRoutes() {
      // 不作为 computed 属性是因为要根据其他参数动态更新(见watch)
      this.filteredRoutes = this.routes.filter(route => {
        // 检查 requiresAuth
        if (route.meta) {
          if (route.meta.requiresAuth && !this.isAuthenticated) {
            console.log(`Exclude ${route.name} because it requires authentication.`)
            return false;
          }
          // 检查 blockWhenAuthenticated
          if (route.meta.blockWhenAuthenticated && this.isAuthenticated) {
            console.log(`Exclude ${route.name} because it blocks when authenticated.`)
            return false;
          }
          // 检查 requiresPermission
          if (route.meta.requiresPermission) {
            for (let permission of route.meta.requiresPermission) {
              if (!this.hasPermission(permission)) {
                console.log(`Exclude ${route.name} because it requires permission ${permission}.`)
                return false;
              }
            }
          }
        }
        return true;
      });
    }
  },
  computed: {
    ...mapGetters(['isAuthenticated', 'hasPermission']),
    ...mapState(['isInitialized', 'permissions']),
    groupedRoutes() {
      const groupedRoutes = {};
      const routes = this.filteredRoutes;
      routes.forEach(route => {
        // 获取route的groupIndex
        const groupName = route.meta && typeof route.meta.groupName !== 'undefined'
            ? route.meta.groupName
            : null;

        if (groupName !== null) {
          // 初始化组，如果还没有初始化
          if (!groupedRoutes[groupName]) {
            groupedRoutes[groupName] = [];
          }
          // 将route添加到对应的组
          groupedRoutes[groupName].push(route);
        } else {
          // 如果没有groupName，将route添加到ungrouped组
          if (!groupedRoutes['ungrouped']) {
            groupedRoutes['ungrouped'] = [];
          }
          groupedRoutes['ungrouped'].push(route);
        }
      });
      return groupedRoutes;
    }
  },
  watch: {
    isInitialized: {
      immediate: true,
      handler(newVal, oldVal) {
        // 等待初始化后再过滤路由
        if (newVal) {
          this.filterRoutes();
        }
      }
    },
    isAuthenticated(newVal, oldVal) {
      // 在已经初始化，然后改变登录状态的情况下重新过滤路由
      if (this.isInitialized && this.permissions !== null) {
        this.filterRoutes();
      }
    },
    permissions(newVal, oldVal) {
      // 在刷新页面，首次登录后，等待权限初始化后再过滤路由
      if (newVal !== null && this.isAuthenticated) {
        this.filterRoutes();
      }
    }
  },
};
</script>

<style scoped>
.layout-menu {
  width: 220px;
  border-radius: 8px;
  position: absolute;
  left: 20px;
  top: 20px;
  overflow: hidden;
  transition: width .3s ease;
}

.layout-menu .menu-logo {
  font-size: 30px;
  text-align: center;
  padding: 20px 0;
  margin: 0;
  cursor: pointer;
  white-space: nowrap;
}

.menu-logo img {
  margin-right: 10px;
  width: 38px;
}

.menu-groups {
  height: calc(100vh - 172px);
  overflow: hidden;
}

.menu-group {
  padding: 0 30px;
  margin-bottom: 20px;
}

.menu-group .g-title {
  font-size: 16px;
  margin-bottom: 8px;
  padding-left: 15px;
  color: rgba(0, 0, 0, .631372549);
}

.menu-group .g-links {
  list-style: none;
  padding: 0;
  margin: 0;
  overflow: hidden;
}

.menu-group .g-links li {
  margin-bottom: 5px;
}

.menu-group .g-links .link {
  display: flex;
  padding: 12px 25px 12px 15px;
  border-radius: 8px;
  align-items: center;
  flex-direction: row;
  flex-wrap: nowrap;
  cursor: pointer;
}

.menu-group .g-links li.is-active .link {
  background-color: #e8f0ff;
}

.menu-group .g-links .tit {
  font-size: 16px;
  color: #000;
  margin-left: 10px;
  white-space: nowrap;
}

.version {
  font-size: 12px;
  padding: 15px 10px;
  color: #999;
  text-align: center;
  margin: 0;
}
</style>
