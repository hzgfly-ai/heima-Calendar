# heima-Calendar

黑马课表日历订阅源。由 AI 根据截图自动维护 `ke.ics`。

## 订阅方式

Mac 日历 → 文件 → 新建日历订阅 → 填：

```
https://hzgfly-ai.github.io/heima-Calendar/ke.ics
```

## 更新流程

1. 把新的课表截图发给 AI
2. AI 提取数据 → 跑 `python3 generate.py` → push 到 main 分支
3. GitHub Pages 自动更新，订阅端无需任何操作

## 文件

- `generate.py` — 根据 `data/schedule.json` 生成 `ke.ics`
- `data/schedule.json` — 课程数据（AI 维护，不要手动改）
- `ke.ics` — 生成的日历文件（自动生成，不要手动改）