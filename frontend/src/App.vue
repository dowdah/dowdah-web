<template>
  <Fingerprint />
   <a-config-provider :theme="currentTheme">
     <a-spin :spinning='isLoading' :delay="500" size="large" :indicator="loadingIndicator">
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
        @show-login-modal="showLoginModal = true" @show-register-modal="showRegisterModal = true" />
      </a-layout-header>
      <a-layout-content :style="{ margin: '24px 16px 0', overflow: 'initial' }">
        <router-view></router-view>
      </a-layout-content>
      <a-layout-footer style="text-align: center">
        {{ title }} ©{{ currentYear }} Created by 练习时长两年半的个人练习生 测试版本不代表最终品质<br><br>
        <p>浏览和使用本网站提供的服务，视为您理解并同意
          <a href="https://r2.dowdah.com/Dowdah_ToS.txt" target="_blank">《服务条款》</a>。</p>
      </a-layout-footer>
    </a-layout>
  </a-layout>
  <LoginModal v-model:mOpen="showLoginModal"/>
  <RegisterModal v-model:mOpen="showRegisterModal"/>
  </a-spin>
  </a-config-provider>
</template>

<script>
import { theme } from 'ant-design-vue';
import { mapGetters, mapState } from 'vuex';
import { h } from 'vue';
import NavBar from "./components/NavBar.vue";
import TopBar from "./components/TopBar.vue";
import LoginModal from "./components/LoginModal.vue";
import RegisterModal from "./components/RegisterModal.vue";
import Fingerprint from "./components/Fingerprint.vue";
import dayjs from 'dayjs';

export default {
  name: 'App',
  components: {
    TopBar,
    NavBar,
    LoginModal,
    Fingerprint,
    RegisterModal
  },
  data() {
    return {
      collapsed: false,
      showLoginModal: false,
      showRegisterModal: false,
      loadingIndicator: h('img', {
        src: 'https://r2.dowdah.com/loading_0d00.png', // 你的图片路径
        class: 'loading-spin-img'
      })
    };
  },
  computed: {
    ...mapGetters(['isAuthenticated']),
    ...mapState(['user', 'title', 'theme', 'isLoading']),
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

@keyframes shake {
  0%   { transform: translate(-50%, -50%) rotate(0deg); }
  10%  { transform: translate(calc(-50% - 1px), calc(-50% + 1px)) rotate(-1deg); }
  20%  { transform: translate(calc(-50% + 1px), calc(-50% - 1px)) rotate(1deg); }
  30%  { transform: translate(calc(-50% - 1px), calc(-50% + 1px)) rotate(0deg); }
  40%  { transform: translate(calc(-50% + 1px), calc(-50% - 1px)) rotate(1deg); }
  50%  { transform: translate(calc(-50% - 1px), calc(-50% + 1px)) rotate(-1deg); }
  60%  { transform: translate(calc(-50% + 1px), calc(-50% - 1px)) rotate(0deg); }
  70%  { transform: translate(calc(-50% - 1px), calc(-50% + 1px)) rotate(1deg); }
  80%  { transform: translate(calc(-50% + 1px), calc(-50% - 1px)) rotate(-1deg); }
  90%  { transform: translate(calc(-50% - 1px), calc(-50% + 1px)) rotate(0deg); }
  100% { transform: translate(-50%, -50%) rotate(0deg); }
}

.loading-spin-img {
  width: 200px !important;
  height: 200px !important;
  position: fixed !important;
  top: 50% !important;
  left: 50% !important;
  animation: shake 0.5s infinite;
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