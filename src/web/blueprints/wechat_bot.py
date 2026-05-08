# -*- coding: utf-8 -*-
"""
WeChat Bot Webhook Blueprint
"""

import logging
from flask import Blueprint, request, make_response

logger = logging.getLogger(__name__)

wechat_bot_bp = Blueprint('wechat_bot', __name__, url_prefix='/api/wechat_bot')


@wechat_bot_bp.route('/webhook', methods=['GET', 'POST'])
def wechat_webhook():
    """
    Handle WeChat server verification (GET) and messages (POST).
    GET: echo back echostr for server URL verification
    POST: receive and respond to user messages
    """
    if request.method == 'GET':
        echostr = request.args.get('echostr', '')
        # TODO: verify signature before echoing
        return make_response(echostr)

    # POST: handle incoming message
    # TODO: parse XML, process via chat manager, build reply
    logger.info("Received WeChat webhook POST (not yet implemented)")
    return make_response("success")
