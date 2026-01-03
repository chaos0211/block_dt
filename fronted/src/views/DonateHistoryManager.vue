<template>
  <div class="space-y-6">
    <!-- 顶部标题 -->
    <div class="flex flex-col md:flex-row md:items-center md:justify-between">
      <div>
        <h2 class="text-[clamp(1.5rem,3vw,2rem)] font-bold text-gray-800">
          捐赠记录管理
        </h2>

      </div>
    </div>

    <!-- 列表表格区 -->
    <div class="bg-white rounded-xl shadow-card overflow-hidden">
      <div class="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
        <div class="text-sm text-gray-600">共 {{ total }} 条记录</div>
      </div>

      <div class="overflow-x-auto">
        <table class="min-w-full">
          <thead class="bg-gray-50">
            <tr class="text-left text-xs font-semibold text-gray-500">
              <th class="px-5 py-3">项目</th>
              <th class="px-5 py-3">金额(元)</th>
              <th class="px-5 py-3">状态</th>
              <th class="px-5 py-3">Gas Fee</th>
              <th class="px-5 py-3">创建时间</th>
            </tr>
          </thead>

          <tbody>
            <tr
              v-for="d in donations"
              :key="d.id"
              class="border-t border-gray-100 text-sm text-gray-700 hover:bg-gray-50/60"
            >
              <td class="px-5 py-4">
                <div class="text-gray-900 font-medium">{{ d.project_title || `项目 #${d.project_id}` }}</div>
              </td>
              <td class="px-5 py-4 text-gray-900">¥{{ formatNumber(d.amount) }}</td>
              <td class="px-5 py-4">
                <span
                  class="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium"
                  :class="statusBadgeClass(d.status)"
                >
                  {{ statusText(d.status) }}
                </span>
              </td>
              <td class="px-5 py-4 text-gray-900">{{ formatGas(d.gas_fee) }}</td>
              <td class="px-5 py-4 text-gray-600">{{ formatTime(d.created_at) }}</td>
            </tr>

            <tr v-if="!loading && donations.length === 0">
              <td class="px-5 py-10 text-center text-gray-500" colspan="5">暂无数据</td>
            </tr>
            <tr v-if="loading">
              <td class="px-5 py-10 text-center text-gray-500" colspan="5">加载中...</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 分页 -->
      <div class="px-5 py-4 border-t border-gray-100 flex items-center justify-end gap-2">
        <button
          class="px-3 py-1.5 rounded-lg border border-gray-200 text-gray-600 hover:bg-gray-50 text-sm disabled:opacity-60"
          :disabled="page <= 1 || loading"
          @click="handlePageChange(page - 1)"
        >
          上一页
        </button>
        <div class="text-sm text-gray-600 px-2">
          第 {{ page }} 页
        </div>
        <button
          class="px-3 py-1.5 rounded-lg border border-gray-200 text-gray-600 hover:bg-gray-50 text-sm disabled:opacity-60"
          :disabled="loading || donations.length < pageSize"
          @click="handlePageChange(page + 1)"
        >
          下一页
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import http from '@/api/http'

type DonationStatus = 'pending' | 'in_pool' | 'mining' | 'confirmed' | 'failed' | string

interface DonationItem {
  id: number
  amount: number
  project_id: number
  project_title?: string | null
  status: DonationStatus
  gas_fee?: number | null
  created_at?: string | null
}

const donations = ref<DonationItem[]>([])
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)
const loading = ref(false)

const loadDonations = async () => {
  loading.value = true
  try {
    const { data } = await http.get(`/api/v1/donations/my`, {
      params: { page: page.value, limit: pageSize.value }
    })

    // 兼容两种返回：数组 或 {items,total}
    const list = Array.isArray(data) ? data : (data?.items ?? data?.donations ?? [])
    const t = Array.isArray(data) ? (data?.total ?? list.length) : (data?.total ?? list.length)

    donations.value = (list || []).map((d: any) => ({
      id: d.id,
      amount: Number(d.amount ?? 0),
      project_id: Number(d.project_id ?? 0),
      project_title: d.project_title ?? null,
      status: (d.status ?? '').toString().toLowerCase(),
      gas_fee: d.gas_fee != null ? Number(d.gas_fee) : null,
      created_at: d.created_at ?? null,
    }))

    total.value = Number(t ?? donations.value.length)
  } catch (e) {
    console.error('[DonationHistory] load failed', e)
    donations.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

onMounted(() => loadDonations())

const handlePageChange = async (newPage: number) => {
  if (newPage < 1) return
  page.value = newPage
  await loadDonations()
}

const formatNumber = (num: number | null | undefined) => {
  const n = Number(num ?? 0)
  if (Number.isNaN(n)) return '0'
  return n.toLocaleString('zh-CN', { minimumFractionDigits: 0, maximumFractionDigits: 0 })
}

const formatGas = (v: number | null | undefined) => {
  const n = Number(v ?? 0)
  if (Number.isNaN(n)) return '0'
  // gas_fee 一般很小，保留 2 位
  return n.toLocaleString('zh-CN', { minimumFractionDigits: 0, maximumFractionDigits: 2 })
}

const shortHash = (h?: string | null) => {
  if (!h) return '—'
  const s = String(h)
  if (s.length <= 14) return s
  return `${s.slice(0, 6)}...${s.slice(-6)}`
}

const formatTime = (t?: string | null) => {
  if (!t) return '—'
  // 直接展示后端字符串；若为 ISO，可切到秒
  return String(t).replace('T', ' ').slice(0, 19)
}

const statusText = (status: DonationStatus) => {
  const map: Record<string, string> = {
    pending: '待处理',
    in_pool: '交易池中',
    mining: '挖矿中',
    confirmed: '已完成',
    failed: '失败'
  }
  return map[String(status).toLowerCase()] || String(status)
}

const statusBadgeClass = (status: DonationStatus) => {
  const s = String(status).toLowerCase()
  const map: Record<string, string> = {
    pending: 'bg-warning-light text-warning',
    in_pool: 'bg-primary-light text-primary',
    mining: 'bg-warning-light text-warning',
    confirmed: 'bg-success-light text-success',
    failed: 'bg-red-100 text-red-600'
  }
  return map[s] || 'bg-gray-100 text-gray-600'
}
</script>
