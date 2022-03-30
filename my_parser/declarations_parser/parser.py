
import logging
import os
import typing

from my_parser.declarations_parser.data_cleaner import DataCleaner
from my_parser.declarations_parser.docx_parser import DocxParser
from tqdm import tqdm

logging.basicConfig(format=u'%(filename)+13s [ LINE:%(lineno)-4s] %(levelname)-8s %(message)s',
                    level=logging.DEBUG)

logger = logging.getLogger(__name__)


class Parser:

    def __init__(self) -> None:
        self.pdf_parser = ''
        self.excel_parser = ''
        self.docx_parser = DocxParser()
        self.data_cleaner = DataCleaner()

    def parse_file(self, file: str, out_format='xlsx') -> None:

        if file.split('.')[-1] not in ['docx', 'xlsx', 'pdf']:
            raise ValueError('Допустимые форматы: .docx, .xlsx, .pdf')

        if file.endswith('.xlsx'):
            dfs = self.excel_parser(file)

        elif file.endswith('.docx'):
            dfs = self.docx_parser.parse_file(file)

        elif file.endswith('.pdf'):
            dfs = self.pdf_parser(file)

        dfs = [self.data_cleaner.clean_df(df) for df in dfs]

        try:
            os.mkdir('parsing_results')
        except FileExistsError:
            pass

        if out_format == 'xslx':
            dfs[0].to_excel('parsing_results/res_cleaned.xlsx')
            print(f'Из файла {file} выгружено сколько-то таблиц')

        elif out_format == 'json':
            pass

    def parse_folder(self, folder):
        pass
