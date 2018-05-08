#!/usr/bin/python
# -*- coding: UTF-8 -*-

import smtplib
from email.mime.text import MIMEText
from email.header import Header
from MaxValue.conf import stmp_config
import arrow


def _send_error_msg_by_email(subject, msg, receivers=['349106576@qq.com']):
    sender = stmp_config.username
    # 三个参数：第一个为文本内容，第二个 plain 设置文本格式，第三个 utf-8 设置编码
    message = MIMEText(msg, 'plain', 'utf-8')
    message['From'] = Header("交易执行主机<%>".format(stmp_config.username), 'utf-8')
    message['Subject'] = Header(subject, 'utf-8')

    try:
        smtpObj = smtplib.SMTP_SSL(stmp_config.server, stmp_config.port)
        smtpObj.login(stmp_config.username, stmp_config.password)
        smtpObj.sendmail(sender, receivers, message.as_string())
        print("邮件发送成功")
    except smtplib.SMTPException:
        import traceback
        traceback.print_exc()
        print("Error: 无法发送邮件")


def _send_error_msg_by_local_email(subject, msg, receivers=['349106576@qq.com']):
    sender = stmp_config.username
    # 三个参数：第一个为文本内容，第二个 plain 设置文本格式，第三个 utf-8 设置编码
    message = MIMEText(msg, 'html', 'utf-8')
    message['From'] = Header("交易执行主机<{0}>".format(stmp_config.username), 'utf-8')
    message['Subject'] = Header(subject, 'utf-8')

    try:
        smtpObj = smtplib.SMTP(stmp_config.server, stmp_config.port)
        smtpObj.ehlo()
        smtpObj.starttls()
        smtpObj.login(stmp_config.username, stmp_config.password)
        smtpObj.sendmail(sender, receivers, message.as_string())
        print("邮件发送成功")
    except smtplib.SMTPException:
        import traceback
        traceback.print_exc()
        print("Error: 无法发送邮件")


def send_error_msg_by_email(subject="交易出错", msg="",
                            receivers=['349106576@qq.com', "978437333@qq.com", "64541665@qq.com"]):
    sender = stmp_config.username + "@qq.com"
    # 三个参数：第一个为文本内容，第二个 plain 设置文本格式，第三个 utf-8 设置编码

    msg = "交易检测到出错，请重置交易后，重新运行程序。\r\n" \
          "重置的方法为：\r\n" \
          "" \
          "1.重置所有的交易\r\n" \
          "2.重置程序\r\n " \
          "   2.1 登录okex，bitemx页面," \
          "当前时间为：" + str(arrow.utcnow())

    _send_error_msg_by_local_email(subject, msg, receivers)


if __name__ == "__main__":
    send_error_msg_by_email(subject="交易出错", msg="请重置程序")
