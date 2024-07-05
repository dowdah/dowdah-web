<template>
  <transition name="spinner">
    <div class="spinner-overlay" v-if="isLoading">
      <div class="spinner"></div>
    </div>
  </transition>
</template>

<script>
import {mapState} from 'vuex';

export default {
  computed: {
    ...mapState(['isLoading'])
  }
}
</script>

<style>
.spinner-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1001;
}

.spinner {
  border: 16px solid #f3f3f3;
  border-radius: 50%;
  border-top: 16px solid #3498db;
  width: 120px;
  height: 120px;
  animation: spin 2s linear infinite;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

.spinner-enter-active,
.spinner-leave-active {
  transition: opacity 100ms ease;
}

.spinner-enter-from,
.spinner-leave-to {
  opacity: 0;
}
</style>
