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
  created_at?: string
  wallet_address?: string | null
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