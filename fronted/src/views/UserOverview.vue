<template>
  <div class="min-h-screen flex flex-col">
    <!-- 页面标题区域 -->
    <header class="bg-white shadow-sm py-6 px-4 md:px-8">
      <div class="max-w-7xl mx-auto">


        <!-- 搜索和筛选区域（预留扩展） -->
        <div class="mt-6 flex flex-col sm:flex-row gap-4">
          <div class="relative flex-grow max-w-md">
            <input
              v-model="keyword"
              type="text"
              placeholder="搜索公益项目..."
              class="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all duration-300"
            />
            <i
              class="fas fa-search absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400"
            />
          </div>

        </div>
      </div>
    </header>

    <!-- 主内容区域 -->
    <main class="flex-1 bg-gray-50 py-8 px-4 md:px-8">
      <div class="max-w-7xl mx-auto">
        <div class="flex items-center justify-between mb-6">
          <div class="text-sm text-gray-600">
            当前余额：
            <span class="font-semibold text-gray-800">¥{{ maskBalance(balance) }}</span>
            <span class="ml-3 text-gray-400" v-if="username">用户：{{ username }}</span>
          </div>
        </div>

        <UserProjectCardGrid
          :projects="displayProjects"
          @view="openDetail"
        />

        <div
          v-if="!loading && displayProjects.length === 0"
          class="bg-white rounded-xl border border-gray-100 p-10 text-center text-gray-500"
        >
          暂无已上链项目
        </div>

        <div
          v-if="loading"
          class="bg-white rounded-xl border border-gray-100 p-10 text-center text-gray-500"
        >
          正在加载...
        </div>
      </div>
    </main>

    <!-- 详情弹窗（含捐赠） -->
    <UserProjectDetailModal
      :visible="detailVisible"
      :project="currentProject"
      :balance="balance"
      @close="closeDetail"
      @donate="handleDonate"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import UserProjectCardGrid from '@/components/common/UserProjectCardGrid.vue'
import UserProjectDetailModal from '@/components/common/UserProjectDetailModal.vue'
import { apiListProjectsForUser, apiGetMe, apiCreateDonationForUser } from '@/api/user_overview'

type ProjectStatus = 'PENDING' | 'APPROVED' | 'ON_CHAIN' | 'COMPLETED' | string

interface ProjectItem {
  id: number
  title: string
  description?: string
  img_url?: string | null
  target_amount: number
  current_amount: number
  status: ProjectStatus
  blockchain_address?: string | null
  created_at?: string | null
}

const loading = ref(false)
const keyword = ref('')
const projects = ref<ProjectItem[]>([])
const currentProject = ref<ProjectItem | null>(null)
const detailVisible = ref(false)

const balance = ref<number>(0)
const username = ref<string>('')

const formatInt = (n: number | string | null | undefined) => {
  const v = Number(n ?? 0)
  if (Number.isNaN(v)) return '0'
  return v.toLocaleString('zh-CN', { maximumFractionDigits: 0 })
}

const maskBalance = (n: number | string | null | undefined, keepStart = 2, keepEnd = 2) => {
  const v = Number(n ?? 0)
  if (!Number.isFinite(v)) return '0'

  // 余额显示按“整数金额”处理
  const raw = Math.floor(v).toString()
  const len = raw.length

  // 太短就不遮
  if (len <= keepStart + keepEnd) return raw

  // 至少保留前后各 1 位
  const ks = Math.max(1, Math.min(keepStart, len - 1))
  const ke = Math.max(1, Math.min(keepEnd, len - ks))

  const head = raw.slice(0, ks)
  const tail = raw.slice(len - ke)

  // 用 ** 做中间掩码（与示例一致：¥99**00）
  return `${head}**${tail}`
}

const displayProjects = computed(() => {
  const kw = keyword.value.trim().toLowerCase()
  // 只展示“已上链/进行中”的项目
  const list = projects.value
    .filter(p => String(p.status).toUpperCase() === 'ON_CHAIN')
    .filter(p => (kw ? (p.title || '').toLowerCase().includes(kw) : true))

  return list
})

const refresh = async () => {
  loading.value = true
  try {
    // 拉项目（直接用 projects 列表接口，前端筛 ON_CHAIN）
    const res = await apiListProjectsForUser({ page: 1, limit: 200 })
    const raw = (res?.projects ?? res ?? []) as any[]

    projects.value = raw.map((p) => ({
      id: p.id,
      title: p.title,
      description: p.description,
      img_url: p.img_url ?? null,
      target_amount: Number(p.target_amount ?? 0),
      current_amount: Number(p.current_amount ?? 0),
      status: String(p.status ?? '').toUpperCase(),
      blockchain_address: p.blockchain_address ?? null,
      created_at: p.created_at ?? null,
    }))
  } finally {
    loading.value = false
  }

  // 拉当前用户（余额/用户名）
  try {
    const me = await apiGetMe()
    if (me) {
      balance.value = Number(me.balance ?? 0)
      username.value = String(me.username ?? '')
    }
  } catch {
    // 忽略
  }
}

onMounted(() => refresh())

const openDetail = (p: ProjectItem) => {
  currentProject.value = p
  detailVisible.value = true
}

const closeDetail = () => {
  detailVisible.value = false
  currentProject.value = null
}

const handleDonate = async (payload: { projectId: number; amount: number; isAnonymous: boolean }) => {
  const amount = Number(payload.amount ?? 0)
  if (!payload.projectId || !amount || amount <= 0) return

  const remain = Number(balance.value ?? 0) - amount
  const ok = window.confirm(`您是否确认捐赠 ${amount} 元？\n捐赠后剩余 ${remain} 元`)
  if (!ok) return

  try {
    await apiCreateDonationForUser({
      project_id: payload.projectId,
      amount,
      is_anonymous: payload.isAnonymous
    })

    // 前端先扣余额（后端也会扣，这里为了即时体验）
    balance.value = remain

    // 刷新项目金额（可选）
    await refresh()
    closeDetail()
    window.alert('捐赠已提交，等待后续上链确认')
  } catch (e) {
    console.error('[Donate] failed', e)
    window.alert('捐赠失败，请稍后重试')
  }
}
</script>