<template>
<video ref="camera" autoplay playinline style="display: none;"></video>
<el-container style="height: 100%;" class="stream">
  <el-aside style="width: calc(50vw - 20px); height: 100%;">
    <el-empty v-if="!isProcessing" :image-size="200" description="尚未开始" style="height: calc(calc(50vw - 20px) * 0.75);"/>
    <img id="frame" :class="{'none': !isProcessing}" style="width: 100%; height: calc(calc(50vw - 20px) * 0.75);"/>
    <div style="margin-top: 5px;">
      <div style="width: 40%; display: inline-block;">
        <div class="half">
          <info-icon><camera-filled/></info-icon>
          <connect-info :type="cameraStat">{{ cameraMessage }}</connect-info>
        </div>
        <div class="half">
          <info-icon><upload-filled/></info-icon>
          <connect-info :type="socketStat">{{ socketMessage }}</connect-info>
        </div>
      </div>
      <div style="width: 60%; display: inline-block;">
        <div class="half">
          <info-icon><timer/></info-icon> 延迟 <strong>{{ delay.toFixed(0) }}</strong>ms
        </div>
        <div class="half">
          <info-icon><arrow-up-bold/></info-icon> <strong>{{ cameraFPS }}</strong>FPS&nbsp;/&nbsp;
          <info-icon><arrow-down-bold/></info-icon> <strong>{{ frameFPS }}</strong>FPS
        </div>
      </div>
    </div>
  </el-aside>
  <el-main style="padding: 0 0 0 20px;">
    <el-button class="full" v-if="!isProcessing" type="success" @click="startProcessing" :disabled="!isAvailable">▶ 开始</el-button>
    <el-button class="full" v-if="isProcessing" type="danger" @click="stopProcessing">◼ 停止</el-button>
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
          <el-checkbox-button value="road" disabled>道路识别</el-checkbox-button>
          <el-checkbox-button value="cp">车辆行人</el-checkbox-button>
          <el-checkbox-button value="sign">交通标志</el-checkbox-button>
        </el-checkbox-group>        
      </div>
    </div>
    <div style="height: 60px; margin: 15px 0 5px 0; border: 1px solid #DCDFE6; border-radius: 5px;">
      <analysis-info name="车辆" :data="currentData.carCount" width="20%" color='#337ECC'><Van/></analysis-info>
      <analysis-info name="行人" :data="currentData.personCount" width="20%" color='#79BBFF'><User/></analysis-info>
      <analysis-info name="交通标志" :data="currentData.signCount" width="20%" color='#25D5D5'><Guide/></analysis-info>
      <analysis-info name="最近距离" :data="currentData.minDistance" width="40%"
        :color=calcMinDistanceColor(currentData.minDistance)><MapLocation/></analysis-info>
    </div>
    <div id="line-chart" style="height: calc(calc(calc(50vw - 20px) * 0.75) - 152px); margin-top: 10px;"
      @mouseover="highlightSeries" @mouseout="cancelHighlight"></div>
  </el-main>
</el-container>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { io } from 'socket.io-client'
import { ElNotification } from 'element-plus'
import { ArrowDownBold, ArrowUpBold, CameraFilled, Clock, Guide, MapLocation, PictureFilled, Timer, Van, UploadFilled, User} from '@element-plus/icons-vue'
import * as echarts from 'echarts'

import InfoIcon from './InfoIcon.vue'
import ConnectInfo from './ConnectInfo.vue'
import AnalysisInfo from './AnalysisInfo.vue'

const camera = ref(null)
const isAvailable = ref(false)  //是否允许传输
const isProcessing = ref(false)
const cameraFPS = ref(0)
const frameFPS = ref(0)
const delay = ref(0)
const cameraStat = ref('off')
const socketStat = ref('off')
const cameraMessage = ref('未连接')
const socketMessage = ref('未连接')
const currentData = ref({'carCount': '--', 'personCount': '--', 'signCount': '--', 'minDistance': '--'})

const targetFPS = ref(10)
const streamQuality = ref(0.5)
const detectOptions = ref([])

let mediaStream = null
let socket = null
let cameraFPSCounter = 0
let frameFPSCounter = 0
let cameraInterval = null  //记录帧率用的定时器
let frameInterval = null
let sendTimes = new Map()
let options = [false, false, false, false] //检测选项
let totalFrames = 0

let cameraCanvas = null
let cameraCanvasContext = null
let frame = null

let lineChart = null
let lineAxis = []
let historyData = {}
const maxHistory = 100
const boxSize = 5 //平滑程度
const sharedOptions = {type: 'line', smooth: true, showSymbol: false, emphasis: {focus: 'series'}}
const blankAxisArray = Array.from(new Array(100), (v, k) => k)

const cameraInfo = { width: 600, height: 400, frameRate: 30 } //捕获摄像机的参数
const frameInfo = {width: 600, height: 400} //传给后端的帧的参数
const HOST_IP = import.meta.env.VITE_BASE_URL //后端url

onMounted(() => {
  initCamera()
  initSocket()

  cameraCanvas = document.createElement('canvas')
  cameraCanvas.setAttribute('height', cameraInfo.height)
  cameraCanvas.setAttribute('width', cameraInfo.width)
  cameraCanvasContext = cameraCanvas.getContext('2d')

  frame = document.getElementById('frame')
})

//初始化摄像头
const initCamera = async () => {
  try {
    const constraints = {
      video: {
        width: { ideal: cameraInfo.width },
        height: { ideal: cameraInfo.height },
        frameRate: { ideal: cameraInfo.frameRate }
      },
      audio: false
    }   
    mediaStream = await navigator.mediaDevices.getUserMedia(constraints)
    
    if (camera.value) {
      camera.value.srcObject = mediaStream
      updateCameraStat('ready', '已就绪')
    }
    startFPSCounter()
  } catch (error) {
    popNotification('error', '摄像头初始化失败' + error)
    updateCameraStat('error', '初始化失败')
  }
}

//初始化WebSocket
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
      isAvailable.value = true
      popNotification('success', 'WebSocket已连接')
      updateSocketStat('ready', '已就绪')
    })
    
    socket.on('disconnect', () => {
      if (isProcessing.value === true) {
        stopProcessing()
        updateSocketStat('off', '未连接')
      }
    })

    //接收处理后的帧
    socket.on('sendFrame', (data) => {
      const receiveTime = performance.now() //计算往返延迟，使用Map来存储发送时间
      if (sendTimes.has(data.frameId)) {
        const sendTime = sendTimes.get(data.frameId)
        const latency = receiveTime - sendTime
        delay.value = latency

        sendTimes.delete(data.frameId)
      }
      frameFPSCounter++    
      renderFrame(data.imageData) //渲染

      let frameTime = Math.floor(totalFrames * 1000 / targetFPS.value)
      let minute = Math.floor(frameTime / (60 * 1000))
      let second = (frameTime - minute * 60 * 1000) / 1000
      lineAxis.push(minute.toString() + (second < 10 ? ":0" : ":") + second.toFixed(2))
      if (totalFrames > maxHistory) lineAxis.shift(1)
 
      for (let key in data.analysis) {  //将当前帧的数据按key放入对应数组中
        let result = 0
        if (data.analysis[key] > 100) result = NaN
        else {
            let boxData = data.analysis[key]  //平滑数据，取最后boxSize-1个历史数据，与当前值取平均
            let len = key in historyData ? historyData[key].length : 0
            for (let i = len - 1; i > 0 && i > len - boxSize; i--) {
              if (Number.isNaN(Number(historyData[key][i])) === true) continue
              else boxData += Number(historyData[key][i])
            }
            if (totalFrames > maxHistory) historyData[key].shift(1)
            //摆烂了家人们，不封装了
            if (key === 'minDistance') result = (boxData / Math.min(totalFrames + 1, boxSize)).toFixed(2)
            else result = Math.floor(boxData / Math.min(totalFrames + 1, boxSize))     
        }
        if (key in historyData) historyData[key].push(result)
        else historyData[key] = [result]

        currentData.value[key] = result
      }
      let minDistanceAxisMax = lineChart.getModel().getComponent('yAxis', 1).axis.scale._extent[1]
      lineChart.setOption({
        xAxis: {type: 'category', data: lineAxis, axisLabel: {interval: lineAxis.length - 2}},
        yAxis: {index: 2, data: blankAxisArray.slice(0, minDistanceAxisMax)},
        series: [
          {name: '车辆', data: historyData.carCount},
          {name: '行人', data: historyData.personCount},
          {name: '交通标志', data: historyData.signCount},
          {name: '最近距离', data: historyData.minDistance},
          {name: 'axis', data: new Array(minDistanceAxisMax).fill(100)}
        ]
      })
      totalFrames++ 
    })

    socket.on('connect_error', (error) => {
      isAvailable.value = false
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

//在右侧弹出信息
const popNotification = (type, message) => {
  ElNotification({
    type: type,
    position: 'bottom-right',
    dangerouslyUseHTMLString: true,
    message: '<div><strong>' + message + '</strong></div>' + getTime()
  })
}

//更新摄像机状态
const updateCameraStat = (stat, message) => {
  cameraStat.value = stat
  cameraMessage.value = message
}

//更新WebSocket连接状态
const updateSocketStat = (stat, message) => {
  socketStat.value = stat
  socketMessage.value = message
}

//计算数字颜色
const calcMinDistanceColor = (value) => {
  if (Number.isNaN(value)) return '#E6A23C'
  else if (value < 25.0) return '#F56C6C'
  else if (value > 55.0) return '#E6A23C'
  else return '#E6A23C'
}

//启动FPS计数器
const startFPSCounter = () => {
  if (cameraInterval) clearInterval(cameraInterval)
  
  cameraFPSCounter = 0
  frameFPSCounter = 0
  
  cameraInterval = setInterval(() => { 
    cameraFPS.value = cameraFPSCounter  //每秒重置帧的个数，统计帧率
    frameFPS.value = frameFPSCounter
    cameraFPSCounter = 0
    frameFPSCounter = 0
  }, 1000)
}

//开始处理画面
const startProcessing = () => {
  if (!mediaStream || isProcessing.value === true) return
  
  isProcessing.value = true
  popNotification('primary', '开始传输画面')
  updateCameraStat('working', '录制中')
  updateSocketStat('working', '传输中')
  totalFrames = 0

  if (detectOptions.value.includes('road')) options[3] = true
  else options[3] = false
  if (detectOptions.value.includes('cp')) options[1] = true
  else options[1] = false
  if (detectOptions.value.includes('sign')) options[2] = true
  else options[2] = false

  if (lineChart !== null) {lineChart.dispose()}
  lineChart = echarts.init(document.getElementById('line-chart')) //初始化统计图
  lineAxis = []
  historyData = {}
  lineChart.setOption({
    visualMap: [
      {
        show: false, type: 'continuous', seriesIndex: 3, min: 10, max: 70,
        inRange: {color: ['#F56C6C', '#E6A23C', '#67C23A']}
      },
      {
        show: false, type: 'continuous', seriesIndex: 4, min: 10, max: 70, dimension: 1,
        inRange: {color: ['#F56C6C', '#E6A23C', '#67C23A']}
      }
    ],
    grid: {top: '40px', bottom: '25px', left: '5%', right: '5%'},
    tooltip: {trigger: 'axis', axisPointer: {axis: 'x'}},
    legend: {data: ['车辆', '行人', '交通标志',
      {
        name: '最近距离', itemStyle: {color: {type: 'linear',x: 0, y: 0, x2: 1.25, y2: 1.25,
        colorStops: [{offset: 1, color: '#F56C6C'}, {offset: 0.6, color: '#E6A23C'}, {offset: 0, color: '#67C23A'}]}}
      }
    ], icon: 'roundRect'},
    xAxis: [
      {type: 'category', data: lineAxis},
      {type: 'value', min: 0, max: 100, show: false}
    ],
    yAxis: [
      {
        name: '个数', type: 'value', minInterval: 1, animation: false,
        axisLine: {show: true, lineStyle: {width: 2, color: '#337ECC'}}
      },
      {name: '距离(m)', type: 'value', minInterval: 1, position: 'right', animation: false, axisLine: {show: false}},
      {type: 'category', show: false, boundaryGap: false, data: []}
    ],
    series: [
      Object.assign({
        name: '车辆', data: [], color: '#337ECC'
      }, sharedOptions),
      Object.assign({
        name: '行人', data: [], color: '#79BBFF'
      }, sharedOptions),
      Object.assign({
        name: '交通标志', data: [], color: '#25D5D5'
      }, sharedOptions),
      Object.assign({
        name: '最近距离', data: [], color: '#F56C6C', yAxisIndex: 1, lineStyle: {width: 3}
      }, sharedOptions),
      Object.assign({
        name: 'axis', data: [], xAxisIndex: 1, yAxisIndex: 2, animation: false, tooltip: {show: false}, lineStyle: {width: 3}
      }, sharedOptions)
    ]
  })
  lineChart.on('mouseover', (params) => {
    console.log(params)
  })
  
  const interval = 1000 / targetFPS.value
  frameInterval = setInterval(() => {
      sendCamera()
  }, interval)
}

//捕获并发送帧，MediaStream->canvas->webp->压缩->blob
const sendCamera = () => {
  if (!camera.value || !socket || isProcessing.value === false) return
  
  cameraCanvasContext.drawImage(camera.value, 0, 0, cameraCanvas.width, cameraCanvas.height)  //绘制当前视频帧

  const frameId = Date.now() + '-' + Math.random().toString(36).substr(2, 9)  //生成唯一帧ID
  sendTimes.set(frameId, performance.now())

  cameraCanvas.toBlob((blob) => {
    const reader = new FileReader()
    reader.onload = () => {
      const arrayBuffer = reader.result
      
      socket.emit('sendCamera', {
        frameId: frameId,
        imageData: {
          data: arrayBuffer,
          width: frameInfo.width,
          height: frameInfo.height
        },
        options: options,
        quality: streamQuality.value,
        fps: targetFPS.value
      })
    }
    reader.readAsArrayBuffer(blob)
  }, 'image/webp', 1)

  cameraFPSCounter++
}

//渲染处理后的帧，arrayBuffer->blob->dataURL->渲染到<img/>
const renderFrame = (data) => {
  const reader = new FileReader()
  reader.onload = (event) => {
    const data = event.target.result
    frame.setAttribute('src', data)
  }
  reader.readAsDataURL(new Blob([data], { type: 'image/webp' }));
}

//停止处理
const stopProcessing = () => {
  isProcessing.value = false
  if (frameInterval) {
    clearInterval(frameInterval)
    frameInterval = null
  }
  updateCameraStat('ready', '已就绪')
  updateSocketStat('ready', '已就绪')
}

//组件卸载时清理
onBeforeUnmount(() => {
  stopProcessing()
  if (socket) socket.disconnect()
  if (mediaStream) mediaStream.getTracks().forEach(track => track.stop())
  if (cameraInterval) clearInterval(cameraInterval)
})
</script>