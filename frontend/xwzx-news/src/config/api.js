/**
 * API配置文件
 * 包含API基础URL和AI问答功能所需的API参数
 */

// API基础URL配置
export const apiConfig = {
  // 后端API基础URL
  baseURL: 'http://127.0.0.1:8000',
}

export const aiChatConfig = {
  // OpenAI API地址
  apiEndpoint: 'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions',

  // 本地开发从 .env.local 读取；不要把真实密钥写入源码或提交到 Git
  apiKey: import.meta.env.VITE_AI_CHAT_API_KEY || '',

  // 使用的模型
  model: 'qwen3-max-preview'
}
