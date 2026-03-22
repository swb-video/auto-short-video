#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
支付回调处理服务 - Flask Web服务器
功能：
  1. 接收虎皮椒支付回调通知，更新飞书多维表格订单状态
  2. 接收飞书机器人消息，识别支付意图并发送交互式支付卡片
  3. 处理卡片按钮点击，生成虎皮椒支付链接
"""

import os
import json
import time
import hashlib
import random
import string
import requests
from flask import Flask, request, jsonify
from datetime import datetime
from pathlib import Path

app = Flask(__name__)

# 虎皮椒支付配置
HUPJ_CONFIG = {
    'app_id': '201906177799',
    'app_secret': '11d8cf1343ecaba02946e7c1625d438b',
    'api_url': 'https://api.xunhupay.com/payment/do.html',
    'notify_url': 'https://swb-tools-shop-khlpp0yl9j.edgeone.cool/payment/notify',
    'return_url': 'https://swb-tools-shop-khlpp0yl9j.edgeone.cool/payment/success',
}

# 飞书配置
FEISHU_CONFIG = {
    'app_id': 'cli_a9313d8d55f85cd3',
    'app_secret': 'akfB2o9Bx1ZBjGRLL2Lldcbf3c07PQNK',
    'app_token': 'SyKOwjdrkidJhWki56rcLwKtnVe',
    'table_id': 'tbl7jWfDKbVQswii',
    # 飞书事件订阅验证Token（在飞书开放平台 -> 事件订阅页面获取）
    'verification_token': os.environ.get('FEISHU_VERIFICATION_TOKEN', 'your_verification_token'),
    # 飞书加密Key（可选，若开启消息加密需填写）
    'encrypt_key': os.environ.get('FEISHU_ENCRYPT_KEY', ''),
}

# 商品目录（可根据实际情况修改）
PRODUCT_CATALOG = [
    {'id': 'basic',  'name': 'AI数字员工系统-基础版', 'price': 999,  'desc': '适合个人/小团队，含核心AI员工模块'},
    {'id': 'pro',    'name': 'AI数字员工系统-专业版', 'price': 1999, 'desc': '适合成长型企业，全功能解锁'},
    {'id': 'video',  'name': '短视频运营服务包',      'price': 599,  'desc': '短视频全流程AI自动化'},
]

# 支付意图关键词
PAY_KEYWORDS = ['支付', '购买', '付款', '买', '下单', '要买', '想买', '付', 'pay', 'buy']


def generate_hash(params, app_secret):
    """生成虎皮椒签名"""
    filtered = {k: v for k, v in params.items() if v and k != 'hash'}
    sorted_params = sorted(filtered.items())
    string_a = '&'.join([f"{k}={v}" for k, v in sorted_params])
    string_sign = string_a + app_secret
    return hashlib.md5(string_sign.encode('utf-8')).hexdigest()


def verify_notify(notify_data):
    """验证支付回调签名"""
    if 'hash' not in notify_data:
        return False
    received_hash = notify_data['hash']
    calculated_hash = generate_hash(notify_data, HUPJ_CONFIG['app_secret'])
    return received_hash == calculated_hash


def get_feishu_token():
    """获取飞书access token"""
    url = 'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal'
    headers = {'Content-Type': 'application/json'}
    data = {
        'app_id': FEISHU_CONFIG['app_id'],
        'app_secret': FEISHU_CONFIG['app_secret']
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        result = response.json()
        if result.get('code') == 0:
            return result.get('tenant_access_token')
    except Exception as e:
        print(f"[错误] 获取token失败: {e}")
    return None


def find_order_record(order_id):
    """在飞书表格中查找订单记录"""
    token = get_feishu_token()
    if not token:
        return None
    
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_CONFIG['app_token']}/tables/{FEISHU_CONFIG['table_id']}/records"
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(url, headers=headers, params={'page_size': 500})
        result = response.json()
        if result.get('code') == 0:
            items = result.get('data', {}).get('items', [])
            for item in items:
                fields = item.get('fields', {})
                if fields.get('订单号') == order_id:
                    return item
    except Exception as e:
        print(f"[错误] 查找订单失败: {e}")
    
    return None


def update_order_status(record_id, status, pay_time=None, transaction_id=None):
    """更新订单状态"""
    token = get_feishu_token()
    if not token:
        return False
    
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_CONFIG['app_token']}/tables/{FEISHU_CONFIG['table_id']}/records/{record_id}"
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    fields = {'支付状态': status}
    if pay_time:
        fields['支付时间'] = pay_time
    if transaction_id:
        fields['交易号'] = transaction_id
    
    try:
        response = requests.put(url, headers=headers, json={'fields': fields})
        result = response.json()
        return result.get('code') == 0
    except Exception as e:
        print(f"[错误] 更新订单失败: {e}")
        return False


def log_payment_notify(data):
    """记录支付回调日志"""
    log_file = Path('output/payment_notify_log.json')
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    logs = []
    if log_file.exists():
        with open(log_file, 'r', encoding='utf-8') as f:
            logs = json.load(f)
    
    logs.append({
        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'data': data
    })
    
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)


@app.route('/')
def index():
    """首页"""
    return jsonify({
        'status': 'running',
        'service': 'AI支付回调处理服务',
        'version': '1.0.0',
        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })


@app.route('/payment/notify', methods=['POST'])
def payment_notify():
    """
    接收虎皮椒支付回调通知
    虎皮椒会在用户支付成功后发送POST请求到这个URL
    """
    print("\n" + "=" * 60)
    print("[回调] 收到支付通知")
    print("=" * 60)
    
    # 获取回调数据
    notify_data = request.form.to_dict()
    print(f"[数据] {json.dumps(notify_data, ensure_ascii=False)}")
    
    # 记录日志
    log_payment_notify(notify_data)
    
    # 验证签名
    if not verify_notify(notify_data):
        print("[错误] 签名验证失败")
        return "fail", 400
    
    print("[验证] 签名验证通过")
    
    # 提取订单信息
    order_id = notify_data.get('trade_order_id')
    status = notify_data.get('status')  # OD=已支付, WP=待支付, CD=已取消
    amount = notify_data.get('total_fee')
    pay_time = notify_data.get('paid_time')
    transaction_id = notify_data.get('openid')
    
    print(f"[订单] {order_id}")
    print(f"[状态] {status}")
    print(f"[金额] {amount}")
    
    # 处理支付成功
    if status == 'OD':
        print("[处理] 订单已支付，更新状态...")
        
        # 查找飞书记录
        record = find_order_record(order_id)
        if record:
            record_id = record.get('id')
            if update_order_status(record_id, '已支付', pay_time, transaction_id):
                print("[成功] 订单状态已更新为'已支付'")
                # 发送通知到飞书群（可选）
                # send_feishu_notification(order_id, amount)
            else:
                print("[错误] 更新订单状态失败")
        else:
            print(f"[警告] 未找到订单记录: {order_id}")
    
    # 必须返回"success"，否则虎皮椒会认为通知失败并重复发送
    return "success"


@app.route('/payment/success', methods=['GET'])
def payment_success():
    """
    支付成功跳转页面
    用户支付成功后会被重定向到这个页面
    """
    order_id = request.args.get('trade_order_id')
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>支付成功</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                margin: 0;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            }}
            .container {{
                background: white;
                padding: 40px;
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                text-align: center;
                max-width: 400px;
            }}
            .success-icon {{
                width: 80px;
                height: 80px;
                background: #52c41a;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 0 auto 20px;
            }}
            .success-icon::after {{
                content: "✓";
                color: white;
                font-size: 40px;
            }}
            h1 {{
                color: #333;
                margin: 0 0 10px;
            }}
            p {{
                color: #666;
                margin: 0 0 30px;
            }}
            .order-info {{
                background: #f5f5f5;
                padding: 15px;
                border-radius: 10px;
                margin-bottom: 20px;
            }}
            .order-info p {{
                margin: 5px 0;
                font-size: 14px;
            }}
            .btn {{
                background: #667eea;
                color: white;
                padding: 12px 30px;
                border: none;
                border-radius: 25px;
                font-size: 16px;
                cursor: pointer;
                text-decoration: none;
                display: inline-block;
            }}
            .btn:hover {{
                background: #5568d3;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="success-icon"></div>
            <h1>支付成功!</h1>
            <p>感谢您的购买，我们将尽快为您处理订单</p>
            <div class="order-info">
                <p><strong>订单号:</strong> {order_id}</p>
                <p><strong>支付时间:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            <a href="/" class="btn">返回首页</a>
        </div>
    </body>
    </html>
    """


@app.route('/api/payment/create', methods=['POST'])
def api_create_payment():
    """
    API接口：创建支付订单
    用于前端或其他服务调用
    """
    data = request.json
    order_id = data.get('order_id')
    amount = data.get('amount')
    title = data.get('title')
    
    if not all([order_id, amount, title]):
        return jsonify({'success': False, 'error': '参数不完整'}), 400
    
    # 这里可以调用ai_payment_processor.py中的方法
    # 简化起见，直接返回成功
    return jsonify({
        'success': True,
        'order_id': order_id,
        'message': '订单创建成功（演示）'
    })


# ============================================================
# 飞书机器人工具函数
# ============================================================

def _feishu_token():
    """获取飞书 tenant_access_token（复用已有逻辑）"""
    return get_feishu_token()


def _nonce_str(length=16):
    """生成随机字符串用于订单号"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


def send_feishu_message(receive_id, receive_id_type, content_type, content):
    """
    发送飞书消息
    receive_id_type: open_id / user_id / chat_id
    content_type: text / interactive
    content: str（JSON 字符串）
    """
    token = _feishu_token()
    if not token:
        print("[错误] 无法获取飞书 token，消息发送失败")
        return False
    url = 'https://open.feishu.cn/open-apis/im/v1/messages'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }
    payload = {
        'receive_id': receive_id,
        'msg_type': content_type,
        'content': content,
    }
    try:
        resp = requests.post(url, headers=headers, json=payload,
                             params={'receive_id_type': receive_id_type})
        result = resp.json()
        if result.get('code') == 0:
            print(f"[飞书] 消息已发送 -> {receive_id}")
            return True
        else:
            print(f"[飞书] 消息发送失败: {result.get('msg')}")
            return False
    except Exception as e:
        print(f"[错误] 发送飞书消息异常: {e}")
        return False


def build_payment_card(chat_id):
    """
    构建飞书交互式支付卡片（展示商品列表 + 支付按钮）
    返回卡片 JSON 字符串
    """
    elements = []

    # 标题区
    elements.append({
        "tag": "div",
        "text": {
            "tag": "lark_md",
            "content": "**🛒 请选择您要购买的商品，点击按钮即可发起支付：**"
        }
    })
    elements.append({"tag": "hr"})

    # 商品列表 + 按钮
    for product in PRODUCT_CATALOG:
        elements.append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": (
                    f"**{product['name']}**\n"
                    f"💰 ¥{product['price']} 元\n"
                    f"📌 {product['desc']}"
                )
            }
        })
        elements.append({
            "tag": "action",
            "actions": [{
                "tag": "button",
                "text": {"tag": "plain_text", "content": f"立即支付 ¥{product['price']}"},
                "type": "primary",
                "value": {
                    "action": "create_payment",
                    "product_id": product['id'],
                    "product_name": product['name'],
                    "price": str(product['price']),
                    "chat_id": chat_id,
                }
            }]
        })
        elements.append({"tag": "hr"})

    card = {
        "config": {"wide_screen_mode": True},
        "header": {
            "title": {"tag": "plain_text", "content": "💳 AI数字员工系统 · 在线支付"},
            "template": "blue"
        },
        "elements": elements
    }
    return json.dumps(card, ensure_ascii=False)


def create_hupj_payment(order_id, amount, title):
    """
    调用虎皮椒 API 创建支付订单，返回支付链接
    """
    params = {
        'version': '1.1',
        'appid': HUPJ_CONFIG['app_id'],
        'trade_order_id': order_id,
        'total_fee': str(amount),
        'title': title,
        'time': str(int(time.time())),
        'notify_url': HUPJ_CONFIG['notify_url'],
        'return_url': HUPJ_CONFIG['return_url'],
        'nonce_str': _nonce_str(),
    }
    # 生成签名
    filtered = {k: v for k, v in params.items() if v and k != 'hash'}
    sorted_params = sorted(filtered.items())
    string_a = '&'.join([f"{k}={v}" for k, v in sorted_params])
    params['hash'] = hashlib.md5((string_a + HUPJ_CONFIG['app_secret']).encode()).hexdigest()

    try:
        resp = requests.post(HUPJ_CONFIG['api_url'], data=params, timeout=30)
        result = resp.json()
        if result.get('errcode') == 0:
            return {
                'success': True,
                'pay_url': result.get('url'),
                'qrcode_url': result.get('url_qrcode'),
            }
        else:
            return {'success': False, 'error': result.get('errmsg', '未知错误')}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def build_pay_url_card(product_name, price, order_id, pay_url):
    """构建包含支付链接的结果卡片"""
    card = {
        "config": {"wide_screen_mode": True},
        "header": {
            "title": {"tag": "plain_text", "content": "✅ 支付链接已生成"},
            "template": "green"
        },
        "elements": [
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": (
                        f"**商品：** {product_name}\n"
                        f"**金额：** ¥{price} 元\n"
                        f"**订单号：** `{order_id}`"
                    )
                }
            },
            {"tag": "hr"},
            {
                "tag": "action",
                "actions": [{
                    "tag": "button",
                    "text": {"tag": "plain_text", "content": "🔗 点击前往支付"},
                    "type": "primary",
                    "url": pay_url,
                }]
            },
            {
                "tag": "note",
                "elements": [{
                    "tag": "plain_text",
                    "content": "⚠️ 支付链接 30 分钟内有效，请尽快完成支付"
                }]
            }
        ]
    }
    return json.dumps(card, ensure_ascii=False)


# ============================================================
# 飞书事件订阅路由
# ============================================================

@app.route('/api/feishu/webhook', methods=['POST'])
def feishu_webhook():
    """
    飞书统一事件入口
    处理：
      - URL 验证（challenge）
      - 消息事件（识别支付意图 -> 发送支付卡片）
      - 卡片按钮点击（生成支付链接）
    """
    body = request.get_json(silent=True) or {}
    print(f"\n[飞书事件] {json.dumps(body, ensure_ascii=False)[:300]}")

    # 1. URL 验证（飞书首次配置事件订阅时的 challenge）
    if body.get('type') == 'url_verification':
        return jsonify({'challenge': body.get('challenge', '')})

    # 2. 判断是事件回调还是卡片回调
    # 卡片回调的特征：有 action 字段
    if 'action' in body and body.get('action', {}).get('value'):
        return _handle_card_action(body)

    # 3. 事件回调（消息等）
    event_type = body.get('header', {}).get('event_type', '')
    event = body.get('event', {})

    # 飞书旧版回调兼容
    if not event_type and 'event' in body:
        event_type = body.get('event', {}).get('type', '')
        event = body.get('event', {})

    if event_type in ('im.message.receive_v1', 'message'):
        _handle_message_event(event)

    return jsonify({'code': 0})


def _handle_message_event(event):
    """处理飞书消息事件"""
    msg = event.get('message', event)  # 兼容新旧版结构
    chat_id = msg.get('chat_id') or event.get('open_chat_id', '')
    sender_open_id = event.get('sender', {}).get('sender_id', {}).get('open_id', '')
    msg_type = msg.get('message_type', msg.get('msg_type', ''))

    if msg_type != 'text':
        return  # 只处理文本消息

    # 解析消息内容
    try:
        content_str = msg.get('content', '{}')
        content_obj = json.loads(content_str) if isinstance(content_str, str) else content_str
        text = content_obj.get('text', '').strip()
    except Exception:
        text = ''

    # 去除 @机器人 的 mention
    import re
    text = re.sub(r'@\S+', '', text).strip()

    print(f"[飞书消息] chat_id={chat_id} text={text}")

    # 识别支付意图
    if any(kw in text for kw in PAY_KEYWORDS):
        card_content = build_payment_card(chat_id)
        send_feishu_message(
            receive_id=chat_id,
            receive_id_type='chat_id',
            content_type='interactive',
            content=card_content,
        )


# ============================================================
# 飞书卡片按钮点击处理（被统一入口调用）
# ============================================================

def _handle_card_action(body):
    """
    处理飞书交互式卡片按钮点击
    当用户点击"立即支付"按钮时触发
    """
    print(f"\n[卡片点击] {json.dumps(body, ensure_ascii=False)[:300]}")

    action_value = body.get('action', {}).get('value', {})
    action_type = action_value.get('action', '')
    open_id = body.get('open_id', '')
    chat_id = action_value.get('chat_id', '') or body.get('open_chat_id', '')

    if action_type != 'create_payment':
        return jsonify({'code': 0})

    product_name = action_value.get('product_name', '未知商品')
    price = action_value.get('price', '0')
    product_id = action_value.get('product_id', 'unknown')

    # 生成订单号
    order_id = f"FS{datetime.now().strftime('%Y%m%d%H%M%S')}{_nonce_str(6)}"

    print(f"[支付] 创建订单: {order_id} | {product_name} | ¥{price}")

    # 调用虎皮椒创建支付订单
    result = create_hupj_payment(order_id, price, product_name)

    if result['success']:
        pay_url = result['pay_url']

        # 回写飞书卡片（更新为支付链接卡片）
        updated_card = build_pay_url_card(product_name, price, order_id, pay_url)
        response_body = {
            "toast": {
                "type": "success",
                "content": "支付链接已生成，请点击按钮完成支付"
            },
            "card": {
                "type": "raw",
                "data": json.loads(updated_card)
            }
        }

        # 同时将订单写入飞书多维表格（异步不阻塞）
        _save_order_to_feishu(order_id, product_name, price, open_id, pay_url)

        print(f"[成功] 支付链接: {pay_url}")
        return jsonify(response_body)
    else:
        error_msg = result.get('error', '支付创建失败')
        print(f"[失败] {error_msg}")
        return jsonify({
            "toast": {
                "type": "error",
                "content": f"支付创建失败：{error_msg}"
            }
        })


def _save_order_to_feishu(order_id, product_name, price, open_id, pay_url):
    """将新订单写入飞书多维表格"""
    token = _feishu_token()
    if not token:
        return
    url = (f"https://open.feishu.cn/open-apis/bitable/v1/apps/"
           f"{FEISHU_CONFIG['app_token']}/tables/{FEISHU_CONFIG['table_id']}/records")
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }
    fields = {
        '订单号': order_id,
        '商品名称': product_name,
        '订单金额': float(price),
        '支付状态': '待支付',
        '创建时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        '用户ID': open_id,
        '支付链接': pay_url,
    }
    try:
        resp = requests.post(url, headers=headers, json={'fields': fields})
        result = resp.json()
        if result.get('code') == 0:
            print(f"[飞书表格] 订单 {order_id} 已写入多维表格")
        else:
            print(f"[飞书表格] 写入失败: {result.get('msg')}")
    except Exception as e:
        print(f"[错误] 写入飞书表格异常: {e}")


# ============================================================
# 服务启动
# ============================================================

def start_server():
    """启动服务器"""
    print("=" * 60)
    print("[启动] AI支付回调处理服务")
    print("=" * 60)
    print("\n服务地址:")
    print("  - 首页:           http://localhost:5000/")
    print("  - 虎皮椒回调:     http://localhost:5000/payment/notify")
    print("  - 支付成功页:     http://localhost:5000/payment/success")
    print("  - 飞书统一入口:   http://localhost:5000/api/feishu/webhook")
    print("\n按 Ctrl+C 停止服务\n")

    app.run(host='0.0.0.0', port=5000, debug=False)


if __name__ == '__main__':
    start_server()
