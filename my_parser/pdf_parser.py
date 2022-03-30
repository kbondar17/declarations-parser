
from collections import Counter
import requests
import re
import time
import os
import urllib.request
from typing import Union
import csv
import statistics
import pdf2docx

import pickle

import requests
import re
import time
import os
import urllib.request
from typing import Union
import csv
import statistics
import pdf2docx

import pickle

import camelot
import typing
import io
import numpy as np
from docx import Document
import matplotlib
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import pytesseract
import sys
from pdf2image import convert_from_path
import os

import pandas as pd
from pathlib import Path
# import tqdm.notebook.tqdm as tqdm
from tqdm import tqdm_notebook
import matplotlib.pyplot as plt
import logging
logging.basicConfig(format=u'%(filename)+13s [ LINE:%(lineno)-4s] %(levelname)-8s %(message)s',
                    level=logging.DEBUG)

logger = logging.getLogger(__name__)


class IncorrectHeaders:
    """класс для таблиц с неопределенными заголовками.
        1. Пытаемся найти название учреждений в объединенных ячейках.
        2. Если не получается, для учреждения берем текст, предшествующий таблице. 
    """

    # если прошелся по таблице и нашел вложения внутри - пусть это будет офис.
    # если не нашел - берем название офиса из абзацев вокруг таблиц (если их число плюс минус совпадает)

    def __init__(self):
        pass
        # TODO: добавить обработку чисто docx

        # self.docx_parser = DocxParser()
        # self.pdf_parser = PdfParser()

    @staticmethod
    def drop_col_with_N(df: pd.DataFrame):
        expr = '(№|п/п)'
        for c in df.columns:

            if re.search(expr, str(c)):
                df.drop(columns=c, inplace=True)

        return df

    @staticmethod
    def drop_short_cols(df: pd.DataFrame):
        df = df.applymap(str)
        df = df.applymap(str)
        bool_df = df.applymap(lambda x: len(x) < 4)
        to_remove = []

        columns_numbers = [x for x in range(df.shape[1])]

        for i in columns_numbers:
            col_len = len(bool_df.iloc[:, i])
            if sum(bool_df.iloc[:, i]) > col_len // 2:
                to_remove.append(i)

        if to_remove:
            for e in to_remove:
                columns_numbers.remove(e)

        return df.iloc[:, columns_numbers]

    @staticmethod
    def drop_short_headers(df: pd.DataFrame) -> pd.DataFrame:
        # ЭТО ЧУШЬ
        for i in range(3):
            cols = list(map(str, df.columns))
            cols = list(map(len, cols))
            if statistics.mean(cols) < 3 and i < 2:
                df.columns = df.iloc[0, :]
            else:
                return df

    def table_splitter(self, table: pd.DataFrame) -> tuple[bool, list[pd.DataFrame]]:
        # TODO: он не должен разделять таблицы. а просто давать деп в колонку

        def check_if_same(my_array: list) -> bool:
            '''проверяем одинаковые ли колонки'''

            if len(set(my_array)) > 1:
                return False
            return True

        def get_indexes_to_split(table):
            '''определяем индекс строки таблицы, по которому надо разделить'''

            index_to_split = []
            for e in range(len(table)):
                cols = table.iloc[e, :].values[:-1]
                if check_if_same(cols):
                    index_to_split.append(e)
            return index_to_split

            # если разделили и нашли офис - True
        def split_table(table: pd.DataFrame, index_to_split: Union[int, list[int]]) -> tuple[bool, list[pd.DataFrame]]:
            """разделяет таблицу в случае когда название учреждения поместили в середину вот так:
                -должность-  -имя-  -зарплата-
                        -ГБОУ школа 112-
                 директор     Ваня    100 руб

             """
            if not index_to_split:
                return False, table

            dfs = np.array_split(table, index_to_split)
            dfs = [e for e in dfs if len(e) > 0]
            # TODO: здесь криво определяет когда учреждение идет после заголовков сразу
            # 83334_2018

            result_dfs = []
            for df in dfs:
                office = df.iloc[0, :][0]
                df = df.iloc[1:, :]
                df['department'] = office
                result_dfs.append(df)

            result_dfs = [e for e in result_dfs if not e.empty]
            try:
                result_dfs = pd.concat(result_dfs)
                return result_dfs
            except Exception as ex:
                print(ex)
                # print('rogue file---', table)

        index_to_split = get_indexes_to_split(table.iloc[:, :-1])
        splitted_dfs = split_table(table, index_to_split)
        return {'was_split': True, 'df': splitted_dfs}

    def get_only_text_from_pdf(self, PDF_file) -> str:
        # идет сплит по \n\n

        pages = convert_from_path(PDF_file, 500)
        image_counter = 1
        for page in pages:

            filename = "page_"+str(image_counter)+".jpg"
            page.save(filename, 'JPEG')
            image_counter = image_counter + 1

        filelimit = image_counter-1
        outfile = "out_text.txt"

        f = open(outfile, "a")
        result = ''
        for i in range(1, filelimit + 1):
            filename = "page_"+str(i)+".jpg"

            text = str(
                ((pytesseract.image_to_string(Image.open(filename), lang='rus'))))
            text = text.replace('-\n', '')
            result += text

        f.close()
        result = result.split('\n\n')
        return result

    @staticmethod
    def check_if_columns_ok(cols: tuple) -> bool:
        '''проверяем, есть ли в заголовках таблицы нужная инфа'''

        cols = list(map(str, cols))
        cols = list(map(str.lower, cols))

        ok_cols = 0
        for col in cols:
            name_salary_position_pattern = '(фамилия|имя|фио|ф\.и\.о\.|ф\.и\.о|отчество|плат[ы, а]|заработная|плата|cреднемесячн[ая, ой]|зарплат[а, ной, ы]|должность)'

            res = re.search(pattern=name_salary_position_pattern, string=col)
            if res:
                ok_cols += 1

        if ok_cols > 1:
            return True

        return False

    def find_ok_cols(self, df: pd.DataFrame) -> dict['df':pd.DataFrame, 'if_ok_cols':bool]:

        cols = df.columns
       # если колонки норм, отдаем df
        if self.check_if_columns_ok(cols):
            return {'df': df, 'if_ok_cols': True}

        i = -1
        for _, row in df.iterrows():
            i += 1
            found_cols = self.check_if_columns_ok(list(row))

            if found_cols:
                df.columns = df.iloc[i, :]
                # TODO: возможно тут надо отдавать i+2
                return {'df': df.iloc[i+1:, :], 'if_ok_cols': True}

            if i > 5:
                break

        # если не ок
        return {'df': df, 'if_ok_cols': False}

    @staticmethod
    def if_office_in_cols(dfs: list[pd.DataFrame]) -> list[dict[pd.DataFrame, bool]]:

        office_pattern = '(предприяти[е,я]|учреждени[е,я]|юридическ[ие, ое]|организаци|наименование МО)'

        res = []

        if type(dfs) == pd.DataFrame:
            cols = dfs.columns

            cols = list(map(str, cols))
            cols = list(map(str.lower, cols))

            if not any([re.search(pattern=office_pattern, string=col) for col in cols]):
                res.append({'df': dfs, 'has_office': False})
            else:
                res.append({'df': dfs, 'has_office': True})

        elif type(dfs) == list:
            for df in dfs:
                cols = df.columns

                cols = list(map(str, cols))
                cols = list(map(str.lower, cols))

                if not any([re.search(pattern=office_pattern, string=col) for col in cols]):
                    res.append({'df': df, 'has_office': False})
                else:
                    res.append({'df': df, 'has_office': True})

        return res

    @staticmethod
    def get_departments_from_raw_text(raw_text: list[str]) -> list[str]:

        def check_if_headers(col_str: str) -> bool:
            pattern = '(фамилия|имя|фио|ф\.и\.о\.|ф\.и\.о|отчество|должност)'
            return bool(re.search(pattern=pattern, string=col_str))

        deps = []
        previous_is_header = False
        for i, row in enumerate(raw_text):

            if check_if_headers(row):

                if previous_is_header:
                    pass

                elif not previous_is_header:
                    previous_is_header = True
                    deps.append(raw_text[i-4:i])
            else:
                previous_is_header = False

        return deps

    def concatenate_if_possible(self, dfs: list[dict['df':pd.DataFrame, 'if_ok_cols':bool]]) -> list[pd.DataFrame]:

        all_oks = [e['if_ok_cols'] for e in dfs]

        if all(all_oks):
            return [e['df'] for e in dfs]

        result_df = []
        df_to_concat = pd.DataFrame()
        for i, df_info in enumerate(dfs):
            # df_info['df'].to_excel(f'concat_test/{i}.xlsx')

            if df_info['if_ok_cols']:
                if not df_to_concat.empty:
                    result_df.append(df_to_concat)
                df_to_concat = df_info['df']

            # оставляем только таблицы, у которых совпадает число колонок
            # с df у которых мы колонки нашли
            # если не нашли колонки и не к чему присоединять - дропаем

            # TODO: ОН СЛЕПИЛ БЕЗЫМЯННЫЕ КОЛОНКИ НАП РЕДЯДЕМ ЭТАПЕ

            elif not df_info['if_ok_cols'] and not df_to_concat.empty \
                    and len(df_to_concat.columns) == len(df_info['df'].columns):

                df_info['df'].columns = df_to_concat.columns
                df_to_concat = pd.concat([df_to_concat, df_info['df']])
                df_to_concat = df_to_concat.replace(
                    r'^\s*$', np.nan, regex=True)
                df_to_concat = df_to_concat.reset_index(
                    drop=True).fillna(method='ffill', axis=0)

        result_df.append(df_to_concat)

        return result_df
        # нумерует безымянные колонки

    @staticmethod
    def give_numbers_to_unnamed_cols(df) -> pd.DataFrame:

        def fun():
            for e in range(100, 200, 3):
                yield e

        numbers = fun()
        df.columns = [e if e else next(numbers) for e in df.columns]
        return df

    def parse(self, tables: list[pd.DataFrame], pdf_filename) -> tuple[bool, pd.DataFrame]:

        tables = [self.give_numbers_to_unnamed_cols(
            e) for e in tables]  # именуем безымянные

        # tables = [self.drop_short_headers(e) for e in tables]
        tables = [self.drop_col_with_N(e) for e in tables]
        tables = [e for e in tables if type(e) == pd.DataFrame]
        # дропаем маленькие колонки
        tables = [self.drop_short_cols(e) for e in tables]

        def sjoin(x): return ';'.join(set(x[x.notnull()].astype(str)))
        tables = [df.groupby(level=0, axis=1, sort=False).apply(
            lambda x: x.apply(sjoin, axis=1)) for df in tables]

        # # у нас тут лист словарей {df:bool}. к каждой таблице мы должны приделать True или False
        tables = [self.find_ok_cols(e) for e in tables]
        # # TODO: если нет ни одной таблицы с ок загами -> скипаем все

        at_least_one_table_ok = any([e['if_ok_cols'] for e in tables])

        if not at_least_one_table_ok:
            raise ValueError('не нашли заголовки таблиц')
            return False, []

        # теперь надо склеить таблицы, если есть таблицы с ок колонками
        # tables[0].to_excel('temp2.xlsx')
        tables = self.concatenate_if_possible(tables)
        tables = [self.drop_short_cols(e) for e in tables]

        # проверяем есть ли учреждение
        tables_with_office = self.if_office_in_cols(
            tables)  # {'df':df, 'has_office':bool}

        if all([e['has_office'] for e in tables_with_office]):
            return tables

        if not any([e['has_office'] for e in tables_with_office]):

            # сплитим таблицу
            # {'was_split':bool, 'df':df}
            splited = [self.table_splitter(tab) for tab in tables]
            for e in splited:
                if e['was_split']:
                    return [i['df'] for i in splited]

            raw_document_text = self.get_only_text_from_pdf(
                PDF_file=pdf_filename)
            deps = self.get_departments_from_raw_text(raw_document_text)

            if len(deps) - len(tables) == 1:
                deps.pop()

            if len(deps) == len(tables):
                for dep, df in zip(deps, tables):
                    df['department'] = dep

        return tables


def get_dfs_from_pkl(path): return pickle.load(open(path, 'rb'))


def save_to_pkl(data, file): pickle.dump(obj=data, file=open(file, 'wb'))


pkl_folder = r'D:\PROGR\LEARN_PYTHON\Declarator\declarations-parser'
pdf_folder = r'D:\PROGR\LEARN_PYTHON\Declarator\declarations-parser\data_ids\pdf\converted'
result_folder = r'D:\PROGR\LEARN_PYTHON\Declarator\declarations-parser\data_ids\pdf\converted\second_parsed_from_pickle'
incor_parser = IncorrectHeaders()
file = r'83304_2018_Rukovoditeli,_zamestiteli_i_glavnye_bukhgaltery_podvedomstvennykh_uchrezhdenii.pdf.pkl'

path = pkl_folder + '\\' + file
tables = get_dfs_from_pkl(path)
# print(len(tables))
# print(type(tables[0]))
# print(tables[0])
# for i, t in enumerate(tables):
#     t.to_excel(f'{i}.xlsx')
res = incor_parser.parse(tables=tables[:3], pdf_filename='')
for i, e in enumerate(res):
    e.to_excel(f'{i}_temp_res.xlsx')
res = incor_parser.parse
errors = []
res = incor_parser.parse(tables, '')
# res


# for file in  tqdm_notebook(os.listdir(pkl_folder)):
#     if file.endswith('pkl'):
#         try:
#             pdf_file = file.strip('.pkl')
#             tables = get_dfs_from_pkl(pkl_folder + '\\' + file)
#             res = incor_parser.parse(tables=tables, pdf_filename=pdf_file)
#             save_to_pkl(res, result_folder + '//' + file)

#         except Exception as ex:
#             errors.append({'file':file, 'err':ex})
#             #save_to_pkl(tables, result_folder + '//' + file)


# file = r"D:\PROGR\LEARN_PYTHON\Declarator\declarations-parser\85445_2018_Rukovoditeli,_zamestiteli_i_glavnye_bukhgaltery_podvedomstvennykh_uchrezhdenii.PDF.pkl"


# РАБОТАЮЩИЙ ПАРСИНГ
# folder = r'D:\PROGR\LEARN_PYTHON\Declarator\declarations-parser'
# files = [e for e in os.listdir(folder) if e.endswith('pkl')]
# result_folder = r'D:\PROGR\LEARN_PYTHON\Declarator\declarations-parser\data_ids\pdf\converted\parsed_pdf_ok_not_cleaned'
# pdf_folder = r'D:\PROGR\LEARN_PYTHON\Declarator\declarations-parser\data_ids\pdf\converted'

# result = []
# not_list = []
# for file in tqdm_notebook(files):
#     try:
#         pdf_file = pdf_folder + '\\' + file.strip('.pkl')
#         tables = get_dfs_from_pkl(folder + '\\' + file)
#         tables = incor_parser.parse(tables, pdf_filename=pdf_file)

#         if type(tables) == list:
#             for i, tab in enumerate(tables):
#                 file_id = '_'.join(file.split('_')[:2])
#                 tab.to_excel(result_folder + '\\' +
#                              f'{i}_' + file_id + '.xlsx')

#     except Exception as ex:
#         not_list.append({'file': file, 'ex': ex})


# with open('exceptions.pkl', 'wb') as f:
#     pickle.dump(not_list, f)
