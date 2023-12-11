from celery import shared_task
from laikeapi.libs.tx_sms.tencentapi import send_message as sms
# 记录日志：
import logging
logger = logging.getLogger("django")


@shared_task(name="send_sms")
def send_sms(mobile, datas):
    """异步发送短信"""
    try:
        return sms(mobile, datas)
    except Exception as e:
        logger.error(f"手机号：{mobile}，发送短信失败错误: {e}")