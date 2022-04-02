
import os
import json
from pathlib import Path

from myparser.data_cleaner import DataCleaner
from myparser.docx_parser import DocxParser
from myparser.excel_parser import ExcelParser
from myparser.pdf_parser import PdfParser
from myparser.utils import convert_df_to_json


from myparser.my_logger import get_logger

logger = get_logger(__name__)


class Parser:

    def __init__(self) -> None:
        self.pdf_parser = PdfParser()
        self.excel_parser = ExcelParser()
        self.docx_parser = DocxParser()
        self.data_cleaner = DataCleaner()

    def parse_file(self, file: str, out_format='xlsx', destination_folder='parsing_results') -> None:

        if file.split('.')[-1] not in ['docx', 'xlsx', 'pdf']:
            raise ValueError('Допустимые форматы: .docx, .xlsx, .pdf')

        if file.endswith('.xlsx'):
            dfs = self.excel_parser.parse_file(Path(file))

        elif file.endswith('.docx'):
            dfs = self.docx_parser.parse_file(file)

        elif file.endswith('.pdf'):
            dfs = self.pdf_parser.parse(file)

        dfs = [self.data_cleaner.clean_df(df) for df in dfs]

        destination_folder = Path(destination_folder)
        new_filename = Path(file).stem

        try:
            os.mkdir(destination_folder)
            logger.debug('создали папку "parsing_results". сохраняем в нее')
        except FileExistsError:
            logger.debug('папка "parsing_results" уже есть. сохраняем в нее')

        if out_format == 'xlsx':
            new_filename += '.xlsx'
            for i, df in enumerate(dfs):
                new_filename_with_number = f'{i}_' + new_filename
                new_file_path = destination_folder / new_filename_with_number
                df.to_excel(new_file_path, index=False)

            logger.debug('Из файла %s выгружено таблиц: %s', file, i+1)

        elif out_format == 'json':
            my_json = [convert_df_to_json(df) for df in dfs]
            for i, table in enumerate(my_json):
                new_file_name = f'{i}_' + Path(file).stem + '.json'
                with open(destination_folder / new_file_name, 'w') as f:
                    json.dump(table, f)

            logger.debug('Из файла %s выгружено таблиц: %s', file, i+1)

 