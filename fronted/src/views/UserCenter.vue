<template>
  <div class="bg-neutral-100 font-inter text-neutral-800 min-h-screen">
    <main class="container mx-auto px-4 py-8 max-w-4xl">
      <div class="space-y-8">
        <!-- 页面标题 -->
        <div class="flex justify-between items-center">
          <div>
            <h1 class="text-[clamp(1.5rem,3vw,2.5rem)] font-bold text-neutral-900">
              个人中心
            </h1>
            <p class="text-neutral-700 mt-1">查看和管理您的账户信息</p>
          </div>
        </div>

        <!-- 基本信息 -->
        <div class="bg-white rounded-xl p-6 card-shadow">
          <h2 class="text-xl font-semibold mb-6 flex items-center">
            <i class="fas fa-user-circle text-primary mr-2"></i>
            账户基本信息
          </h2>

          <div class="space-y-6">
            <!-- 用户名 -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4 items-center">
              <label class="font-medium">用户名</label>
              <div class="md:col-span-2 bg-neutral-100 rounded-lg p-3">
                {{ user.username || '—' }}
              </div>
            </div>

            <!-- 邮箱 -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4 items-center">
              <label class="font-medium">绑定邮箱</label>
              <div class="md:col-span-2 flex items-center gap-3">
                <div class="flex-1 bg-neutral-100 rounded-lg p-3">
                  {{ user.email || '—' }}
                </div>
                <button class="btn-secondary text-sm" :disabled="loading" @click="openEmailModal">
                  <i class="fas fa-pencil-alt mr-1"></i> 编辑
                </button>
              </div>
            </div>

            <!-- 钱包地址 -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4 items-start">
              <label class="font-medium pt-3">区块链钱包地址</label>
              <div class="md:col-span-2 space-y-2">
                <div class="bg-neutral-100 rounded-lg p-3 break-all">
                  {{ user.wallet_address || '—' }}
                </div>
                <button class="btn-secondary text-sm" @click="copyWallet">
                  <i class="fas fa-copy mr-1"></i> 复制地址
                </button>
              </div>
            </div>

            <!-- 创建时间 -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4 items-center">
              <label class="font-medium">账户创建时间</label>
              <div class="md:col-span-2 bg-neutral-100 rounded-lg p-3">
                {{ formatTime(user.created_at) }}
              </div>
            </div>
          </div>
        </div>

        <!-- 账户余额 -->
        <div class="bg-white rounded-xl p-6 card-shadow">
          <h2 class="text-xl font-semibold mb-6 flex items-center">
            <i class="fas fa-wallet text-secondary mr-2"></i>
            账户资产与状态
          </h2>

          <div class="bg-neutral-100 rounded-lg p-4">
            <div class="flex items-baseline">
              <span class="text-2xl font-bold text-secondary">
                {{ formatBalance(user.balance) }}
              </span>
              <span class="ml-2">元</span>
            </div>

          </div>
        </div>
      </div>
    </main>

    <!-- 编辑邮箱弹窗 -->
    <div v-if="showEmailModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-white rounded-xl p-6 max-w-md w-full">
        <h3 class="text-xl font-semibold mb-4">编辑邮箱</h3>

        <input
          v-model="newEmail"
          type="email"
          class="w-full border rounded-lg p-3 mb-2"
          placeholder="请输入新邮箱地址"
        />

        <p v-if="emailError" class="text-red-500 text-sm mb-2">
          请输入有效的邮箱地址
        </p>

        <div class="flex justify-end gap-3">
          <button class="btn-secondary" @click="closeEmailModal">取消</button>
          <button class="btn-primary" :disabled="loading" @click="saveEmail">保存</button>
        </div>
      </div>
    </div>

    <!-- 复制提示 -->
    <div
      v-if="showToast"
      class="fixed bottom-6 right-6 bg-green-500 text-white px-4 py-2 rounded-lg shadow-lg flex items-center"
    >
      <i class="fas fa-check-circle mr-2"></i>
      {{ toastText }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { apiGetMe, apiUpdateMe, type UserItem } from '@/api/auth'

const user = ref<UserItem>({
  id: 0,
  username: '',
  email: '',
  is_admin: false,
  is_active: true,
  wallet_address: '',
  balance: 0,
  created_at: '',
  updated_at: ''
})

const loading = ref(false)

const showEmailModal = ref(false)
const newEmail = ref('')
const emailError = ref(false)

const showToast = ref(false)
const toastText = ref('')

const formatTime = (t?: string | null) => {
  if (!t) return '—'
  return String(t).replace('T', ' ').slice(0, 19)
}

const formatBalance = (v: any) => {
  const n = Number(v ?? 0)
  if (Number.isNaN(n)) return '0'
  // 余额保留 2 位展示（数据库可能是 decimal 字符串）
  return n.toLocaleString('zh-CN', { minimumFractionDigits: 0, maximumFractionDigits: 2 })
}

const toast = (msg: string) => {
  toastText.value = msg
  showToast.value = true
  setTimeout(() => (showToast.value = false), 3000)
}

const loadMe = async () => {
  loading.value = true
  try {
    const me = await apiGetMe()
    user.value = me
  } catch (e) {
    console.error('[UserCenter] apiGetMe failed', e)
    toast('获取个人信息失败，请重新登录')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadMe()
})

const openEmailModal = () => {
  newEmail.value = String(user.value.email ?? '')
  showEmailModal.value = true
}

const closeEmailModal = () => {
  showEmailModal.value = false
  emailError.value = false
}

const saveEmail = async () => {
  const reg = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!reg.test(newEmail.value)) {
    emailError.value = true
    return
  }

  try {
    const updated = await apiUpdateMe({ email: newEmail.value })
    user.value = updated
    closeEmailModal()
    toast('邮箱更新成功')
  } catch (e: any) {
    console.error('[UserCenter] apiUpdateMe failed', e)
    const msg = e?.response?.data?.detail || '邮箱更新失败'
    toast(msg)
  }
}

const copyWallet = async () => {
  try {
    await navigator.clipboard.writeText(String(user.value.wallet_address ?? ''))
    toast('钱包地址复制成功')
  } catch (e) {
    console.error('[UserCenter] copy failed', e)
    toast('复制失败')
  }
}
</script>

<style scoped>
.card-shadow {
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}
.btn-primary {
  background: #3b82f6;
  color: #fff;
  padding: 0.5rem 1rem;
  border-radius: 0.5rem;
}
.btn-secondary {
  background: #fff;
  border: 1px solid #e5e7eb;
  padding: 0.5rem 1rem;
  border-radius: 0.5rem;
}
</style>