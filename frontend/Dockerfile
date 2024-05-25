# 使用官方 Node.js 镜像作为基础镜像
FROM node:16

# 设置工作目录
WORKDIR /app

# 复制 package.json 和 package-lock.json
COPY package*.json ./

# 安装依赖
RUN npm install

# 复制应用程序代码
COPY . .

# 构建应用程序
RUN npm run build

# 安装 serve 用于提供静态文件
RUN npm install -g serve

# 暴露应用程序的端口
EXPOSE 80

# 使用 serve 提供构建后的应用程序
CMD ["serve", "-s", "dist", "-l", "80"]
