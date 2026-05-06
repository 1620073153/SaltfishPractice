<script setup>
import { computed } from 'vue'
import {
  CircleCheckFilled, WarningFilled, CreditCard, Coin, TrendCharts, Timer
} from '@element-plus/icons-vue'

const props = defineProps({ result: Object })
const emit = defineEmits(['reset'])

function fmtMoney(v) {
  if (v >= 10000) return (v / 10000).toFixed(v % 10000 ? 1 : 0) + '万'
  return v.toLocaleString()
}

const scoreColor = computed(() => {
  const s = props.result.score
  if (s >= 750) return '#0d9488'
  if (s >= 700) return '#2563eb'
  if (s >= 650) return '#7c3aed'
  if (s >= 600) return '#d97706'
  if (s >= 550) return '#ea580c'
  return '#dc2626'
})
</script>

<template>
  <div class="result-block">
    <!-- Score -->
    <el-card shadow="never" class="score-card">
      <div class="score-row">
        <el-icon :size="28" color="#10b981"><CircleCheckFilled /></el-icon>
        <span class="score-label">您的征信分数</span>
        <span class="score-num" :style="{ color: scoreColor }">{{ result.score }}</span>
        <span class="score-unit">分</span>
        <el-tag :type="result.score >= 700 ? 'success' : result.score >= 600 ? 'warning' : 'danger'" size="large">
          {{ result.score >= 700 ? '优质' : result.score >= 600 ? '良好' : '待提升' }}
        </el-tag>
      </div>
      <p class="score-range">所属档位：{{ result.scoreRange }}</p>
    </el-card>

    <!-- No banks -->
    <el-card v-if="!result.banks.length" shadow="never" class="empty-card">
      <div class="empty-box">
        <el-icon :size="48" color="#e6a23c"><WarningFilled /></el-icon>
        <p>{{ result.message }}</p>
      </div>
    </el-card>

    <!-- Bank list -->
    <template v-else>
      <div class="result-header">
        <h3>为您匹配 <strong>{{ result.total }}</strong> 家可贷款银行</h3>
        <el-button type="primary" plain size="small" @click="emit('reset')">重新上传分析</el-button>
      </div>

      <div class="bank-grid">
        <el-card
          v-for="(bank, i) in result.banks"
          :key="i"
          shadow="hover"
          class="bank-card"
          :class="{ 'is-top': i === 0 }"
        >
          <template #header>
            <div class="bank-header">
              <span class="bank-name">{{ bank.name }}</span>
              <el-tag v-if="i === 0" type="success" size="small" effect="dark">推荐</el-tag>
            </div>
          </template>

          <div class="bank-body">
            <div class="bank-stat">
              <el-icon :size="18" color="#1a6fb5"><Coin /></el-icon>
              <div>
                <span class="stat-val">{{ fmtMoney(bank.minAmount) }} - {{ fmtMoney(bank.maxAmount) }}</span>
                <span class="stat-lab">可贷额度</span>
              </div>
            </div>
            <div class="bank-stat">
              <el-icon :size="18" color="#1a6fb5"><TrendCharts /></el-icon>
              <div>
                <span class="stat-val">{{ bank.rate }}</span>
                <span class="stat-lab">年利率</span>
              </div>
            </div>
            <div class="bank-stat">
              <el-icon :size="18" color="#1a6fb5"><Timer /></el-icon>
              <div>
                <span class="stat-val">{{ bank.term }}</span>
                <span class="stat-lab">贷款期限</span>
              </div>
            </div>
            <p class="bank-remark">{{ bank.remark }}</p>
          </div>
        </el-card>
      </div>
    </template>

    <!-- Disclaimer -->
    <el-alert
      type="info" :closable="false" show-icon
      title="以上结果基于您上传的征信报告自动分析生成，实际可贷额度、利率以银行最终审批为准。"
      style="margin-top:20px"
    />
  </div>
</template>

<style scoped>
.result-block { margin-top: 24px; animation: fadeIn .4s ease; }
@keyframes fadeIn { from { opacity:0; transform:translateY(12px); } to { opacity:1; transform:translateY(0); } }

.score-card { margin-bottom: 20px; border-radius: 12px; }
.score-row {
  display: flex; align-items: center; gap: 12px; flex-wrap: wrap;
}
.score-label { color: #606266; font-size: 15px; }
.score-num { font-size: 42px; font-weight: 800; line-height: 1; }
.score-unit { font-size: 16px; color: #909399; margin-right: 8px; }
.score-range { font-size: 12px; color: #a8abb2; margin-top: 12px; padding-top: 12px; border-top: 1px solid #ebeef5; }

.empty-card { border-radius: 12px; }
.empty-box { text-align: center; padding: 32px 0; }
.empty-box p { color: #909399; margin-top: 16px; font-size: 15px; }

.result-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 16px;
}
.result-header h3 { font-size: 17px; font-weight: 500; }
.result-header strong { color: #1a6fb5; }

.bank-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}

.bank-card { border-radius: 12px; transition: transform .2s; }
.bank-card:hover { transform: translateY(-2px); }
.bank-card.is-top { border-color: #10b981; }

.bank-header {
  display: flex; justify-content: space-between; align-items: center;
}
.bank-name { font-weight: 600; font-size: 16px; }

.bank-body { display: flex; flex-direction: column; gap: 12px; }
.bank-stat {
  display: flex; align-items: center; gap: 10px;
}
.stat-val { display: block; font-size: 15px; font-weight: 600; color: #303133; }
.stat-lab { display: block; font-size: 11px; color: #a8abb2; }
.bank-remark {
  font-size: 12px; color: #909399;
  padding-top: 10px; border-top: 1px dashed #ebeef5;
}
</style>
