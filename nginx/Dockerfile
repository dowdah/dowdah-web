# 使用官方 Nginx 镜像作为基础镜像
FROM nginx:latest

# 复制自定义的 Nginx 配置文件到容器中的 Nginx 配置目录
COPY nginx.conf /etc/nginx/nginx.conf

# 如果有其他的 Nginx 配置文件，如 conf.d 或者 site-enabled
# 可以通过以下命令复制到相应的目录中
# COPY conf.d/ /etc/nginx/conf.d/

# 暴露80端口
EXPOSE 80
