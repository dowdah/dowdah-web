<template>
  <a-skeleton :paragraph="{rows: 40}" active />
</template>

<script>
import {mapGetters} from 'vuex';

export default {
  name: 'Home',
  computed: {
    ...mapGetters(['isAuthenticated'])
  }
};
</script>
