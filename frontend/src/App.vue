<template>
  <div id="app">
    <div class="layout-container">
      <NavBar/>
      <TopBar/>
      <div class="layout-main">
        <router-view></router-view>
      </div>
    </div>
    <LoadingSpinner/>
  </div>
</template>

<script>
import {mapGetters, mapState} from 'vuex';
import LoadingSpinner from "./components/LoadingSpinner.vue";
import NavBar from "./components/NavBar.vue";
import TopBar from "./components/TopBar.vue";

export default {
  name: 'App',
  data() {
    return {
      title: process.env.VUE_APP_TITLE
    };
  },
  components: {
    TopBar,
    NavBar,
    LoadingSpinner
  },
  computed: {
    ...mapGetters(['isAuthenticated']),
    ...mapState(['user']),
    unconfirmed() {
      return this.isAuthenticated && !this.user.confirmed;
    }
  }
};
</script>

<style>
body {
  font-family: open sans, Helvetica, Arial, sans-serif;
  color: #000;
}

#app {
  position: relative;
  z-index: 2;
}

.layout-container {
  background-color: #fafafa;
  height: 100vh;
  overflow: hidden;
}

.layout-container .layout-main {
  position: absolute;
  left: 260px;
  top: 0;
  right: 0;
  bottom: 0;
  overflow: auto;
  padding: 80px 20px 0;
}

.use-shadow {
  border-radius: 6px;
  background-color: #fff;
  box-shadow: 0 0 16px 0 rgba(0, 0, 0, .04);
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