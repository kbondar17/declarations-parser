from pdfminer.layout import LAParams
from io import StringIO
import pdfminer
from pdfminer.high_level import extract_text_to_fp
file = r"D:\PROGR\LEARN_PYTHON\Declarator\declarations-parser\data_ids\pdf\converted\188456_2020_Rukovoditeli_podvedomstvennykh_uchrezhdenii_(obrazovanie).pdf"
file = r"D:\PROGR\LEARN_PYTHON\Declarator\declarations-parser\data_ids\pdf\converted\189429_2020_Rektor,_prorektory,_glavnyi_bukhgalter.pdf"
# text = pdfminer.high_level.extract_text(file)
# text

#text = pdfminer.high_level.extract_text(file)
# repr(text)

# output_string = open('temp.html', 'w')
output_string = StringIO()


with open(file, 'rb') as fin:
    res = extract_text_to_fp(fin, output_string, laparams=LAParams(),
                             output_type='html', codec=None)
    output_string.seek(0)
    print(output_string.read())


# import io
# buf = io.StringIO('hui')
# print(buf)
