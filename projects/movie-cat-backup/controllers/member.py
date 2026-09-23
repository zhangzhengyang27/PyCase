# -*- coding: utf-8 -*-
from application import app, db
from flask import Blueprint, render_template, request, jsonify, make_response, redirect
from common.libs.Helper import ops_renderJSON, ops_renderErrJSON
from common.libs.DataHelper import getCurrentTime
from common.libs.UrlManager import UrlManager
from common.models.user import User
from common.libs.UserService import UserService

member_page = Blueprint("member_page", __name__)


@member_page.route("/reg", methods=["GET", "POST"])
def reg():
    if request.method == "GET":
        return render_template("member/reg.html")

    req = request.values  # 获取请求参数
    nickname = req['nickname'] if "nickname" in req else ""  # 获取昵称
    login_name = req['login_name'] if "login_name" in req else ""  # 获取登录名
    login_pwd = req['login_pwd'] if "login_pwd" in req else ""  # 获取登录密码
    login_pwd2 = req['login_pwd2'] if "login_pwd2" in req else ""  # 获取确认登录密码

    if login_name is None or len(login_name) < 1:
        return ops_renderErrJSON(msg="请输入正确的登录用户名~~")

    if login_pwd is None or len(login_pwd) < 6:
        return ops_renderErrJSON(msg="请输入正确的登录密码，并且不能小于6个字符~~")

    if login_pwd != login_pwd2:
        return ops_renderErrJSON(msg="请输入正确的确认登录密码~~")

    user_info = User.query.filter_by(login_name=login_name).first()  # 查询数据库中是否有该用户
    if user_info:
        return ops_renderErrJSON(msg="登录用户名已被注册，请换一个~~")  # 如果有该用户，返回错误信息

    model_user = User()
    model_user.login_name = login_name
    model_user.nickname = nickname if nickname is not None else login_name
    model_user.login_salt = UserService.geneSalt(8)  # 生成8位的随机字符串
    model_user.login_pwd = UserService.genePwd(login_pwd, model_user.login_salt)  # 生成密码
    model_user.created_time = model_user.updated_time = getCurrentTime()  # 获取当前时间
    db.session.add(model_user)  # 添加到数据库
    db.session.commit()  # 提交到数据库
    return ops_renderJSON(msg="注册成功~~")


@member_page.route("/login",methods = [ "GET","POST" ])
def login():
    if request.method == "GET":
        return render_template("member/login.html")

    req = request.values
    login_name = req['login_name'] if 'login_name' in req else ''
    login_pwd = req['login_pwd'] if 'login_pwd' in req else ''
    if login_name is None or len( login_name ) < 1:
        return ops_renderErrJSON(  "请输入正确的登录用户名~~" )

    if login_pwd is None or len( login_pwd ) < 6:
        return ops_renderErrJSON("请输入正确的登录密码~~")
    user_info = User.query.filter_by( login_name = login_name ).first()
    if not user_info:
        return ops_renderErrJSON("请输入正确的登录用户名和密码 -1~~")

    if user_info.login_pwd != UserService.genePwd( login_pwd,user_info.login_salt ):
        return ops_renderErrJSON("请输入正确的登录用户名和密码 -2 ~~")

    if user_info.status != 1:
        return ops_renderErrJSON( "账号被禁用，请联系管理员处理~~" )

    #session['uid'] = user_info.id
    response = make_response( ops_renderJSON( msg="登录成功~~" ) )
    response.set_cookie(app.config['AUTH_COOKIE_NAME'],
                        "%s#%s"%( UserService.geneAuthCode( user_info ),user_info.id ),60 * 60 *24 *120 )
    return response


@member_page.route("/logout")
def logOut():
    response = make_response( redirect( UrlManager.buildUrl("/") ) )
    response.delete_cookie(  app.config['AUTH_COOKIE_NAME'] )
    return response

