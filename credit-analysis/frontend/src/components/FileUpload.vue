<script setup>
import { ref } from 'vue'
import { UploadFilled } from '@element-plus/icons-vue'
import { uploadFile } from '../api/index.js'

const props = defineProps({ analyzing: Boolean })
const emit = defineEmits(['analyze-start', 'result', 'error'])

const fileList = ref([])
const uploadRef = ref(null)

function beforeUpload(file) {
  const allowed = ['application/pdf', 'image/png', 'image/jpeg', 'image/bmp', 'image/tiff']
  if (!allowed.includes(file.type)) {
    emit('error', '仅支持 PDF、PNG、JPG、BMP、TIFF 格式')
    return false
  }
  if (file.size > 10 * 1024 * 1024) {
    emit('error', '文件大小不能超过 10MB')
    return false
  }
  return true
}

async function handleUpload(options) {
  emit('analyze-start')
  try {
    const res = await uploadFile(options.file)
    emit('result', res.data)
  } catch (e) {
    const msg = e.response?.data?.error || e.message || '上传失败，请重试'
    emit('error', msg)
  } finally {
    fileList.value = []
  }
}

function handleRemove() {
  fileList.value = []
}
</script>

<template>
  <div class="upload-area" :class="{ 'is-loading': analyzing }">
    <el-upload
      ref="uploadRef"
      v-model:file-list="fileList"
      drag
      :auto-upload="true"
      :before-upload="beforeUpload"
      :http-request="handleUpload"
      :on-remove="handleRemove"
      :limit="1"
      :disabled="analyzing"
    >
      <div class="upload-inner">
        <el-icon :size="48" color="#1a6fb5"><UploadFilled /></el-icon>
        <div class="upload-text">
          <p class="upload-title">点击或拖拽文件到此区域上传</p>
          <p class="upload-sub">PDF / PNG / JPG · 单文件不超过 10MB</p>
        </div>
      </div>
    </el-upload>
  </div>
</template>

<style scoped>
.upload-area { position: relative; }
.upload-area.is-loading { pointer-events: none; opacity: .65; }
.upload-inner { padding: 16px 0; }
.upload-text { margin-top: 12px; }
.upload-title { font-size: 15px; color: #303133; margin-bottom: 4px; }
.upload-sub  { font-size: 12px; color: #a8abb2; }
</style>
