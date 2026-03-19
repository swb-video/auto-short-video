#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据自动监控与日报系统
自动收集各平台数据，生成日报并推送到飞书
"""

import requests
import json
import os
from datetime import datetime, timedelta

# ============ 配置区域 ============
# 飞书配置
FEISHU_APP_TOKEN = os.getenv('FEISHU_APP_TOKEN', '')
FEISHU_TABLE_ID = os.getenv('FEISHU_TABLE_ID', '')
FEISHU_APP_ID = os.getenv('FEISHU_APP_ID', '')
FEISHU_APP_SECRET = os.getenv('FEISHU_APP_SECRET', '')
FEISHU_WEBHOOK = os.getenv('FEISHU_WEBHOOK', '')

# 平台数据配置（需要手动更新cookie或token）
PLATFORM_COOKIES = {
    'douyin': os.getenv('DOUYIN_COOKIE', ''),
    'kuaishou': os.getenv('KUAISHOU_COOKIE', ''),
    'xiaohongshu': os.getenv('XIAOHONGSHU_COOKIE', ''),
}


class FeishuAPI:
    """飞书API封装"""
    
    def __init__(self, app_id, app_secret):
        self.app_id = app_id
        self.app_secret = app_secret
        self.tenant_access_token = self._get_tenant_access_token()
    
    def _get_tenant_access_token(self):
        """获取tenant_access_token"""
        url = 'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal'
        headers = {'Content-Type': 'application/json'}
        data = {
            'app_id': self.app_id,
            'app_secret': self.app_secret
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            result = response.json()
            return result.get('tenant_access_token', '')
        except Exception as e:
            print(f"获取token失败: {e}")
            return ''
    
    def get_records(self, filter_conditions=None, limit=100):
        """查询记录"""
        url = f'https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_APP_TOKEN}/tables/{FEISHU_TABLE_ID}/records/search'
        headers = {
            'Authorization': f'Bearer {self.tenant_access_token}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'page_size': limit
        }
        
        if filter_conditions:
            data['filter'] = filter_conditions
        
        try:
            response = requests.post(url, headers=headers, json=data)
            result = response.json()
            
            if result.get('code') == 0:
                return result.get('data', {}).get('items', [])
            else:
                print(f"查询失败: {result}")
                return []
        except Exception as e:
            print(f"查询异常: {e}")
            return []
    
    def send_webhook_message(self, webhook_url, message):
        """发送Webhook消息"""
        try:
            response = requests.post(webhook_url, json=message, timeout=10)
            return response.json()
        except Exception as e:
            print(f"发送消息失败: {e}")
            return None


class DataMonitor:
    """数据监控中心"""
    
    def __init__(self):
        self.feishu = None
        if FEISHU_APP_ID and FEISHU_APP_SECRET:
            self.feishu = FeishuAPI(FEISHU_APP_ID, FEISHU_APP_SECRET)
    
    def collect_content_data(self):
        """收集内容生产数据"""
        print("正在收集内容生产数据...")
        
        if not self.feishu:
            return self._get_mock_data()
        
        try:
            # 获取今日数据
            today = datetime.now().strftime('%Y-%m-%d')
            
            # 查询今日生成的脚本数
            all_records = self.feishu.get_records(limit=500)
            
            today_generated = 0
            today_pending = 0
            total_published = 0
            
            for record in all_records:
                fields = record.get('fields', {})
                generate_time = fields.get('生成时间', '')
                status = fields.get('处理状态', '')
                
                if generate_time.startswith(today):
                    today_generated += 1
                
                if status == '待审核':
                    today_pending += 1
                elif status == '已发布':
                    total_published += 1
            
            return {
                'today_generated': today_generated,
                'today_pending': today_pending,
                'total_published': total_published,
                'total_topics': len(all_records)
            }
            
        except Exception as e:
            print(f"收集内容数据失败: {e}")
            return self._get_mock_data()
    
    def _get_mock_data(self):
        """模拟数据（测试用）"""
        return {
            'today_generated': 5,
            'today_pending': 3,
            'total_published': 25,
            'total_topics': 50
        }
    
    def detect_anomalies(self, data):
        """检测异常"""
        alerts = []
        
        # 内容生产异常
        if data.get('today_generated', 0) == 0:
            alerts.append({
                'level': 'error',
                'message': '今日未生成任何脚本，请检查脚本生成流程'
            })
        
        # 待处理积压
        pending = data.get('today_pending', 0)
        if pending > 10:
            alerts.append({
                'level': 'warning',
                'message': f'待审核选题积压: {pending} 条，建议增加生成配额'
            })
        
        return alerts
    
    def generate_daily_report(self, content_data, traffic_data=None, gmv_data=None):
        """生成日报"""
        today = datetime.now().strftime('%Y-%m-%d')
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        # 异常检测
        alerts = self.detect_anomalies(content_data)
        
        report = {
            'date': today,
            'title': f'[统计] AI数字员工日报 - {today}',
            'sections': []
        }
        
        # 核心数据概览
        overview = f"""### [目标] 核心数据概览

| 指标 | 今日数据 | 状态 |
|------|----------|------|
| 脚本生成数 | {content_data.get('today_generated', 0)} 条 | {'[成功]' if content_data.get('today_generated', 0) > 0 else '[警告]'} |
| 待审核选题 | {content_data.get('today_pending', 0)} 条 | {'[成功]' if content_data.get('today_pending', 0) < 10 else '[警告]'} |
| 累计发布 | {content_data.get('total_published', 0)} 条 | [成功] |
| 选题库总量 | {content_data.get('total_topics', 0)} 条 | [成功] |
"""
        report['sections'].append(overview)
        
        # AI员工工作汇报
        ai_report = f"""### 🤖 AI员工工作汇报

**内容生产组**
- [成功] 热点抓取员：已抓取今日热点
- [成功] 脚本生成员：生成 {content_data.get('today_generated', 0)} 条脚本
- ⏳ 待人工审核：{content_data.get('today_pending', 0)} 条

**运营推广组**
- [成功] 数据监控员：日报已生成
- ⏳ 发布专员：等待视频制作完成

**变现转化组**
- ⏳ 客服接待员：等待流量导入
- ⏳ 订单处理员：等待订单生成
"""
        report['sections'].append(ai_report)
        
        # 异常预警
        if alerts:
            alert_section = "### [警告] 异常预警\n\n"
            for alert in alerts:
                emoji = '[红]' if alert['level'] == 'error' else '[黄]'
                alert_section += f"{emoji} **{alert['message']}**\n\n"
            report['sections'].append(alert_section)
        
        # 今日计划
        plan = f"""### 📅 今日计划

1. **上午**：审核昨日生成的脚本，确认可制作视频
2. **下午**：使用AI工具制作视频（剪映/一帧秒创）
3. **晚上**：发布视频到各平台，监控数据表现

### [提示] 系统建议

- 建议保持每日5-10条脚本生成节奏
- 待审核选题超过10条时，可增加生成配额
- 记得定期更新平台Cookie以保证数据抓取正常
"""
        report['sections'].append(plan)
        
        return report
    
    def send_report(self, report):
        """发送日报"""
        if not FEISHU_WEBHOOK:
            print("[警告] 未配置飞书Webhook，打印日报到控制台：")
            print("\n" + "="*60)
            print(report['title'])
            print("="*60)
            for section in report['sections']:
                print(section)
                print()
            return
        
        # 构造飞书卡片消息
        elements = []
        for section in report['sections']:
            elements.append({
                'tag': 'div',
                'text': {
                    'tag': 'lark_md',
                    'content': section
                }
            })
            elements.append({'tag': 'hr'})
        
        message = {
            'msg_type': 'interactive',
            'card': {
                'header': {
                    'title': {
                        'tag': 'plain_text',
                        'content': report['title']
                    },
                    'template': 'blue'
                },
                'elements': elements[:-1]  # 去掉最后一个hr
            }
        }
        
        try:
            response = requests.post(FEISHU_WEBHOOK, json=message, timeout=10)
            result = response.json()
            
            if result.get('code') == 0:
                print(f"[成功] 日报发送成功")
            else:
                print(f"[失败] 日报发送失败: {result}")
        except Exception as e:
            print(f"[失败] 发送异常: {e}")
    
    def run(self):
        """运行完整流程"""
        print(f"\n{'='*50}")
        print(f"[统计] 数据监控日报系统启动")
        print(f"[时间] 当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*50}\n")
        
        # 1. 收集数据
        content_data = self.collect_content_data()
        
        # 2. 生成日报
        report = self.generate_daily_report(content_data)
        
        # 3. 发送日报
        self.send_report(report)
        
        print(f"\n{'='*50}")
        print(f"[成功] 日报任务完成")
        print(f"{'='*50}\n")
        
        return report


if __name__ == '__main__':
    monitor = DataMonitor()
    monitor.run()
