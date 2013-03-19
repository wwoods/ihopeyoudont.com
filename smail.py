
def send_mail(app, to, subject, body, frm=None):
    """Sends an e-mail to "to" with subject "subject" and body "body".
    "frm" may optionally be specified to send as under a different account
    than the default.
    """
    conf = app.config['SITE_EMAIL']
    if conf is None:
        raise RuntimeError('send_mail() called, but no site_email provided')

    frm = frm or conf['default']

    import smtplib
    from email.mime.text import MIMEText

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = frm
    msg['To'] = to

    server = conf.get('smtpserver')
    port = conf.get('smtpport') or 25
    use_ssl = conf.get('smtpssl')
    if use_ssl:
        s = smtplib.SMTP_SSL(server, port)
    else:
        s = smtplib.SMTP(server, port)
    user = conf.get('smtpuser')
    if user:
        password = conf.get('smtppass')
        s.login(user, password)
    else:
        s.connect()
    try:
        s.sendmail(frm, to, msg.as_string())
    finally:
        s.quit()