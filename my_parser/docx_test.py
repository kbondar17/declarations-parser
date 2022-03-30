import pandas as pd
from docx2python import docx2python
import re
from pathlib import Path
import typing
import pdf2docx


class Parser:

    def convert_pdf_to_docx_to_find_info(self, filename: Path) -> Path:
        # переводим пфд в ворд
        assert str(filename).endswith('.pdf'), 'Файл должен быть в PDF !'
        folder = filename.parents[0]

        orig_file_name = filename.name.strip('.pdf')
        new_name = 'temp_to_delete_' + orig_file_name + '.docx'

        pdf2docx.parse(str(filename), str(folder / new_name))
        return folder / new_name

    def detect_headers_in_raw_doc(self, filename, parsed_tables: list[pd.DataFrame]) -> list[pd.DataFrame]:

        def get_headers(filename: str) -> list[str]:  # filename:docx

            doc = docx2python(filename)

            table_pattern = '(фамилия|имя|фио|ф\.и\.о\.|ф\.и\.о|отчество|должность)'

            offices = []
            gathering_office_info = ''

            for paragraph in doc.body_runs:  # параграфы в виде вложенных листов

                paragraph = sum(sum(paragraph, []), [])
                paragraph_text = ''
                for e in paragraph:
                    try:
                        paragraph_text += ' ' + e[0] + ' '
                    except IndexError:
                        pass

                paragraph_text = paragraph_text.lower()
                its_table = re.findall(
                    pattern=table_pattern, string=paragraph_text)

                if not its_table:
                    gathering_office_info += paragraph_text

                elif its_table:
                    offices.append(gathering_office_info)
                    gathering_office_info = ''
            print('ы')
            return [e for e in offices if e]

        def compile_office_info_and_df(filename: Path, departments: list, tables: list[pd.DataFrame]) -> typing.Union[None, list[pd.DataFrame]]:
            # все правильно. логика такая, что камелотом лучше парсить!
            # а док только для загов таблиц

            # tables = self.convert_pdf_to_dfs(filename)

            ok_dfs = []

            print('Количество заголовков --- ', len(departments))
            print('Количество таблиц --- ', len(tables))

            if len(departments) - len(tables) == 1:
                departments.pop()

            if len(departments) == len(tables):
                for table, dep in zip(tables, departments):
                    table['Учреждение'] = dep
                    table['Учреждение'][0] = 'Учреждение'

                    ok_dfs.append(table)

                return ok_dfs

            with open(str(filename) + '.txt', 'w') as f:
                text = f'Разное число таблиц ({len(tables)}) и учреждений ({len(departments)})'
                f.write(text)

            raise ValueError(
                f'Разное число таблиц ({len(tables)}) и учреждений ({len(departments)})')

        temp_docfile = self.convert_pdf_to_docx_to_find_info(
            filename)  # получили path временного docx файла
        departments = get_headers(temp_docfile)
        dfs = compile_office_info_and_df(filename, departments, parsed_tables)
        return dfs


parser = Parser()
file = r'100185_2019_Rukovoditeli_podvedomstvennykh_uchrezhdenii_(sport).pdf'
file = r"D:\PROGR\LEARN_PYTHON\Declarator\declarations-parser\data_ids\pdf\converted\100185_2019_Rukovoditeli_podvedomstvennykh_uchrezhdenii_(sport).pdf"
print(parser.detect_headers_in_raw_doc(Path(file), '!'))
