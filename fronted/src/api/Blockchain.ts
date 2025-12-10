// frontend/src/api/Blockchain.ts
// 区块链相关接口封装，统一从这里调用

import service from './http'
/**
 * 链状态信息，从 /api/v1/blockchain/info 获取
 */
export interface LatestBlockInfo {
  block_number: number
  block_hash: string
  previous_hash: string
  transactions_count: number
  timestamp: string | null
  miner_address: string
}

export interface ChainInfo {
  total_blocks: number          // 区块总数
  height: number                // 当前区块高度
  total_transactions: number    // 链上总交易（捐赠）笔数
  pending_pool_size: number     // 交易池待处理数量
  latest_block: LatestBlockInfo | null
  chain_valid: boolean          // 链是否通过校验
}

/**
 * 区块简要信息，用于列表展示，对应 /api/v1/blockchain/blocks
 */
export interface BlockSummary {
  height: number
  block_hash: string
  prev_hash: string | null
  timestamp: string
  tx_count: number
  total_amount_in_block: number
  project_ids?: string | null
  meta?: string | null
}

/**
 * 区块列表返回结构
 */
export interface BlocksResponse {
  total: number
  offset: number
  limit: number
  items: BlockSummary[]
}

/**
 * 区块内单笔交易信息，对应后端 ChainTransactionInfo
 */
export interface ChainTransactionInfo {
  id: number
  project_id: number
  donor_username: string | null
  amount: number
  remark: string | null
  tx_hash: string
  tx_index: number
  timestamp: string
  external_donate_id: number | null
}

/**
 * 区块详情，对应 /api/v1/blockchain/blocks/{height}
 */
export interface BlockDetail {
  height: number
  block_hash: string
  prev_hash: string | null
  timestamp: string
  tx_count: number
  total_amount_in_block: number
  meta?: string | null
  txs: ChainTransactionInfo[]
}

/**
 * 挖矿结果，对应 /api/v1/blockchain/mine-pending
 */
export interface MinePendingResult {
  message: string
  block_index: number
  block_hash: string
  tx_count: number
}

/**
 * 校验链结果，对应 /api/v1/blockchain/validate
 */
export interface ValidateChainResult {
  valid: boolean
  message: string
}

/**
 * 获取链整体状态：当前高度、总笔数等
 * GET /api/v1/blockchain/info
 */
export const getChainInfo = () =>
  service.get<ChainInfo>('/api/v1/blockchain/info').then(r => r.data)

/**
 * 分页获取区块列表
 * GET /api/v1/blockchain/blocks?offset=&limit=
 */
export const getBlocks = (params: { offset?: number; limit?: number } = {}) =>
  service.get('/api/v1/blockchain/blocks', { params }).then(r => r.data)

/**
 * 获取指定高度的区块详情
 * GET /api/v1/blockchain/blocks/{height}
 */
export const getBlockDetail = (index: number) =>
  service.get(`/api/v1/blockchain/blocks/${index}`).then(r => r.data)

/**
 * 触发一次“打包待处理交易并挖矿”
 * POST /api/v1/blockchain/mine-pending
 */
export const minePendingBlocks = () =>
  service.post('/api/v1/blockchain/mine-pending').then(r => r.data)

/**
 * 校验当前链是否有效
 * POST /api/v1/blockchain/validate
 */
export const validateBlockchain = () =>
  service.post('/api/v1/blockchain/validate').then(r => r.data)