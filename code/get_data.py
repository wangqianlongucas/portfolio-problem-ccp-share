# -*- coding: utf-8 -*-

# @Time : 2022/5/10 20:21
# @Author : wangqianlong
# @Email : 1763423314@qq.com
# @File : get_data.py


import tushare as ts
import pandas as pd


def get_data_by_tushare(ts_pro, st_list, start_date, end_date, path_data):
    start_year = int(start_date[:4])
    end_year = int(end_date[:4])
    date = int(start_date[4:])
    # change percent / year
    percent_data = {}
    for st_code in st_list:
        # 获取数据  st_code = 600000 + .SH
        st_df = ts_pro.daily(ts_code=st_code, start_date=start_date, end_date=end_date)
        # 输出数据
        path_csv = f'{path_data}{st_code[:-3]}.csv'
        st_df.set_index(keys=['trade_date'], inplace=True)
        st_df.to_csv(path_csv)
        percent_data[st_code] = []
        for year in range(start_year, end_year):
            st_date = date
            while True:
                if str(year) + '0' + str(st_date) in st_df.index.values:
                    before_year_index = st_df.loc[str(year) + '0' + str(st_date), 'close']
                    break
                else:
                    st_date += 1
            st_date = date
            while True:
                if str(year + 1) + '0' + str(st_date) in st_df.index.values:
                    now_year_index = st_df.loc[str(year + 1) + '0' + str(st_date), 'close']
                    break
                else:
                    st_date += 1
            # percent_year = (now_year_index - before_year_index) / before_year_index
            percent_year = now_year_index / before_year_index
            percent_data[st_code].append(percent_year)

    percent = pd.DataFrame(percent_data, index=list(range(start_year, end_year)))
    return percent


if __name__ == '__main__':
    # 初始化
    MY_TOKEN = '****'
    PATH_DATA = '..//data//'
    TS_PRO = ts.pro_api(MY_TOKEN)
    # 读取股票列表
    with open(PATH_DATA + 'ST_LIST.txt', 'r') as f:
        lines = f.readlines()
        START_DATE, END_DATE = lines[1][:-1], lines[2][:-1]
        ST_list = [line[:-1] for line in lines[4:]]
    # 输出文件: row_index: 时间 (年为单位, 五月开盘的第一天）, col_index : st_list, 值: 变化率
    st_percent = get_data_by_tushare(TS_PRO, ST_list, START_DATE, END_DATE, PATH_DATA)

    st_percent.to_csv(f'{PATH_DATA}st_percent.csv')

