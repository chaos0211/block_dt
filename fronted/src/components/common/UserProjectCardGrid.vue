<template>
  <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
    <div
      v-for="p in projects"
      :key="p.id"
      class="bg-white rounded-xl shadow-card border border-gray-100 overflow-hidden hover:shadow-md transition-shadow duration-200"
    >
      <!-- 项目图片（不超过边框） -->
      <div class="h-40 bg-gray-100 overflow-hidden">
        <img
          v-if="p.img_url && !brokenImgIds.has(p.id)"
          :src="p.img_url"
          :alt="p.title"
          class="block w-full h-full object-cover object-center"
          loading="lazy"
          :data-pid="p.id"
          @error="onImgError"
        />
        <div v-else class="h-full w-full flex items-center justify-center text-gray-400">
          <i class="fas fa-image text-3xl" />
        </div>
      </div>

      <div class="p-5 space-y-3">
        <div class="flex items-start justify-between gap-3">
          <h3 class="text-base font-semibold text-gray-900 line-clamp-2">
            {{ p.title }}
          </h3>
          <span class="text-xs px-2 py-1 rounded-full bg-success-light text-success whitespace-nowrap">
            已上链
          </span>
        </div>

        <p class="text-sm text-gray-600 line-clamp-2 min-h-[2.5rem]">
          {{ p.description || '暂无描述' }}
        </p>

        <div class="text-sm text-gray-700">
          <div class="flex items-center justify-between">
            <span class="text-gray-500">已筹</span>
            <span class="font-medium">¥{{ formatInt(p.current_amount) }}</span>
          </div>
          <div class="flex items-center justify-between mt-1">
            <span class="text-gray-500">目标</span>
            <span class="font-medium">¥{{ formatInt(p.target_amount) }}</span>
          </div>
        </div>

        <div class="pt-2 flex items-center justify-end">
          <button
            class="px-4 py-2 rounded-lg bg-primary text-white hover:bg-primary/90 text-sm"
            type="button"
            @click="$emit('view', p)"
          >
            查看并捐赠
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  projects: Array<{
    id: number
    title: string
    description?: string
    img_url?: string
    target_amount: number
    current_amount: number
    status?: string
  }>
}>()

defineEmits<{
  (e: 'view', p: any): void
}>()

const brokenImgIds = new Set<number>()

const formatInt = (n: number | string | null | undefined) => {
  const v = Number(n ?? 0)
  if (Number.isNaN(v)) return '0'
  return v.toLocaleString('zh-CN', { maximumFractionDigits: 0 })
}

const onImgError = (e: Event) => {
  const img = e.target as HTMLImageElement
  const pid = Number(img.getAttribute('data-pid') || NaN)
  if (!Number.isNaN(pid)) brokenImgIds.add(pid)
}
</script>