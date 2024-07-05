<template>
  <div id="app">
    <h3>{{ title }}</h3>
    <router-view></router-view>
    <LoadingSpinner/>
  </div>
</template>

<script>
import {mapGetters, mapState} from 'vuex';
import LoadingSpinner from '@/components/LoadingSpinner.vue';

export default {
  name: 'App',
  data() {
    return {
      title: process.env.VUE_APP_TITLE
    };
  },
  components: {
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
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  margin-top: 60px;
}

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