<template>
  <div class="layout-topbar">
    <div class="topbar-collapse">
<!--      <div class="svg-icon">-->
<!--        <img-->
<!--            src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAC4AAAAuCAYAAABXuSs3AAAACXBIWXMAAAsTAAALEwEAmpwYAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAChSURBVHgB7dixDQIxDIVhh7sBoL0UMAKMwihMBhuwAmxwTXrooiRSMO0RJAoiufi/xpLl4pXWEwEAAL9zraX3fu+cW4sB4zjObx/71rGGvtZaTQTPOT90bJb7ZvBSykHHVgwYhuEpAABY0fxVpmk6W/lV1C2EcFouV61LDT2LEZplJwAAWNG1nvhWLfxD13oipXTRcZQOutYTMca7AAAAA161FyrWuNUI0AAAAABJRU5ErkJggg==">-->
<!--      </div>-->
      <MenuOutlined />
      <div class="title">{{ $store.state.topBarTitle }}</div>
    </div>
    <div class="corner-bar">
      <div class="item">
        <a-dropdown placement="bottomRight" arrow v-if="user">
          <a-button class="rightbar">
            <span class="avatar">{{ avatar }}</span>
            <span class="name">{{ user.username }}</span>
          </a-button>
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
          <a-button class="rightbar">
            <span class="avatar">N</span>
            <span class="name">未登录</span>
          </a-button>
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
    </div>
  </div>
</template>

<script>
import {mapState} from 'vuex';

export default {
  name: 'TopBar',
  computed: {
    ...mapState(['user']),
    avatar() {
      return this.user.username[0].toUpperCase();
    }
  }
};
</script>

<style>
.layout-topbar {
  position: absolute;
  left: 260px;
  height: 80px;
  top: 0;
  right: 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px 0 10px;
  background-color: hsla(0, 0%, 98%, .8);
  -webkit-backdrop-filter: saturate(180%) blur(20px);
  backdrop-filter: saturate(180%) blur(20px);
  z-index: 5;
}

.topbar-collapse {
  display: flex;
  flex-direction: row;
  align-items: center;
}

.topbar-collapse .title {
  font-size: 24px;
  margin-left: 20px;
}

.corner-bar {
  display: flex;
  align-items: center;
  margin-right: -8px;
}

.corner-bar .item {
  cursor: pointer;
  margin: 0 8px;
}

.corner-bar .avatar {
  display: flex;
  justify-content: center;
  align-items: center;
  font-weight: 700;
  font-size: 16px;
  color: #bc3aaf;
  line-height: 1;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background-color: #fff;
  filter: drop-shadow(0 0 4px rgba(0, 0, 0, .08));
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
  padding: 4px;
  border-radius: 30px;
  background-color: #f2f2f2;
  box-shadow: inset 0 0 5px 0 rgba(0, 0, 0, .05);
}
</style>
