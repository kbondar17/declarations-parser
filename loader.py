import requests
import urllib.request
import pandas as pd


df = pd.read_csv('salaries_with_ext.csv')
print(df['document_file_id'])

# r = requests.get(link)
# urllib.request.urlretrieve(url=link, filename='test')


# def get_files(link):
#     file = requests.get(link).headers['Content-Disposition']
#     return file
#
# def ext(file):
#     return file.split('.')[-1].strip('"')

# df['file'] = df['link'].apply(get_files)
# df['extension'] = df['file'].apply(ext)
# df.to_csv('salaries_with_ext.csv')



# for e in links:
#     print(e)
#     print(requests.get(e).headers.keys())
#     print(requests.get(e).headers['Content-Disposition'])
#
#     print('=====')

#print(requests.get(link).headers)
# import urllib.request
# with urllib.request.urlopen('http://www.example.com/') as f:
#     html = f.read().decode('utf-8')
#    print(html)
