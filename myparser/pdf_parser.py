import re
import statistics
from pathlib import Path
import os

import camelot
import numpy as np
import pandas as pd
import pytesseract
from pdf2image import convert_from_path
from PIL import Image

from myparser.my_logger import get_logger
from myparser.config import config

logger = get_logger(__name__)

pytesseract.pytesseract.tesseract_cmd = config['tesseract_location']

class PdfParser:
 
    @staticmethod
    def convert_pdf_to_df(filename) -> list[pd.DataFrame]:
        tables = camelot.read_pdf(str(filename), line_tol=2, joint_tol=10, line_scale=40, copy_text=[
                                  'v', 'h'], pages='1-end', suppress_stdout=False) 
        tables = [e.df for e in tables]
        logger.debug('Нашли в документе таблиц: %s', len(tables))
        
        return tables

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

    def find_and_split_departments(self, df: pd.DataFrame) -> pd.DataFrame:
        """
            разделяет таблицу в случае когда название учреждения поместили в середину вот так:
                -должность-  -имя-  -зарплата-
                        -ГБОУ школа 112-
                    директор     Ваня    100 руб
        """

        def _add_department_info_to_df(df: pd.DataFrame, dep_info: list[dict[int, str]]) -> pd.DataFrame:
            df['department'] = None
            for data in dep_info:
                df.at[data['index'], 'department'] = data['dep']
            df = df.dropna(axis=1, how='all').fillna(method='ffill', axis=0)
            return df

        def _find_department_in_table(df: pd.DataFrame) -> list[dict[int, str]]:
            # [index, department]
            departments_n_indexes = []
            for row in df.itertuples():
                index = row[0]
                row = list(row)[1:-1]
                row = [e for e in row if len(str(e)) > 4]
                if len(set(row)) < 2:
                    if not all([type(e) in [int, float] for e in row]):
                        if statistics.mean([len(e) for e in row]) > 4:
                            departments_n_indexes.append(
                                {'index': index, 'dep': row[0]})
            return departments_n_indexes

        dep_info = _find_department_in_table(df)

        if not dep_info:
            return df

        df = _add_department_info_to_df(df, dep_info)
        return df


    def get_only_text_from_pdf(self, PDF_file) -> str:
        # берем из пдф только текст

        pages = convert_from_path(PDF_file, 500)
        image_counter = 1
        for page in pages:

            filename = "page_"+str(image_counter)+".jpg"
            page.save(filename, 'JPEG')
            image_counter = image_counter + 1

        filelimit = image_counter-1

        result = ''
        for i in range(1, filelimit + 1):
            filename = "page_"+str(i)+".jpg"

            text = str(
                ((pytesseract.image_to_string(Image.open(filename), lang='rus'))))
            text = text.replace('-\n', '')
            result += text
            os.remove(filename)

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
        
    @staticmethod
    def give_numbers_to_unnamed_cols(df) -> pd.DataFrame:
    # нумерует безымянные колонки

        def fun():
            for e in range(100, 200, 3):
                yield e

        numbers = fun()
        df.columns = [e if e else next(numbers) for e in df.columns]
        return df

    @staticmethod
    def add_file_info(dfs: list[pd.DataFrame], filepath: str) -> list[pd.DataFrame]:
        file = Path(filepath).name
        file_id = file.split('_')[0]
        logger.debug('Нашли в имени файла айди -- %s', file_id)
        for df in dfs:
            df['documentfile_id'] = file_id

        return dfs


    def parse(self, pdf_filename) -> list[pd.DataFrame]:
        
        dfs = self.convert_pdf_to_df(pdf_filename)

        dfs = [self.give_numbers_to_unnamed_cols(
            e) for e in dfs]  # именуем безымянные

       # дропаем маленькие колонки
        dfs = [self.drop_col_with_N(e) for e in dfs]
        dfs = [e for e in dfs  if type(e) == pd.DataFrame]
        dfs = [self.drop_short_cols(e) for e in dfs]

        def sjoin(x): return ';'.join(set(x[x.notnull()].astype(str)))
        dfs = [df.groupby(level=0, axis=1, sort=False).apply(
            lambda x: x.apply(sjoin, axis=1)) for df in dfs]

        # у каждой таблицы ищем заголовки. {'df':pd.Dataframe, 'if_ok_cols':bool}
        dfs = [self.find_ok_cols(e) for e in dfs]
        
        at_least_one_table_ok = any([e['if_ok_cols'] for e in dfs])

        if not at_least_one_table_ok: # не нашли заголовки - скпипаем
            raise ValueError('не нашли заголовки таблиц')

        # если таблицы разбиты на несколько страниц - склеиваем
        dfs = self.concatenate_if_possible(dfs)
        dfs = [self.drop_short_cols(e) for e in dfs]

        # проверяем есть ли учреждение {'df':df, 'has_office':bool}
        dfs_with_office = self.if_office_in_cols(
            dfs) 

        if all([e['has_office'] for e in dfs_with_office]):
            # если у всех есть учреждение - отдаем
            dfs = self.add_file_info(dfs, pdf_filename)
            return dfs

        if not any([e['has_office'] for e in dfs_with_office]):
            
            # если нет учреждения - идем искать в тело таблицы  
            dfs = [self.find_and_split_departments(df) for df in dfs]

            # если учреждений больше, чем у половины таблиц, то отдаем
            how_many_dfs_with_departments = sum(
                [1 for df in dfs if 'department' in df.columns])
            if how_many_dfs_with_departments > len(dfs) // 2:
                logger.debug('нашли заголовки таблиц')
                dfs = self.add_file_info(dfs=dfs, filepath=pdf_filename)
                return dfs

            # если учреждения все еще нет - переводим PDF в текст
            # и берем в качестве учреждения текст перед таблицей.
            raw_document_text = self.get_only_text_from_pdf(
                PDF_file=pdf_filename)
            deps = self.get_departments_from_raw_text(raw_document_text)

            if len(deps) - len(dfs) == 1:
                deps.pop()
            if len(deps) == len(dfs):
                for dep, df in zip(deps, dfs):
                    df['department'] = dep
        
        dfs = self.add_file_info(dfs, pdf_filename)
        return dfs
