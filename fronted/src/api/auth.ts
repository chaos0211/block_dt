import service from './http'

export interface LoginPayload {
  username: string
  password: string
}

export interface RegisterPayload {
  username: string
  email: string
  password: string
  is_admin?: boolean
}

export interface UserItem {
  id: number
  username: string
  email: string | null
  is_admin: boolean
  is_active?: boolean
  wallet_address?: string | null
  balance?: string | number | null
  created_at?: string | null
  updated_at?: string | null
}
export interface MeUpdatePayload {
  username?: string
  email?: string
  password?: string
}

export interface UserListResponse {
  data: UserItem[]
  total?: number
}

// 登录
export const apiLogin = (payload: LoginPayload) =>
  service.post('/api/v1/auth/login', payload).then(r => r.data)

// 注册
export const apiRegister = (payload: RegisterPayload) =>
  service.post('/api/v1/auth/register', payload).then(r => r.data)

// 获取当前登录用户信息（个人中心）
export const apiGetMe = () => service.get<UserItem>('/api/v1/auth/me').then(r => r.data)

// 更新当前登录用户信息（个人中心：username/email/password）
export const apiUpdateMe = (payload: MeUpdatePayload) =>
  service.put<UserItem>('/api/v1/auth/me', payload).then(r => r.data)

// 获取用户列表（分页）
export const apiListUsers = (params: { page?: number; limit?: number }) =>
  service
    .get<UserItem[]>('/api/v1/auth/users', { params })
    .then(r => r.data)

// 获取单个用户详情
export const apiGetUser = (userId: number) =>
  service.get<UserItem>(`/api/v1/auth/users/${userId}`).then(r => r.data)

// 更新用户
export const apiUpdateUser = (
  userId: number,
  payload: Partial<RegisterPayload> & { is_admin?: boolean }
) =>
  service
    .put<UserItem>(`/api/v1/auth/users/${userId}`, payload)
    .then(r => r.data)

// 删除用户
export const apiDeleteUser = (userId: number) =>
  service.delete<void>(`/api/v1/auth/users/${userId}`).then(r => r.data)