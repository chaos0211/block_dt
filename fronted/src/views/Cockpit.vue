<template>
  <div class="space-y-6">
    <!-- 页面标题 -->


    <!-- 统计卡片区 -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <StatsCards
        :value="totalAmount"
        trend-text="12.5% 较上月"
        :trend-up="true"
        icon="fas fa-wallet"
        icon-bg="bg-primary-light text-primary"
      >
        <template #title>累计捐赠总额</template>
      </StatsCards>

      <StatsCards
        :value="todayAmount"
        trend-text="8.2% 较昨日"
        :trend-up="true"
        icon="fas fa-calendar-day"
        icon-bg="bg-secondary-light text-secondary"
      >
        <template #title>今日捐赠金额</template>
      </StatsCards>

      <StatsCards
        :value="activeProjects"
        trend-text="2 较上周"
        :trend-up="false"
        icon="fas fa-project-diagram"
        icon-bg="bg-warning-light text-warning"
      >
        <template #title>进行中的公益项目</template>
      </StatsCards>

      <StatsCards
        :value="blockHeight"
        trend-text="同步中"
        :trend-up="true"
        icon="fas fa-link"
        icon-bg="bg-info-light text-info"
      >
        <template #title>区块链区块高度</template>
      </StatsCards>
    </div>

    <!-- 图表区 -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- 捐赠金额趋势图 -->
      <div class="bg-white rounded-xl shadow-card p-6">
        <div class="flex items-center justify-between mb-6">
          <h3 class="font-semibold text-gray-800">捐赠金额趋势</h3>
          <div class="flex space-x-2">
            <button class="text-xs px-3 py-1 rounded-full bg-primary text-white">
              周
            </button>
            <button
              class="text-xs px-3 py-1 rounded-full bg-gray-100 text-gray-600 hover:bg-gray-200"
            >
              月
            </button>
            <button
              class="text-xs px-3 py-1 rounded-full bg-gray-100 text-gray-600 hover:bg-gray-200"
            >
              年
            </button>
          </div>
        </div>

        <TrendChart />
      </div>

      <!-- 捐赠分布饼图 -->
      <div class="bg-white rounded-xl shadow-card p-6">
        <div class="flex items-center justify-between mb-6">
          <h3 class="font-semibold text-gray-800">捐赠分布</h3>
          <div class="flex space-x-2">
            <button class="text-xs px-3 py-1 rounded-full bg-primary text-white">
              项目
            </button>
            <button
              class="text-xs px-3 py-1 rounded-full bg-gray-100 text-gray-600 hover:bg-gray-200"
            >
              组织
            </button>
          </div>
        </div>

        <CategoryPie />
      </div>
    </div>

    <!-- 双列表区：最新捐赠记录 & 最新区块 -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- 最新捐赠记录 -->
      <div class="bg-white rounded-xl shadow-card p-6">
        <div class="flex items-center justify-between mb-6">
          <h3 class="font-semibold text-gray-800">最新捐赠记录</h3>

        </div>
        <div class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200">
            <thead>
              <tr>
                <th
                  class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                >
                  时间
                </th>
                <th
                  class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                >
                  项目名称
                </th>
                <th
                  class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                >
                  捐赠人
                </th>
                <th
                  class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                >
                  金额
                </th>
                <th
                  class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                >
                  区块哈希
                </th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-for="item in latestDonations" :key="item.transaction_hash" class="hover:bg-gray-50 transition-colors duration-150">
                <td class="px-4 py-4 whitespace-nowrap text-sm text-gray-500">{{ item.time }}</td>
                <td class="px-4 py-4 whitespace-nowrap text-sm font-medium text-gray-800">{{ item.project_name }}</td>
                <td class="px-4 py-4 whitespace-nowrap text-sm text-gray-600">{{ item.donor }}</td>
                <td class="px-4 py-4 whitespace-nowrap text-sm font-medium text-success">¥{{ item.amount }}</td>
                <td class="px-4 py-4 whitespace-nowrap text-sm text-gray-500">{{ item.block_hash }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- 最新区块 -->
      <div class="bg-white rounded-xl shadow-card p-6">
        <div class="flex items-center justify-between mb-6">
          <h3 class="font-semibold text-gray-800">最新区块</h3>

        </div>
        <div class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200">
            <thead>
              <tr>
                <th
                  class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                >
                  区块高度
                </th>
                <th
                  class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                >
                  时间
                </th>
                <th
                  class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                >
                  哈希
                </th>
                <th
                  class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                >
                  捐赠笔数
                </th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-for="b in latestBlocks" :key="b.block_hash" class="hover:bg-gray-50 transition-colors duration-150">
                <td class="px-4 py-4 whitespace-nowrap text-sm font-medium text-gray-800">{{ b.block_number }}</td>
                <td class="px-4 py-4 whitespace-nowrap text-sm text-gray-500">{{ b.time }}</td>
                <td class="px-4 py-4 whitespace-nowrap text-sm text-gray-600">{{ b.block_hash }}</td>
                <td class="px-4 py-4 whitespace-nowrap text-sm text-gray-600">{{ b.transaction_count }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import TrendChart from '@/components/charts/DonationTrendSimple.vue'
import CategoryPie from '@/components/charts/CategoryPie.vue'
import StatsCards from '@/components/charts/StatsCards.vue'
import { getChainInfo, getBlocks } from '@/api/Blockchain'
import { apiListProjects } from '@/api/projects'
import { apiListRecentDonations } from '@/api/donate'

// 这四个值由后端接口赋值（为空时 StatsCards 组件内部会显示为 0）
const totalAmount = ref<number | null>(null)
const todayAmount = ref<number | null>(null)
const activeProjects = ref<number | null>(null)
const blockHeight = ref<number | null>(null)

const latestDonations = ref<any[]>([])
const latestBlocks = ref<any[]>([])

/**
 * 加载首页仪表盘统计数据：
 * - 区块高度：来自 /api/v1/blockchain/info
 * - 进行中项目数：来自 /api/v1/projects（按状态过滤）
 * - 累计捐赠总额：汇总所有项目 current_amount
 * - 今日捐赠金额：当前版本暂用 0，占位，后续可接入捐赠统计 API
 */
const loadDashboardData = async () => {
  try {
    // 并行请求链信息和项目列表
    const [chainInfo, projectResp] = await Promise.all([
      getChainInfo(),
      apiListProjects({ page: 1, limit: 100 })
    ])

    // 区块高度
    blockHeight.value = (chainInfo as any)?.height ?? 0

    // 解析项目列表返回结构：优先 projects，其次 items，再退化为数组
    const list =
      (projectResp as any)?.projects ??
      (projectResp as any)?.items ??
      (Array.isArray(projectResp) ? projectResp : [])

    // 累计捐赠总额：所有项目 current_amount 之和
    totalAmount.value = list.reduce(
      (sum: number, p: any) => sum + (p.current_amount || 0),
      0
    )

    // 进行中的公益项目：已上链或已审核状态
    activeProjects.value = list.filter(
      (p: any) => p.status === 'on_chain' || p.status === 'approved'
    ).length

    // 今日捐赠金额：当前版本先置为 0，后续再接入捐赠统计 API
    todayAmount.value = 0

  } catch (err) {
    console.error('[Cockpit] loadDashboardData error', err)
    // 出错时保持默认值（0）
    totalAmount.value = totalAmount.value ?? 0
    todayAmount.value = todayAmount.value ?? 0
    activeProjects.value = activeProjects.value ?? 0
    blockHeight.value = blockHeight.value ?? 0
  }
}

const loadLatestDonations = async () => {
  try {
    // 通过封装好的 axios 实例调用后端 8000 端口
    const data: any = await apiListRecentDonations({ page: 1, limit: 5 })

    const list =
      (Array.isArray(data) ? data : null) ||
      data?.donations ||
      data?.items ||
      []

    latestDonations.value = list.map((d: any) => {
      // 时间：优先使用 confirmed_at，否则用 created_at
      const created = d.confirmed_at || d.created_at || ''
      const time = created ? String(created).replace('T', ' ').slice(0, 19) : ''

      // 项目名称：当前接口只返回 project_id，这里用「项目 #ID」占位
      const projectName = `${d.project_name ?? '-'}`

      // 捐赠人：匿名 or "用户 #ID"
      const donorName = d.is_anonymous
        ? '匿名捐赠者'
        : (d.donor_name ?? `用户 #${d.donor_id ?? '-'}`)

      // 区块哈希：如果已上链，则截断展示；否则显示“未上链”
      const blockHashRaw = d.block_hash || d.transaction_hash || ''
      const blockHash = blockHashRaw
        ? `${String(blockHashRaw).slice(0, 10)}...${String(blockHashRaw).slice(-6)}`
        : '未上链'

      return {
        transaction_hash: d.transaction_hash || d.id || `${time}-${projectName}`,
        time,
        project_name: projectName,
        donor: donorName,
        amount: d.amount || 0,
        block_hash: blockHash
      }
    })
  } catch (err) {
    console.error('[Cockpit] loadLatestDonations error', err)
    latestDonations.value = []
  }
}

const loadLatestBlocks = async () => {
  try {
    // 通过 Blockchain.ts 中的封装函数走同一个 axios / baseURL
    const data: any = await getBlocks({ page: 1, limit: 5 })

    const list =
      (Array.isArray(data) ? data : null) ||
      data?.blocks ||
      data?.items ||
      []

    latestBlocks.value = list.map((b: any) => {
      const ts = b.timestamp || b.created_at || ''
      const time = ts ? String(ts).replace('T', ' ').slice(0, 19) : ''

      const hash = b.block_hash || b.hash || ''

      return {
        block_number: b.block_number ?? b.height ?? 0,
        time,
        block_hash: hash
          ? `${String(hash).slice(0, 10)}...${String(hash).slice(-6)}`
          : '未知',
        transaction_count: b.transaction_count ?? b.transactions_count ?? 0
      }
    })
  } catch (err) {
    console.error('[Cockpit] loadLatestBlocks error', err)
    latestBlocks.value = []
  }
}

onMounted(() => {
  loadDashboardData()
  loadLatestDonations()
  loadLatestBlocks()
})
</script>
