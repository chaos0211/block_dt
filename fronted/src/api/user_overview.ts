import service from './http'

// 普通用户：公益项目概览使用（直接拉 projects 列表，前端筛 ON_CHAIN）
export const apiListProjectsForUser = (params: { page?: number; limit?: number }) =>
  service.get('/api/v1/projects/', { params }).then(r => r.data)

// 当前登录用户信息（用于余额/用户名）
// 你的后端如果是 /api/v1/auth/me 或 /api/v1/users/me，二选一改一下即可
export const apiGetMe = () =>
  service.get('/api/v1/auth/me').then(r => r.data)

// 创建捐赠（后端从 token 拿 donor_id，不需要前端传 donor_id）
export const apiCreateDonationForUser = (payload: {
  project_id: number
  amount: number
  is_anonymous: boolean
}) => service.post('/api/v1/donations/', payload).then(r => r.data)