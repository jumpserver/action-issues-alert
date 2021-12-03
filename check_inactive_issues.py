#!/usr/bin/python

import textwrap
import datetime
import argparse
import os
import time

import requests
from github import Github


parser = argparse.ArgumentParser(description='检查 issues 情况 提醒开发')
parser.add_argument('repo', type=str, help='项目仓库, 如: jumpserver/jumpserver')
parser.add_argument('--hook', type=str, help='企业微信群机器人 web hook 地址')
parser.add_argument('--inactive', type=int, default=30, help='不活跃天数')
parser.add_argument('--recent', type=int, default=2, help='最近天数')
parser.add_argument('--type', type=str, choices=['inactive', 'recent', 'all'])
args = parser.parse_args()

now = datetime.datetime.now()


def get_issues(since=None, **kwargs):
    token = os.environ.get('GITHUB_TOKEN', '')
    _args = []
    if token:
        _args.append(token)
    g = Github(*_args)
    repo = g.get_repo(args.repo)
    kwargs['state'] = 'open'
    if since:
        kwargs['since'] = since
    issues = repo.get_issues(**kwargs)
    t = time.time()
    issues = [i for i in issues if not i.pull_request]
    using = int(time.time() - t)
    print("获取 issues 完成, 用时 {}s".format(using))
    return issues


def format_issues(issues):
    msg = ''
    for issue in issues:
        title = issue.title
        if len(title) > 30:
            title = title[:30] + '...'
        user = issue.assignee.name if issue.assignee else '未知'
        msg += '[#{0.number} {1}]({0.html_url}) @{2}\n'.format(issue, title, user)

    if len(msg) > 2048:
        msg = msg[:2048]
        msg = msg.split('\n')
        msg = '\n'.join(msg[:len(msg) - 1])
    return msg


def send_wechat_msg(msg):
    url = args.hook
    data = {
        "msgtype": 'markdown',
        "markdown": {
            "content": msg
        }
    }
    if args.hook:
        response = requests.post(url, json=data)
        print(response.status_code)
        print(response.content)
    else:
        print("没有 webhook 通知连接，打印看看")
        print(msg)


def send_inactive_issues_alert_msg():
    inactive_day = now - datetime.timedelta(days=args.inactive)
    issues = get_issues()
    issues = [i for i in issues if i.updated_at < inactive_day]
    kwargs = dict(repo=args.repo, days=args.inactive, count=len(issues))

    if len(issues) == 0:
        msg = '### **[{repo}]** {days} 天不活跃 issues 居然是 {count}，太厉害了'.format(**kwargs)
        send_wechat_msg(msg)
        return
    msg = textwrap.dedent("""
    ### **[{repo}]** {days} 天不活跃 issues 有 {count} 个, 赶紧去看看吧
    ---
    """).format(**kwargs)
    msg += format_issues(issues)
    day_str = inactive_day.strftime('%Y-%m-%d')
    url = 'https://github.com/{}/issues?q=is:issue+is:open+updated:<={}'.format(args.repo, day_str)
    msg += '\n[...查看更多]({})'.format(url)
    send_wechat_msg(msg)


def get_recent_unhandled_issues():
    recent_day = now - datetime.timedelta(days=args.recent)
    latest_issues = get_issues(since=recent_day)
    issues = []

    for i in latest_issues:
        if i.comments == 0:
            issues.append(i)
            continue
        comments = list(i.get_comments())
        # 可能删掉了
        if not comments:
            issues.append(i)
            continue
        # issue 用户和最后一次回复 是一个人, 代表需要处理
        if comments[-1].user.id == i.user.id:
            issues.append(i)
    return issues


def send_recent_issue_alert_msg():
    issues = get_recent_unhandled_issues()
    kwargs = dict(recent=args.recent, repo=args.repo, count=len(issues))
    if len(issues) == 0:
        msg = '### **[{repo}]** {recent} 天内未处理 issues 居然是 {count}, 有点厉害啊'.format(**kwargs)
        send_wechat_msg(msg)
        return
    msg = textwrap.dedent("""
    ### **[{repo}]** {recent} 天内未处理 issues 有 {count} 个, 赶紧去看看吧
    _
    """).format(**kwargs)
    msg += format_issues(issues)
    url = 'https://github.com/{}/issues'.format(args.repo)
    msg += '\n[...查看更多]({})'.format(url)
    send_wechat_msg(msg)


def main():
    tp = args.type
    if tp == 'inactive':
        send_inactive_issues_alert_msg()
    elif tp == 'recent':
        send_recent_issue_alert_msg()
    else:
        send_recent_issue_alert_msg()
        send_inactive_issues_alert_msg()


if __name__ == '__main__':
    main()
