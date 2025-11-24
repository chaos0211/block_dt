<template>
  <div class="flex justify-end items-center mb-3 gap-2">
    <input
      v-model.number="maxTransactions"
      type="number"
      min="1"
      class="w-24 px-2 py-1 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary"
      placeholder="数量"
    />
    <button
      class="px-4 py-2 rounded-lg bg-primary text-white hover:bg-primary/90 text-sm"
      @click="handleMine"
    >
      挖矿
    </button>
  </div>
  <ProjectList
    :projects="poolItems"
    :total="poolTotal"
    :page="page"
    :page-size="pageSize"
    titleText="交易池列表"
    @change-page="onPoolPageChange"
  >
    <!-- 自定义表头 -->
    <template #header>
      <th class="px-6 py-4 text-sm font-semibold text-gray-700">交易哈希</th>
      <th class="px-6 py-4 text-sm font-semibold text-gray-700">来源地址</th>
      <th class="px-6 py-4 text-sm font-semibold text-gray-700">目标地址</th>
      <th class="px-6 py-4 text-sm font-semibold text-gray-700">金额</th>
      <th class="px-6 py-4 text-sm font-semibold text-gray-700">创建时间</th>
    </template>
    <!-- 自定义每一行 -->
    <template #row="{ project: tx }">
      <td class="px-6 py-4 text-xs">
        {{ shorten(tx.transaction_hash) }}
      </td>
      <td class="px-6 py-4 text-xs">
        {{ tx.from_address }}
      </td>
      <td class="px-6 py-4 text-xs">
        {{ shorten(tx.to_address) }}
      </td>
      <td class="px-6 py-4 text-sm">
        ¥{{ tx.amount }}
      </td>
      <td class="px-6 py-4 text-sm">
        {{ tx.created_at || '-' }}
      </td>
    </template>
  </ProjectList>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import ProjectList from '@/components/charts/ProjectList.vue'
import { apiListPool as apiListPool } from '@/api/TransactionPool'
import { apiMineBlock } from '@/api/TransactionPool'

interface PoolItem {
  id: number
  transaction_hash: string
  from_address: string
  to_address: string
  amount: number
  created_at: string | null
  project_id?: number | null
}

const poolItems = ref<PoolItem[]>([])
const poolTotal = ref(0)
const page = ref(1)
const pageSize = ref(10)

const maxTransactions = ref(10)

const shorten = (value: string, head = 6, tail = 4): string => {
  if (!value) return ''
  if (value.length <= head + tail) return value
  return value.slice(0, head) + '...' + value.slice(-tail)
}

const loadPool = async () => {
  try {
    const res = await apiListPool({ page: page.value, limit: pageSize.value })
    poolItems.value = res.items || []
    poolTotal.value = res.total || 0
  } catch (e) {
    console.error('[TransactionPool] 加载失败', e)
  }
}

const onPoolPageChange = async (p: number) => {
  page.value = p
  await loadPool()
}

const handleMine = async () => {
  if (!maxTransactions.value || maxTransactions.value <= 0) {
    window.alert('请输入大于 0 的挖矿数量')
    return
  }
  try {
    const res = await apiMineBlock({
      miner_address: '0xTEST_MINER',
      max_transactions: maxTransactions.value
    })
    window.alert(`挖矿成功！区块哈希：${res.block_hash}`)
    await loadPool()
  } catch (e) {
    console.error('挖矿失败', e)
    window.alert('挖矿失败，请检查后台日志')
  }
}

loadPool()
</script>