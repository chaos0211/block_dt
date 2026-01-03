<template>
  <div
    v-if="visible && project"
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm"
  >
    <div class="bg-white rounded-xl shadow-xl w-full max-w-3xl mx-4 overflow-hidden">
      <div class="flex items-center justify-between px-6 py-4 border-b border-gray-100">
        <h3 class="text-lg font-semibold text-gray-800">项目详情</h3>
        <button class="text-gray-400 hover:text-gray-600" type="button" @click="$emit('close')">
          <i class="fas fa-times" />
        </button>
      </div>

      <div class="p-6">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <!-- 左侧：项目图片 -->
          <div class="rounded-xl bg-gray-100 h-56 overflow-hidden">
            <img
              v-if="project.img_url"
              :src="project.img_url"
              :alt="project.title"
              class="block w-full h-full object-cover object-center"
              loading="lazy"
            />
            <div v-else class="h-full flex items-center justify-center text-gray-400">
              <div class="text-center">
                <i class="fas fa-image text-4xl" />
                <div class="text-xs mt-2">暂无图片</div>
              </div>
            </div>
          </div>

          <!-- 右侧：介绍 + 金额 + 捐赠 -->
          <div class="space-y-3">
            <div class="text-lg font-semibold text-gray-900">
              {{ project.title }}
            </div>
            <div class="text-sm text-gray-600 leading-relaxed">
              {{ project.description || '暂无描述' }}
            </div>

            <div class="bg-gray-50 rounded-xl p-4 space-y-2">
              <div class="flex items-center justify-between text-sm">
                <span class="text-gray-500">已筹金额</span>
                <span class="font-semibold text-gray-900">¥{{ formatInt(project.current_amount) }}</span>
              </div>
              <div class="flex items-center justify-between text-sm">
                <span class="text-gray-500">目标金额</span>
                <span class="font-semibold text-gray-900">¥{{ formatInt(project.target_amount) }}</span>
              </div>
              <div class="flex items-center justify-between text-sm pt-1">
                <span class="text-gray-500">我的余额</span>
                <span class="font-semibold text-gray-900">¥{{ formatInt(balance) }}</span>
              </div>
            </div>

            <div class="mt-2">
              <div class="text-xs text-gray-500 mb-1">捐赠金额</div>
              <div class="flex items-center gap-2">
                <span class="text-sm text-gray-700">¥</span>
                <input
                  v-model.number="amount"
                  type="number"
                  min="1"
                  class="w-40 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary text-sm"
                />
                <label class="text-xs text-gray-500 flex items-center gap-2">
                  <input v-model="isAnonymous" type="checkbox" />
                  匿名捐赠
                </label>
              </div>
            </div>

            <div class="pt-3 flex items-center justify-end gap-3">
              <button
                class="px-4 py-2 rounded-lg border border-gray-200 text-gray-600 hover:bg-gray-50 text-sm"
                type="button"
                @click="$emit('close')"
              >
                关闭
              </button>
              <button
                class="px-4 py-2 rounded-lg bg-primary text-white hover:bg-primary/90 text-sm disabled:opacity-60 disabled:cursor-not-allowed"
                type="button"
                :disabled="!amount || amount < 1 || Number(balance) < Number(amount)"
                @click="emitDonate"
              >
                捐赠
              </button>
            </div>

            <div v-if="Number(balance) < Number(amount)" class="text-xs text-red-500">
              余额不足，请调整捐赠金额
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

const props = defineProps<{
  visible: boolean
  project: {
    id: number
    title: string
    description?: string
    img_url?: string
    target_amount: number
    current_amount: number
  } | null
  balance: number
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'donate', payload: { projectId: number; amount: number; isAnonymous: boolean }): void
}>()

const amount = ref<number>(1)
const isAnonymous = ref<boolean>(false)

watch(
  () => props.visible,
  (v) => {
    if (v) {
      amount.value = 1
      isAnonymous.value = false
    }
  }
)

const emitDonate = () => {
  if (!props.project) return
  emit('donate', {
    projectId: props.project.id,
    amount: Number(amount.value ?? 0),
    isAnonymous: Boolean(isAnonymous.value)
  })
}

const formatInt = (n: number | string | null | undefined) => {
  const v = Number(n ?? 0)
  if (Number.isNaN(v)) return '0'
  return v.toLocaleString('zh-CN', { maximumFractionDigits: 0 })
}
</script>