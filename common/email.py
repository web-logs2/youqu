import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To

from common import log
from config import project_conf,channel_conf
import common.const as const
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

def send_email_with_template(to_email, subject, template_id, dynamic_template_data=None):
    from_email = Email(const.EMAIL_SENDER)  # 更改为您的发件人邮箱
    to_email = To(to_email)

    message = Mail(from_email=from_email, to_emails=to_email)
    message.template_id = template_id

    if dynamic_template_data:
        message.dynamic_template_data = dynamic_template_data

    try:
        api_key=project_conf("sendgrid_api_key")
        sendgrid_client = SendGridAPIClient(api_key)
        response = sendgrid_client.send(message)

        log.info("Request headers:{}", sendgrid_client.client.default_headers)
        log.info("Request body:{}", message.get())
        # 也可以使用下面的方式打印请求体
        # print("Request body:", json.dumps(message.get(), indent=4))

        log.info("Email sent successfully!")
        return response.status_code

    except Exception as e:
        log.info("Error occurred while sending email: ", e)



def send_reset_password(token: str, recipient_email: str):
    template_id = const.EMAIL_TEMPLATE_RESET_PASSWORD  # 替换为您的SendGrid模板ID
    domain_name = channel_conf(const.HTTP).get('domain_name')
    reset_password_url = f"{domain_name}#/reset_password?token={token}"
    log.info("reset_password_url:{} ", reset_password_url)
    dynamic_template_data = {"email": recipient_email,"url":reset_password_url}  # 您要替换的动态模板数据
    subject = "Reset your password"
    send_email_with_template(recipient_email, subject, template_id, dynamic_template_data)