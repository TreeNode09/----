<template>
<video ref="camera" autoplay playinline></video>
<img id="frame" :width="frameInfo.width" :height="frameInfo.height"/>
<h2>{{ delay.toFixed(2) }}</h2>
<h3>{{ junkText }}</h3>
<div>{{ cameraFPS }} : {{ frameFPS }}</div>
<el-button v-if="!isProcessing" type="success" @click="startProcessing">开始</el-button>
<el-button v-if="isProcessing" type="danger" @click="stopProcessing">停止</el-button>

</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { io } from 'socket.io-client'

const camera = ref(null)
const isProcessing = ref(false)
const cameraFPS = ref(0)
const frameFPS = ref(0)
const framesProcessed = ref(0)
const delay = ref(0)
const socketStatus = ref('未连接')
const targetFPS = ref(20)

const junkText = ref('')

let mediaStream = null
let socket = null
let cameraFPSCounter = 0
let frameFPSCounter = 0
let FPSInterval = null
let frameCaptureInterval = null
let sendTimes = new Map()

let cameraCanvas = null
let cameraCanvasContext = null
let frame = null

const cameraInfo = { width: 600, height: 400, frameRate: 30 } //捕获摄像机的参数
const frameInfo = {width: 600, height: 400} //传给后端的帧的参数
const HOST_IP = "http://127.0.0.1:5000" //后端url

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
    }
    
    startFPSCounter()
  } catch (error) {
    console.error('摄像头初始化失败:', error)
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
      socketStatus.value = '已连接'
    })
    
    socket.on('disconnect', () => {
      socketStatus.value = '已断开'
      if (isProcessing.value === true) {
        stopProcessing()
      }
    })
    
    socket.on('connect_error', (error) => {
      socketStatus.value = '连接错误'
      console.error('WebSocket连接错误:', error)
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
    })

    socket.on('yourJunk', (data) => {
      const receiveTime = performance.now()
      if (sendTimes.has(data.frameId)) {
        const sendTime = sendTimes.get(data.frameId)
        const latency = receiveTime - sendTime

        delay.value = latency

        sendTimes.delete(data.frameId)
      }
      frameFPSCounter++    
      junkText.value = data.data
    })

  } catch (error) {
    console.error('WebSocket初始化失败:', error)
  }
}

//启动FPS计数器
const startFPSCounter = () => {
  if (FPSInterval) clearInterval(FPSInterval)
  
  cameraFPSCounter = 0
  frameFPSCounter = 0
  
  FPSInterval = setInterval(() => { 
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
  framesProcessed.value = 0
  
  const interval = 1000 / targetFPS.value
  frameCaptureInterval = setInterval(() => {
      sendCamera()
      //sendJunk()
  }, interval)
}

const sendJunk = () => {
  const junk = Date.now() + '-' + Math.random().toString(36).substr(2, 9)
  sendTimes.set(junk, performance.now())
  socket.emit('sendJunk', {
    frameId: junk
  })
  cameraFPSCounter++
}

//捕获并发送帧
const sendCamera = () => {
  const start = performance.now()
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
        }
        
      })
    }
    reader.readAsArrayBuffer(blob);
  }, 'image/webp', 0.5)

  cameraFPSCounter++
}

//渲染处理后的帧
const renderFrame = (data) => {
  const reader = new FileReader()
  reader.onload = (event) => {
    const data = event.target.result
    frame.setAttribute('src', data)
  }
  reader.readAsDataURL(new Blob([data.data], { type: 'image/webp' }));
  framesProcessed.value++
}

//停止处理
const stopProcessing = () => {
  isProcessing.value = false
  if (frameCaptureInterval) {
    clearInterval(frameCaptureInterval)
    frameCaptureInterval = null
  }
}

//组件卸载时清理
onBeforeUnmount(() => {
  stopProcessing()
  if (socket) socket.disconnect()
  if (mediaStream) mediaStream.getTracks().forEach(track => track.stop())
  if (FPSInterval) clearInterval(FPSInterval)
})
</script>