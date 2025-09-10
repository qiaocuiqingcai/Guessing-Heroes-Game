from flask import render_template, request, session
import pandas as pd

# 王者荣耀游戏相关常量
EXCEL_FILE = 'heroes.xlsx'
FIELDS = [
    '职业', '种族', '性别', '阵营', '区域', '城市', '身高(cm)', '皮肤数量',
    '上线时间'
]

def load_heroes_data():
    """加载王者荣耀英雄数据"""
    df = pd.read_excel(EXCEL_FILE)
    df.columns = df.columns.str.strip()  # 去除列名空格
    return df

def get_hero_names():
    """获取王者荣耀英雄名称列表"""
    df = load_heroes_data()
    return df['英雄名'].tolist()

def wangzhe_game(check_win_func, new_round_func, user=None, leaderboard=None):
    """王者荣耀游戏主逻辑
    参数:
        check_win_func: 检查胜利条件的函数
        new_round_func: 开始新游戏的函数
        user: 用户数据
        leaderboard: 排行榜数据
    """
    if 'answer' not in session:
        new_round_func()
    
    df = load_heroes_data()
    HERO_NAMES = get_hero_names()
    
    message = ''
    guesses = session.get('guesses', [])
    max_attempts = session.get('max_attempts', 5)
    current_attempt = len(guesses)
    answer_fields = []
    has_failed = False

    # 检查是否失败（超过最大尝试次数）
    if current_attempt >= max_attempts and not check_win_func(guesses):
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
        has_won=check_win_func(guesses),
        has_failed=session.pop('has_failed', False),
        has_surrendered=session.pop('has_surrendered', False),
        answer_name=session['answer']['英雄名'],
        answer_fields=answer_fields,
        image_folder='date',
        user=user,
        leaderboard=leaderboard
    )

def wangzhe_autocomplete(prefix):
    """王者荣耀英雄名称自动完成功能"""
    df = load_heroes_data()
    
    # 王者荣耀只使用英雄名列表
    HERO_NAMES = df['英雄名'].tolist()
    
    # 匹配输入的前缀
    matches = [name for name in HERO_NAMES if name.startswith(prefix)]
    
    return matches[:10]  # 返回前10个匹配项

def new_wangzhe_round():
    """开始新一轮王者荣耀游戏"""
    df = load_heroes_data()
    hero = df.sample().iloc[0].to_dict()
    return hero