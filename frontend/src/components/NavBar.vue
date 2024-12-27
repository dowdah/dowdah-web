<template>
  <a-menu
      v-model:openKeys="openKeys"
      v-model:selectedKeys="selectedKeys"
      mode="inline"
      :items="menuItems"
      @click="handleMenuClick"
  />
</template>

<script>
import {h} from 'vue';
import {QuestionCircleOutlined, AppstoreOutlined} from '@ant-design/icons-vue';
import {mapState, mapMutations, mapGetters} from 'vuex';

export default {
  data() {
    return {
      selectedKeys: [],
      openKeys: [],
      menuItems: []
    };
  },
  methods: {
    ...mapMutations(['changeTheme']),
    handleMenuClick({key}) {
      this.$router.push(key);
    },
    generateMenuItems() {
      const router = this.$router;
      const groupedRoutes = router.options.routes.reduce((groups, route) => {
        const groupName = route.meta && route.meta.groupName;
        const hidden = route.meta && route.meta.notShownInMenu;
        const requiresAuth = route.meta && route.meta.requiresAuth;
        const permissions = route.meta.requiresPermission;
        let hasPermission = true;
        if (permissions) {
          if (this.isAuthenticated) {
            hasPermission = permissions.some(permission => this.hasPermission(permission));
          } else {
            hasPermission = false;
          }
        }
        // console.log(route.name, requiresAuth, hasPermission);
        if (!(hidden || (requiresAuth && !this.isAuthenticated) || !hasPermission)) {
          if (groupName) {
            if (!groups[groupName]) {
              groups[groupName] = [];
            }
            groups[groupName].push(route);
          } else {
            if (!groups['__ungrouped__']) {
              groups['__ungrouped__'] = [];
            }
            groups['__ungrouped__'].push(route);
          }
        }
        return groups;
      }, {});

      this.menuItems = Object.entries(groupedRoutes).map(([groupName, routes]) => {
        if (groupName === '__ungrouped__') {
          // 没有 groupName 的路由单独成项
          return routes.map((route) => ({
            key: route.path,
            icon: () => route.meta.icon ? h(route.meta.icon) : h(QuestionCircleOutlined),
            label: route.name,
            title: route.name,
          }));
        } else {
          // 有 groupName 的路由生成子菜单
          return {
            key: groupName,
            icon: () => h(AppstoreOutlined),
            label: groupName,
            title: groupName,
            children: routes.map((route) => ({
              key: route.path,
              label: route.name,
              title: route.name,
              icon: () => route.meta.icon ? h(route.meta.icon) : h(QuestionCircleOutlined),
            })),
          };
        }
      }).flat();
    }
  },
  computed: {
    ...mapState(['theme', 'isInitialized', 'permissions']),
    ...mapGetters(['hasPermission', 'isAuthenticated']),
  },
  watch: {
    $route() {
      // 当路由变化时，更新选中的菜单项
      this.selectedKeys = [this.$route.path];
    },
    isInitialized: {
      immediate: true,
      handler(newVal, oldVal) {
        // 等待初始化后再过滤路由
        if (newVal) {
          this.generateMenuItems()
        }
      }
    },
    isAuthenticated(newVal, oldVal) {
      // 在已经初始化，然后改变登录状态的情况下重新过滤路由
      if (this.isInitialized && this.permissions !== null) {
        this.generateMenuItems()
      }
    },
    permissions(newVal, oldVal) {
      // 在刷新页面，首次登录后，等待权限初始化后再过滤路由
      if (newVal !== null && this.isAuthenticated) {
        this.generateMenuItems()
      }
    }
  },
};
</script>
