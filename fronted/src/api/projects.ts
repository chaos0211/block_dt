import service from './http'

/** 获取项目列表（分页） */
export const apiListProjects = (params: { page?: number; limit?: number }) =>
  service.get('/api/v1/projects', { params }).then(r => r.data)

/** 获取单个项目详情 */
export const apiGetProject = (projectId: number) =>
  service.get(`/api/v1/projects/${projectId}`).then(r => r.data)

/** 创建项目 */
export const apiCreateProject = (data: any) =>
  service.post('/api/v1/projects', data).then(r => r.data)

/** 更新项目 */
export const apiUpdateProject = (projectId: number, data: any) =>
  service.put(`/api/v1/projects/${projectId}`, data).then(r => r.data)

/** 删除项目（逻辑删除） */
export const apiDeleteProject = (projectId: number) =>
  service.delete(`/api/v1/projects/${projectId}`).then(r => r.data)

// 提交项目上链（入池）
export const apiPutProjectOnChain = (projectId: number) =>
  service.put(`/api/v1/projects/${projectId}/on-chain`).then(r => r.data)

/** 状态：进行中项目 */
export const apiListOngoingProjects = (params: { page?: number; limit?: number }) =>
  service.get('/api/v1/projects/status/ongoing', { params }).then(r => r.data)

/** 状态：已结束项目 */
export const apiListFinishedProjects = (params: { page?: number; limit?: number }) =>
  service.get('/api/v1/projects/status/finished', { params }).then(r => r.data)

/** 状态：审核中项目 */
export const apiListPendingProjects = (params: { page?: number; limit?: number }) =>
  service.get('/api/v1/projects/status/pending', { params }).then(r => r.data)

/** 审核通过 */
export const apiApproveProject = (
  projectId: number,
  data: { approved: boolean; comment?: string; approved_at?: string }
) =>
  service.put(`/api/v1/projects/${projectId}/approve`, data).then(r => r.data)

/** 审核拒绝 */
export const apiRejectProject = (
  projectId: number,
  data: { comment?: string; approved_at?: string }
) =>
  service.put(`/api/v1/projects/${projectId}/reject`, data).then(r => r.data)

/** 用户公开项目详情 */
export const apiGetPublicProject = (projectId: number) =>
  service.get(`/api/v1/projects/${projectId}/public`).then(r => r.data)

/** 查询项目链上交易记录 */
export const apiGetProjectChainTx = (projectId: number) =>
  service.get(`/api/v1/projects/${projectId}/chain-tx`).then(r => r.data)