<template>
   <a-config-provider :theme="currentTheme">
     <a-spin :spinning='isLoading' :delay="500" tip="加载中..." size="large" :indicator="loadingIndicator">
  <a-layout style="min-height: 100vh" has-sider>
    <a-layout-sider v-model:collapsed="collapsed" :trigger="null" collapsible
                    :style="{ overflow: 'auto', height: '100vh', position: 'fixed', left: 0, top: 0, bottom: 0 ,
                    backgroundColor: theme === 'dark' ? '#141414' : '#fff' }">
      <div class="logo"><a-avatar src="/favicon.ico" /><span :style="{ position: 'fixed', top: '20px', left: '52px',
      display: collapsed ? 'none':'inline-block', fontSize: '20px', fontWeight: 'bold'}">{{ title }}</span></div>
      <NavBar/>
    </a-layout-sider>
    <a-layout :style="{ marginLeft: leftMargin, transition: 'margin-left 0.2s' }">
      <a-layout-header :style="{ paddingInline: '20px', backgroundColor: theme === 'dark' ? '#141414' : '#fff'}">
        <TopBar @toggle-collapse="collapsed = !collapsed" :collapsed="collapsed"
        @show-login-modal="showLoginModal = true"/>
      </a-layout-header>
      <a-layout-content :style="{ margin: '24px 16px 0', overflow: 'initial' }">
        <router-view></router-view>
      </a-layout-content>
      <a-layout-footer style="text-align: center">
        {{ title }} ©{{ currentYear }} Created by 练习时长两年半的个人练习生 测试版本不代表最终品质
      </a-layout-footer>
    </a-layout>
  </a-layout>
  <LoginModal v-model:mOpen="showLoginModal"/>
  </a-spin>
  </a-config-provider>
</template>

<script>
import { theme } from 'ant-design-vue';
import {mapGetters, mapState} from 'vuex';
import { LoadingOutlined } from '@ant-design/icons-vue';
import { h } from 'vue';
import NavBar from "./components/NavBar.vue";
import TopBar from "./components/TopBar.vue";
import LoginModal from "./components/LoginModal.vue";
import dayjs from 'dayjs';

export default {
  name: 'App',
  components: {
    TopBar,
    NavBar,
    LoginModal
  },
  data() {
    return {
      collapsed: false,
      showLoginModal: false,
      loadingIndicator: h(LoadingOutlined, {style: {fontSize: '30px'}})
    };
  },
  computed: {
    ...mapGetters(['isAuthenticated']),
    ...mapState(['user', 'title', 'theme', 'isLoading']),
    unconfirmed() {
      return this.isAuthenticated && !this.user.confirmed;
    },
    currentTheme() {
      return {
        algorithm: this.theme === 'light' ? theme.defaultAlgorithm : theme.darkAlgorithm
      }
    },
    leftMargin() {
      return this.collapsed ? '80px' : '200px';
    },
    currentYear() {
      return dayjs().format('YYYY');
    }
  }
};
</script>

<style>
body {
  font-family: open sans, Helvetica, Arial, sans-serif;
  color: #000;
}

.use-shadow {
  border-radius: 6px;
  background-color: #fff;
  box-shadow: 0 0 16px 0 rgba(0, 0, 0, .04);
}

html, body, #app {
  margin: 0;
  padding: 0;
  width: 100%;
  height: 100%;
}

.logo {
  height: 32px;
  margin: 16px;
}

/* 自定义滚动条样式 */

::-webkit-scrollbar {
  height: 8px; /* 设置滚动条的高度 */
}

::-webkit-scrollbar-track {
  background: #f1f1f1; /* 滚动条轨道背景色 */
}

::-webkit-scrollbar-thumb {
  background: #888; /* 滚动条滑块背景色 */
  border-radius: 4px; /* 滚动条滑块圆角 */
}

::-webkit-scrollbar-thumb:hover {
  background: #555; /* 滚动条滑块悬停时背景色 */
}
</style>