from typing import Any
from flask import render_template, request, session
import pandas as pd

# 英雄联盟游戏相关常量
EXCEL_FILE = 'heroes_lol.xlsx'
FIELDS = [
    '分路', '职业', '地区', '带位移', '攻击距离', '上线时间', '外号'
]

def load_heroes_data():
    """加载英雄联盟英雄数据"""
    df = pd.read_excel(EXCEL_FILE)
    df.columns = df.columns.str.strip()  # 去除列名空格
    return df

def get_hero_names():
    """获取英雄联盟英雄名称列表（包括中文名、英文名、称号和外号）"""
    df = load_heroes_data()
    return df['英雄名'].tolist() + df['英文名'].tolist() + df['称号'].tolist() + df['外号'].tolist()

def lol_game(check_win_func, new_round_func, user=None, leaderboard=None):
    """英雄联盟游戏主逻辑
    参数:
        check_win_func: 检查胜利条件的函数
        new_round_func: 开始新游戏的函数
        user: 用户数据
        leaderboard: 排行榜数据
    """
    df = load_heroes_data()
    HERO_NAMES = get_hero_names()

    if 'answer' not in session:
        new_round_func()

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
        has_won=check_win_func(guesses),
        has_failed=session.pop('has_failed', False),
        has_surrendered=session.pop('has_surrendered', False),
        answer_name=session['answer']['英雄名'],
        answer_fields=answer_fields,
        image_folder='date',
        user=user,
        leaderboard=leaderboard
    )

def lol_autocomplete(prefix):
    """英雄联盟英雄名称自动完成功能"""
    df = load_heroes_data()
    
    # 合并 英雄名、称号、外号 和 英文名 列为一个统一的列表
    HERO_NAMES = df['英雄名'].tolist() + df['称号'].tolist() + df['外号'].tolist() + df['英文名'].tolist()
    
    # 匹配输入的前缀
    matches = [name for name in HERO_NAMES if name.startswith(prefix)]
    
    return matches[:10]  # 返回前10个匹配项

def new_lol_round():
    """开始新一轮英雄联盟游戏"""
    df: Any = load_heroes_data()
    hero = df.sample().iloc[0].to_dict()
    return hero