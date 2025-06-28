<template>
<el-container style="height: 100%;" class="file">
  <el-aside style="width: calc(50vw - 20px); height: 100%;">
    <el-empty v-if="firstVideo" :image-size="200" :description="uploadStat + '中'" style="height: calc(calc(50vw - 20px) * 0.75);"/>
    <video ref="videoPlayer" controls :class="{'none': firstVideo === true}" 
      style="width: 100%; height: calc(calc(50vw - 20px) * 0.75);">
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
          <el-checkbox-button value="road" :class="{'selected': detectOptions.includes('road')}">车道</el-checkbox-button>
          <el-checkbox-button value="cp" :class="{'selected': detectOptions.includes('cp')}">车辆行人</el-checkbox-button>
          <el-checkbox-button value="sign" :class="{'selected': detectOptions.includes('sign')}">交通标志</el-checkbox-button>
        </el-checkbox-group>        
      </div>
    </div>
    <div id="line-chart" style="height: calc(calc(calc(50vw - 20px) * 0.75) - 102px); margin-top: 10px;" @click="setVideoTime"></div>
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
let originalData = null
const sharedOptions = {type: 'line', showSymbol: false, smooth: true, emphasis: {focus: 'series'}}

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
      originalData = data.analysis   
      lineAxis = []
      for (let i = 0; i < data.totalFrame; i++) { //得到折线图的时间轴
        let frameTime = Math.floor(i * 1000 / targetFPS.value)
        let minute = Math.floor(frameTime / (60 * 1000))
        let second = (frameTime - minute * 60 * 1000) / 1000
        lineAxis.push(minute.toString() + (second < 10 ? ":0" : ":") + second.toFixed(2))
      }
      if (lineChart !== null) {lineChart.dispose()}
      lineChart = echarts.init(document.getElementById('line-chart'))
      lineChart.setOption({
        visualMap: [
          {
            show: false, type: 'continuous', seriesIndex: 3, min: 10, max: 70, calculable: true,
            inRange: {color: ['#F56C6C', '#E6A23C', '#67C23A']}
          },
          {
            show: false, type: 'continuous', seriesIndex: 4, min: 10, max: 70, dimension: 1,
            inRange: {color: ['#F56C6C', '#E6A23C', '#67C23A']}
          }
        ],
        grid: {top: '40px', bottom: '75px', left: '5%', right: '5%'},
        tooltip: {trigger: 'axis', axisPointer: {axis: 'x'}},
        dataZoom: {type: 'slider', show: true, xAxisIndex: [0], startValue: 0, endValue: 100},
        legend: {data: ['车辆', '行人', '交通标志', '最近距离']},
        xAxis: [
          {type: 'category', data: lineAxis},
          {type: 'value', min: 0, max: 100, show: false}
        ],
        yAxis: [
          {name: '个数', type: 'value', minInterval: 1, axisLine: {show: true, lineStyle: {color: '#337ECC'}}},
          {name: '距离(m)', type: 'value', minInterval: 1, position: 'right', axisLine: {show: false}},
          {name: 'axis', type: 'category', show: false, boundaryGap: false,data: Array.from(new Array(100), (v, k) => k)}
        ],
        series: [
          Object.assign({
            name: '车辆', data: smoothData(5, originalData.carCount, 0, true), color: '#337ECC'
          }, sharedOptions),
          Object.assign({
            name: '行人', data: smoothData(5, originalData.personCount, 0, true), color: '#79BBFF'
          }, sharedOptions),
          Object.assign({
            name: '交通标志', data: smoothData(5, originalData.signCount, 0, true), color: '#9FCEFF'
          }, sharedOptions),
          Object.assign({
            name: '最近距离', data: smoothData(5, originalData.minDistance, 5, false), color: '#F56C6C',
            yAxisIndex: 1, lineStyle: {width: 3}
          }, sharedOptions),
          Object.assign({
            name: 'axis', data: new Array(100).fill(100),
            xAxisIndex: 1, yAxisIndex: 2, animation: false, tooltip: {show: false}, lineStyle: {width: 3}
        }, sharedOptions)
        ]
      })
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

const smoothData = (boxSize, original, offset, toInt) => {
  let smoothed = []
  let dataBox = 0
  for (let i = 0; i < original.length; i++) {
    if (original[i] === 10000) {
      smoothed.push(NaN)
      continue
    }
    dataBox += original[i]
    if (i < boxSize) smoothed.push((dataBox / (i + 1)).toFixed(2))
    else {
      dataBox -= original[i - boxSize]
      smoothed.push((dataBox / boxSize).toFixed(2))
    }
  }
  if (toInt === true) {
    for (let i = 0; i < smoothed.length; i++) smoothed[i] = Math.floor(smoothed[i])
  }
  if (offset !== 0) {
    for (let i = 0; i < offset; i++) smoothed[i] = NaN
  }
  return smoothed
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

  videoProgress.value = 0.0

  axios.post('/upload', data
  ).then(response => {
    uploadStat.value = '处理'
    updateSocketStat('working', '处理中')
  }).catch(error => {alert(error)})
}

//添加文件后立刻检查文件格式
const checkFormat = (file, files) => {
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
        }).then((result) => {
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

    let minDistanceAxisMax = lineChart.getModel().getComponent('yAxis', 1).axis.scale._extent[1]
    lineChart.setOption({
      yAxis: [
        {name: 'axis', data: Array.from(new Array(minDistanceAxisMax), (v, k) => k)}
      ],
      series: [
        {
          name: 'axis', data: new Array(minDistanceAxisMax).fill(100)
        }
      ]
    })
    uploadStat.value = '完成'
    updateSocketStat('ready', '已就绪')
    fileList.value = []
    firstVideo.value = false
  }).catch(error => alert(error))


}

const setVideoTime = (events) => {
  const pixelPos = [events.offsetX, events.offsetY]
  const gridPos = lineChart.convertFromPixel('grid', pixelPos)
  videoPlayer.value.currentTime = gridPos[0] / targetFPS.value
}

onBeforeUnmount(() => {
  if (socket) socket.disconnect()
})
</script>