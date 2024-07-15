#pip install gmft -q
#https://github.com/conjuncts/gmft/tree/main

from gmft.pdf_bindings import PyPDFium2Document
from gmft import CroppedTable, TableDetector
from gmft import AutoTableFormatter
from gmft import AutoFormatConfig
from gmft import TATRFormatConfig
import pandas as pd

config = AutoFormatConfig()
config.enable_multi_header = True
config.semantic_spanning_cells = True
TATRFormatConfig.force_large_table_assumption = False
config.large_table_assumption = False

detector = TableDetector()

def ingest_pdf(pdf_path) -> list[CroppedTable]:
    doc = PyPDFium2Document(pdf_path)

    tables = []
    for page in doc:
        tables += detector.extract(page)
    return tables, doc

country = 'madagascar'
tables, doc = ingest_pdf('/content/drive/MyDrive/'+country+'_short.pdf')
#tables, doc = ingest_pdf('/content/drive/MyDrive/'+country+'.pdf')
len(tables)
#Madagascar takes 15m (410 tables)
#Eswatini takes 1m (21 tables)

formatter = AutoTableFormatter()

for i in range(0, len(tables)):
  print(tables[i].confidence_score)
  if tables[i].confidence_score >= 0.995:
      print(tables[i].confidence_score)
      ft = formatter.extract(tables[i])
      with pd.option_context('display.multi_sparse', False):
        display(ft.df(config_overrides=config))
        display(ft.image())
        df = ft.df()
        df.fillna("",inplace=True)
      with pd.option_context('display.max_rows', None, 'display.max_columns', None):
          display(ft.df())
      df.to_csv('/content/drive/MyDrive/'+country+'/'+country+'_table'+str(i)+'.csv', sep='\t',index=False)



