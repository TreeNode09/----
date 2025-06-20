<template>
<el-container style="height: 100%;" class="file">
  <el-aside style="width: calc(50vw - 20px); height: 100%;">
    <el-empty v-if="!isProcessing" :image-size="200" description="尚未上传" style="height: calc(calc(50vw - 20px) * 0.75);"/>
    <img :src="imageSource" :class="{'none': !isProcessing}" style="width: 100%; height: calc(calc(50vw - 20px) * 0.75);">
  </el-aside>
  <el-main style="padding: 0 0 0 20px;">
    <el-upload v-model:file-list="fileList" ref="upload" action :http-request="uploadVideo"
      :auto-upload="false" :multiple="false" :limit="1" list-type="picture" :class="{'no-trigger': fileList.length!==0}"> 
      <template #trigger>
        <el-button v-if="fileList.length===0" class="full" type="primary" plain :icon="DocumentAdd">选择视频</el-button>
      </template>
      <el-button v-if="fileList.length!==0" class="full" type="primary" :icon="Upload" @click="submitUpload">上传</el-button>
      <template #tip v-if="fileList.length===0">
        <div class="el-upload__tip">允许上传的视频格格式: MP4</div>
      </template>
    </el-upload>
    <div style="margin-top: 10px;">
      <div style="width: 60%; display: inline-block;">
        <div class="half"><info-icon><clock/></info-icon> 帧率
          <el-slider v-model="targetFPS" :min="1" :max="30" :disabled="isProcessing"
            style="width: calc(100% - 130px); margin: 0 12px; display: inline-flex; vertical-align: middle;"/>
          <strong>{{ targetFPS }}</strong>FPS
        </div>
        <div class="half"><info-icon><picture-filled/></info-icon> 画质
          <el-slider v-model="streamQuality" :min="0" :max="1" :step="0.1" :disabled="isProcessing"
            style="width: calc(100% - 120px); margin: 0 12px; display: inline-flex; vertical-align: middle;"/>
          <strong>{{ streamQuality.toFixed(1) }}</strong>
        </div>        
      </div>
      <div style="width: 40%; display: inline-block; vertical-align: top;">
        <el-checkbox-group v-model="detectOptions" :disabled="isProcessing" style="float: right;">
          <el-checkbox-button value="road" disabled>车道</el-checkbox-button>
          <el-checkbox-button value="sign">交通标志</el-checkbox-button>
          <el-checkbox-button value="cp">车辆行人</el-checkbox-button>
        </el-checkbox-group>        
      </div>
    </div>
  </el-main>
</el-container>
</template>

<script setup>
import { ref, onMounted, useTemplateRef } from 'vue'
import { ElNotification } from 'element-plus'
import { Clock, DocumentAdd, PictureFilled, Upload } from '@element-plus/icons-vue'
import axios from 'axios'

import InfoIcon from './InfoIcon.vue'

const upload = ref(null)
const fileList = ref([])
const message = ref('')
const isSelected = ref(false)
const isProcessing = ref(false)

const targetFPS = ref(10)
const streamQuality = ref(0.5)
const detectOptions = ref([])

const imageSource = import.meta.env.VITE_BASE_URL + '/video-feed'

onMounted(() => {
  upload.value = useTemplateRef('upload')
})

function uploadVideo(item){
    let data = new FormData()
    data.append("video", item.file)
    console.log(item)

    isProcessing.value = true

    axios.post('/upload', data
        ).then(response => {
            message.value = response.data
        })
        .catch(error => {alert(error)})
}

const submitUpload = () =>{
  upload.value.submit()
  console.log(fileList.value)
}
</script>
