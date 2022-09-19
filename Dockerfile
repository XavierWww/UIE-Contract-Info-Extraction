### 源镜像 ###
FROM harbor.deepwisdomai.com/deepwisdom/dw_ubuntu1804_py37_torch180_x86_64_455.45_cuda111_cudnn850:v1.0

RUN mkdir -p /wow/contract_info
WORKDIR /wow/contract_info

# 将当前repo全部代码放入镜像
COPY . /wow/contract_info/

# 安装相关的依赖
RUN pip3 install -r requirements.txt -i https://mirror.baidu.com/pypi/simple

# 暴露端口
EXPOSE 8080