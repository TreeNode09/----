<template>
<div style="display: inline-block; vertical-align: text-top;" :style="{'width': props.width}">
  <div style="display: inline-block; margin-bottom: 15px; vertical-align: middle;">
    <info-icon><slot></slot></info-icon> {{ props.name }}&nbsp;
  </div>
  <span style="font-size: 35px; font-weight: bold;" :style="{'color': props.color}">{{ props.data }}</span>
  <span v-if="name==='最近距离'"> m</span>
</div>
</template>

<script setup>
import InfoIcon from './InfoIcon.vue'
const props = defineProps(['name', 'data', 'width', 'color'])
</script>