import pandas as pd


def convert_df_to_json(df: pd.DataFrame) -> dict:

    def convert_excel(df):
        current_sheet = df['sheet_name'][0]
        my_json = {}
        my_json["documents"] = []
        my_json["persons"] = []
        persons = []

        for e in df.itertuples():

            if e.sheet_name != current_sheet:

                document = {
                    "documentfile_id": e.documentfile_id,
                    "sheet_title": current_sheet,
                }
                my_json["documents"].append(document)
                my_json["persons"].append(persons)
                persons = []
                current_sheet = e.sheet_name

            person = {
                "person": {
                    "name": e.name,
                    "role": e.position,
                    "department": e.department,
                    "incomes": [e.salary],
                    "raw_income": e.raw_salary

                }
            }

            persons.append(person)

        return my_json

    def convert_docx_n_pdf(df):

        my_json = {}
        documentfile_id = df['documentfile_id'][0]
        my_json["documents"] = [{'documentfile_id': documentfile_id}]
        my_json["persons"] = []
        for data in df.itertuples():
            data = data._asdict()
            person = {
                "person": {
                    "name": data.get('name', ''),
                    "role": data.get('position', ''),
                    "department": data.get('department', ''),
                    "incomes": [int(data.get('salary', '0'))],
                    "raw_income": data.get('salary_raw', ''),
                }
            }

            my_json["persons"].append(person)

        return my_json

    if 'sheet_name' in df.columns:
        data = convert_excel(df)
    else:
        data = convert_docx_n_pdf(df)

    return data
