<template>
  <a-flex verticle="true" justify="space-between" align="middle">
    <a-flex verticle="true" align="center">
      <menu-unfold-outlined
          v-if="collapsed"
          @click="$emit('toggle-collapse')"
          class="trigger"
      />
      <menu-fold-outlined v-else class="trigger" @click="$emit('toggle-collapse')"/>
      <div class="title">{{ $store.state.topBarTitle }}</div>
    </a-flex>
    <a-flex verticle="true" align="center" class="corner-bar">
      <div class="item">
        <a-dropdown placement="bottomRight" arrow v-if="user">
          <template #default>
            <a-button class="rightbar">
              <a-avatar>{{ avatar }}</a-avatar>
              <span class="name">{{ user.username }}</span>
            </a-button>
          </template>
          <template #overlay>
            <a-menu>
              <a-menu-item>
                <a href="javascript:;">个人中心</a>
              </a-menu-item>
              <a-menu-item>
                <a href="javascript:;">退出登录</a>
              </a-menu-item>
            </a-menu>
          </template>
        </a-dropdown>
        <a-dropdown placement="bottomRight" arrow v-else>
          <template #default>
            <a-button class="rightbar">
              <a-avatar>N</a-avatar>
              <span class="name">未登录</span>
            </a-button>
          </template>
          <template #overlay>
            <a-menu>
              <a-menu-item>
                <a href="javascript:;">登录</a>
              </a-menu-item>
              <a-menu-item>
                <a href="javascript:;">注册</a>
              </a-menu-item>
            </a-menu>
          </template>
        </a-dropdown>
      </div>
    </a-flex>
  </a-flex>
</template>

<script>
import {MenuFoldOutlined, MenuUnfoldOutlined} from '@ant-design/icons-vue';
import {mapState} from 'vuex';

export default {
  name: 'TopBar',
  props: ['collapsed'],
  emits: ['toggle-collapse'],
  components: {
    MenuFoldOutlined,
    MenuUnfoldOutlined
  },
  computed: {
    ...mapState(['user']),
    avatar() {
      return this.user && this.user.username ? this.user.username[0].toUpperCase() : '';
    },
  },
};
</script>

<style scoped>
.trigger {
  font-size: 18px;
  line-height: 64px;
  cursor: pointer;
  transition: color 0.3s;
}

.trigger:hover {
  color: #1890ff;
}

.title {
  font-size: 24px;
  margin-left: 20px;
}

.corner-bar {
  margin-right: -8px;
}

.corner-bar .item {
  cursor: pointer;
  margin: 0 8px;
}

.corner-bar .name {
  font-weight: 700;
  font-size: 16px;
  margin: 0;
  line-height: 1;
  margin-right: 10px;
  margin-left: 10px;
}

.corner-bar .rightbar {
  display: flex;
  flex-direction: row;
  align-items: center;
  padding: 20px 10px;
  border-radius: 30px;
  box-shadow: inset 0 0 5px 0 rgba(0, 0, 0, 0.05);
}
</style>