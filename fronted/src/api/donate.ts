import service from './http'
// 创建捐赠
export const apiCreateDonation = (data: {
  donor_name: string;
  project_id: number;
  amount: number;
  currency?: string;
  message?: string;
}) => service.post('/api/v1/donations', data).then(r => r.data);

// 确认捐赠（入池）
export const apiEnqueueDonation = (id: number) =>
  service.post(`/api/v1/donations/${id}/enqueue`).then(r => r.data);

// 挖矿（打包交易）
export const apiMinePending = () =>
  service.post('/api/v1/blockchain/mine-pending').then(r => r.data);