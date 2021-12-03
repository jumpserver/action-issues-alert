# 查询 issues，并发通知

- 近几天没有处理的 issues
- 长时间没有反馈/处理的 issues

## Inputs
## `hook`
**Required** 发送通知的 企业微信群 web hook 地址

## `type`
**Optional** 检查的类型 recent, inactive, all

## `repo`
**Optional** 检查的仓库地址，默认 当前仓库

## `inactive`
**Optional** 不活跃天数

## `recent`
**Optional** 近一段时间指天数


## Example usage

```yaml
on:
  schedule:
    - cron: "7 17 * * *"

jobs:
  issue-check-inactive:
    runs-on: ubuntu-latest
    steps:
      - name: check-inactive
        uses: jumpserver/action-issues-alert@master
        with:
          repo: jumpserver/jumpserver
          type: recent
          rencent: 3

```
