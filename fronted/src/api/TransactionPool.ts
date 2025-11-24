import service from './http'

// 获取交易池
export const apiListPool = (params: { page?: number; limit?: number }) =>
  service.get('/api/v1/blockchain/transaction-pool/list', { params }).then(r => r.data)

// 提交流程（保留原来的）
export const apiPutProjectOnChain = (projectId: number) =>
  service.put(`/api/v1/projects/${projectId}/on-chain`).then(r => r.data)

// 挖矿接口
export const apiMineBlock = (params: { miner_address: string; max_transactions?: number }) =>
  service.post('/api/v1/blockchain/mine', null, { params }).then(r => r.data)