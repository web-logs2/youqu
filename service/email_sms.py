import re

from sendgrid import SendGridAPIClient
import ssl

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To
from twilio.rest import Client

import common.const as const
import common.log as logger
import config
from config import project_conf, channel_conf


# ssl._create_default_https_context = ssl._create_unverified_context


def send_email_with_template(to_email, subject, template_id, dynamic_template_data=None):
    from_email = Email(const.EMAIL_SENDER)  # 更改为您的发件人邮箱
    to_email = To(to_email)

    message = Mail(from_email=from_email, to_emails=to_email)
    message.template_id = template_id

    if dynamic_template_data:
        message.dynamic_template_data = dynamic_template_data

    try:
        api_key = project_conf("sendgrid_api_key")
        sendgrid_client = SendGridAPIClient(api_key)
        response = sendgrid_client.send(message)

        logger.info("Request headers:{}", sendgrid_client.client.default_headers)
        logger.info("Request body:{}", message.get())
        # 也可以使用下面的方式打印请求体
        # print("Request body:", json.dumps(message.get(), indent=4))

        logger.info("Email sent successfully!")
        return response.status_code

    except Exception as e:
        logger.info("Error occurred while sending email: ", e)


def send_reset_password(token: str, recipient_email: str, first_name: str):
    template_id = const.EMAIL_TEMPLATE_RESET_PASSWORD  # 替换为您的SendGrid模板ID
    domain_name = channel_conf(const.HTTP).get('domain_name')
    reset_password_url = f"{domain_name}#/reset_password?token={token}"
    logger.info("reset_password_url:{} ", reset_password_url)
    dynamic_template_data = {"first_name": first_name, "url": reset_password_url}  # 您要替换的动态模板数据
    subject = "Reset your password"
    send_email_with_template(recipient_email, subject, template_id, dynamic_template_data)
    logger.info("send_reset_password:{}", recipient_email)


def send_verify_code_email(recipient_email: str, code: str):
    template_id = const.EMAIL_TEMPLATE_VERIFY_CODE  # 替换为您的SendGrid模板ID
    dynamic_template_data = {"code": code}  # 您要替换的动态模板数据
    subject = "Your verification code"
    send_email_with_template(recipient_email, subject, template_id, dynamic_template_data)
    logger.info("send_verify_code_email:{}", recipient_email)


def send_sms(messageContent: str, recipient_phone: str):
    account_sid = project_conf("twilio_api_sid")
    auth_token = project_conf("twilio_api_token")
    client = Client(account_sid, auth_token)
    if not messageContent or len(messageContent) > 60:
        logger.error("Invalid message content:{}", messageContent)
        return

    if not is_valid_phone_number(recipient_phone):
        logger.error("Invalid phone number:{}", recipient_phone)
        return

    message = client.messages.create(
        from_='+12512202845',
        body=messageContent,
        to=recipient_phone
    )

    logger.info(message.sid)


def is_valid_phone_number(number):
    pattern = r'^\+861\d{10}$'
    if re.match(pattern, number):
        return True
    else:
        return False


if __name__ == '__main__':
    config.load_config()
    send_sms("test", "+8613006601253")
