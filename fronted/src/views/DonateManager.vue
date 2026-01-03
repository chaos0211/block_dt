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
      </div>
      <div class="flex space-x-3">
        <button
          class="bg-primary hover:bg-primary/90 text-white px-4 py-2 rounded-lg flex items-center shadow-sm hover:shadow transition-all duration-300 text-sm"
          @click="openCreateModal"
        >
          <i class="fas fa-plus mr-2" />
          <span>新增项目</span>
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
            <option value="PENDING">待审核</option>
            <option value="APPROVED">已审核</option>
            <option value="ON_CHAIN">已上链</option>
            <option value="COMPLETED">已结束</option>
          </select>
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
      @edit="openEditModal"
      @delete="openDeleteConfirm"
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
              项目详情描述 <span class="text-red-500">*</span>
            </label>
            <textarea
              v-model="createForm.description"
              rows="4"
              placeholder="请详细描述受助对象、资金需求、使用计划与预期成果等信息"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary resize-none"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">
              目标筹款金额（元） <span class="text-red-500">*</span>
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
              项目图片 URL
            </label>
            <input
              v-model="createForm.img_url"
              type="text"
              placeholder="请输入项目图片的网络地址"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary"
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
            :disabled="!createForm.title || !createForm.description || !createForm.targetAmount"
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

        <div class="px-6 py-4" v-if="currentProject">
          <div class="flex flex-col md:flex-row gap-4">
            <!-- 左侧图片 -->
            <div class="w-full md:w-5/12">
              <div class="rounded-xl bg-gray-100 h-56 overflow-hidden">
                <img
                  v-if="currentProject.img_url"
                  :src="currentProject.img_url"
                  :alt="currentProject.title"
                  class="block w-full h-full object-cover object-center"
                  loading="lazy"
                />
                <div v-else class="h-full flex items-center justify-center text-gray-400">
                  <i class="fas fa-image text-4xl" />
                </div>
              </div>
            </div>

            <!-- 右侧字段 -->
            <div class="w-full md:w-7/12 space-y-3">
              <div>
                <div class="text-xs text-gray-500 mb-1">项目名称</div>
                <div class="text-sm font-medium text-gray-900">{{ currentProject.title }}</div>
              </div>

              <div>
                <div class="text-xs text-gray-500 mb-1">项目描述</div>
                <div class="text-sm text-gray-800 whitespace-pre-line">{{ currentProject.description || '—' }}</div>
              </div>

              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <div class="text-xs text-gray-500 mb-1">创建时间</div>
                  <div class="text-sm text-gray-800">{{ currentProject.created_at ? currentProject.created_at.slice(0, 10) : '—' }}</div>
                </div>
              </div>

              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <div class="text-xs text-gray-500 mb-1">目标筹款金额</div>
                  <div class="text-sm text-gray-900">{{ formatNumber(currentProject.target_amount || 0) }} 元</div>
                </div>
                <div>
                  <div class="text-xs text-gray-500 mb-1">当前已筹</div>
                  <div class="text-sm text-gray-900">{{ formatNumber(currentProject.current_amount || 0) }} 元</div>
                </div>
              </div>

              <div>
                <div class="text-xs text-gray-500 mb-1">状态</div>
                <div
                  class="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium"
                  :class="statusBadgeClass(currentProject.status)"
                >
                  {{ statusText(currentProject.status) }}
                </div>
              </div>
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

          <!-- 状态为 APPROVED 时显示提交上链按钮（入池） -->
          <button
            v-if="currentProject && currentProject.status === 'APPROVED'"
            class="px-4 py-2 rounded-lg border border-gray-200 text-gray-600 hover:bg-gray-50 text-sm"
            @click="handleOnChain"
          >
            提交上链
          </button>

          <!-- 状态为 PENDING 时显示审核按钮（在关闭右侧），用于直接审核 -->
          <button
            v-else-if="currentProject && currentProject.status === 'PENDING'"
            class="px-4 py-2 rounded-lg border border-gray-200 text-gray-600 hover:bg-gray-50 text-sm"
            @click="handleAuditApprove"
          >
            审核
          </button>
        </div>
      </div>
    </div>

    <!-- 编辑项目弹窗 -->
    <div
      v-if="showEditModal && editProject"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm"
    >
      <div class="bg-white rounded-xl shadow-xl w-full max-w-xl mx-4">
        <div class="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <h3 class="text-lg font-semibold text-gray-800">编辑项目</h3>
          <button class="text-gray-400 hover:text-gray-600" @click="closeEditModal">
            <i class="fas fa-times" />
          </button>
        </div>

        <div class="px-6 py-4 space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">项目名称 <span class="text-red-500">*</span></label>
            <input
              v-model="editForm.title"
              type="text"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">项目详情描述 <span class="text-red-500">*</span></label>
            <textarea
              v-model="editForm.description"
              rows="4"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary resize-none"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">目标筹款金额（元） <span class="text-red-500">*</span></label>
            <input
              v-model.number="editForm.targetAmount"
              type="number"
              min="0"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">项目图片 URL</label>
            <input
              v-model="editForm.img_url"
              type="text"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary"
            />
          </div>
        </div>

        <div class="flex items-center justify-end gap-3 px-6 py-4 border-t border-gray-100">
          <button class="px-4 py-2 rounded-lg border border-gray-200 text-gray-600 hover:bg-gray-50 text-sm" @click="closeEditModal">取消</button>
          <button
            class="px-4 py-2 rounded-lg bg-primary text-white hover:bg-primary/90 text-sm disabled:opacity-60 disabled:cursor-not-allowed"
            :disabled="!editForm.title || !editForm.description || !editForm.targetAmount"
            @click="handleUpdateProject"
          >
            保存修改
          </button>
        </div>
      </div>
    </div>

    <!-- 删除确认弹窗 -->
    <div
      v-if="showDeleteConfirm && deleteTarget"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm"
    >
      <div class="bg-white rounded-xl shadow-xl w-full max-w-md mx-4">
        <div class="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <h3 class="text-lg font-semibold text-gray-800">删除项目</h3>
          <button class="text-gray-400 hover:text-gray-600" @click="closeDeleteConfirm">
            <i class="fas fa-times" />
          </button>
        </div>
        <div class="px-6 py-4 text-sm text-gray-700">
          确认删除项目：<span class="font-medium text-gray-900">{{ deleteTarget.title }}</span> ？
        </div>
        <div class="flex items-center justify-end gap-3 px-6 py-4 border-t border-gray-100">
          <button class="px-4 py-2 rounded-lg border border-gray-200 text-gray-600 hover:bg-gray-50 text-sm" @click="closeDeleteConfirm">取消</button>
          <button class="px-4 py-2 rounded-lg bg-red-600 text-white hover:bg-red-700 text-sm" @click="handleDeleteProject">确认删除</button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref, onMounted } from 'vue'
import { apiListProjects, apiCreateProject, apiApproveProject, apiPutProjectOnChain, apiUpdateProject, apiDeleteProject } from '@/api/projects'
import StatsCards from '@/components/charts/StatsCards.vue'
import ProjectList from '@/components/charts/ProjectList.vue'

type ProjectStatus = 'PENDING' | 'APPROVED' | 'ON_CHAIN' | 'COMPLETED'

interface Project {
  id: number
  title: string
  description?: string
  img_url?: string | null
  target_amount: number
  current_amount: number
  status: ProjectStatus | string
  created_at: string
  blockchain_address?: string | null
  blockchain_tx_hash?: string | null
  on_chain_at?: string | null
}

const projects = ref<Project[]>([])
const page = ref(1)
const pageSize = ref(5)
const total = ref(0)

const showCreateModal = ref(false)
const showDetailModal = ref(false)
const currentProject = ref<Project | null>(null)

const showEditModal = ref(false)
const editProject = ref<Project | null>(null)

const editForm = reactive({
  title: '',
  description: '',
  targetAmount: 0,
  img_url: ''
})

const showDeleteConfirm = ref(false)
const deleteTarget = ref<Project | null>(null)

const createForm = reactive({
  title: '',
  description: '',
  targetAmount: 0,
  img_url: '',
})

const openCreateModal = () => {
  // 重置表单再打开
  createForm.title = ''
  createForm.description = ''
  createForm.targetAmount = 0
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


// 接入后端 /api/v1/projects 创建项目
const handleCreateProject = async () => {
  if (!createForm.title) return

  const payload = {
    title: createForm.title,
    description: createForm.description,
    target_amount: createForm.targetAmount,
    img_url: createForm.img_url,
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
  // 后端返回格式 { projects, total, page, size }
  projects.value = (res.projects || []).map((p: any) => ({
    id: p.id,
    title: p.title,
    description: p.description,
    img_url: p.img_url ?? null,
    target_amount: Number(p.target_amount ?? 0),
    current_amount: Number(p.current_amount ?? 0),
    status: (p.status || '').toString().toUpperCase(),
    created_at: p.created_at,
    blockchain_address: p.blockchain_address,
    blockchain_tx_hash: p.blockchain_tx_hash,
    on_chain_at: p.on_chain_at
  }))
  total.value = res.total ?? 0
}
const openEditModal = (project: Project) => {
  editProject.value = project
  editForm.title = project.title
  editForm.description = project.description || ''
  editForm.targetAmount = Number(project.target_amount ?? 0)
  editForm.img_url = project.img_url || ''
  showEditModal.value = true
}

const closeEditModal = () => {
  showEditModal.value = false
  editProject.value = null
}

const openDeleteConfirm = (project: Project) => {
  deleteTarget.value = project
  showDeleteConfirm.value = true
}

const closeDeleteConfirm = () => {
  showDeleteConfirm.value = false
  deleteTarget.value = null
}

onMounted(() => loadProjects())

const filters = reactive({
  keyword: '',
  status: '',
  dateRange: ''
})

const filteredProjects = computed(() => {
  return projects.value.filter((p) => {
    const nameMatch = filters.keyword
      ? p.title.toLowerCase().includes(filters.keyword.toLowerCase())
      : true
    const statusMatch = filters.status ? p.status === filters.status : true
    return nameMatch && statusMatch
  })
})

const stats = computed(() => {
  const inProgress = projects.value.filter((p) => p.status === 'ON_CHAIN').length
  const completed = projects.value.filter((p) => p.status === 'COMPLETED').length
  const waitingChain = projects.value.filter((p) => p.status === 'APPROVED').length
  const onChain = projects.value.filter((p) => p.status === 'ON_CHAIN' || p.status === 'COMPLETED').length
  return { inProgress, completed, waitingChain, onChain }
})

// 分页由后端控制，这里只做占位和事件转发

const handlePageChange = async (newPage: number) => {
  page.value = newPage
  await loadProjects()
}

const applyFilters = () => {
  // 这里只是触发 computed 重新计算，真实项目一般会调 API
}

const resetFilters = () => {
  filters.keyword = ''
  filters.status = ''
  filters.dateRange = ''
}

const progressPercent = (p: Project) => {
  if (!p.target_amount) return 0
  return Math.min(100, Math.round((p.current_amount / p.target_amount) * 100))
}

const statusText = (status: ProjectStatus | string) => {
  const map: Record<string, string> = {
    PENDING: '待审核',
    APPROVED: '待上链',
    ON_CHAIN: '进行中',
    COMPLETED: '已结束'
  }
  return map[status] || (status as string)
}

const statusBadgeClass = (status: ProjectStatus | string) => {
  const map: Record<string, string> = {
  PENDING: 'bg-warning-light text-warning',
  APPROVED: 'bg-primary-light text-primary',
  ON_CHAIN: 'bg-success-light text-success',
  COMPLETED: 'bg-gray-100 text-gray-700'
}
  return map[status] || 'bg-gray-100 text-gray-500'
}

const formatNumber = (num: number | null | undefined) => {
  const n = Number(num ?? 0)
  if (Number.isNaN(n)) return '0'
  return n.toLocaleString('zh-CN', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  })
}

const handleAuditApprove = async () => {
  if (!currentProject.value) return
  try {
    await apiApproveProject(currentProject.value.id, {
      approved: true,
      rejection_reason: null
    })
    await loadProjects()
    const updated = projects.value.find(p => p.id === currentProject.value!.id)
    if (updated) {
      currentProject.value = { ...updated }
    }
  } catch (e) {
    console.error('[AuditProject] failed', e)
  }
}

const handleOnChain = async () => {
  if (!currentProject.value) return
  try {
    await apiPutProjectOnChain(currentProject.value.id)
    await loadProjects()
    const updated = projects.value.find(p => p.id === currentProject.value!.id)
    if (updated) {
      currentProject.value = { ...updated }
    }
    // 提交成功提示，并关闭详情窗口
    window.alert('申请提交，请等待审核')
    showDetailModal.value = false
    currentProject.value = null
  } catch (e) {
    console.error('[OnChain] failed', e)
    // 提交失败提示，并关闭详情窗口
    window.alert('申请入池失败')
    showDetailModal.value = false
    currentProject.value = null
  }
}
const handleUpdateProject = async () => {
  if (!editProject.value) return

  const payload = {
    title: editForm.title,
    description: editForm.description,
    target_amount: editForm.targetAmount,
    img_url: editForm.img_url,
  }

  try {
    await apiUpdateProject(editProject.value.id, payload)
    await loadProjects()
    closeEditModal()
    window.alert('更新成功')
  } catch (e) {
    console.error('[UpdateProject] failed', e)
    window.alert('更新失败')
  }
}

const handleDeleteProject = async () => {
  if (!deleteTarget.value) return
  try {
    await apiDeleteProject(deleteTarget.value.id)
    await loadProjects()
    closeDeleteConfirm()
    // 如果刚好在详情页，关闭详情
    if (currentProject.value && currentProject.value.id === deleteTarget.value.id) {
      closeDetailModal()
    }
    window.alert('删除成功')
  } catch (e) {
    console.error('[DeleteProject] failed', e)
    window.alert('删除失败')
  }
}
</script>