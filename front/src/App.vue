<template>
<el-container style="height: 100%; width: 100vw;">
  <el-header height="50px">
    <div style="margin-top: 15px;">
      <span :class="{'camera': !isVideo}">实时录制</span>
      <el-switch class="switch" v-model="isVideo" size="large"/>
      <span :class="{'video': isVideo}">本地视频</span>
    </div>  
  </el-header>
  <el-main>
    <UploadVideo v-if="isVideo"/>
    <VideoStream v-if="!isVideo"/>
  </el-main>
</el-container>
</template>

<script setup>
import { ref } from 'vue'
import UploadVideo from './components/UploadVideo.vue'
import VideoStream from './components/VideoStream.vue'

const isVideo = ref(false)
</script>

<style>
#app
{
  height: 100vh;
  margin: 0;
  padding: 0;
}

.half
{
  width: calc(50% - 10px);
  padding: 0 5px;
  display: inline-block;
  vertical-align: top;
}

.none
{
  display: none;
}

.el-switch.switch
{
  padding: 0 10px;
  --el-switch-on-color: var(--el-color-primary);
  --el-switch-off-color: var(--el-color-success);
}

.camera
{
  color: var(--el-color-success);
  font-weight: bold;
}

.video
{
  color: var(--el-color-primary);
  font-weight: bold;
}

.el-button.full
{
  width: 100%;
  height: 50px;

  font-size: larger;
  font-weight: bold;
}

.el-notification.right
{
  --el-notification-width: 250px;
}

.half .el-slider
{
  --el-slider-button-size: 15px;  
}

.stream .el-slider
{
  --el-slider-main-bg-color: var(--el-color-success);
}

.stream .el-checkbox-button
{
    --el-checkbox-button-checked-bg-color: var(--el-color-success);
    --el-checkbox-button-checked-border-color: var(--el-color-success);
}

.stream .el-checkbox-button__inner:hover
{
  color: var(--el-color-success);
}

.el-upload
{
  width: 100%;
}

.no-trigger .el-upload--picture
{
  display: none;
}
</style>
