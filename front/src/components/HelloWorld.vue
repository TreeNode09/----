<template>
<el-upload action :http-request="uploadFile"
:before-upload="beforeUpload" :on-remove="handleRemove" :on-exceed="handleExceed"
v-model:file-list="fileList" :limit=1 list-type="picture">
    <el-button type="primary">Click to upload</el-button>
</el-upload>
<h1>{{ message }}</h1>
</template>

<script setup>
import { handleError, ref } from 'vue'
import axios from 'axios'

const message = ref('Hi, Vite!')
var showing = false

function getMessage(){
    showing = !showing
    if(showing === true){
        axios.get('/' 
        ).then(response => {
            message.value = response.data
        })
        .catch(error => {alert(error)})
    }
     else{
        message.value = 'Hi, Vite!'
    }
}

const fileList = ref([])
const formats = ['png', 'jpg', 'jpeg']

function beforeUpload(file){
    if (file.type != "" || file.type != null || file.type != undefined){
		const format = file.name.replace(/.+\./, "").toLowerCase()
        if(formats.includes(format) === false){
            alert("仅支持png、jpg、jpeg格式图片!")
            return false
        }
		if (file.size / 1024 / 1024 > 1) {
			alert("上传文件大小不能超过 1MB!")
			return false
		}
        return true
    }
    alert("文件格式有误!");
    return false
}

function handleRemove(){
    message.value = 'Try again!'
}

function handleExceed(){
    alert("仅能上传1张图片!")
    return
}

function uploadFile(item){
    let data = new FormData()
    data.append("file", item.file)
    axios.post('/upload', data
        ).then(response => {
            message.value = response.data
        })
        .catch(error => {alert(error)})
}
</script>

<style scoped>

</style>
