#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统配置文件
"""

import os

# ============ 热点抓取配置 ============
HOTSPOT_CONFIG = {
    # 抓取的关键词列表
    'keywords': [
        'AI工具', '人工智能', 'ChatGPT', '效率提升', '副业赚钱',
        '职场技能', '自媒体', '短视频', '创业', '搞钱',
        'AI绘画', 'Midjourney', 'Stable Diffusion', '提示词',
        '办公技巧', 'Excel技巧', 'PPT技巧', '时间管理'
    ],
    
    # 抓取平台配置
    'platforms': {
        'douyin': {
            'enabled': True,
            'url': 'https://www.iesdouyin.com/web/api/v2/hotsearch/billboard/',
            'limit': 50
        },
        'weibo': {
            'enabled': True,
            'url': 'https://weibo.com/ajax/side/hotSearch',
            'limit': 50
        },
        'zhihu': {
            'enabled': True,
            'url': 'https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total',
            'limit': 50
        }
    },
    
    # 匹配规则
    'match_rules': {
        'min_match_score': 1,  # 最少匹配关键词数
        'max_results': 20,      # 最大返回结果数
    }
}

# ============ AI脚本生成配置 ============
SCRIPT_CONFIG = {
    # 每日生成限制
    'daily_limit': 10,
    
    # API配置
    'api': {
        'primary': 'deepseek',  # 主用API
        'backup': 'silicon',    # 备用API
        'timeout': 60,
        'retry_times': 3
    },
    
    # 脚本参数
    'script_params': {
        'min_length': 250,      # 最小字数
        'max_length': 350,      # 最大字数
        'target_duration': 60,  # 目标时长（秒）
    },
    
    # 模板选择规则
    'template_rules': {
        'knowledge': ['教程', '方法', '技巧', '攻略', '指南'],
        'story': ['故事', '经历', '案例', '亲身'],
        'comparison': ['对比', 'vs', '区别', '哪个好'],
        'list': ['盘点', '合集', '清单', '推荐']
    }
}

# ============ 视频制作配置 ============
VIDEO_CONFIG = {
    # 视频参数
    'params': {
        'ratio': '9:16',        # 视频比例
        'resolution': '1080p',  # 分辨率
        'fps': 30,              # 帧率
    },
    
    # 配音配置
    'voice': {
        'default': 'xiaoyan',   # 默认音色
        'options': ['xiaoyan', 'xiaosi', 'xiaoxin']
    },
    
    # 背景音乐
    'bgm': {
        'default': 'light',
        'options': ['light', 'upbeat', 'calm', 'professional']
    }
}

# ============ 发布配置 ============
PUBLISH_CONFIG = {
    # 发布时间（小时:分钟）
    'schedule': [
        '07:30',
        '12:00',
        '18:00',
        '21:00'
    ],
    
    # 平台配置
    'platforms': {
        'douyin': {
            'enabled': True,
            'tags': ['AI工具', '效率神器', '职场干货']
        },
        'kuaishou': {
            'enabled': True,
            'tags': ['AI', '办公技巧', '赚钱']
        },
        'xiaohongshu': {
            'enabled': True,
            'tags': ['AI工具', '效率提升', '打工人必备']
        },
        'shipinhao': {
            'enabled': True,
            'tags': ['人工智能', '科技', '知识分享']
        }
    }
}

# ============ 数据监控配置 ============
MONITOR_CONFIG = {
    # 监控频率
    'frequency': {
        'data_collection': 'daily',    # 数据收集
        'report_generation': 'daily',  # 日报生成
        'health_check': 'hourly'       # 健康检查
    },
    
    # 异常阈值
    'thresholds': {
        'min_daily_scripts': 1,         # 最少日生成脚本数
        'max_pending_topics': 10,       # 最大待处理选题数
        'min_conversion_rate': 0.01,    # 最低转化率
        'max_conversion_rate': 0.20     # 最高转化率（异常高）
    },
    
    # 通知配置
    'notifications': {
        'enabled': True,
        'channels': ['feishu'],         # 通知渠道
        'alert_levels': ['error', 'warning']  # 通知级别
    }
}

# ============ 飞书表格字段配置 ============
FEISHU_FIELDS = {
    'hotspots_table': {
        '标题': 'text',
        '热度值': 'number',
        '来源平台': 'text',
        '链接': 'text',
        '匹配关键词': 'text',
        '匹配分数': 'number',
        '抓取时间': 'datetime',
        '处理状态': 'select',  # 待审核/脚本已生成/已发布/已忽略
    },
    'scripts_table': {
        '选题': 'text',
        '脚本标题': 'text',
        '脚本内容': 'text',
        '视频标题': 'text',
        '标签': 'text',
        '生成时间': 'datetime',
        '制作状态': 'select',  # 待制作/制作中/已完成
        '发布状态': 'select',  # 待发布/已发布
    }
}

# ============ 日志配置 ============
LOG_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file': 'logs/auto_short_video.log',
    'max_size': 10 * 1024 * 1024,  # 10MB
    'backup_count': 5
}
