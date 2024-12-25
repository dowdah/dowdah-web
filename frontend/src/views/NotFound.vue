<template>
  <a-result status="404" title="404" sub-title="给我干哪来了？这还是地球吗？">
    <template #extra>
      <a-button type="primary" @click="$router.push('/')">回家</a-button>
    </template>
  </a-result>
</template>

<script>
export default {
  name: 'NotFound',
};
</script>
