<template>
<!--  <Dashboard v-if="isAuthenticated"></Dashboard>-->
  <a-skeleton :paragraph="{rows: 40}" active />
</template>

<script>
import Dashboard from '../components/Dashboard.vue';
import {mapGetters} from 'vuex';

export default {
  name: 'Home',
  components: {Dashboard},
  computed: {
    ...mapGetters(['isAuthenticated'])
  }
};
</script>
