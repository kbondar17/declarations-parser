import pandas as pd
import re
from myparser.config import get_logger

logger = get_logger(__name__)


class DataCleaner:
    
    """убирает лишние данные, конвертирует зарплату."""

    def __init__(self):
        self.cols_we_need = ['department', 'page',  'name',	'position',
                             'salary', 'sheet_name', 'raw_salary', 'documentfile_id']

    @staticmethod
    def rename_col(col: str) -> str:

        col = str(col).lower()
        if re.search(pattern='(фамилия|имя|фио|ф\.и\.о\.|ф\.и\.о|отчество)', string=col):
            return "name"

        elif re.search(pattern='(рублей|руб|cреднемесячная|зарпл.|плат[ы, а]|заработн[ой, ая] плат[а, ы]|cреднемесячн[ая, ой]|зарплат[а, ной, ы])', string=col):
            return "salary"

        elif re.search(pattern='(должност)', string=col):
            return 'position'

        elif re.search(pattern='(предприяти[е,я]|учреждени[е,я]|юридическ|организаци)', string=col):
            return 'department'

        return col

    @staticmethod
    def remove_unwanted_symbols(df):
        # TODO: чистка всех колонок
        df = df.applymap(lambda x: str(x).replace('\n', ' '))
        df = df.applymap(lambda x: ' '.join(str(x).split()))

        return df

    @staticmethod
    def remove_unwanted_rows(df: pd.DataFrame):
        headers_pattern = '(фамилия|имя|фио|ф\.и\.о\.|ф\.и\.о|отчество|\
                рублей|руб|cреднемесячная|зарпл.|плат[ы, а, е]|заработн[ой, ая]|плат[е, а, ы]|\
                    cреднемесячн[ая, ой]|зарплат[а, е, ной, ы]|должност|предприяти[е,я]|учреждени[е,я]|юридическое лицо)'

        to_delete = []
        temp_df = df.copy()
        temp_df = temp_df.applymap(lambda x: str(x).lower())

        for row in temp_df.itertuples():
            index = row[0]
            # удаляем если:
            # в ряду только цифы цифры
            try:
                if str(row.name).replace(' ', '').isdigit() and str(row.position).replace(' ', '').isdigit():
                    to_delete.append(index)
                    continue
            except:
                pass

            # ряд состоит из заголовков
            row = row[1:]
            headers_in_row = sum(
                [bool(re.search(pattern=headers_pattern, string=str(e))) for e in list(row)])
            if headers_in_row > 1:
                to_delete.append(index)
                continue
            # если в ряду много повторов

            row = [e for e in row if e]
            if len(set(row)) <= len(row) // 2:
                to_delete.append(index)
                continue

        logger.debug('Посчитали неподходящими и удаляем эти ряды: %s',
                     df.iloc[to_delete, :].values)
        df.drop(index=to_delete, axis=1, inplace=True)

        return df

    @staticmethod
    def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
        if 'name' in df.columns and 'salary' in df.columns:
            df.drop_duplicates(subset=['name', 'salary'], inplace=True)
        return df

    @staticmethod
    def concat_same_cols(df: pd.DataFrame):
        def sjoin(x): return ' '.join(x[x.notnull()].astype(str))
        return df.groupby(level=0, axis=1).apply(lambda x: x.apply(sjoin, axis=1))

    @staticmethod
    def salary_parser(salary: str) -> int:
        if not salary:
            return 0

        salary = str(salary)
        salary = salary.split(',')[0]
        salary = salary.split('.')[0]
        salary = salary.replace(' ', '')
        salary = ''.join([c for c in salary if c.isdigit()])

        if salary.isalnum():
            return int(salary) * 12

        return salary

    @staticmethod
    def get_numeric_salary(df: pd.DataFrame):
        # иногда в salary попадают колонки с описанием

        cols = list(df.columns)
        if cols.count('salary') <= 1:
            return df

        def drop_not_numeric_salary(df) -> int:
            # берем только salary где большая часть - цифры

            max_val = 0
            realy_salary_col = 0
            for i in range(len(df.columns)):

                num_of_numeric_vals = sum(df.iloc[:, i].values)
                if num_of_numeric_vals > max_val:
                    realy_salary_col = i

            return realy_salary_col

        salary_subset = df['salary'].copy()
        if type(salary_subset) == pd.DataFrame:
            bool_salary_subset = salary_subset.applymap(
                lambda x: str(x).isdigit())
        elif type(salary_subset) == pd.Series:
            bool_salary_subset = salary_subset.apply(
                lambda x: str(x).isdigit())

        salary_col = drop_not_numeric_salary(bool_salary_subset)
        salary_subset = salary_subset.iloc[:, salary_col]
        df['salary'].drop(columns=['salary'], inplace=True)
        df.reset_index(inplace=True, drop=True)
        salary_subset.reset_index(inplace=True, drop=True)
        df['salary'] = salary_subset
        df = df.T.groupby(level=0).first().T  # удалили дубликаты

        return df

    def clean_df(self, df:pd.DataFrame):
        
        df.columns = [self.rename_col(col) for col in df.columns]
        df = df[[col for col in df.columns if col in self.cols_we_need]]

        df = self.remove_unwanted_symbols(df)

        df = self.get_numeric_salary(df)
        if 'salary' in df.columns:
            df['salary_raw'] = df['salary'].copy()
            df['salary'] = df['salary'].apply(self.salary_parser)

        df = self.remove_unwanted_rows(df)

        return df
