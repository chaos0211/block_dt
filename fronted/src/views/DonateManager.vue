<template>
  <div class="space-y-6">
    <!-- 顶部标题 + 操作按钮 -->
    <div
      class="flex flex-col md:flex-row md:items-center md:justify-between space-y-4 md:space-y-0"
    >
      <div>
        <h2 class="text-[clamp(1.5rem,3vw,2rem)] font-bold text-gray-800">
          公益项目管理
        </h2>
        <p class="text-gray-500 mt-1">
          管理、查看和维护所有在链上登记的爱心公益项目
        </p>
      </div>
      <div class="flex space-x-3">
        <button
          class="bg-primary hover:bg-primary/90 text-white px-4 py-2 rounded-lg flex items-center shadow-sm hover:shadow transition-all duration-300 text-sm"
          @click="openCreateModal"
        >
          <i class="fas fa-plus mr-2" />
          <span>新增项目</span>
        </button>
        <button
          class="bg-white border border-gray-200 hover:bg-gray-50 text-gray-700 px-4 py-2 rounded-lg flex items-center shadow-sm hover:shadow transition-all duration-300 text-sm"
        >
          <i class="fas fa-file-import mr-2" />
          <span>批量导入</span>
        </button>
      </div>
    </div>

    <!-- 筛选查询条件区 -->
    <!-- TODO: 这里可以拆成 <ProjectFilterBar /> 组件 -->
    <div class="bg-white rounded-xl shadow-card p-5 mb-2">
      <div class="flex flex-col md:flex-row gap-4">
        <div class="flex-grow">
          <label class="block text-sm font-medium text-gray-500 mb-1">
            项目名称关键字
          </label>
          <div class="relative">
            <i
              class="fas fa-search absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400"
            />
            <input
              v-model="filters.keyword"
              type="text"
              placeholder="请输入项目名称关键字"
              class="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all duration-300"
            />
          </div>
        </div>

        <div class="w-full md:w-48">
          <label class="block text-sm font-medium text-gray-500 mb-1">
            项目状态
          </label>
          <select
            v-model="filters.status"
            class="w-full px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all duration-300 bg-white"
          >
            <option value="">全部状态</option>
            <option value="inProgress">进行中</option>
            <option value="completed">已结束</option>
            <option value="reviewing">审核中</option>
            <option value="rejected">已驳回</option>
          </select>
        </div>

        <div class="w-full md:w-64">
          <label class="block text-sm font-medium text-gray-500 mb-1">
            所属组织
          </label>
          <select
            v-model="filters.org"
            class="w-full px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all duration-300 bg-white"
          >
            <option value="">全部组织</option>
            <option value="org1">爱心公益协会</option>
            <option value="org2">阳光慈善基金会</option>
            <option value="org3">温暖救助中心</option>
            <option value="org4">希望工程办公室</option>
          </select>
        </div>

        <div class="w-full md:w-64">
          <label class="block text-sm font-medium text-gray-500 mb-1">
            创建时间
          </label>
          <div class="relative">
            <i
              class="fas fa-calendar absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400"
            />
            <input
              v-model="filters.dateRange"
              type="text"
              placeholder="选择时间范围（占位）"
              class="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all duration-300"
            />
          </div>
        </div>

        <div class="flex items-end space-x-3">
          <button
            class="bg-primary hover:bg-primary/90 text-white px-6 py-2 rounded-lg flex items-center shadow-sm hover:shadow transition-all duration-300 text-sm"
            @click="applyFilters"
          >
            <i class="fas fa-search mr-2" />
            <span>查询</span>
          </button>
          <button
            class="bg-white border border-gray-200 hover:bg-gray-50 text-gray-700 px-6 py-2 rounded-lg flex items-center shadow-sm hover:shadow transition-all duration-300 text-sm"
            @click="resetFilters"
          >
            <i class="fas fa-sync-alt mr-2" />
            <span>重置</span>
          </button>
        </div>
      </div>
    </div>

    <!-- 项目概览统计卡片区 -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
      <StatsCards :value="stats.inProgress" icon="fas fa-hourglass-half" icon-bg="bg-primary-light text-primary">
        <template #title>当前进行中项目</template>
      </StatsCards>
      <StatsCards :value="stats.completed" icon="fas fa-check-circle" icon-bg="bg-success-light text-success">
        <template #title>已结束项目</template>
      </StatsCards>
      <StatsCards :value="stats.waitingChain" icon="fas fa-clock-rotate-left" icon-bg="bg-warning-light text-warning">
        <template #title>待上链项目</template>
      </StatsCards>
      <StatsCards :value="stats.onChain" icon="fas fa-link" icon-bg="bg-gray-100 text-gray-700">
        <template #title>链上已记录项目总数</template>
      </StatsCards>
    </div>

    <!-- 项目列表表格区 -->
    <ProjectList
      :projects="filteredProjects"
      :total="total"
      :page="page"
      :page-size="pageSize"
      @change-page="handlePageChange"
      @view="openDetailModal"
    />

    <!-- 新增项目弹窗 -->
    <div
      v-if="showCreateModal"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm"
    >
      <div class="bg-white rounded-xl shadow-xl w-full max-w-xl mx-4">
        <div class="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <h3 class="text-lg font-semibold text-gray-800">
            新增公益项目
          </h3>
          <button
            class="text-gray-400 hover:text-gray-600"
            @click="closeCreateModal"
          >
            <i class="fas fa-times" />
          </button>
        </div>

        <div class="px-6 py-4 space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">
              项目名称 <span class="text-red-500">*</span>
            </label>
            <input
              v-model="createForm.title"
              type="text"
              placeholder="请输入项目名称"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">
              所属机构
            </label>
            <select
              v-model="createForm.orgCode"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary bg-white"
            >
              <option value="">请选择发起机构</option>
              <option value="org1">爱心公益协会</option>
              <option value="org2">阳光慈善基金会</option>
              <option value="org3">温暖救助中心</option>
              <option value="org4">希望工程办公室</option>
            </select>
            <p class="mt-1 text-xs text-gray-400">
              后续会根据登录用户角色自动锁定或下拉选择机构。
            </p>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">
                目标筹款金额（元）
              </label>
              <input
                v-model.number="createForm.targetAmount"
                type="number"
                min="0"
                placeholder="例如 500000"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">
                项目类别
              </label>
              <input
                v-model="createForm.category"
                type="text"
                placeholder="例如 教育、医疗、环保等"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary"
              />
            </div>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">
              项目简介
            </label>
            <textarea
              v-model="createForm.shortDesc"
              rows="3"
              placeholder="简要描述项目背景、用途与预期影响"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary resize-none"
            />
          </div>
        </div>

        <div class="flex items-center justify-end gap-3 px-6 py-4 border-t border-gray-100">
          <button
            class="px-4 py-2 rounded-lg border border-gray-200 text-gray-600 hover:bg-gray-50 text-sm"
            @click="closeCreateModal"
          >
            取消
          </button>
          <button
            class="px-4 py-2 rounded-lg bg-primary text-white hover:bg-primary/90 text-sm disabled:opacity-60 disabled:cursor-not-allowed"
            :disabled="!createForm.title"
            @click="handleCreateProject"
          >
            确认创建
          </button>
        </div>
      </div>
    </div>

    <!-- 项目详情弹窗 -->
    <div
      v-if="showDetailModal && currentProject"
      class="fixed inset-0 z-40 flex items-center justify-center bg-black/40 backdrop-blur-sm"
    >
      <div class="bg-white rounded-xl shadow-xl w-full max-w-xl mx-4">
        <div class="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <h3 class="text-lg font-semibold text-gray-800">
            项目详情
          </h3>
          <button
            class="text-gray-400 hover:text-gray-600"
            @click="closeDetailModal"
          >
            <i class="fas fa-times" />
          </button>
        </div>

        <div class="px-6 py-4 space-y-3" v-if="currentProject">
          <div>
            <div class="text-xs text-gray-500 mb-1">项目名称</div>
            <div class="text-sm font-medium text-gray-900">{{ currentProject.name }}</div>
          </div>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <div class="text-xs text-gray-500 mb-1">所属机构</div>
              <div class="text-sm text-gray-800">{{ currentProject.organization || '—' }}</div>
            </div>
            <div>
              <div class="text-xs text-gray-500 mb-1">创建时间</div>
              <div class="text-sm text-gray-800">{{ currentProject.createdAt || '—' }}</div>
            </div>
          </div>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <div class="text-xs text-gray-500 mb-1">目标筹款金额</div>
              <div class="text-sm text-gray-900">{{ formatNumber(currentProject.targetAmount || 0) }} 元</div>
            </div>
            <div>
              <div class="text-xs text-gray-500 mb-1">当前已筹</div>
              <div class="text-sm text-gray-900">{{ formatNumber(currentProject.raisedAmount || 0) }} 元</div>
            </div>
          </div>
          <div class="mt-2">
            <div class="text-xs text-gray-500 mb-1">本次捐赠金额</div>
            <div class="flex items-center gap-2">
              <span class="text-sm text-gray-700">¥</span>
              <input
                v-model.number="donationAmount"
                type="number"
                min="1"
                class="w-32 px-3 py-1.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary text-sm"
              />
              <span class="text-xs text-gray-400">最低 1 元起捐</span>
            </div>
          </div>
          <div>
            <div class="text-xs text-gray-500 mb-1">链上状态</div>
            <div class="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium" :class="statusBadgeClass(currentProject.status)">
              {{ currentProject.blockchainInfo }} · {{ statusText(currentProject.status) }}
            </div>
          </div>
        </div>

        <div class="flex items-center justify-end gap-3 px-6 py-4 border-t border-gray-100">
          <button
            class="px-4 py-2 rounded-lg border border-gray-200 text-gray-600 hover:bg-gray-50 text-sm"
            @click="closeDetailModal"
          >
            关闭
          </button>
          <button
            class="px-4 py-2 rounded-lg bg-primary text-white hover:bg-primary/90 text-sm"
            @click="openDonateConfirm"
          >
            捐赠
          </button>
        </div>
      </div>
    </div>

    <!-- 确认捐赠弹窗 -->
    <div
      v-if="showDonateConfirm && currentProject"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm"
    >
      <div class="bg-white rounded-xl shadow-xl w-full max-w-sm mx-4">
        <div class="px-6 py-4 border-b border-gray-100">
          <h3 class="text-lg font-semibold text-gray-800">确认捐赠</h3>
        </div>
        <div class="px-6 py-4 space-y-2 text-sm text-gray-700">
          <p>确认向「{{ currentProject.name }}」捐赠 {{ donationAmount }} 元吗？</p>
        </div>
        <div class="flex items-center justify-end gap-3 px-6 py-4 border-t border-gray-100">
          <button
            class="px-4 py-2 rounded-lg border border-gray-200 text-gray-600 hover:bg-gray-50 text-sm"
            @click="cancelDonate"
          >
            取消
          </button>
          <button
            class="px-4 py-2 rounded-lg bg-primary text-white hover:bg-primary/90 text-sm"
            @click="confirmDonate"
          >
            确认捐赠
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref, onMounted } from 'vue'
import { apiListProjects, apiCreateProject } from '@/api/projects'
import StatsCards from '@/components/charts/StatsCards.vue'
import ProjectList from '@/components/charts/ProjectList.vue'
import { apiCreateDonation, apiEnqueueDonation } from '@/api/donate'

type ProjectStatus = 'inProgress' | 'completed' | 'reviewing' | 'rejected'

interface Project {
  id: number
  name: string
  organization: string
  targetAmount: number
  raisedAmount: number
  status: ProjectStatus
  createdAt: string
  blockchainInfo: '已上链' | '待上链'
  blockHeight?: number | ''
}

const projects = ref<Project[]>([])
const page = ref(1)
const pageSize = ref(5)
const total = ref(0)

const showCreateModal = ref(false)
const showDetailModal = ref(false)
const currentProject = ref<Project | null>(null)
const donationAmount = ref(1)
const showDonateConfirm = ref(false)

const createForm = reactive({
  title: '',
  orgCode: '',
  targetAmount: 0,
  category: '',
  shortDesc: ''
})

const openCreateModal = () => {
  // 重置表单再打开
  createForm.title = ''
  createForm.orgCode = ''
  createForm.targetAmount = 0
  createForm.category = ''
  createForm.shortDesc = ''
  showCreateModal.value = true
}

const closeCreateModal = () => {
  showCreateModal.value = false
}

const openDetailModal = (project: Project) => {
  currentProject.value = project
  showDetailModal.value = true
}

const closeDetailModal = () => {
  showDetailModal.value = false
  currentProject.value = null
}

const openDonateConfirm = () => {
  if (!currentProject.value) return
  if (!donationAmount.value || donationAmount.value < 1) {
    donationAmount.value = 1
  }
  showDonateConfirm.value = true
}

const cancelDonate = () => {
  showDonateConfirm.value = false
}

const confirmDonate = async () => {
  if (!currentProject.value) return
  if (!donationAmount.value || donationAmount.value < 1) {
    donationAmount.value = 1
  }

  try {
    // 1) 创建捐赠记录
    const donation = await apiCreateDonation({
      donor_name: '', // 实际使用后端从 JWT 中解析出的用户名
      project_id: currentProject.value.id,
      amount: donationAmount.value,
      currency: 'CNY',
      message: ''
    })

    // // 2) 将捐赠记录加入交易池，等待后续挖矿
    // if (donation && donation.id) {
    //   await apiEnqueueDonation(donation.id)
    // }

    // 关闭弹窗
    showDonateConfirm.value = false
    showDetailModal.value = false
  } catch (e) {
    console.error('[Donate] failed', e)
    // 出错时只关闭确认弹窗，保留详情弹窗以便用户重试或修改金额
    showDonateConfirm.value = false
  }
}

// 接入后端 /api/v1/projects 创建项目
const handleCreateProject = async () => {
  if (!createForm.title) return

  const payload = {
    title: createForm.title,
    // org_name 先用映射后的中文名称，没有则用原始编码
    org_name: orgName(createForm.orgCode) || createForm.orgCode || null,
    target_amount: createForm.targetAmount || null,
    category: createForm.category || null,
    short_desc: createForm.shortDesc || null
  }

  try {
    await apiCreateProject(payload)
    showCreateModal.value = false
    // 新建成功后刷新当前页列表
    await loadProjects()
  } catch (e) {
    console.error('[CreateProject] failed', e)
  }
}

const loadProjects = async () => {
  const res = await apiListProjects({ page: page.value, limit: pageSize.value })
  // 后端返回格式 { items, total }
  projects.value = res.items.map((p: any) => ({
    id: p.id,
    name: p.title,
    organization: p.org_name || '',
    targetAmount: Number(p.target_amount || 0),
    raisedAmount: Number(p.raised_amount || 0),
    status:
      p.status === 'ONGOING' || p.status === 'PENDING'
        ? 'inProgress'
        : p.status === 'FINISHED'
        ? 'completed'
        : 'rejected',
    createdAt: p.created_at?.slice(0, 10) || '',
    blockchainInfo: p.chain_status === 'FULL' ? '已上链' : '待上链',
    blockHeight: p.block_height || ''
  }))
  total.value = res.total
}

onMounted(() => loadProjects())

const filters = reactive({
  keyword: '',
  status: '',
  org: '',
  dateRange: ''
})

const filteredProjects = computed(() => {
  return projects.value.filter((p) => {
    const nameMatch = filters.keyword
      ? p.name.toLowerCase().includes(filters.keyword.toLowerCase())
      : true
    const statusMatch = filters.status ? p.status === filters.status : true
    const orgMatch = filters.org ? p.organization === filters.org : true
    // 时间筛选先不实现，后面接 date picker 再说
    return nameMatch && statusMatch && orgMatch
  })
})

const stats = computed(() => {
  const inProgress = projects.value.filter((p) => p.status === 'inProgress').length
  const completed = projects.value.filter((p) => p.status === 'completed').length
  const waitingChain = projects.value.filter((p) => p.blockchainInfo === '待上链').length
  const onChain = projects.value.filter((p) => p.blockchainInfo === '已上链').length
  return { inProgress, completed, waitingChain, onChain }
})

// 分页由后端控制，这里只做占位和事件转发

const handlePageChange = (newPage: number) => {
  page.value = newPage
  // TODO: 后续接入后端接口时，在这里根据 newPage 请求新数据
}

const applyFilters = () => {
  // 这里只是触发 computed 重新计算，真实项目一般会调 API
}

const resetFilters = () => {
  filters.keyword = ''
  filters.status = ''
  filters.org = ''
  filters.dateRange = ''
}

const progressPercent = (p: Project) => {
  if (!p.targetAmount) return 0
  return Math.min(100, Math.round((p.raisedAmount / p.targetAmount) * 100))
}

const statusText = (status: ProjectStatus) => {
  const map: Record<ProjectStatus, string> = {
    inProgress: '进行中',
    completed: '已结束',
    reviewing: '审核中',
    rejected: '已驳回'
  }
  return map[status] || status
}

const statusBadgeClass = (status: ProjectStatus) => {
  const map: Record<ProjectStatus, string> = {
    inProgress: 'bg-primary-light text-primary',
    completed: 'bg-success-light text-success',
    reviewing: 'bg-warning-light text-warning',
    rejected: 'bg-danger-light text-danger'
  }
  return map[status] || 'bg-gray-100 text-gray-500'
}

const orgName = (orgCode: string) => {
  const map: Record<string, string> = {
    org1: '爱心公益协会',
    org2: '阳光慈善基金会',
    org3: '温暖救助中心',
    org4: '希望工程办公室'
  }
  return map[orgCode] || orgCode
}

const formatNumber = (num: number) => {
  return num.toLocaleString('zh-CN', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  })
}
</script>