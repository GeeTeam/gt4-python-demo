import tornado.web
import tornado.ioloop
import requests
import hmac
import json


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("static/index.html", )


class LoginHandler(tornado.web.RequestHandler):
    def get(self):
        self.post()

    def post(self):
        # 1.初始化极验参数信息
        captcha_id = '647f5ed2ed8acb4be36784e01556bb71'
        captcha_key = 'b09a7aafbfd83f73b35a9b530d0337bf'
        api_server = 'http://gcaptcha4.geetest.com'

        # 2.获取用户验证后前端传过来的验证流水号等参数
        lot_number = self.get_argument('lot_number', '')
        captcha_output = self.get_argument('captcha_output', '')
        pass_token = self.get_argument('pass_token', '')
        gen_time = self.get_argument('gen_time', '')

        # 3.生成签名
        # 生成签名使用标准的hmac算法，使用用户当前完成验证的流水号lot_number作为原始消息message，使用客户验证私钥作为key
        # 采用sha256散列算法将message和key进行单向散列生成最终的签名
        lotnumber_bytes = lot_number.encode()
        prikey_bytes = captcha_key.encode()
        sign_token = hmac.new(prikey_bytes, lotnumber_bytes, digestmod='SHA256').hexdigest()

        # 4.上传校验参数到极验二次验证接口, 校验用户验证状态
        query = {
            "lot_number": lot_number,
            "captcha_output": captcha_output,
            "pass_token": pass_token,
            "gen_time": gen_time,
            "sign_token": sign_token,
        }
        # captcha_id 参数建议放在 url 后面, 方便请求异常时可以在日志中根据id快速定位到异常请求
        url = api_server + '/validate' + '?captcha_id={}'.format(captcha_id)
        # 注意处理接口异常情况，当请求极验二次验证接口异常时做出相应异常处理
        # 保证不会因为接口请求超时或服务未响应而阻碍业务流程
        try:
            res = requests.post(url, query)
            assert res.status_code == 200
            gt_msg = json.loads(res.text)
        except Exception as e:
            gt_msg = {'result': 'success', 'reason': 'request geetest api fail'}

        # 5.根据极验返回的用户验证状态, 网站主进行自己的业务逻辑
        if gt_msg['result'] == 'success':
            self.write({'login': 'success', 'reason': gt_msg['reason']})
        else:
            self.write({'login': 'fail', 'reason': gt_msg['reason']})


if __name__ == '__main__':
    app = tornado.web.Application([
        (r'/', MainHandler),
        (r'/login', LoginHandler),
    ])
    app.listen(8077)
    tornado.ioloop.IOLoop.instance().start()
