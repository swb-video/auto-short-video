#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
热点自动抓取机器人
每日自动抓取抖音、微博、知乎等平台热点，筛选匹配关键词后存入飞书表格
"""

import requests
import json
import os
import re
from datetime import datetime
from urllib.parse import quote
import time

# ============ 配置区域 ============
# 关键词配置 - 修改为您业务相关的关键词
KEYWORDS = [
    'AI工具', '人工智能', 'ChatGPT', '效率提升', '副业赚钱',
    '职场技能', '自媒体', '短视频', '创业', '搞钱'
]

# 飞书配置 - 需要替换为您的实际配置
FEISHU_APP_TOKEN = os.getenv('FEISHU_APP_TOKEN', '')
FEISHU_TABLE_ID = os.getenv('FEISHU_TABLE_ID', '')
FEISHU_APP_ID = os.getenv('FEISHU_APP_ID', '')
FEISHU_APP_SECRET = os.getenv('FEISHU_APP_SECRET', '')

# 钉钉/飞书机器人Webhook - 用于通知
WEBHOOK_URL = os.getenv('WEBHOOK_URL', '')


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
    
    def add_records(self, app_token, table_id, records):
        """批量添加记录"""
        url = f'https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_create'
        headers = {
            'Authorization': f'Bearer {self.tenant_access_token}',
            'Content-Type': 'application/json'
        }
        
        # 构造记录格式
        formatted_records = []
        for record in records:
            formatted_records.append({
                'fields': {
                    '标题': record.get('title', ''),
                    '热度值': record.get('hot_value', 0),
                    '来源平台': record.get('source', ''),
                    '链接': record.get('url', ''),
                    '匹配关键词': ', '.join(record.get('matched_keywords', [])),
                    '匹配分数': record.get('match_score', 0),
                    '抓取时间': record.get('crawl_time', ''),
                    '处理状态': '待审核'
                }
            })
        
        data = {'records': formatted_records}
        
        try:
            response = requests.post(url, headers=headers, json=data)
            result = response.json()
            if result.get('code') == 0:
                return True, result
            else:
                return False, result
        except Exception as e:
            return False, str(e)


class HotSpotCrawler:
    """热点爬虫主类"""
    
    def __init__(self):
        self.keywords = KEYWORDS
        self.feishu = None
        if FEISHU_APP_ID and FEISHU_APP_SECRET:
            self.feishu = FeishuAPI(FEISHU_APP_ID, FEISHU_APP_SECRET)
        
        # 请求头
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }
    
    def fetch_douyin_hot(self):
        """抓取抖音热榜"""
        print("正在抓取抖音热榜...")
        hotspots = []
        
        try:
            # 抖音热榜API
            url = 'https://www.iesdouyin.com/web/api/v2/hotsearch/billboard/'
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                billboard_list = data.get('billboard_list', [])
                
                for i, item in enumerate(billboard_list[:50]):  # 取前50
                    title = item.get('title', '')
                    hot_value = item.get('hot_value', 0)
                    
                    hotspots.append({
                        'title': title,
                        'hot_value': hot_value,
                        'source': '抖音',
                        'url': f'https://www.douyin.com/search/{quote(title)}',
                        'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'rank': i + 1
                    })
                
                print(f"✅ 抖音热榜抓取成功: {len(hotspots)} 条")
            else:
                print(f"❌ 抖音热榜抓取失败: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ 抖音热榜抓取异常: {e}")
        
        return hotspots
    
    def fetch_weibo_hot(self):
        """抓取微博热搜"""
        print("正在抓取微博热搜...")
        hotspots = []
        
        try:
            url = 'https://weibo.com/ajax/side/hotSearch'
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                realtime_list = data.get('data', {}).get('realtime', [])
                
                for i, item in enumerate(realtime_list[:50]):
                    title = item.get('word', '')
                    hot_value = item.get('raw_hot', 0)
                    
                    hotspots.append({
                        'title': title,
                        'hot_value': hot_value,
                        'source': '微博',
                        'url': f'https://s.weibo.com/weibo?q={quote(title)}',
                        'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'rank': i + 1
                    })
                
                print(f"✅ 微博热搜抓取成功: {len(hotspots)} 条")
            else:
                print(f"❌ 微博热搜抓取失败: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ 微博热搜抓取异常: {e}")
        
        return hotspots
    
    def fetch_zhihu_hot(self):
        """抓取知乎热榜"""
        print("正在抓取知乎热榜...")
        hotspots = []
        
        try:
            url = 'https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total'
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                hot_list = data.get('data', [])
                
                for i, item in enumerate(hot_list[:50]):
                    target = item.get('target', {})
                    title = target.get('title', '')
                    hot_value = item.get('detail_text', '').replace('万', '0000').replace('热度', '')
                    
                    try:
                        hot_value = int(float(hot_value))
                    except:
                        hot_value = 0
                    
                    hotspots.append({
                        'title': title,
                        'hot_value': hot_value,
                        'source': '知乎',
                        'url': target.get('url', ''),
                        'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'rank': i + 1
                    })
                
                print(f"✅ 知乎热榜抓取成功: {len(hotspots)} 条")
            else:
                print(f"❌ 知乎热榜抓取失败: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ 知乎热榜抓取异常: {e}")
        
        return hotspots
    
    def filter_by_keywords(self, hotspots):
        """根据关键词筛选热点"""
        print(f"正在根据关键词筛选...关键词: {self.keywords}")
        matched = []
        
        for hot in hotspots:
            title = hot.get('title', '')
            matched_keywords = []
            
            for keyword in self.keywords:
                if keyword in title:
                    matched_keywords.append(keyword)
            
            if matched_keywords:
                hot['matched_keywords'] = matched_keywords
                hot['match_score'] = len(matched_keywords)
                matched.append(hot)
        
        # 按匹配分数和热度值排序
        matched.sort(key=lambda x: (x.get('match_score', 0), x.get('hot_value', 0)), reverse=True)
        
        print(f"✅ 筛选完成: 从 {len(hotspots)} 条中匹配到 {len(matched)} 条")
        return matched
    
    def save_to_feishu(self, hotspots):
        """保存到飞书表格"""
        if not self.feishu or not FEISHU_APP_TOKEN or not FEISHU_TABLE_ID:
            print("⚠️ 飞书配置不完整，跳过保存到飞书")
            # 保存到本地JSON作为备份
            self._save_to_local(hotspots)
            return False
        
        print(f"正在保存到飞书表格...")
        
        try:
            success, result = self.feishu.add_records(
                FEISHU_APP_TOKEN,
                FEISHU_TABLE_ID,
                hotspots
            )
            
            if success:
                print(f"✅ 成功保存 {len(hotspots)} 条记录到飞书")
                return True
            else:
                print(f"❌ 保存到飞书失败: {result}")
                self._save_to_local(hotspots)
                return False
                
        except Exception as e:
            print(f"❌ 保存到飞书异常: {e}")
            self._save_to_local(hotspots)
            return False
    
    def _save_to_local(self, hotspots):
        """保存到本地JSON文件"""
        filename = f"data/hotspots_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(hotspots, f, ensure_ascii=False, indent=2)
            print(f"💾 已保存到本地文件: {filename}")
        except Exception as e:
            print(f"❌ 保存到本地失败: {e}")
    
    def send_notification(self, hotspots):
        """发送通知"""
        if not WEBHOOK_URL:
            return
        
        message = f"""## 🔥 热点抓取完成

**抓取时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**匹配热点数**: {len(hotspots)} 条

### TOP 5 热点
"""
        for i, hot in enumerate(hotspots[:5], 1):
            message += f"{i}. **{hot['title']}** ({hot['source']})\n"
        
        try:
            requests.post(WEBHOOK_URL, json={
                'msg_type': 'interactive',
                'card': {
                    'header': {
                        'title': {'tag': 'plain_text', 'content': '🔥 热点抓取完成'},
                        'template': 'blue'
                    },
                    'elements': [{'tag': 'div', 'text': {'tag': 'lark_md', 'content': message}}]
                }
            })
        except Exception as e:
            print(f"发送通知失败: {e}")
    
    def run(self):
        """运行完整流程"""
        print(f"\n{'='*50}")
        print(f"🚀 热点抓取机器人启动")
        print(f"⏰ 当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*50}\n")
        
        # 1. 抓取各平台热点
        all_hotspots = []
        
        all_hotspots.extend(self.fetch_douyin_hot())
        time.sleep(1)
        
        all_hotspots.extend(self.fetch_weibo_hot())
        time.sleep(1)
        
        all_hotspots.extend(self.fetch_zhihu_hot())
        
        print(f"\n📊 总计抓取: {len(all_hotspots)} 条热点")
        
        # 2. 关键词筛选
        matched_hotspots = self.filter_by_keywords(all_hotspots)
        
        # 3. 保存结果
        if matched_hotspots:
            self.save_to_feishu(matched_hotspots)
            self.send_notification(matched_hotspots)
        else:
            print("⚠️ 没有匹配的热点，跳过保存")
        
        print(f"\n{'='*50}")
        print(f"✅ 热点抓取完成")
        print(f"{'='*50}\n")
        
        return matched_hotspots


if __name__ == '__main__':
    crawler = HotSpotCrawler()
    crawler.run()
