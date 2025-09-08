from flask import Flask, render_template, request, jsonify, session,redirect
import pandas as pd
import random
import os

app = Flask(__name__)
app.secret_key = 'guess-hero-secret'

# 读取数据


# 字段顺序控制
# FIELDS = ['职业', '皮肤数量', '保留项1']

@app.route('/', methods=['GET', 'POST'])
def select():
    if request.method == 'POST':
        mode = request.form.get('mode')
        if mode == 'lol':
            session['game_mode'] = 'lol'
            return redirect('/lol')
        else:
            session['game_mode'] = 'wangzhe'
            return redirect('/wangzhe')
    return render_template('select.html')  # 创建这个模板文件

@app.route('/switch_mode', methods=['POST'])
def switch_mode():
    mode = request.form.get('mode')
    if mode == 'lol':
        session['game_mode'] = 'lol'
    else:
        session['game_mode'] = 'wangzhe'
    
    # 强制重置游戏
    max_attempts = session.get('max_attempts', 5)
    session.clear()  # 清空所有session
    session['game_mode'] = mode  # 重新设置模式
    session['max_attempts'] = max_attempts  # 保留尝试次数设置
    new_round()  # 开始新游戏
    
    # 根据当前模式重定向
    if mode == 'lol':
        return redirect('/lol')
    else:
        return redirect('/wangzhe')


# @app.route('/lol', methods=['GET', 'POST'])
# def newindex():
#     FIELDS = [
#     '分路', '职业','地区','攻击距离',  '上线时间'
# ]
#     df = pd.read_excel('heroes_lol.xlsx')
#     df.columns = df.columns.str.strip()  # 去除列名空格
#     HERO_NAMES = df['英雄名'].tolist()
#     if 'answer' not in session:
#         new_round()

#     message = ''
#     guesses = session.get('guesses', [])
#     max_attempts = session.get('max_attempts', 5)
#     current_attempt = len(guesses)
#     answer_fields = []
#     has_failed = False

#     # 检查是否失败（超过最大尝试次数）
#     if current_attempt >= max_attempts and not check_win(guesses):
#         has_failed = True
#         session['has_failed'] = True

#     # 准备正确答案的字段数据（失败或投降时显示）
#     if session.get('has_failed', False) or session.get('has_surrendered', False):
#         answer_data = session['answer']
#         for field in FIELDS:
#             answer_fields.append({
#                 '名称': field,
#                 '值': answer_data.get(field, 'N/A')
#             })

#     if request.method == 'POST':
#         guess_name = request.form['hero'].strip()
#         if guess_name not in HERO_NAMES:
#             message = f"英雄 [{guess_name}] 不存在。"
#         else:
#             guess_data = df[df['英雄名'] == guess_name].iloc[0].to_dict()
#             answer_data = session['answer']

#             result = {
#                 '英雄名': guess_name,
#                 '字段': []
#             }

#             for field in FIELDS:
#                 try:
#                     guess_value = guess_data[field]
#                     answer_value = answer_data[field]

#                     if guess_value == answer_value:
#                         status = 'correct'
#                     elif isinstance(answer_value, (int, float)) and isinstance(guess_value, (int, float)):
#                         status = 'up' if guess_value < answer_value else 'down'
#                     else:
#                         status = 'wrong'
#                 except KeyError:
#                     status = 'wrong'
#                     guess_value = 'N/A'

#                 result['字段'].append({
#                     '名称': field,
#                     '值': guess_value,
#                     '状态': status
#                 })

#             guesses.append(result)
#             session['guesses'] = guesses
#             current_attempt += 1
#     return render_template('index.html',
#                           guesses=guesses,
#                           attempts=f"{current_attempt}/{max_attempts}",
#                           max_attempts=max_attempts,
#                           has_won=check_win(guesses),
#                           has_failed=session.pop('has_failed', False),
#                           has_surrendered=session.pop('has_surrendered', False),
#                           answer_name=session['answer']['英雄名'],
#                           answer_fields=answer_fields,
#                           image_folder='date')

@app.route('/lol', methods=['GET', 'POST'])
def newindex():
    FIELDS = [
        '分路', '职业', '地区','带位移','攻击距离', '上线时间','外号'
    ]
    df = pd.read_excel('heroes_lol.xlsx')
    df.columns = df.columns.str.strip()  # 去除列名空格

    # 创建一个包含中文名、英文名和称号的统一列表
    HERO_NAMES = df['英雄名'].tolist() + df['英文名'].tolist() + df['称号'].tolist()+df['外号'].tolist()

    if 'answer' not in session:
        new_round()

    message = ''
    guesses = session.get('guesses', [])
    max_attempts = session.get('max_attempts', 5)
    current_attempt = len(guesses)
    answer_fields = []
    has_failed = False

    # 检查是否失败（超过最大尝试次数）
    if current_attempt >= max_attempts and not check_win(guesses):
        has_failed = True
        session['has_failed'] = True

    # 准备正确答案的字段数据（失败或投降时显示）
    if session.get('has_failed', False) or session.get('has_surrendered', False):
        answer_data = session['answer']
        for field in FIELDS:
            answer_fields.append({
                '名称': field,
                '值': answer_data.get(field, 'N/A')
            })

    if request.method == 'POST':
        guess_name = request.form['hero'].strip()

        # 检查用户输入的名称是否在 HERO_NAMES 列表中
        if guess_name not in HERO_NAMES:
            message = f"英雄 [{guess_name}] 不存在。"
        else:
            # 找到匹配的英雄并获取其详细数据
            if guess_name in df['英雄名'].values:
                # 如果输入的是英雄中文名，直接使用该名
                guess_name_unified = guess_name
                guess_data = df[df['英雄名'] == guess_name].iloc[0].to_dict()
            elif guess_name in df['英文名'].values:
                # 如果输入的是英文名，统一转换为对应的英雄中文名
                guess_name_unified = df[df['英文名'] == guess_name]['英雄名'].iloc[0]
                guess_data = df[df['英文名'] == guess_name].iloc[0].to_dict()
            elif guess_name in df['称号'].values:
                # 如果输入的是称号，统一转换为对应的英雄中文名
                guess_name_unified = df[df['称号'] == guess_name]['英雄名'].iloc[0]
                guess_data = df[df['称号'] == guess_name].iloc[0].to_dict()
            else:
                # 如果输入的是外号，统一转换为对应的英雄中文名
                guess_name_unified = df[df['外号'] == guess_name]['英雄名'].iloc[0]
                guess_data = df[df['外号'] == guess_name].iloc[0].to_dict()
        

            answer_data = session['answer']

            result = {
                '英雄名': guess_name_unified,  # 使用统一后的英雄名
                '字段': []
            }

            for field in FIELDS:
                try:
                    guess_value = guess_data[field]
                    answer_value = answer_data[field]

                    if guess_value == answer_value:
                        status = 'correct'
                    elif isinstance(answer_value, (int, float)) and isinstance(guess_value, (int, float)):
                        status = 'up' if guess_value < answer_value else 'down'
                    else:
                        status = 'wrong'
                except KeyError:
                    status = 'wrong'
                    guess_value = 'N/A'

                result['字段'].append({
                    '名称': field,
                    '值': guess_value,
                    '状态': status
                })

            guesses.append(result)
            session['guesses'] = guesses
            current_attempt += 1

    return render_template('index.html',
                          guesses=guesses,
                          attempts=f"{current_attempt}/{max_attempts}",
                          max_attempts=max_attempts,
                          has_won=check_win(guesses),
                          has_failed=session.pop('has_failed', False),
                          has_surrendered=session.pop('has_surrendered', False),
                          answer_name=session['answer']['英雄名'],
                          answer_fields=answer_fields,
                          image_folder='date')




@app.route('/wangzhe', methods=['GET', 'POST'])
def index():
    if 'answer' not in session:
        new_round()
    
    df = pd.read_excel('heroes.xlsx')
    df.columns = df.columns.str.strip()  # 去除列名空格
    HERO_NAMES = df['英雄名'].tolist()
    FIELDS = [
    '职业', '种族','性别','阵营',  '区域', '城市' ,'身高(cm)', '皮肤数量',
    '上线时间'
    ]
    message = ''
    guesses = session.get('guesses', [])
    max_attempts = session.get('max_attempts', 5)
    current_attempt = len(guesses)
    answer_fields = []
    has_failed = False

    # 检查是否失败（超过最大尝试次数）
    if current_attempt >= max_attempts and not check_win(guesses):
        has_failed = True
        session['has_failed'] = True

    # 准备正确答案的字段数据（失败或投降时显示）
    if session.get('has_failed', False) or session.get('has_surrendered', False):
        answer_data = session['answer']
        for field in FIELDS:
            answer_fields.append({
                '名称': field,
                '值': answer_data.get(field, 'N/A')
            })

    if request.method == 'POST':
        guess_name = request.form['hero'].strip()
        if guess_name not in HERO_NAMES:
            message = f"英雄 [{guess_name}] 不存在。"
        else:
            guess_data = df[df['英雄名'] == guess_name].iloc[0].to_dict()
            answer_data = session['answer']

            result = {
                '英雄名': guess_name,
                '字段': []
            }

            for field in FIELDS:
                try:
                    guess_value = guess_data[field]
                    answer_value = answer_data[field]

                    if guess_value == answer_value:
                        status = 'correct'
                    elif isinstance(answer_value, (int, float)) and isinstance(guess_value, (int, float)):
                        status = 'up' if guess_value < answer_value else 'down'
                    else:
                        status = 'wrong'
                except KeyError:
                    status = 'wrong'
                    guess_value = 'N/A'

                result['字段'].append({
                    '名称': field,
                    '值': guess_value,
                    '状态': status
                })

            guesses.append(result)
            session['guesses'] = guesses
            current_attempt += 1
    return render_template('index.html',
                          guesses=guesses,
                          attempts=f"{current_attempt}/{max_attempts}",
                          max_attempts=max_attempts,
                          has_won=check_win(guesses),
                          has_failed=session.pop('has_failed', False),
                          has_surrendered=session.pop('has_surrendered', False),
                          answer_name=session['answer']['英雄名'],
                          answer_fields=answer_fields,
                          image_folder='date')



@app.route('/start', methods=['POST'])
# def start():
#     max_attempts = int(request.form.get('max_attempts', 10))
#     session['max_attempts'] = max_attempts
#     new_round()
#     return jsonify({'success': True})
def start():
    max_attempts = int(request.form.get('max_attempts', 5))
    session['max_attempts'] = max_attempts
    
    # 清除所有游戏相关session
    session.pop('answer', None)
    session.pop('guesses', None)
    session.pop('has_surrendered', None)
    session.pop('has_failed', None)
    
    # 开始新游戏
    new_round()
    
    return jsonify({'success': True})


@app.route('/surrender', methods=['POST'])
def surrender():
    session['has_surrendered'] = True
    return jsonify({'success': True})


# @app.route('/autocomplete')
# def autocomplete():
#     if session['game_mode'] == 'lol':
#         df = pd.read_excel('heroes_lol.xlsx')
#         df.columns = df.columns.str.strip()  # 去除列名空格
#         HERO_NAMES = df['英雄名'].tolist()
#         prefix = request.args.get('prefix', '').strip()
#         matches = [name for name in HERO_NAMES if name.startswith(prefix)]
#         return jsonify(matches[:10])  # 返回前10个匹配项
#     else:
#         df = pd.read_excel('heroes.xlsx')
#         df.columns = df.columns.str.strip()  # 去除列名空格
#         HERO_NAMES = df['英雄名'].tolist()
#         prefix = request.args.get('prefix', '').strip()
#         matches = [name for name in HERO_NAMES if name.startswith(prefix)]
#         return jsonify(matches[:10])  # 返回前10个匹配项

@app.route('/autocomplete')
def autocomplete():
    if session['game_mode'] == 'lol':
        df = pd.read_excel('heroes_lol.xlsx')
        df.columns = df.columns.str.strip()  # 去除列名空格
        
        # 合并 英雄名、称号 和 英文名 列为一个统一的列表
        HERO_NAMES = df['英雄名'].tolist() + df['称号'].tolist() + df['外号'].tolist() + df['英文名'].tolist()
        
        prefix = request.args.get('prefix', '').strip()
        
        # 匹配输入的前缀
        matches = [name for name in HERO_NAMES if name.startswith(prefix)]
        
        return jsonify(matches[:10])  # 返回前10个匹配项
    else:
        df = pd.read_excel('heroes.xlsx')
        df.columns = df.columns.str.strip()  # 去除列名空格
        
        # 合并 英雄名、称号 和 英文名 列为一个统一的列表
        HERO_NAMES = df['英雄名'].tolist()
        
        prefix = request.args.get('prefix', '').strip()
        
        # 匹配输入的前缀
        matches = [name for name in HERO_NAMES if name.startswith(prefix)]
        
        return jsonify(matches[:10])  # 返回前10个匹配项



# def new_round():
#     hero = df.sample().iloc[0].to_dict()
#     session['answer'] = hero
#     session['guesses'] = []
#     session['has_surrendered'] = False
#     session['has_failed'] = False

def new_round():
    game_mode = session.get('game_mode', 'wangzhe')  # 默认为王者荣耀
    
    if game_mode == 'lol':
        df = pd.read_excel('heroes_lol.xlsx')
    else:
        df = pd.read_excel('heroes.xlsx')
        
    hero = df.sample().iloc[0].to_dict()
    session['answer'] = hero
    session['guesses'] = []
    session['has_surrendered'] = False
    session['has_failed'] = False


def check_win(guesses):
    if not guesses:
        return False
    return all(field['状态'] == 'correct' for field in guesses[-1]['字段'])


if __name__ == '__main__':
    app.run(host='0.0.0.0',debug=True, use_reloader=False,port=50050)