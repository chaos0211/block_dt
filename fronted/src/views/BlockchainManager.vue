<template>
  <div class="space-y-6">
    <!-- 顶部标题 + 操作按钮 -->
    <div
      class="flex flex-col md:flex-row md:items-center md:justify-between space-y-4 md:space-y-0"
    >
      <div>
        <h2 class="text-[clamp(1.5rem,3vw,2rem)] font-bold text-gray-800">
          区块链管理
        </h2>
        <p class="text-gray-500 mt-1">
          监控爱心捐赠系统的链上运行状态，查看区块、节点与链配置信息
        </p>
      </div>
      <div class="flex space-x-3">
        <button
          class="bg-white border border-gray-200 hover:bg-gray-50 text-gray-700 px-4 py-2 rounded-lg flex items-center shadow-sm hover:shadow transition-all duration-300 text-sm"
          @click="loadChainInfo"
        >
          <i class="fas fa-sync-alt mr-2" />
          <span>刷新状态</span>
        </button>
        <button
          class="bg-primary hover:bg-primary/90 text-white px-4 py-2 rounded-lg flex items-center shadow-sm hover:shadow transition-all duration-300 text-sm"
          @click="handleSyncChain"
        >
          <i class="fas fa-bolt mr-2" />
          <span>同步区块</span>
        </button>
      </div>
    </div>

    <!-- 区块链统计卡片 -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <StatsCards
        :value="chainStats.height"
        trend-text=""
        :trend-up="true"
        icon="fas fa-layer-group"
        icon-bg="bg-primary-light text-primary"
      >
        <template #title>当前区块高度</template>
      </StatsCards>

      <StatsCards
        :value="chainStats.txCount"
        trend-text=""
        :trend-up="true"
        icon="fas fa-receipt"
        icon-bg="bg-secondary-light text-secondary"
      >
        <template #title>链上捐赠笔数</template>
      </StatsCards>

      <StatsCards
        :value="chainStats.nodeOnline"
        trend-text=""
        :trend-up="true"
        icon="fas fa-server"
        icon-bg="bg-success-light text-success"
      >
        <template #title>在线节点数</template>
      </StatsCards>

      <StatsCards
        :value="chainStats.syncStatus"
        trend-text=""
        :trend-up="true"
        icon="fas fa-heartbeat"
        icon-bg="bg-info-light text-info"
      >
        <template #title>同步状态</template>
      </StatsCards>
    </div>

    <!-- 主体：左侧项目列表 + 右侧链详情 -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- 左侧：已上链项目列表（管理员视角） -->
      <div class="lg:col-span-2 space-y-4">
        <div class="flex items-center justify-between">
          <h3 class="font-semibold text-gray-800">项目链上记录</h3>
          <span class="text-xs text-gray-400">
            仅展示已上链 / 待上链的公益项目
          </span>
        </div>

        <ProjectList
          :projects="projects"
          :total="totalProjects"
          :page="page"
          :page-size="pageSize"
          user-role="admin"
          @change-page="handlePageChange"
        />
      </div>

      <!-- 右侧：区块详情 + 节点状态 + 链配置 -->
      <div class="lg:col-span-1 space-y-4">
        <!-- 区块详情 -->
        <div class="bg-white rounded-xl shadow-card p-4 md:p-5">
          <div class="flex items-center justify-between mb-3">
            <h3 class="font-semibold text-gray-800">区块详情</h3>
            <span class="text-xs text-gray-400">
              当前展示为整体链状态
            </span>
          </div>

          <div class="space-y-2 text-sm text-gray-700">
            <div class="flex justify-between">
              <span class="text-gray-500">最新区块高度</span>
              <span class="font-medium">
                {{ chainStats.height || 0 }}
              </span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-500">最近出块时间</span>
              <span class="font-medium">
                {{
                  latestBlock && latestBlock.timestamp
                    ? latestBlock.timestamp.replace('T', ' ').slice(0, 19)
                    : '暂无数据'
                }}
              </span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-500">最近区块哈希</span>
              <span class="font-mono text-xs text-gray-600 truncate max-w-[160px]">
                {{
                  latestBlock && latestBlock.block_hash
                    ? `${latestBlock.block_hash.slice(0, 10)}...${latestBlock.block_hash.slice(-6)}`
                    : '无'
                }}
              </span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-500">当前交易池大小</span>
              <span class="font-medium">
                {{ pendingPoolSize || 0 }}
              </span>
            </div>
          </div>
        </div>


        <!-- 链配置信息 -->
        <div class="bg-white rounded-xl shadow-card p-4 md:p-5">
          <div class="flex items-center justify-between mb-3">
            <h3 class="font-semibold text-gray-800">链配置信息</h3>
          </div>

          <div class="space-y-2 text-sm text-gray-700">
            <div class="flex justify-between">
              <span class="text-gray-500">网络类型</span>
              <span class="font-medium">
                私有链
              </span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-500">共识机制</span>
              <span class="font-medium">
                PoW
              </span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-500">数据持久化策略</span>
              <span class="font-medium">
                区块 + MySQL 双存储
              </span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-500">区块生成间隔</span>
              <span class="font-medium">
                15 分钟
              </span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-500">当前网络 ID</span>
              <span class="font-mono text-xs text-gray-700">
                donation-chain-local-1
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import StatsCards from '@/components/charts/StatsCards.vue'
import ProjectList from '@/components/charts/ProjectList.vue'
import { getChainInfo, minePendingBlocks } from '@/api/Blockchain'
import { apiListProjects } from '@/api/projects'

// 已上链 / 待上链项目列表
const projects = ref<any[]>([])
const totalProjects = ref(0)

const latestBlock = ref<any | null>(null)
const pendingPoolSize = ref(0)


// 分页（这里只做简单前端分页控制，实际数据由后端返回）
const page = ref(1)
const pageSize = ref(5)

const loadProjectRecords = async () => {
  try {
    const data = await apiListProjects({
      page: page.value,
      limit: pageSize.value,
      // 仅展示已上链 / 待上链项目，如果后端支持 status 过滤，可根据需要调整
      // 这里优先展示已上链项目
      status: 'on_chain'
    })

    // 兼容不同返回结构：优先 projects，其次 items，最后直接使用 data 作为数组
    const list =
      (data && (data.projects || data.items)) ||
      (Array.isArray(data) ? data : [])

    projects.value = list
    // 如果后端返回 total，使用它；否则退化为当前列表长度
    totalProjects.value = (data && (data.total as number)) || list.length
  } catch (e) {
    console.error('[BlockchainManager] loadProjectRecords error', e)
    projects.value = []
    totalProjects.value = 0
  }
}

const handlePageChange = (newPage: number) => {
  page.value = newPage
  // 翻页时重新拉取已上链项目
  loadProjectRecords()
}

// 区块链整体统计信息（从后端 /api/v1/chain/info 获取）
const chainStats = ref({
  height: 0, // 当前区块高度
  txCount: 0, // 链上捐赠交易笔数
  nodeOnline: 0, // 在线节点数
  syncStatus: '未同步' // 同步状态展示字符串
})

const loadingChain = ref(false)
const chainError = ref('')

const loadChainInfo = async () => {
  loadingChain.value = true
  chainError.value = ''
  try {
    const data = await getChainInfo()

    // 当前区块高度：总区块数 - 1（index 从 0 开始，创世块 index=0）
    const totalBlocks = (data.total_blocks as number | undefined) ?? 0
    chainStats.value.height = totalBlocks > 0 ? totalBlocks - 1 : 0

    // 链上捐赠笔数：后端统计的 total_transactions
    chainStats.value.txCount = (data.total_transactions as number | undefined) ?? 0

    // 当前是本地私有链，默认只有一个节点
    chainStats.value.nodeOnline = 1

    // 同步状态：根据链校验结果给出简单文案
    chainStats.value.syncStatus = (data as any).chain_valid ? '运行正常' : '链异常'

    // 记录最新区块与交易池大小
    latestBlock.value = (data as any).latest_block || null
    pendingPoolSize.value = (data as any).pending_pool_size ?? 0
  } catch (e) {
    console.error('[BlockchainManager] loadChainInfo error', e)
    chainError.value = '区块链状态获取失败'
    chainStats.value.syncStatus = '获取失败'
  } finally {
    loadingChain.value = false
  }
}

// 同步区块：当前简单调用挖矿接口，完成后刷新链信息
const handleSyncChain = async () => {
  try {
    await minePendingBlocks()
  } catch (e) {
    // 没有待打包交易等错误在这里打印即可
    console.warn('[BlockchainManager] minePendingBlocks error', e)
  } finally {
    await loadChainInfo()
  }
}

onMounted(() => {
  loadChainInfo()
  loadProjectRecords()
})
</script>