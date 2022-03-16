import logging
from tqdm import tqdm_notebook
from pathlib import Path
import requests
import re
import time
import os
import urllib.request
from typing import Union
import csv
import statistics

import typing
import io
import numpy as np
from docx import Document


import camelot

import pandas as pd
logging.basicConfig(format=u'%(filename)+13s [ LINE:%(lineno)-4s] %(levelname)-8s %(message)s',
                    level=logging.DEBUG)

logger = logging.getLogger(__name__)


class PdfParser:

    @staticmethod
    def convert_pdf_to_df(filename) -> list[pd.DataFrame]:
        tables = camelot.read_pdf(filename, line_tol=2, joint_tol=10, line_scale=40, copy_text=[
                                  'v'], pages='1-end')  # , flavor='stream' row_tol=10
        tables = [e.df for e in tables]
        return tables


base = '../data_ids/pdf/converted/'
file = '../data_ids/pdf/converted/189273_2020_Rektor,_prorektory,_glavnyi_bukhgalter.pdf'
file = "D:/PROGR/LEARN_PYTHON/Declarator/declarations-parser/data_ids/pdf/converted/189273_2020_Rektor,_prorektory,_glavnyi_bukhgalter.pdf"


def convert_pdf_to_df(file) -> list[pd.DataFrame]:
    tables = camelot.read_pdf(file, line_tol=2, joint_tol=10, line_scale=40, copy_text=[
                              'v'], pages='1-end')  # , flavor='stream' row_tol=10
    tables = [e.df for e in tables]
    return tables


print('!!')
