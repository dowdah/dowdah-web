<template>
  <a-result status="403" title="403" sub-title="您配吗？">
    <template #extra>
      <a-button type="primary" @click="$router.push('/')">回家</a-button>
    </template>
  </a-result>
</template>

<script>
export default {
  name: 'PermissionDenied',
};
</script>
