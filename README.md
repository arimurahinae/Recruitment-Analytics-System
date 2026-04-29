liepin-recruit
一个基于Django + Vue 3 + MySQL + Redis + ECharts的招聘数据可视化与岗位检索系统，包含用户认证、岗位查询、岗位详情、数据统计看板和招聘大屏展示等功能。
项目特色
- 用户注册、登录、登出、个人资料管理
- 岗位列表查询，支持关键词、城市、行业、学历、经验、公司规模、薪资区间筛选
- 岗位详情展示，包含公司信息、招聘者信息、岗位标签与描述
- 数据统计看板，支持城市、省份、行业、学历、工作年限、薪资区间等多维分析
- 招聘数据可视化大屏，包含全国地图、趋势图、排行图和分类统计图
- 薪资预测页面预留，当前为前端占位展示
技术栈
- 后端：Django 6、MySQL、Redis、django-redis、django-cors-headers
- 前端：Vue 3、Vue Router、Element Plus、ECharts
- 数据处理：CSV 导入、岗位数据清洗、薪资区间解析
主要接口
- POST /api/auth/register/：用户注册
- POST /api/auth/login/：用户登录
- POST /api/auth/logout/：退出登录
- GET /api/auth/me/：获取当前用户信息
- PUT /api/auth/me/：更新当前用户信息
- GET /api/job/list/：岗位列表
- GET /api/job/detail/<job_id>/：岗位详情
- GET /api/job/dashboard/：统计看板数据
> 需要登录的接口使用 Authorization: Bearer <token> 鉴权。
> 本地运行
>  后端
cd project/django_recruit
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
前端
cd project/frontend
npm install
npm run dev
前端默认运行在 http://localhost:5173，并将 /api 代理到 http://127.0.0.1:8000。
数据导入
项目提供岗位数据抓取与导入脚本：
project/spiderMain/spider.py：抓取岗位数据并生成 CSV
project/spiderMain/import_data.py：将 liepin_jobs.csv 导入数据库
执行导入：
python project/spiderMain/import_data.py
页面说明
/login：登录页
/register：注册页
/workspace：系统首页
/workspace/jobs：岗位列表
/workspace/jobs/:jobId：岗位详情
/workspace/profile：个人资料
/workspace/salary-predict：薪资预测占位页
/bigscreen：招聘数据可视化大屏
