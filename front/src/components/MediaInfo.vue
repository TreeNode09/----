<template>
<div style="height: 30px; margin: 0 5px;">
  <div v-if="props.type==='ready'" class="dot" style="background-color: var(--el-color-success);"></div>
  <div v-if="props.type==='working'" class="dot" style="background-color: var(--el-color-danger);"></div>
  <div v-if="props.type==='error'" class="dot" style="background-color: var(--el-color-warning);"></div>
  <div v-if="props.type==='off'" class="dot" style="width: 9px; height: 9px; border: solid 3px var(--el-text-color-disabled);"></div>

  <div v-if="props.type==='error'" style="color: var(--el-color-danger-dark-2);"><slot></slot></div>
  <div v-else><slot></slot></div>
</div>

</template>

<script setup>
const props = defineProps(['type'])
</script>

<style scoped>
div
{
  display: inline-block;
}

div > div
{
  vertical-align: middle;
}

.dot
{
  width: 15px;
  height: 15px;
  margin-right: 5px;

  border-radius: 50%;
}
</style>