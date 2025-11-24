<template>
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
      <th class="px-6 py-4 text-sm font-semibold text-gray-700 text-right">
        操作
      </th>
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
      <td class="px-6 py-4 text-right text-sm">
        <button
          class="text-primary hover:text-primary/80"
          @click="handleOnChain(tx)"
        >
          上链
        </button>
      </td>
    </template>
  </ProjectList>
  <div
    v-if="showMineDialog"
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/30"
  >
    <div class="bg-white rounded-xl shadow-lg w-full max-w-sm p-6">
      <h3 class="text-base font-semibold text-gray-800 mb-3">确认挖矿</h3>
      <p class="text-sm text-gray-600 mb-6">
        将对选中的交易执行挖矿操作，生成新区块。
      </p>
      <div class="flex justify-end gap-3">
        <button
          class="px-4 py-2 rounded-lg border border-gray-200 text-gray-600 hover:bg-gray-50 text-sm"
          @click="closeMineDialog"
        >
          关闭
        </button>
        <button
          class="px-4 py-2 rounded-lg bg-primary text-white hover:bg-primary/90 text-sm"
          @click="handleMineConfirm"
        >
          挖矿
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import ProjectList from '@/components/charts/ProjectList.vue'
import { apiPutProjectOnChain } from '@/api/TransactionPool'
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

const showMineDialog = ref(false)
const currentTx = ref<PoolItem | null>(null)

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

const handleOnChain = (tx: PoolItem) => {
  currentTx.value = tx
  showMineDialog.value = true
}

const closeMineDialog = () => {
  showMineDialog.value = false
  currentTx.value = null
}

const handleMineConfirm = async () => {
  if (!currentTx.value) return;
  try {
    const res = await apiMineBlock({
      miner_address: '0xTEST_MINER',
      max_transactions: 20
    });
    window.alert(`挖矿成功！区块哈希：${res.block_hash}`);
    await loadPool();
  } catch (e) {
    console.error('挖矿失败', e);
    window.alert('挖矿失败，请检查后台日志');
  }
  closeMineDialog();
}

loadPool()
</script>