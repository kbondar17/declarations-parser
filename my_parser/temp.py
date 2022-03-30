import pandas as pd
import camelot
import logging
from pathlib import Path

logging.getLogger('camelot').setLevel('ERROR')

logging.basicConfig(format=u'%(filename)+13s [ LINE:%(lineno)-4s] [ Function %(funcName)s ] :::   %(message)s',
                    level=logging.DEBUG, filename='my_log.log', filemode='w')

my_logger = logging.getLogger(__name__)


class PdfParser:

    @staticmethod
    def convert_pdf_to_df(filename) -> list[pd.DataFrame]:
        tables = camelot.read_pdf(str(filename), line_tol=2, joint_tol=10, line_scale=40, copy_text=[
                                  'v'], pages='1-end')  # , flavor='stream' row_tol=10
        tables = [e.df for e in tables]
        return tables

    def get_camelot_tables(self, filename):
        tables = camelot.read_pdf(str(filename), line_tol=2, joint_tol=100, line_scale=40, copy_text=[
                                  'v'], pages='1-end')  # , flavor='stream' row_tol=10
        return tables


file = r"D:\PROGR\LEARN_PYTHON\Declarator\declarations-parser\data_ids\pdf\83327_2016_Rukovoditeli,_zamestiteli_i_glavnye_bukhgaltery_podvedomstvennykh_uchrezhdenii.pdf"
file = r"D:\PROGR\LEARN_PYTHON\Declarator\declarations-parser\data_ids\pdf\converted\83304_2018_Rukovoditeli,_zamestiteli_i_glavnye_bukhgaltery_podvedomstvennykh_uchrezhdenii.pdf"

parser = PdfParser()
tables = parser.convert_pdf_to_df(file)
tables[0].to_excel('opened_pdf.xlsx')
