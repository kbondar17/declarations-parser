import pandas as pd


def convert_df_to_json(df: pd.DataFrame) -> dict:

    def convert_excel(df: pd.DataFrame) -> dict:
        my_json = {}

        my_json["documents"] = []         
        my_json["persons"] = []

        sheets = set(df['sheet_name'].values)
        persons = []
        for sheet in sheets:
            sheet_df = df[df['sheet_name']==sheet]
            for data in sheet_df.itertuples():
                data = data._asdict()
                incomes = data.get('salary', '0')
                if not incomes or not incomes.split():
                    incomes = 0      # "incomes": [int(data.get('salary', '0'))],
                
                person = {
                    "person": {
                        "name": data.get('name', ''),
                        "role": data.get('position', ''),
                        "department": data.get('department', ''),
                        "raw_income": data.get('raw_salary', ''),
                        "incomes": incomes
                    }
                }

                persons.append(person)

            documentfile_id = df['documentfile_id'].values[0]
            document = {"documentfile_id":documentfile_id, "sheet_name":sheet}                        
            my_json["documents"].append(document)
            my_json["persons"].append(persons)
            persons = []
    
        return my_json        

        
        
    def convert_docx_n_pdf(df):
        pass
        my_json = {}
        documentfile_id = df['documentfile_id'].values[0]
        my_json["documents"] = [{'documentfile_id': documentfile_id}]
        my_json["persons"] = []
        for data in df.itertuples():
            data = data._asdict()
            incomes = data.get('salary', '0')
            if not incomes or not str(incomes).split():
                incomes = 0      # "incomes": [int(data.get('salary', '0'))],
                
            person = {
                "person": {
                    "name": data.get('name', ''),
                    "role": data.get('position', ''),
                    "department": data.get('department', ''),
  
                    "raw_income": data.get('raw_salary', ''),
                }
            }

            my_json["persons"].append(person)

        return my_json

    if 'sheet_name' in df.columns:
        data = convert_excel(df)
    else:
        data = convert_docx_n_pdf(df)

    return data
