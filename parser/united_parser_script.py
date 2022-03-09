# %%

import camelot
import requests
import re
import time
import os
import urllib.request
from typing import Union
import csv
import statistics

import typing
import io
import numpy as np
from docx import Document
import matplotlib
import numpy as np
import matplotlib.pyplot as plt

import pandas as pd
from pathlib import Path
# import tqdm.notebook.tqdm as tqdm
from tqdm import tqdm_notebook
import matplotlib.pyplot as plt
import logging
logging.basicConfig(format=u'%(filename)+13s [ LINE:%(lineno)-4s] %(levelname)-8s %(message)s',
                    level=logging.DEBUG)

logger = logging.getLogger(__name__)


# %%


# tables = camelot.read_pdf(file, line_tol=2, joint_tol=10, line_scale=40, copy_text=['v'], pages='1-end') # , flavor='stream' row_tol=10


# split_text , strip_text  line_tol=2, joint_tol=2, line_scale=15

# tables[8].df


# КОРОЧЕ ЮЗАЕМ КАМЕЛОТ (мб предлагать юзеру настройки распознавания)

# res = []
# for e in tables:
#     res.append(e.df)

# df = pd.concat(res)
# df.to_excel('camelot_test.xlsx')


# len(tables)
# tables[1].df
# df = tables[2].df
# camelot.plot(tables[0], kind='joint')
# df

# tables[0].parsing_report

# tables[0].to_csv('foo.csv') # to_json, to_excel,   down, to_sqlite
# tables[0].df # get a pandas DataFrame!

class PdfParser:

    @staticmethod
    def convert_pdf_to_df(filename) -> list[pd.DataFrame]:
        tables = camelot.read_pdf(filename, line_tol=2, joint_tol=10, line_scale=40, copy_text=[
                                  'v'], pages='1-end')  # , flavor='stream' row_tol=10
        tables = [e.df for e in tables]
        return tables


# base = 'data_idus/pdf/converted/'
# file = '189273_2020_Rektor,_prorektory,_glavnyi_bukhgalter.pdf'
file = "D:/PROGR/LEARN_PYTHON/Declarator/declarations-parser/data_ids/pdf/converted/90569_2018_Rukovoditeli,_zamestiteli_i_glavnye_bukhgaltery_podvedomstvennykh_uchrezhdenii.pdf"
# par = PdfParser()
# res = par.convert_pdf_to_df(file)
# res


# %%

class CorrectHeadersParser:

    '''класс для парсинга таблиц, у которых на месте колонки, которые нам нужны'''

    def table_splitter(self, table: pd.DataFrame) -> list[pd.DataFrame]:
        '''разделяет таблицы, в которых учреждение указано внутри таблицы'''

        def check_if_same(my_array: list) -> bool:
            '''проверяем одинаковые ли колонки'''

            if len(set(my_array)) > 1:
                return False
            return True

            # first = my_array[0]
            # for e in my_array[1:]:
            #     if e != first:
            #         return False
            # return True

        def get_indexes_to_split(table):
            index_to_split = []
            for e in range(len(table)):
                cols = table.iloc[e, :].values
                if check_if_same(cols):
                    index_to_split.append(e)
            return index_to_split

        def split_table(table: pd.DataFrame, index_to_split: Union[int, list[int]], file_name) -> list[pd.DataFrame]:
            """разделяет таблицу в случае когда название учреждения поместили в середину

                -должность-  -имя-  -зарплата-
                        -ГБОУ школа 112-
                директор     Ваня    100 руб

             """
            dfs = np.array_split(table, index_to_split)
            dfs = [e for e in dfs if len(e) > 0]

            result_dfs = []
            for df in dfs:
                office = df.iloc[0, :][0]
                df = df.iloc[1:, :]
                df['office'] = office
                result_dfs.append(df)

            result_dfs = [e for e in result_dfs if not e.empty]
            try:
                result_dfs = pd.concat(result_dfs)
                return result_dfs
            except Exception as ex:
                print(ex)
                print('rogue file---', table)

        index_to_split = get_indexes_to_split(table)

        if not index_to_split:
            return table

        splitted_dfs = split_table(table, index_to_split)
        return splitted_dfs

    def concat_name(self, df: pd.DataFrame) -> pd.DataFrame:
        '''соединяем колонки ФИО, если они в разных'''

        if 'name' not in df.columns:
            return df

        names_df = df['name']

        if isinstance(names_df, str) or isinstance(names_df, pd.Series):
            return df

        # TODO:
        # дропнуть маленькую колонку

        names = [' '.join(e) for e in names_df.values]

        df.drop(columns=['name'], inplace=True)
        df['name'] = names
        return df

    def parse(self, table: pd.DataFrame) -> pd.DataFrame:
        table = self.concat_name(table)
        table = self.table_splitter(table)
        return table


# %%


class DataCleaner:
    """убирает лишние данные"""

    @staticmethod
    def remove_unwanted_symbols(df):
        # TODO: чистка всех колонок
        df = df.applymap(lambda x: str(x).replace('\n', ' '))
        return df

    @staticmethod
    def remove_unwanted_cells(df):
        # убирает ячейки с нумерацией
        # print('--- DataCleaner.remove_unwanted_cells ---', df.columns)
        df = df[~df['position'].astype(str).str.isdigit()]
        return df

    @staticmethod
    def remove_short_rows(df):
        # удаляет ряды с недостаточными данными
        # ! должно применяться после выбора норм колонок
        to_remove = []
        for tup in df.itertuples():
            res = [len(str(e)) for e in tup]
            if statistics.mean(res) < 5:
                to_remove.append(tup.Index)

        df.drop(to_remove, inplace=True)
        return df

    def clean_df(self, df):
        df = self.remove_unwanted_symbols(df)
        df = self.remove_unwanted_cells(df)

        df = self.remove_short_rows(df)
        # print('!!!',df)

        return df


# %%


class DocxParser:

    def get_docx_tables(self, filename, tab_id=None, **kwargs) -> list[pd.DataFrame]:
        """
            filename:   file name of a Word Document
            tab_id:     parse a single table with the index: [tab_id] (counting from 0).
                        When [None] - return a list of DataFrames (parse all tables)
        """
        def read_docx_tab(tab, **kwargs):
            vf = io.StringIO()
            writer = csv.writer(vf)
            for row in tab.rows:
                writer.writerow(cell.text for cell in row.cells)
            vf.seek(0)
            return pd.read_csv(vf, **kwargs)

        doc = Document(filename)
        if tab_id is None:
            return [read_docx_tab(tab, **kwargs) for tab in doc.tables]
        else:
            try:
                return read_docx_tab(doc.tables[tab_id], **kwargs)
            except IndexError:
                print(
                    'Error: specified [tab_id]: {}  does not exist.'.format(tab_id))
                raise

    def convert_docx_to_df(self, filename: str) -> pd.DataFrame:
        assert filename.endswith('docx'), 'Формат должен быть .docx!'

        doc = Document(filename)
        # TODO: тут взять текст, который потом прикрутить к

        doc_tables = self.get_docx_tables(filename)

        return doc_tables


# %%
class Parser:

    def __init__(self):
        self.cols_we_need = ['name', 'salary', 'position', 'department']
        self.all_docs: list[str]

        self.docx_parser = DocxParser()
        self.pdf_parser = PdfParser()

        self.parse_correct_headers = CorrectHeadersParser()
        self.parse_incorrect_headers = ''

        self.data_cleaner = DataCleaner()

    @staticmethod
    def rename_col(col: str) -> str:

        print('col before rename cols --', col)
        col = col.lower()
        if re.search(pattern='(фамилия|имя|фио|ф\.и\.о\.|ф\.и\.о|отчество)', string=col):
            return "name"

        elif re.search(pattern='(cреднемесячная|зарпл.|плат[ы, а]|заработн[ой, ая] плат[а, ы]|cреднемесячн[ая, ой]|зарплат[а, ной, ы])', string=col):
            return "salary"

        elif re.search(pattern='(должност[ь, и, ей])', string=col):

            return 'position'

        elif re.search(pattern='(предприяти[е,я]|учреждени[е,я]|юридическое лицо)', string=col):
            return 'department'

        return col

    @staticmethod
    def check_if_columns_ok(cols: tuple) -> bool:
        '''проверяем, есть ли в заголовках таблицы название предприятия и другая инфа'''

        cols = list(map(str, cols))
        cols = list(map(str.lower, cols))
        print('зашли в проверку колонок ---', cols)
        ok_cols = 0
        company_found = False
        for col in cols:
            company_pattern = '(предприяти[е,я]|учреждени[е,я]|юридическ[ое,ие])'
            res = re.search(pattern=company_pattern, string=col)
            if res:
                company_found = True
                continue

            name_salary_position_pattern = '(фамилия|имя|фио|ф\.и\.о\.|ф\.и\.о|отчество|плат[ы, а]|заработная|плата|cреднемесячн[ая, ой]|зарплат[а, ной, ы]|должность|)'

            res = re.search(pattern=name_salary_position_pattern, string=col)
            if res:
                ok_cols += 1

        if company_found and ok_cols > 1:
            return True
        return False

    def parse_folder(self, file_path, destination_path):
        for file in os.listdir(file_path):
            try:
                df = self.parse_file(file_path)
                df.to_excel(destination_path + file_path)
            except Exception as ex:
                print(file_path)
                print(ex)
                print('===')

    def parse_file(self, file: str):
        if file.endswith('.pdf'):
            tables = self.pdf_parser.convert_pdf_to_df(file)

        elif file.endswith('docx'):
            tables = self.docx_parser.convert_docx_to_df(file)

        else:
            logger.error('Допустимы расширения: pdf, docx')

        parsed_tables = []
        for table in tables:

            columns_ok = self.check_if_columns_ok(table)
            if not columns_ok:
                # пометить?
                # если учреждения нет - смотрим параграфы.
                # пытаемся найти заголовки, если находим - идем дальше, если нет - дропаем и метим как непаршеный

                pass

            else:
                # если заголовки ок, оставляем только нужные

                table.columns = [self.rename_col(col) for col in table.columns]

                cols_to_leave = [
                    col for col in table.columns if col in self.cols_we_need]
                cols_to_leave = set(cols_to_leave)
                table = table[cols_to_leave]
                # проверяем на наличие вложенных таблиц и фио, разнесенных на несколько стаоблцов
                table = self.parse_correct_headers.parse(table)
                # убираем лишние ячейки и символы
                table = self.data_cleaner.clean_df(table)
                parsed_tables.append(table)
               # print('!!!!',table)

        if isinstance(parsed_tables, list):
            if parsed_tables:
                concat_tables = pd.concat(parsed_tables)
                return concat_tables

        elif isinstance(parsed_tables, pd.DataFrame):
            if not parsed_tables.empty:
                return concat_tables


base = 'data_ids/pdf/converted/'
file = '189273_2020_Rektor,_prorektory,_glavnyi_bukhgalter.pdf'


def convert_pdf_to_df(filename) -> list[pd.DataFrame]:
    tables = camelot.read_pdf(file, line_tol=2, joint_tol=10, line_scale=40, copy_text=[
                              'v'], pages='1-end')  # , flavor='stream' row_tol=10
    tables = [e.df for e in tables]
    return tables


#file = 'data_ids/pdf/converted/189273_2020_Rektor,_prorektory,_glavnyi_bukhgalter.pdf'
file = "D:\PROGR\LEARN_PYTHON\Declarator\declarations-parser\data_ids\docx\83310_2016_Rukovoditeli,_zamestiteli_i_glavnye_bukhgaltery_podvedomstvennykh_uchrezhdenii.docx"
file = r"D:\PROGR\LEARN_PYTHON\Declarator\declarations-parser\data_ids\docx\102907_2019_Rukovoditeli_podvedomstvennykh_uchrezhdenii_(kul'tura).docx"
file = r"D:\PROGR\LEARN_PYTHON\Declarator\declarations-parser\data_ids\pdf\83325_2018_Rukovoditeli,_zamestiteli_i_glavnye_bukhgaltery_podvedomstvennykh_uchrezhdenii.pdf"
# convert_pdf_to_df(file)


def convert_pdf_to_df(filename) -> list[pd.DataFrame]:
    tables = camelot.read_pdf(filename, line_tol=2, joint_tol=10, line_scale=40, copy_text=[
                              'v'], pages='1-end')  # , flavor='stream' row_tol=10
    tables = [e.df for e in tables]
    return tables


# print(convert_pdf_to_df(file)[0].columns)
for i, e in enumerate(convert_pdf_to_df(file)):
    try:
        e.to_excel(f'test_{i}.xlsx')
    except Exception as ex:
        print(ex)

# parser = Parser()
# res = parser.parse_file(file)
# print(res)

# %%
# ДОСОБИРАТЬ ПАРСЕР В ОДНО ЦЕЛОЕ
# ПОФЕЙКАТЬ ПДФ
# ПДФ БУДЕТ РАБОТАТЬ ТОЛЬКО В .PY
