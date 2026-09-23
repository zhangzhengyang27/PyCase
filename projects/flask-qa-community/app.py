from flask import Flask, render_template

app = Flask(__name__, static_folder='assets')


@app.route('/')
def index():
    """ 首页 """
    return render_template('index.html')


@app.route('/follow')
def follow():
    """ 关注 """
    return render_template('follow.html')


@app.route('/login')
def login():
    """ 登录页面 """
    return render_template('login.html')


@app.route('/register')
def register():
    """ 注册 """
    return render_template('register.html')


@app.route('/write')
def write():
    """ 写文章，提问 """
    return render_template('write.html')


@app.route('/mine')
def mine():
    """ 个人中心 """
    return render_template('mine.html')


@app.route('/detail')
def detail():
    """ 问题详情 """
    return render_template('detail.html')


if __name__ == '__main__':
    app.run(debug=True)
