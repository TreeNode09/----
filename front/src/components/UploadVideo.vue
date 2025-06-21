<template>
<el-container style="height: 100%;" class="file">
  <el-aside style="width: calc(50vw - 20px); height: 100%;">
    <el-empty v-if="uploadStat!=='下载'" :image-size="200" description="别急" style="height: calc(calc(50vw - 20px) * 0.75);"/>
    <video ref="videoPlayer" controls
      :class="{'none': uploadStat!=='下载'}" style="width: 100%; height: calc(calc(50vw - 20px) * 0.75);"></video>
    <div style="width: 40%; display: inline-block;">
      <info-icon><upload-filled/></info-icon>
      <connect-info :type="socketStat">{{ socketMessage }}</connect-info>
    </div>
  </el-aside>
  <el-main style="padding: 0 0 0 20px;">
    <el-upload v-model:file-list="fileList" ref="upload" action :http-request="uploadVideo" :on-change="checkFormat"
      :auto-upload="false" :multiple="false" :limit="1" list-type="text" :class="{'trigger-on': uploadStat==='选择'}"> 
      <template #trigger>
        <el-button v-if="uploadStat==='选择'" class="full" type="primary" plain :icon="DocumentAdd">
          选择视频 (<span v-for="format in allowedFormats">{{ format }},&nbsp;</span>≤{{ maxSizeMB }}MB)
        </el-button>
      </template>
      <el-button v-if="uploadStat==='上传'" class="full" type="primary" 
        :disabled="!isConnected" :icon="Upload" @click="submitUpload">上传</el-button>
      <el-button v-if="uploadStat==='处理'" class="full" type="primary">处理中 {{ (videoProgress * 100).toFixed(1) }}%</el-button>
      <div v-if="uploadStat==='处理'"
        style="display: inline-block; position: absolute; height: 50px;
        background-color: rgba(255, 255, 255, 0.3); transition: all 0.5s ease-in-out;"
        :style="{width: 'calc(calc(50vw - 20px) * ' + (1 - videoProgress) + ')',
        left: 'calc(50vw + calc(calc(50vw - 20px) * ' + videoProgress + '))'}"></div>
      <el-button v-if="uploadStat==='下载'" class="full" type="primary" :icon="Download">下载</el-button>
    </el-upload>
    <div style="margin-top: 10px;">
      <div style="width: 60%; display: inline-block;">
        <div class="half"><info-icon><clock/></info-icon> 帧率
          <el-slider v-model="targetFPS" :min="1" :max="originalFPS" :disabled="uploadStat!=='上传'"
            style="width: calc(100% - 130px); margin: 0 12px; display: inline-flex; vertical-align: middle;"/>
          <strong>{{ targetFPS }}</strong>FPS
        </div>
        <div class="half"></div>        
      </div>
      <div style="width: 40%; display: inline-block; vertical-align: top;">
        <el-checkbox-group v-model="detectOptions" :disabled="uploadStat!=='上传'" style="float: right;">
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
import { ref, onMounted, onBeforeUnmount, useTemplateRef } from 'vue'
import { io } from 'socket.io-client'
import { ElNotification } from 'element-plus'
import { Clock, DocumentAdd, Download, Upload, UploadFilled } from '@element-plus/icons-vue'
import axios from 'axios'

import ConnectInfo from './ConnectInfo.vue'
import InfoIcon from './InfoIcon.vue'

const upload = ref(null)
const videoPlayer = ref(null)
const fileList = ref([])
const message = ref('')
const uploadStat = ref('选择')
const isConnected = ref(false)
const videoProgress = ref(0.0)
const socketStat = ref('off')
const socketMessage = ref('未连接')

const targetFPS = ref(10)
const originalFPS = ref(30)
const detectOptions = ref([])

let socket = null
let options = [false, false, false]

const videoURL = ref('')

const allowedFormats = ['.mp4', '.avi']  //允许上传的视频格式
const maxSizeMB = 100
const HOST_IP = import.meta.env.VITE_BASE_URL //后端url

onMounted(() => {
  upload.value = useTemplateRef('upload')
  videoPlayer.value = useTemplateRef('videoPlayer')
  initSocket()
})

const initSocket = () => {
  if (socket) return
  
  try {
    socket = io(HOST_IP, {
      transports: ['websocket'],
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
    })
    
    socket.on('connect', () => {
      isConnected.value = true
      popNotification('success', 'WebSocket已连接')
      updateSocketStat('ready', '已就绪')
    })
    
    socket.on('disconnect', () => {
      updateSocketStat('off', '未连接')
    })

    //接收视频处理进度
    socket.on('updateProgress', (data) => {
      videoProgress.value = data.progress
      console.log(videoProgress.value)
    })

    socket.on('finishProcess', (data) => {
      videoProgress.value = 1.0
      uploadStat.value = '下载'
    })

    socket.on('connect_error', (error) => {
      isConnected.value = false
      fileList.value = []
      uploadStat.value = '选择'
      videoProgress.value = 0
      popNotification('error', 'WebSocket连接错误' + error)
      updateSocketStat('error', '连接错误')
    })

  } catch (error) {
    popNotification('error', 'WebSocket初始化失败' + error)
    updateSocketStat('error', '初始化失败')
  }
}

const getTime = () => {
  let time = new Date()
  let hour = time.getHours()
  let minute = time.getMinutes()
  let second = time.getSeconds()
  return hour + (minute < 10 ? ":0": ":") + minute + (second < 10 ? ":0": ":") + second
}

const popNotification = (type, message) => {
  ElNotification({
    type: type,
    dangerouslyUseHTMLString: true,
    message: '<div><strong>' + message + '</strong></div>' + getTime()
  })
}

const updateSocketStat = (stat, message) => {
  socketStat.value = stat
  socketMessage.value = message
}

async function uploadVideo(item){
  if (detectOptions.value.includes('road')) options[0] = true
  else options[0] = false
  if (detectOptions.value.includes('sign')) options[1] = true
  else options[1] = false
  if (detectOptions.value.includes('cp')) options[2] = true
  else options[2] = false

  let data = new FormData()
  data.append("video", item.file)
  data.append("options", options)
  data.append('fps', targetFPS.value)

  uploadStat.value = '处理'
  updateSocketStat('wordking', '处理中')

  await axios.post('/upload', data
    ).then(response => {
        message.value = response.data //视频处理完毕后才会得到response
    }).catch(error => {alert(error)})
  
  updateSocketStat('ready', '已就绪')
  getProcessedVideo()
}

//添加文件后立刻检查文件格式
const checkFormat = async(file, files) => {
  if (files.length === 0) return

  let fileName = file.name
  let extension = fileName.substring(fileName.lastIndexOf('.'))
  if (allowedFormats.indexOf(extension) === -1) {
    popNotification('error', `文件类型${extension}有误`)
    fileList.value = []
  }
  else if (file.size / 1024 / 1024 > maxSizeMB) {
    popNotification('error', '视频文件过大')
    fileList.value = []
  }
  else {
    uploadStat.value = '上传'
  }
}

const submitUpload = () =>{
  upload.value.submit()
}

const getProcessedVideo = async() => {
  try {
    const response = await axios.get('/processed', {responseType: 'blob'})
    videoURL.value = URL.createObjectURL(response.data)
    videoPlayer.value.src = videoURL.value

    uploadStat.value = '下载'
  }catch(error) {alert(error)}
}

//组件卸载时清理
onBeforeUnmount(() => {
  if (socket) socket.disconnect()
})
</script>