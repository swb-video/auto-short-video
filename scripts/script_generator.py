#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI脚本批量生成机器人
从飞书表格读取待处理选题，使用DeepSeek API批量生成口播脚本
"""

import requests
import json
import os
import time
from datetime import datetime

# ============ 配置区域 ============
# DeepSeek API配置
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', '')
DEEPSEEK_API_URL = 'https://api.deepseek.com/v1/chat/completions'

# 备用：硅基流动API
SILICON_API_KEY = os.getenv('SILICON_API_KEY', '')
SILICON_API_URL = 'https://api.siliconflow.cn/v1/chat/completions'

# 飞书配置
FEISHU_APP_TOKEN = os.getenv('FEISHU_APP_TOKEN', '')
FEISHU_TABLE_ID = os.getenv('FEISHU_TABLE_ID', '')
FEISHU_APP_ID = os.getenv('FEISHU_APP_ID', '')
FEISHU_APP_SECRET = os.getenv('FEISHU_APP_SECRET', '')

# 生成配置
DAILY_GENERATE_LIMIT = int(os.getenv('DAILY_GENERATE_LIMIT', '10'))  # 每日生成数量限制


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
    
    def get_pending_topics(self, limit=10):
        """获取待处理的选题"""
        url = f'https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_APP_TOKEN}/tables/{FEISHU_TABLE_ID}/records/search'
        headers = {
            'Authorization': f'Bearer {self.tenant_access_token}',
            'Content-Type': 'application/json'
        }
        
        # 查询条件：处理状态为"待审核"
        data = {
            'filter': {
                'conjunction': 'and',
                'conditions': [
                    {
                        'field_name': '处理状态',
                        'operator': 'is',
                        'value': '待审核'
                    }
                ]
            },
            'page_size': limit
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            result = response.json()
            
            if result.get('code') == 0:
                records = result.get('data', {}).get('items', [])
                topics = []
                for record in records:
                    fields = record.get('fields', {})
                    topics.append({
                        'record_id': record.get('record_id'),
                        'title': fields.get('标题', ''),
                        'source': fields.get('来源平台', ''),
                        'hot_value': fields.get('热度值', 0),
                        'keywords': fields.get('匹配关键词', '')
                    })
                return topics
            else:
                print(f"查询飞书失败: {result}")
                return []
        except Exception as e:
            print(f"查询飞书异常: {e}")
            return []
    
    def update_record(self, record_id, fields):
        """更新记录"""
        url = f'https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_APP_TOKEN}/tables/{FEISHU_TABLE_ID}/records/{record_id}'
        headers = {
            'Authorization': f'Bearer {self.tenant_access_token}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'fields': fields
        }
        
        try:
            response = requests.put(url, headers=headers, json=data)
            result = response.json()
            return result.get('code') == 0
        except Exception as e:
            print(f"更新记录失败: {e}")
            return False


class ScriptGenerator:
    """AI脚本生成器"""
    
    def __init__(self):
        self.api_key = DEEPSEEK_API_KEY
        self.api_url = DEEPSEEK_API_URL
        self.feishu = None
        
        if FEISHU_APP_ID and FEISHU_APP_SECRET:
            self.feishu = FeishuAPI(FEISHU_APP_ID, FEISHU_APP_SECRET)
        
        # 提示词模板库
        self.prompt_templates = {
            'default': """你是一个专业的短视频口播脚本撰写专家，擅长创作爆款短视频内容。

请为以下选题撰写一个1分钟的口播视频脚本：

选题：{topic}
相关关键词：{keywords}
来源平台：{source}

目标受众：对AI工具、效率提升感兴趣的职场人士和自媒体创作者
内容风格：干货分享、实用性强、口语化、有网感

脚本要求：
1. 【黄金3秒开头】用悬念/痛点/数字/反常识抓人眼球，必须让人想继续看
2. 【中间干货】2-3个核心要点，每个配简单案例或场景
3. 【结尾引导】自然引导点赞关注，加转化钩子（如"评论区领资料"）
4. 【字数】250-350字，语速适中刚好1分钟
5. 【语言】极度口语化，像朋友聊天，避免书面语和生僻词
6. 【情绪】有起伏，适当使用emoji语气词，增加感染力

请按以下格式输出：

【标题】：（15字以内，吸引眼球的标题）

【开头】：（3秒抓人，30字以内）

【正文】：（干货内容，分点阐述）

【结尾】：（引导转化，20字以内）

【标签】：#标签1 #标签2 #标签3（3-5个相关标签）

【拍摄建议】：（场景、道具、表情等简单建议）
""",
            'knowledge': """你是一个知识付费领域的短视频专家，擅长将专业知识转化为通俗易懂的口播内容。

选题：{topic}
关键词：{keywords}

请创作一个知识分享类口播脚本：
- 用"痛点-解决方案-案例"结构
- 体现专业度但不说教
- 结尾引导购买课程/咨询服务
- 字数300字左右

输出格式同上。
""",
            'story': """你是一个故事型短视频创作者，擅长用故事传递观点。

选题：{topic}
关键词：{keywords}

请创作一个故事型口播脚本：
- 用具体人物和场景开场
- 有冲突、有转折、有收获
- 故事后提炼1个核心观点
- 字数300字左右

输出格式同上。
"""
        }
    
    def select_template(self, topic, keywords):
        """根据选题选择合适的模板"""
        # 简单规则：根据关键词选择模板
        if any(kw in keywords for kw in ['教程', '方法', '技巧', '攻略']):
            return 'knowledge'
        elif any(kw in keywords for kw in ['故事', '经历', '案例']):
            return 'story'
        else:
            return 'default'
    
    def generate_script(self, topic, keywords='', source='', template='default'):
        """生成单条脚本"""
        if not self.api_key:
            print("❌ 未配置DeepSeek API Key")
            return None
        
        prompt_template = self.prompt_templates.get(template, self.prompt_templates['default'])
        prompt = prompt_template.format(topic=topic, keywords=keywords, source=source)
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': 'deepseek-chat',
            'messages': [
                {'role': 'system', 'content': '你是短视频脚本创作专家，只输出脚本内容，不输出解释说明'},
                {'role': 'user', 'content': prompt}
            ],
            'temperature': 0.8,
            'max_tokens': 1000,
            'top_p': 0.9
        }
        
        try:
            print(f"  正在生成脚本: {topic[:20]}...")
            response = requests.post(
                self.api_url,
                headers=headers,
                json=data,
                timeout=60
            )
            
            result = response.json()
            
            if 'choices' in result and len(result['choices']) > 0:
                script_content = result['choices'][0]['message']['content']
                
                # 解析脚本各部分
                parsed = self._parse_script(script_content)
                parsed['raw_content'] = script_content
                parsed['topic'] = topic
                
                return parsed
            else:
                print(f"  API返回异常: {result}")
                return None
                
        except Exception as e:
            print(f"  生成失败: {e}")
            return None
    
    def _parse_script(self, content):
        """解析脚本内容"""
        parsed = {
            'title': '',
            'opening': '',
            'body': '',
            'ending': '',
            'tags': '',
            'shooting_tips': ''
        }
        
        # 简单解析
        lines = content.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if line.startswith('【标题】'):
                parsed['title'] = line.replace('【标题】：', '').replace('【标题】:', '').strip()
            elif line.startswith('【开头】'):
                current_section = 'opening'
            elif line.startswith('【正文】'):
                current_section = 'body'
            elif line.startswith('【结尾】'):
                current_section = 'ending'
            elif line.startswith('【标签】'):
                parsed['tags'] = line.replace('【标签】：', '').replace('【标签】:', '').strip()
            elif line.startswith('【拍摄建议】'):
                current_section = 'tips'
            elif current_section == 'opening' and line and not line.startswith('【'):
                parsed['opening'] += line + '\n'
            elif current_section == 'body' and line and not line.startswith('【'):
                parsed['body'] += line + '\n'
            elif current_section == 'ending' and line and not line.startswith('【'):
                parsed['ending'] += line + '\n'
            elif current_section == 'tips' and line and not line.startswith('【'):
                parsed['shooting_tips'] += line + '\n'
        
        # 清理
        for key in parsed:
            if isinstance(parsed[key], str):
                parsed[key] = parsed[key].strip()
        
        return parsed
    
    def generate_batch(self, limit=DAILY_GENERATE_LIMIT):
        """批量生成脚本"""
        print(f"\n{'='*50}")
        print(f"🚀 AI脚本生成机器人启动")
        print(f"⏰ 当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*50}\n")
        
        # 1. 获取待处理选题
        if not self.feishu:
            print("❌ 飞书配置不完整，无法读取选题")
            return []
        
        pending_topics = self.feishu.get_pending_topics(limit=limit)
        
        if not pending_topics:
            print("⚠️ 没有待处理的选题")
            return []
        
        print(f"📋 获取到 {len(pending_topics)} 个待处理选题\n")
        
        # 2. 批量生成
        results = []
        success_count = 0
        
        for i, topic_info in enumerate(pending_topics, 1):
            print(f"[{i}/{len(pending_topics)}] 处理选题: {topic_info['title'][:30]}...")
            
            # 选择模板
            template = self.select_template(
                topic_info['title'],
                topic_info.get('keywords', '')
            )
            
            # 生成脚本
            script = self.generate_script(
                topic=topic_info['title'],
                keywords=topic_info.get('keywords', ''),
                source=topic_info.get('source', ''),
                template=template
            )
            
            if script:
                # 更新飞书记录
                update_fields = {
                    '处理状态': '脚本已生成',
                    '脚本标题': script.get('title', ''),
                    '脚本内容': script.get('raw_content', ''),
                    '视频标题': script.get('title', ''),
                    '标签': script.get('tags', ''),
                    '生成时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                success = self.feishu.update_record(topic_info['record_id'], update_fields)
                
                if success:
                    print(f"  ✅ 生成成功并已保存")
                    success_count += 1
                else:
                    print(f"  ⚠️ 生成成功但保存失败")
                
                results.append({
                    'topic': topic_info['title'],
                    'script': script,
                    'status': 'success'
                })
            else:
                print(f"  ❌ 生成失败")
                results.append({
                    'topic': topic_info['title'],
                    'status': 'failed'
                })
            
            # API限流保护
            if i < len(pending_topics):
                time.sleep(2)
        
        print(f"\n{'='*50}")
        print(f"✅ 批量生成完成")
        print(f"📊 成功: {success_count}/{len(pending_topics)}")
        print(f"{'='*50}\n")
        
        return results
    
    def generate_from_local(self, topics_file):
        """从本地文件生成（测试用）"""
        try:
            with open(topics_file, 'r', encoding='utf-8') as f:
                topics = json.load(f)
            
            results = []
            for topic_info in topics[:DAILY_GENERATE_LIMIT]:
                script = self.generate_script(
                    topic=topic_info.get('title', ''),
                    keywords=topic_info.get('keywords', ''),
                    source=topic_info.get('source', '')
                )
                
                if script:
                    results.append({
                        'topic': topic_info['title'],
                        'script': script,
                        'status': 'success'
                    })
                    
                    # 保存到本地
                    output_file = f"data/script_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(results)}.json"
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(script, f, ensure_ascii=False, indent=2)
                
                time.sleep(2)
            
            return results
            
        except Exception as e:
            print(f"从本地文件生成失败: {e}")
            return []


if __name__ == '__main__':
    generator = ScriptGenerator()
    
    # 检查是否有本地测试文件
    test_file = 'data/test_topics.json'
    if os.path.exists(test_file):
        print("使用本地测试文件...")
        results = generator.generate_from_local(test_file)
    else:
        # 正常流程：从飞书读取
        results = generator.generate_batch()
    
    print(f"\n完成！共生成 {len([r for r in results if r['status']=='success'])} 条脚本")
