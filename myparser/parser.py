
import logging
import os
import typing
import json
from pathlib import Path

from myparser.data_cleaner import DataCleaner
from myparser.docx_parser import DocxParser
from myparser.utils import convert_df_to_json
from tqdm import tqdm

from myparser.config import get_logger

logger = get_logger(__name__)


class Parser:

    def __init__(self) -> None:
        self.pdf_parser = ''
        self.excel_parser = ''
        self.docx_parser = DocxParser()
        self.data_cleaner = DataCleaner()

    def parse_file(self, file: str, out_format='xlsx', destination_folder='parsing_results') -> None:

        if file.split('.')[-1] not in ['docx', 'xlsx', 'pdf']:
            raise ValueError('Допустимые форматы: .docx, .xlsx, .pdf')

        if file.endswith('.xlsx'):
            dfs = self.excel_parser(file)

        elif file.endswith('.docx'):
            dfs = self.docx_parser.parse_file(file)

        elif file.endswith('.pdf'):
            dfs = self.pdf_parser(file)

        dfs = [self.data_cleaner.clean_df(df) for df in dfs]

        destination_folder = Path(destination_folder)
        new_file_name = Path(file).stem

        try:
            os.mkdir(destination_folder)
            logger.debug('создали папку "parsing_results". сохраняем в нее')
        except FileExistsError:
            logger.debug('папка "parsing_results" уже есть. сохраняем в нее')

        if out_format == 'xlsx':
            for i, df in enumerate(dfs):
                new_file_name += '.xlsx'
                new_file_name = f'{i}_' + new_file_name
                new_file_path = destination_folder / new_file_name
                df.to_excel(new_file_path, index=False)

            logger.debug('Из файла %s выгружено таблиц: %s', file, i+1)

        elif out_format == 'json':
            my_json = [convert_df_to_json(df) for df in dfs]
            for i, table in enumerate(my_json):
                new_file_name = f'{i}_' + Path(file).stem + '.csv'
                with open(destination_folder / new_file_name) as f:
                    json.dump(table, f)

            logger.debug('Из файла %s выгружено таблиц: %s', file, i+1)

    def parse_folder(self, folder):
        pass
