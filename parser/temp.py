# def parse(self, filename: Path) -> tuple[bool, pd.DataFrame]:
#     # пытаемся найти учреждения в теле таблиц

#     # TODO: добавить проверку doc или pdf

#     tables = self.convert_pdf_to_df_and_find_tables(filename)

#     tables_with_ok_headers = []

#     for table in tables:
#         res, df = self.table_splitter(table)
#         if res:
#             tables_with_ok_headers.append(df)

#         if not res:
#             del tables
#             # идем парсить весь док, чтобы достать учреждения из текста перед таблицей
#             dfs = self.detect_headers_in_raw_doc(filename)
#             if dfs:
#                 for df in dfs:
#                     tables_with_ok_headers.append(df)
# break

a = None


def fun():

    tables = a

    if 1:
        del tables


fun()
print("!")
