# -*- coding: utf-8 -*-

# @Time : 2022/5/12 13:02
# @Author : wangqianlong
# @Email : 1763423314@qq.com
# @File : model_main.py

import pandas as pd
import time
from gurobipy import *


# construct portfolio
def construct_portfolio(st_per, st_l):
    if len(st_l) >= 2:
        portfolio = list(itertools.product(list(st_per[st_l[0]])[:-1], list(st_per[st_l[1]])[:-1]))
        if len(st_l) >= 3:
            for st in st_l[2:]:
                portfolio = list(itertools.product(portfolio, list(st_per[st])[:-1]))
                portfolio = [list(p[0]) + [p[1]] for p in portfolio]
    else:
        portfolio = None
        print('WARNING: Just One Option, Need Not Optimize!')
    return portfolio


def construct_parameters(path_data, u_l):
    # read data
    st_percent = pd.read_csv(path_data + 'st_percent.csv', index_col=0)
    # increasing average row
    years = list(st_percent.index)
    num_year = len(years)
    st_percent.loc['Row_average'] = st_percent.apply(lambda x: x.sum() / num_year)
    st_percent_t = st_percent[u_l]
    st_list = list(st_percent_t.columns)
    # construct index and st correspondence
    corre_index_st = {index: st_list[index] for index in range(len(st_list))}
    # generate u
    u = [st_percent_t.loc['Row_average', st] for st in st_list]
    # K
    K_portfolio = construct_portfolio(st_percent_t, st_list)
    # parameters
    parameters = {
        'investment_limit': 1,
        'tao': 0.90,
        'alpha': 0.10,
        'M': 100,
        'corre_index_st': corre_index_st,
        'u': u,
        'K': K_portfolio,
        'TimeLimit': 3600,
        'MIPGap': 0,
    }
    return parameters, st_percent_t


# 初始化模型参数函数
def model_initial_parameter(mo, P):
    mo.Params.TimeLimit = P['TimeLimit']
    mo.Params.MIPGap = P['MIPGap']


# 模型变量添加函数
def add_vars(mo, P):
    X = mo.addVars(list(P['corre_index_st'].keys()), vtype=GRB.CONTINUOUS, name='X')
    Z = mo.addVars(list(range(len(P['K']))), vtype=GRB.BINARY, name='Z')
    return X, Z


# 模型目标设置函数
def set_objective(mo, X, P):
    # 销售收入
    obj = quicksum(X[i] * P['u'][i] for i in list(P['corre_index_st'].keys()))
    mo.setObjective(obj, GRB.MAXIMIZE)
    return obj


# 约束条件
def investment_limit(mo, X, P):
    mo.addConstr(quicksum(X[i] for i in list(P['corre_index_st'].keys())) == P['investment_limit'],
                 name='cons_1_investment_limit')


def possible_limit(mo, Z, P):
    mo.addConstr(quicksum(Z[i] for i in list(range(len(P['K'])))) / len(P['K']) >= P['tao'],
                 name='cons_2_possible_limit')


def auxiliary_cons(mo, X, Z, P):
    for k in range(len(P['K'])):
        # R_k --> P['K'][k]
        mo.addConstr(quicksum(X[i] * P['K'][k][i] for i in list(P['corre_index_st'].keys())) - (1 - P['alpha']) >=
                     - P['M'] * (1 - Z[k]), name=f'cons_3_possible_limit_{k}')


def add_constraints(mo, X, Z, P):
    investment_limit(mo, X, P)
    possible_limit(mo, Z, P)
    auxiliary_cons(mo, X, Z, P)


if __name__ == '__main__':
    PATH_DATA = '..\\data\\'
    # use_st_l = ['600519.SH', '600391.SH', '600232.SH', '600396.SH', '600185.SH']
    use_st_l = ['600519.SH', '600391.SH', '600232.SH', '600396.SH']
    # use_st_l = ['600519.SH', '600391.SH', '600232.SH']
    PARAMETERS, st_percent_t = construct_parameters(PATH_DATA, use_st_l)
    # 建立模型
    model = Model('model')
    # 模型初始化
    model_initial_parameter(model, PARAMETERS)
    # 添加模型变量
    X, Z = add_vars(model, PARAMETERS)
    # 设置模型求解目标
    obj = set_objective(model, X, PARAMETERS)
    # 添加模型约束
    add_constraints(model, X, Z, PARAMETERS)
    # 求解
    t_s = time.time()
    model.optimize()
    t_e = time.time()
    # 输出
    if model.Status == 3:
        print('约束冲突')
        # 输出约束冲突内容
        model.computeIIS()
        model.write('model.ilp')
    elif model.Status == 2:
        best_value = model.objVal
        print('求解结果：', obj.getValue(), t_e - t_s)
        # 输出.lp文件
        model.write('model.lp')

        # 输出求解结果
        X_x = [X[i].x for i in list(PARAMETERS['corre_index_st'].keys())]
        print(X_x)
    else:
        print('model.Status:', model.Status)
        model.write('model.lp')
