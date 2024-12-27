module.exports = {
  devServer: {
    port: 80,
    allowedHosts: ['dowdah.com', 'localhost', '127.0.0.1', 'www.dowdah.com'],
    hot: true, // 启用 HMR
    client: {
      webSocketURL: 'ws://localhost:80/ws', // 配置 WebSocket URL
    },
  },
};