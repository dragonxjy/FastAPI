// 浏览器只请求自己的 FastAPI 后端。大模型密钥由后端读取，不能放进 VITE_ 变量。
export const apiConfig = {
  baseURL: (import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000').replace(/\/$/, ''),
}
