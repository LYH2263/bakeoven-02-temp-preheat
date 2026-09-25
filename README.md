# BakeOven

烘焙占炉排程：发酵+烘烤半开区间占用炉位，冲突检测与下一可开工窗口。

温度档与预热：产品登记所需温度档；同一座炉上时间重叠的批次必须是同一温度档。炉位登记换档所需的预热分钟——新批次温度档与炉上紧邻的上一档不同时，会在它占炉之前插入一段预热（预热同样占炉，但不算发酵也不算烘烤）；预热与任何已有占炉重叠则拒绝并记为「预热冲突」。炉位页可改预热分钟，产品页可改温度档，甘特图画出预热条，批次页展示本批温度档。

## 启动

```bash
docker compose up --build
```

| 服务 | 地址 |
| --- | --- |
| 前端 | http://localhost:4500 |
| API | http://localhost:9500 |
| API 文档 | http://localhost:9500/docs |
| Postgres | localhost:5446 |

健康检查：`GET http://localhost:9500/api/health`

## 页面

- `/products` — 产品
- `/ovens` — 炉位
- `/batches` — 批次
- `/gantt` — 甘特
- `/conflicts` — 冲突
- `/windows` — 可开工

## 使用说明

1. 查看产品配方时长与炉位。
2. 创建生产批次，系统按半开区间占炉并检测冲突。
3. 甘特查看占用；冲突与可开工窗口辅助排产。

## 开发与测试

```bash
docker compose exec api pytest -q
```
