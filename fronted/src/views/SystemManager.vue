<template>
  <div class="space-y-6">
    <!-- 顶部标题 + 操作按钮 -->
    <div class="flex items-center justify-between">
      <div class="flex items-center space-x-3">
        <i class="fas fa-heart text-primary text-2xl" />
        <div>
          <h1 class="text-xl font-bold text-gray-700">系统管理</h1>
          <p class="text-sm text-gray-400">
            管理系统用户、角色权限、运行参数与审计日志
          </p>
        </div>
      </div>

      <div class="flex items-center space-x-3">
        <button
          class="bg-primary hover:bg-primary/90 text-white px-4 py-2 rounded-lg flex items-center transition-all duration-300 shadow-sm hover:shadow"
          @click="handleOpenCreate"
        >
          <i class="fas fa-plus mr-2" />
          <span>新增用户</span>
        </button>
      </div>
    </div>



    <!-- 主内容区域：左侧导航 + 右侧不同功能块 -->
    <div class="flex flex-col lg:flex-row gap-6">
      <!-- 左侧系统管理导航 -->
      <div class="lg:w-1/5 bg-white rounded-xl shadow-card p-4 h-fit">
        <nav class="space-y-1">
          <button
            class="w-full text-left px-4 py-3 rounded-lg font-medium flex items-center transition-all duration-300"
            :class="
              currentTab === 'user'
                ? 'bg-primary-light text-primary'
                : 'hover:bg-gray-100 text-gray-700'
            "
            @click="currentTab = 'user'"
          >
            <i class="fas fa-users mr-3 w-5 text-center" />
            <span>用户管理</span>
          </button>

        </nav>
      </div>

      <!-- 右侧内容区 -->
      <div class="lg:w-4/5 space-y-6">
        <!-- 用户管理 -->
        <section v-if="currentTab === 'user'" class="space-y-6">
          <div class="bg-white rounded-xl shadow-card p-6">
            <div class="flex justify-between items-center mb-6">
              <h2 class="text-xl font-bold text-gray-700">用户管理</h2>
              <div class="flex space-x-2">
                <div class="relative">
                  <input
                    type="text"
                    placeholder="搜索用户名或邮箱..."
                    class="pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all duration-300 text-sm"
                  />
                  <i
                    class="fas fa-search absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-xs"
                  />
                </div>
                <select
                  class="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all duration-300"
                >
                  <option>所有状态</option>
                  <option>启用</option>
                  <option>禁用</option>
                </select>
              </div>
            </div>

            <div class="overflow-x-auto">
              <table class="min-w-full divide-y divide-gray-200">
                <thead>
                  <tr class="bg-gray-50">
                    <th
                      class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                    >
                      用户名
                    </th>
                    <th
                      class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                    >
                      邮箱
                    </th>
                    <th
                      class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                    >
                      状态
                    </th>
                    <th
                      class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                    >
                      创建时间
                    </th>
                    <th
                      class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider"
                    >
                      操作
                    </th>
                  </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200">
                  <!-- 从后端加载的用户数据 -->
                  <tr
                    v-for="user in users"
                    :key="user.id"
                    class="hover:bg-gray-50 transition-all duration-300"
                  >
                    <td class="px-6 py-4 whitespace-nowrap">
                      <div class="flex items-center">
                        <div
                          class="h-10 w-10 rounded-full bg-primary-light flex items-center justify-center text-primary font-medium"
                        >
                          {{ (user.username || '?').slice(0, 2).toUpperCase() }}
                        </div>
                        <div class="ml-3">
                          <div class="text-sm font-medium text-gray-700">
                            {{ user.username }}
                          </div>
                          <div class="text-xs text-gray-500">
                            {{ user.is_admin ? '系统管理员' : '普通用户' }}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                      {{ user.email || '—' }}
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap">
                      <span
                        class="px-2 py-1 text-xs rounded-full"
                        :class="user.is_admin ? 'bg-primary-light text-primary' : 'bg-success-light text-success'"
                      >
                        {{ user.is_admin ? '管理员' : '启用' }}
                      </span>
                    </td>
                    <td
                      class="px-6 py-4 whitespace-nowrap text-sm text-gray-500"
                    >
                      {{ user.created_at ? user.created_at.slice(0, 19) : '—' }}
                    </td>
                    <td
                      class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium"
                    >
                      <button
                        class="text-primary hover:text-primary/80 mr-3 transition-colors"
                        @click="handleOpenEdit(user)"
                      >
                        编辑
                      </button>

                      <button
                        class="text-danger hover:text-danger/80 transition-colors"
                      >
                        禁用
                      </button>
                    </td>
                  </tr>

                  <!-- 无数据时占位 -->
                  <tr v-if="!loading && users.length === 0">
                    <td
                      colspan="5"
                      class="px-6 py-10 text-center text-sm text-gray-400"
                    >
                      暂无用户数据
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- 分页占位，后端分页接入后替换 -->
            <div class="flex justify-between items-center mt-6 text-sm text-gray-500">
              <div>
                显示 第 {{ pagination.page }} 页，当前 {{ users.length }} 条记录
              </div>
              <div class="flex space-x-1">
                <button
                  class="px-3 py-1 border border-gray-200 rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  :disabled="pagination.page <= 1 || loading"
                  @click="handlePrevPage"
                >
                  上一页
                </button>
                <button
                  class="px-3 py-1 border border-primary bg-primary text-white rounded"
                  disabled
                >
                  {{ pagination.page }}
                </button>
                <button
                  class="px-3 py-1 border border-gray-200 rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  :disabled="users.length < pagination.limit || loading"
                  @click="handleNextPage"
                >
                  下一页
                </button>
              </div>
            </div>
          </div>
        </section>


      </div>
    </div>

    <!-- 新增用户弹窗 -->
    <div
      v-if="showCreateDialog"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
    >
      <div class="bg-white rounded-xl shadow-xl w-full max-w-md p-6">
        <h2 class="text-lg font-bold text-gray-800 mb-4">新增用户</h2>
        <div class="space-y-4">
          <div>
            <label class="block text-sm text-gray-600 mb-1">用户名</label>
            <input
              v-model="createForm.username"
              type="text"
              class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary"
              placeholder="请输入用户名"
            />
          </div>
          <div>
            <label class="block text-sm text-gray-600 mb-1">邮箱</label>
            <input
              v-model="createForm.email"
              type="email"
              class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary"
              placeholder="请输入邮箱（可选）"
            />
          </div>
          <div>
            <label class="block text-sm text-gray-600 mb-1">密码</label>
            <input
              v-model="createForm.password"
              type="password"
              class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary"
              placeholder="请输入密码"
            />
          </div>
          <p class="text-xs text-gray-400">
            新增用户将作为普通用户创建（is_admin = 0）。
          </p>
        </div>

        <div class="flex justify-end space-x-3 mt-6">
          <button
            class="px-4 py-2 rounded-lg border border-gray-200 text-sm text-gray-600 hover:bg-gray-50 transition-colors"
            @click="showCreateDialog = false"
            :disabled="createLoading"
          >
            取消
          </button>
          <button
            class="px-4 py-2 rounded-lg bg-primary text-white text-sm hover:bg-primary/90 transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
            @click="handleCreateUser"
            :disabled="createLoading"
          >
            {{ createLoading ? '提交中...' : '确认创建' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 编辑用户弹窗 -->
    <div
      v-if="showEditDialog"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
    >
      <div class="bg-white rounded-xl shadow-xl w-full max-w-md p-6">
        <h2 class="text-lg font-bold text-gray-800 mb-4">编辑用户</h2>
        <div class="space-y-4">
          <div>
            <label class="block text-sm text-gray-600 mb-1">用户名</label>
            <div class="w-full border border-gray-100 rounded-lg px-3 py-2 text-sm bg-gray-50 text-gray-700">
              {{ editForm.username || '—' }}
            </div>
          </div>
          <div>
            <label class="block text-sm text-gray-600 mb-1">邮箱</label>
            <div class="w-full border border-gray-100 rounded-lg px-3 py-2 text-sm bg-gray-50 text-gray-700">
              {{ editForm.email || '—' }}
            </div>
          </div>
          <div>
            <label class="block text-sm text-gray-600 mb-1">钱包地址</label>
            <div class="w-full border border-gray-100 rounded-lg px-3 py-2 text-sm bg-gray-50 text-gray-700 break-all">
              {{ editForm.wallet_address || '—' }}
            </div>
          </div>
          <div>
            <label class="block text-sm text-gray-600 mb-1">钱包余额</label>
            <input
              v-model="editForm.balance"
              type="number"
              min="0"
              step="0.01"
              class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary"
              placeholder="请输入钱包余额"
            />
          </div>
        </div>

        <div class="flex justify-end space-x-3 mt-6">
          <button
            class="px-4 py-2 rounded-lg border border-gray-200 text-sm text-gray-600 hover:bg-gray-50 transition-colors"
            @click="showEditDialog = false"
            :disabled="editLoading"
          >
            取消
          </button>
          <button
            class="px-4 py-2 rounded-lg bg-primary text-white text-sm hover:bg-primary/90 transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
            @click="handleUpdateUser"
            :disabled="editLoading"
          >
            {{ editLoading ? '保存中...' : '保存修改' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { apiListUsers, apiRegister, apiUpdateUser, type UserItem } from '@/api/auth'

// 当前激活的右侧 tab（目前只有用户管理）
const currentTab = ref<'user'>('user')

// 用户列表数据与加载状态
const users = ref<UserItem[]>([])
const loading = ref(false)

// 简单分页状态（后端暂未返回 total 时，以当前页数据长度为准）
const pagination = reactive({
  page: 1,
  limit: 10,
  total: 0,
})

// 编辑用户弹窗状态与表单
const showEditDialog = ref(false)
const editLoading = ref(false)
const editForm = reactive({
  id: 0,
  username: '',
  email: '',
  wallet_address: '',
  balance: '' as string | number,
})

// 新增用户弹窗状态与表单
const showCreateDialog = ref(false)
const createLoading = ref(false)
const createForm = reactive({
  username: '',
  email: '',
  password: '',
})

const resetCreateForm = () => {
  createForm.username = ''
  createForm.email = ''
  createForm.password = ''
}

const handleOpenCreate = () => {
  resetCreateForm()
  showCreateDialog.value = true
}

const handleOpenEdit = (user: UserItem) => {
  editForm.id = user.id
  editForm.username = user.username || ''
  editForm.email = (user.email as string) || ''
  editForm.wallet_address = (user as any).wallet_address || ''
  editForm.balance = (user as any).balance ?? ''
  showEditDialog.value = true
}

const handleCreateUser = async () => {
  if (!createForm.username || !createForm.password) {
    // 简单防呆：用户名和密码必填
    return
  }
  try {
    createLoading.value = true
    await apiRegister({
      username: createForm.username,
      email: createForm.email,
      password: createForm.password,
      is_admin: false, // 普通用户
    })
    showCreateDialog.value = false
    resetCreateForm()
    await fetchUsers()
  } catch (e) {
    console.error('创建用户失败', e)
  } finally {
    createLoading.value = false
  }
}

const handleUpdateUser = async () => {
  if (!editForm.id) return
  try {
    editLoading.value = true
    await apiUpdateUser(editForm.id, {
      balance: editForm.balance === '' ? undefined : Number(editForm.balance),
    } as any)
    showEditDialog.value = false
    await fetchUsers()
  } catch (e) {
    console.error('更新用户失败', e)
  } finally {
    editLoading.value = false
  }
}

const fetchUsers = async () => {
  try {
    loading.value = true
    const data = await apiListUsers({
      page: pagination.page,
      limit: pagination.limit,
    })
    users.value = data || []
    pagination.total = users.value.length
  } catch (e) {
    console.error('加载用户列表失败', e)
    users.value = []
    pagination.total = 0
  } finally {
    loading.value = false
  }
}

// 简单的前一页 / 下一页占位逻辑（如果后续需要服务端分页，可再扩展）
const handlePrevPage = () => {
  if (pagination.page <= 1) return
  pagination.page -= 1
  fetchUsers()
}

const handleNextPage = () => {
  // 这里只根据当前页条数是否达到 limit 简单判断是否还有下一页
  if (users.value.length < pagination.limit) return
  pagination.page += 1
  fetchUsers()
}

onMounted(() => {
  fetchUsers()
})
</script>