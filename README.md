# 前端启动
cd fronted

npm run dev


# 后端运行
cd backend
uvicorn app.main:app --reload --port 8000




# spark 配置路径
/opt/homebrew/Cellar/apache-spark/4.0.0/libexec/conf/spark-defaults.conf



# 各个组件说明
CategoryPie.vue 分布饼图
TrendChart.vue 趋势图
DonationTrendSimple.vue 捐赠趋势简易图
StatsCards.vue  小卡片组件
ProjectList.vue  列表组件




# 可执行命令流程
1. 注册
curl -X POST "http://127.0.0.1:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "user1",
    "email": "user1@example.com",
    "password": "123456"
  }'
2. 登录
curl -X POST "http://127.0.0.1:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "user1",
    "password": "123456"
  }'
3. 创建项目
curl -X POST "http://127.0.0.1:8000/api/v1/projects/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyIiwiZXhwIjoxNzYzOTcwNTAxfQ.fup1u0VdW1vX1JLW6PVNspUhpDTulTefopoFl9Ng-SA" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "暖心午餐计划",
    "description": "帮助山区学生解决午餐问题",
    "target_amount": 1000000
  }'
4. 审核
curl -X PUT "http://127.0.0.1:8000/api/v1/projects/2/approve" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyIiwiZXhwIjoxNzYzOTcwNTAxfQ.fup1u0VdW1vX1JLW6PVNspUhpDTulTefopoFl9Ng-SA" \
  -H "Content-Type: application/json" \
  -d '{
    "approved": true,
    "comment": "审核通过，允许上线",
  }'
5. 入池
curl -X PUT "http://127.0.0.1:8000/api/v1/projects/2/on-chain" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyIiwiZXhwIjoxNzYzOTcwNTAxfQ.fup1u0VdW1vX1JLW6PVNspUhpDTulTefopoFl9Ng-SA"
6. 挖矿-上链

curl -X POST "http://127.0.0.1:8000/api/v1/blockchain/mine?miner_address=0xTEST_MINER&max_transactions=20" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyIiwiZXhwIjoxNzYzOTcwNTAxfQ.fup1u0VdW1vX1JLW6PVNspUhpDTulTefopoFl9Ng-SA"
