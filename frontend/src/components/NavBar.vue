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
import {AppstoreOutlined, SettingOutlined} from '@ant-design/icons-vue';
import {mapState, mapMutations} from 'vuex';

export default {
  data() {
    return {
      selectedKeys: [],
      openKeys: [],
      menuItems: [],
    };
  },
  created() {
    const router = this.$router;

    // 动态生成菜单项
    const generateMenuItems = () => {
      const groupedRoutes = router.options.routes.reduce((groups, route) => {
        const groupName = route.meta && route.meta.groupName;
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
        return groups;
      }, {});

      return Object.entries(groupedRoutes).map(([groupName, routes]) => {
        if (groupName === '__ungrouped__') {
          // 没有 groupName 的路由单独成项
          return routes.map((route) => ({
            key: route.path,
            icon: () => h(SettingOutlined),
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
            })),
          };
        }
      }).flat();
    };

    // 初始化菜单
    this.menuItems = generateMenuItems();
    this.selectedKeys = [this.$route.path];
  },
  methods: {
    ...mapMutations(['changeTheme']),
    handleMenuClick({key}) {
      this.$router.push(key);
    },
  },
  computed: {
    ...mapState(['theme']),
  },
};
</script>
