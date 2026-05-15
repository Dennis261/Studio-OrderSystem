# Studio Order System

轻量化网页工单协作系统 MVP，基于 Django 模板实现。

## 功能

- 姓名选择 + 口令进入系统
- 仅管理员创建工单，其他成员可查看和跟帖
- 工单列表、详情、手动状态标签和归档显示
- 客户信息字段 + 图片要求模板版本化，创建时锁定快照
- 跟帖、附件上传、`@成员` 生成待办
- 待办未读、已读、已完成状态
- 管理员维护成员、图片模板、工单状态标签

## 本地运行

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python manage.py migrate
.venv/bin/python manage.py seed_demo
.venv/bin/python manage.py runserver 127.0.0.1:8000
```

开发期如果要直接清空并重建数据库、迁移文件和 mock 数据：

```bash
scripts/rebuild_dev_db.sh
```

只重新灌入 mock 数据：

```bash
scripts/init_mock_data.sh
```

默认演示成员口令均为 `123456`：

- 管理员
- 客服小王
- 建模小李
- 生产小张

## 测试

```bash
.venv/bin/python manage.py test
```
