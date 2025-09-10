from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
import pandas as pd
from wangzhe import wangzhe_game, wangzhe_autocomplete, new_wangzhe_round
from lol import lol_game, lol_autocomplete, new_lol_round
from user_manager import UserManager

app = Flask(__name__)
app.secret_key = 'guess-hero-secret'

# 初始化用户管理器
user_manager = UserManager('userdata.xlsx')

@app.route('/', methods=['GET'])
def index():
    """首页 - 如果已登录则重定向到选择页面，否则重定向到登录页面"""
    if 'username' in session:
        return redirect(url_for('select'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录页面"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if user_manager.verify_user(username, password):
            session['username'] = username
            user_data = user_manager.get_user_data(username)
            session['user_data'] = user_data
            flash('登录成功！', 'success')
            return redirect(url_for('select'))
        else:
            flash('用户名或密码错误！', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """用户注册页面"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('两次输入的密码不一致！', 'error')
            return render_template('register.html')
        
        if user_manager.user_exists(username):
            flash('用户名已存在！', 'error')
            return render_template('register.html')
        
        user_manager.add_user(username, password)
        flash('注册成功，请登录！', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    """用户登出"""
    session.clear()
    flash('您已成功登出！', 'success')
    return redirect(url_for('login'))

@app.route('/user_profile')
def user_profile():
    """用户个人资料页面"""
    if 'username' not in session:
        flash('请先登录！', 'error')
        return redirect(url_for('login'))
    
    username = session['username']
    user_data = user_manager.get_user_data(username)
    
    return render_template('user_profile.html', user=user_data)

@app.route('/clear_history', methods=['POST'])
def clear_history():
    """清除用户游戏历史记录"""
    if 'username' not in session:
        flash('请先登录！', 'error')
        return redirect(url_for('login'))
    
    username = session['username']
    game_type = request.form.get('game_type', 'all')
    
    user_manager.clear_user_history(username, game_type)
    flash('游戏历史记录已清除！', 'success')
    
    # 更新session中的用户数据
    session['user_data'] = user_manager.get_user_data(username)
    
    return redirect(url_for('user_profile'))

@app.route('/select', methods=['GET', 'POST'])
def select():
    """游戏模式选择页面"""
    if 'username' not in session:
        flash('请先登录！', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        mode = request.form.get('mode')
        if mode == 'lol':
            session['game_mode'] = 'lol'
            return redirect(url_for('lol_index'))
        else:
            session['game_mode'] = 'wangzhe'
            return redirect(url_for('wangzhe_index'))
    
    return render_template('select.html', user=session.get('user_data'))

@app.route('/switch_mode', methods=['POST'])
def switch_mode():
    """切换游戏模式"""
    if 'username' not in session:
        flash('请先登录！', 'error')
        return redirect(url_for('login'))
    
    mode = request.form.get('mode')
    if mode == 'lol':
        session['game_mode'] = 'lol'
    else:
        session['game_mode'] = 'wangzhe'
    
    # 强制重置游戏
    max_attempts = session.get('max_attempts', 5)
    username = session['username']
    user_data = session.get('user_data')
    
    # 保留用户信息，清空游戏相关session
    session.pop('answer', None)
    session.pop('guesses', None)
    session.pop('has_surrendered', None)
    session.pop('has_failed', None)
    
    # 重新设置模式和尝试次数
    session['game_mode'] = mode
    session['max_attempts'] = max_attempts
    new_round()  # 开始新游戏
    
    # 根据当前模式重定向
    if mode == 'lol':
        return redirect(url_for('lol_index'))
    else:
        return redirect(url_for('wangzhe_index'))

@app.route('/lol', methods=['GET', 'POST'])
def lol_index():
    """英雄联盟游戏页面"""
    if 'username' not in session:
        flash('请先登录！', 'error')
        return redirect(url_for('login'))
    
    # 获取最新的用户数据
    username = session['username']
    user = user_manager.get_user_data(username)
    session['user_data'] = user
    
    result = lol_game(check_win, new_round, session['user_data'])
    
    # 如果游戏结束，更新用户数据
    if session.get('has_won') or session.get('has_surrendered') or session.get('has_failed'):
        game_won = session.get('has_won', False)
        user_manager.update_game_stats(username, 'lol', game_won)
        session['user_data'] = user_manager.get_user_data(username)
    
    # 获取排行榜数据
    leaderboard_data = user_manager.get_leaderboard(session.get('game_mode', 'all'))
    
    # 如果结果是响应对象，直接返回
    if hasattr(result, '_status_code'):
        return result
    
    # 获取排行榜数据
    leaderboard_data = user_manager.get_leaderboard(session.get('game_mode', 'all'))
    
    # 添加排行榜数据并返回
    if isinstance(result, dict):
        result['leaderboard'] = leaderboard_data[:10]
        return render_template('index.html', **result)
    else:
        return result
    return render_template('index.html', **result)
    
    # 否则添加排行榜数据并返回
    result['leaderboard'] = leaderboard_data[:10]
    return render_template('index.html', **result)

@app.route('/wangzhe', methods=['GET', 'POST'])
def wangzhe_index():
    """王者荣耀游戏页面"""
    if 'username' not in session:
        flash('请先登录！', 'error')
        return redirect(url_for('login'))
    
    # 获取最新的用户数据
    username = session['username']
    user = user_manager.get_user_data(username)
    session['user_data'] = user
    
    result = wangzhe_game(check_win, new_round, session['user_data'])
    
    # 如果游戏结束，更新用户数据
    if session.get('has_won') or session.get('has_surrendered') or session.get('has_failed'):
        game_won = session.get('has_won', False)
        user_manager.update_game_stats(username, 'wangzhe', game_won)
        session['user_data'] = user_manager.get_user_data(username)
    
    return result

@app.route('/start', methods=['POST'])
def start():
    """开始新游戏"""
    if 'username' not in session:
        return jsonify({'success': False, 'message': '请先登录！'})
    
    max_attempts = int(request.form.get('max_attempts', 5))
    session['max_attempts'] = max_attempts
    
    # 清除所有游戏相关session
    session.pop('answer', None)
    session.pop('guesses', None)
    session.pop('has_surrendered', None)
    session.pop('has_failed', None)
    session.pop('has_won', None)
    
    # 开始新游戏
    new_round()
    
    return jsonify({'success': True})

@app.route('/surrender', methods=['POST'])
def surrender():
    """投降功能"""
    if 'username' not in session:
        return jsonify({'success': False, 'message': '请先登录！'})
    
    session['has_surrendered'] = True
    
    # 更新用户游戏数据
    username = session['username']
    game_mode = session.get('game_mode', 'wangzhe')
    user_manager.update_game_stats(username, game_mode, False)
    session['user_data'] = user_manager.get_user_data(username)
    
    return jsonify({'success': True})

@app.route('/autocomplete')
def autocomplete():
    """英雄名称自动完成功能"""
    prefix = request.args.get('prefix', '').strip()
    
    if session.get('game_mode') == 'lol':
        matches = lol_autocomplete(prefix)
    else:
        matches = wangzhe_autocomplete(prefix)
        
    return jsonify(matches)

@app.route('/leaderboard')
def leaderboard():
    """排行榜页面"""
    if 'username' not in session:
        flash('请先登录！', 'error')
        return redirect(url_for('login'))
    
    game_mode = request.args.get('mode', 'all')
    leaderboard_data = user_manager.get_leaderboard(game_mode)
    return render_template('leaderboard.html', 
                         leaderboard=leaderboard_data,
                         game_mode=game_mode,
                         user=session.get('user_data'))

def new_round():
    """开始新一轮游戏，根据当前游戏模式选择相应的游戏"""
    game_mode = session.get('game_mode', 'wangzhe')  # 默认为王者荣耀
    
    if game_mode == 'lol':
        hero = new_lol_round()
    else:
        hero = new_wangzhe_round()
        
    session['answer'] = hero
    session['guesses'] = []
    session['has_surrendered'] = False
    session['has_failed'] = False
    session['has_won'] = False

def check_win(guesses):
    """检查是否猜对了所有字段"""
    if not guesses:
        return False
    
    is_win = all(field['状态'] == 'correct' for field in guesses[-1]['字段'])
    
    if is_win:
        session['has_won'] = True
        
        # 更新用户游戏数据
        if 'username' in session:
            username = session['username']
            game_mode = session.get('game_mode', 'wangzhe')
            user_manager.update_game_stats(username, game_mode, True)
            session['user_data'] = user_manager.get_user_data(username)
    
    return is_win

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, use_reloader=False, port=50050)