<template>

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
