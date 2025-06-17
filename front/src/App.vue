<template>
<el-button-group>
  <el-button @click="toVideo">视频</el-button>
  <el-button @click="toCamera">摄像头</el-button>
</el-button-group>
<UploadVideo v-if="isVideo"/>
<VideoStream v-if="!isVideo"/>
</template>

<script setup>
import { ref } from 'vue'
import UploadVideo from './components/UploadVideo.vue'
import VideoStream from './components/VideoStream.vue'

const isVideo = ref(false)

const toVideo = () => {
  isVideo.value = true
}

const toCamera = () => {
  isVideo.value = false
}
</script>

<style scoped>

</style>
