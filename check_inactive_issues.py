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
parser.add_argument('--untimely', type=int, default=7, help='不及时天数')
parser.add_argument('--type', type=str, choices=['inactive', 'recent', 'untimely', 'all'])
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
    print("获取 issues 完成, 总数 {}, 用时 {}s".format(len(issues), using))
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


def send_untimely_issues():
    issues_old = get_issues(labels=['状态:待处理']) 
    issues_new = get_issues(labels=['🔔 Pending processing'])
    issues = issues_old + issues_new
    untimely_day = datetime.datetime.now() - datetime.timedelta(days=args.untimely)
    issues = [i for i in issues if i.updated_at < untimely_day]
    kwargs = dict(untimely=args.untimely, repo=args.repo, count=len(issues))
    if len(issues) == 0:
        msg = '### **[{repo}]** 超过 {untimely} 天未处理 issues 居然是 {count}, 有点牛皮了'.format(**kwargs)
        send_wechat_msg(msg)
        return
    msg = textwrap.dedent("""
        ### **[{repo}]** 超过 {untimely} 天未处理 issues 有 {count} 个, 赶紧去关闭一下吧
        _
        """).format(**kwargs)
    msg += format_issues(issues)
    if issues_old:
        url = 'https://github.com/{}/issues?q=is:issue+is:open+label:状态:待处理'.format(args.repo)
        msg += '\n[...查看更多]({})'.format(url)
    if issues_new:
        url_new = 'https://github.com/{}/issues?q=is:issue+is:open+label:"🔔+Pending+processing"'.format(args.repo)
        msg += '\n[...查看更多(New)]({})'.format(url_new)
    send_wechat_msg(msg)


def get_recent_unhandled_issues():
    recent_day = now - datetime.timedelta(days=args.recent)
    latest_issues1 = get_issues(since=recent_day, labels=['状态:待处理'])
    latest_issues2 = get_issues(since=recent_day, labels=['🔔 Pending processing'])
    latest_issues = latest_issues1 + latest_issues2
    return latest_issues


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
    elif tp == 'untimely':
        send_untimely_issues()
    else:
        send_recent_issue_alert_msg()
        send_inactive_issues_alert_msg()


if __name__ == '__main__':
    main()
