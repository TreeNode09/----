<template>
<el-container style="height: 100%;" class="file">
  <el-aside style="width: calc(50vw - 20px); height: 100%;">
    <el-empty v-if="firstVideo" :image-size="200" :description="uploadStat + '中'" style="height: calc(calc(50vw - 20px) * 0.75);"/>
    <video ref="videoPlayer" controls @timeupdate="console.log(videoPlayer.duration)"
      :class="{'none': firstVideo === true}" style="width: 100%; height: calc(calc(50vw - 20px) * 0.75);">
    </video>
    <div style="margin-top: 5px;">
      <div class="half">
        <info-icon><upload-filled/></info-icon>
        <connect-info :type="socketStat">{{ socketMessage }}</connect-info>
      </div>
      <div class="half"></div>
    </div>
  </el-aside>
  <el-main style="padding: 0 0 0 20px;">
    <el-upload v-model:file-list="fileList" ref="upload" action :class="{'trigger-on': uploadStat==='选择'||uploadStat==='完成'}"
      :http-request="uploadVideo" :on-change="checkFormat" :on-remove="checkFormat"
      @mouseover="()=>{if(uploadStat==='完成')uploadStat='选择'}"
      @mouseleave="()=>{if(!firstVideo&&uploadStat==='选择')uploadStat='完成'}"
      :auto-upload="false" :multiple="false" :limit="1" list-type="text">
      <template #trigger>
        <el-button v-if="uploadStat==='选择'" class="full"  type="primary" :icon="DocumentAdd">
          <span>选择视频 (<span v-for="format in allowedFormats">{{ format }},&nbsp;</span>≤{{ maxSizeMB }}MB)</span>
        </el-button>
        <el-button v-if="uploadStat==='完成'" class="full"  type="success" :icon="Select">
          <span>完成! 点击继续上传视频</span>
        </el-button>
      </template>
      <el-button v-if="uploadStat==='上传'" class="full" type="primary" 
        :disabled="!isConnected" :icon="Upload" @click="submitUpload">上传</el-button>
      <el-button v-if="uploadStat==='处理'" class="full" type="primary">处理中 {{ (videoProgress * 100).toFixed(1) }}%</el-button>
      <div v-if="uploadStat==='处理'"
        style="display: inline-block; position: absolute; right: 20px; height: 50px;
        background-color: rgba(255, 255, 255, 0.3); transition: all 0.5s ease-in-out;"
        :style="{width: 'calc(calc(50vw - 40px) * ' + (1 - videoProgress) + ')'}"></div>
      <div v-if="uploadStat==='处理'" style="display: inline-block; position: absolute; right: 20px; height: 50px;">
        <el-button style="height: 40px; width: 40px; margin: 5px;" :icon="CloseBold" text @click="cancelProcess"></el-button>
      </div>
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
          <el-checkbox-button value="cp">车辆行人</el-checkbox-button>
          <el-checkbox-button value="sign">交通标志</el-checkbox-button>
        </el-checkbox-group>        
      </div>
      <div id="line-chart" style="height: 400px;"></div>
    </div>
  </el-main>
</el-container>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, useTemplateRef } from 'vue'
import { io } from 'socket.io-client'
import { ElNotification } from 'element-plus'
import { Clock, CloseBold, DocumentAdd, Select, Upload, UploadFilled } from '@element-plus/icons-vue'
import axios from 'axios'
import * as echarts from 'echarts'

import ConnectInfo from './ConnectInfo.vue'
import InfoIcon from './InfoIcon.vue'

const upload = ref(null)
const videoPlayer = ref(null)
const fileList = ref([])
const uploadStat = ref('选择')
const isConnected = ref(false)
const videoProgress = ref(0.0)
const socketStat = ref('off')
const socketMessage = ref('未连接')
const firstVideo = ref(true)

const targetFPS = ref(10)
const originalFPS = ref(10)
const detectOptions = ref([])

let socket = null
let options = [0, 0, 0] //视频文件用flask接收，拿到的是字符串，这样可以直接在Python里转成布尔型

let lineChart = null
let lineAxis = []
let lineData = null

const videoURL = ref('')

const allowedFormats = ['.mp4', '.avi']  //允许上传的视频格式
const maxSizeMB = 100
const HOST_IP = import.meta.env.VITE_BASE_URL //后端url

onMounted(() => {
  upload.value = useTemplateRef('upload')
  videoPlayer.value = useTemplateRef('videoPlayer')
  lineChart = echarts.init(document.getElementById('line-chart'))
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
    
    socket.on('disconnect', (reason) => {
      updateSocketStat('off', '未连接')
      popNotification('warning', '已断开连接: ' + reason)
    })

    //接收视频处理进度
    socket.on('updateProgress', (data) => {
      videoProgress.value = data.progress
    })

    socket.on('finishProcess', (data) => {
      videoProgress.value = 1.0
      if (data.totalFrame == -1) return
      lineData = data.analysis
      lineAxis = []
      for (let i = 0; i < data.totalFrame; i++) { //得到折线图的时间轴
        let frameTime = Math.floor(i * 1000 / targetFPS.value)
        let minute = Math.floor(frameTime / (60 * 1000))
        let second = (frameTime - minute * 60 * 1000) / 1000
        lineAxis.push(minute.toString() + (second < 10 ? ":0" : ":") + second.toFixed(2))
      }
      getProcessedVideo()
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

function uploadVideo(item){
  if (detectOptions.value.includes('road')) options[0] = 1
  else options[0] = 0
  if (detectOptions.value.includes('cp')) options[1] = 1
  else options[1] = 0
  if (detectOptions.value.includes('sign')) options[2] = 1
  else options[2] = 0

  let data = new FormData()
  data.append("video", item.file)
  data.append("options", options)
  data.append('fps', targetFPS.value)

  axios.post('/upload', data
  ).then(response => {
    uploadStat.value = '处理'
    updateSocketStat('working', '处理中')
  }).catch(error => {alert(error)})
}

//添加文件后立刻检查文件格式
const checkFormat = (file, files) => {
  console.log(fileList.value)
  if (files.length === 0) {
    uploadStat.value = '选择'
    return
  }
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
    getOriginalFPS(new Blob([file.raw]))
    .then((result) => originalFPS.value = result)
    .catch((error) => console.log(error))
  }
}

const getOriginalFPS = (file) => {
  return new Promise((resolve, reject) => {
    window.MediaInfo().then((media) => {
      media.analyzeData(
        () => {return file.size},
        (chunkSize, offset) => {
          return new Promise((resolve, reject) => {
            const reader = new FileReader()
            reader.onload = (event) => {
              if (event.target.error) reject(event.target.error)
              else resolve(new Uint8Array(event.target.result))
            }
            reader.readAsArrayBuffer(file.slice(offset, offset + chunkSize))
          })
        }
      ).then((result) => {
        resolve(result.media.track[0].FrameRate)
      }).catch((error) => reject(error))
    }).catch((error) => reject(error))
  })
}

const submitUpload = () =>{
  upload.value.submit()
}

const cancelProcess = () => {
  socket.emit('cancelProcess')
  uploadStat.value = '上传'
  updateSocketStat('ready', '已就绪')
}

const getProcessedVideo = () => {
  axios.get('/processed', {responseType: 'blob'})
  .then(response => {
    videoURL.value = URL.createObjectURL(response.data)
    videoPlayer.value.src = videoURL.value
    lineChart.setOption({
      tooltip: {trigger: 'axis'},
      legend: {data: ['车辆行人', '交通标志']},
      xAxis: {type: 'category', data: lineAxis},
      yAxis: {type: 'value'},
      series: [
        {name: '车辆行人', data: lineData.cpCount, type: 'line', showSymbol: false, smooth: true},
        {name: '交通标志', data: lineData.signCount, type: 'line', showSymbol: false, smooth: true}
      ]
    })
    uploadStat.value = '完成'
    updateSocketStat('ready', '已就绪')
    fileList.value = []
    firstVideo.value = false
  }).catch(error => alert(error))
}

onBeforeUnmount(() => {
  if (socket) socket.disconnect()
})
</script>