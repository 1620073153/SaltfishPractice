<script setup>
import { ref } from 'vue'
import FileUpload from './components/FileUpload.vue'
import ResultCard from './components/ResultCard.vue'

const analyzing = ref(false)
const result = ref(null)
const error = ref('')

function onResult(res) {
  result.value = res
  error.value = ''
}

function onError(msg) {
  error.value = msg
  result.value = null
}

function onReset() {
  result.value = null
  error.value = ''
}
</script>

<template>
  <div class="app-shell">
    <!-- Header -->
    <header class="app-header">
      <div class="brand">
        <span class="brand-icon">🛡️</span>
        <span class="brand-text">征信分析</span>
      </div>
      <div class="header-sub">智能银行贷款匹配系统</div>
    </header>

    <!-- Main -->
    <main class="app-main">
      <el-card class="upload-card" shadow="never">
        <template #header>
          <div class="card-title">
            <span class="step-badge">1</span> 上传您的征信报告
          </div>
        </template>
        <FileUpload
          :analyzing="analyzing"
          @analyze-start="analyzing = true"
          @result="r => { analyzing = false; onResult(r) }"
          @error="e => { analyzing = false; onError(e) }"
        />
        <p class="upload-hint">
          支持 PDF、PNG、JPG 格式 · 文件内容需包含 "征信分数" 或 "信用评分" 等关键词
        </p>
      </el-card>

      <!-- Error -->
      <el-alert
        v-if="error"
        type="error"
        :title="error"
        show-icon
        closable
        @close="error = ''"
        style="margin-top:20px"
      />

      <!-- Loading -->
      <div v-if="analyzing" class="loading-box">
        <el-skeleton :rows="4" animated />
        <p style="text-align:center;color:#909399;margin-top:16px">正在解析文件并匹配银行方案...</p>
      </div>

      <!-- Result -->
      <ResultCard
        v-if="result"
        :result="result"
        @reset="onReset"
      />
    </main>

    <!-- Footer -->
    <footer class="app-footer">
      <p>© 2026 征信分析系统 · 分析结果仅供参考，实际贷款以银行审批为准</p>
    </footer>
  </div>
</template>

<style>
:root {
  --brand: #1a6fb5;
  --brand-light: #e8f4fd;
}

* { margin: 0; padding: 0; box-sizing: border-box; }

body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC",
    "Microsoft YaHei", sans-serif;
  background: #f0f2f5;
  color: #303133;
  min-height: 100vh;
}

.app-shell {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

/* Header */
.app-header {
  background: linear-gradient(135deg, #1a3a5c 0%, #1a6fb5 100%);
  color: #fff;
  padding: 20px 32px;
  display: flex;
  align-items: center;
  gap: 16px;
}
.brand { display: flex; align-items: center; gap: 8px; }
.brand-icon { font-size: 28px; }
.brand-text { font-size: 22px; font-weight: 700; letter-spacing: .5px; }
.header-sub {
  font-size: 13px; opacity: .75;
  border-left: 1px solid rgba(255,255,255,.3);
  padding-left: 16px;
}

/* Main */
.app-main {
  max-width: 860px;
  width: 100%;
  margin: 0 auto;
  padding: 32px 20px;
  flex: 1;
}

.upload-card { border-radius: 12px !important; }
.upload-card .el-card__header {
  background: #fafbfc;
  padding: 16px 20px;
}
.card-title {
  font-size: 16px; font-weight: 600;
  display: flex; align-items: center; gap: 10px;
}
.step-badge {
  width: 26px; height: 26px; border-radius: 50%;
  background: var(--brand); color: #fff;
  display: inline-flex; align-items: center; justify-content: center;
  font-size: 13px; font-weight: 700;
}
.upload-hint {
  font-size: 12px; color: #a8abb2; text-align: center; margin-top: 12px;
}

.loading-box { margin-top: 24px; }

/* Footer */
.app-footer {
  text-align: center;
  padding: 20px;
  font-size: 12px; color: #a8abb2;
  border-top: 1px solid #e4e7ed;
}
</style>
