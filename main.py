from langchain.document_loaders import DataFrameLoader
from langchain.document_loaders import CSVLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain_elasticsearch import ElasticsearchStore
from langchain.text_splitter import RecursiveCharacterTextSplitter
import tempfile
import mysql.connector as connection
import pandas as pd
import mysql
import os


def ingestadata(request):
    apikey="xxxxxxxxxxxxxxx"
    os.environ["OPENAI_API_KEY"] =apikey
    #credenciales mysql
    myhost="xx.xx.xx.xx"
    myuser="xxxxx"
    mypws="xxxxx"
    mydb="classicmodels"
    myquery= """SELECT productName, productline, quantityInStock as stock, MSRP as precio FROM
      `classicmodels`.`products`;
    """
    #credenciales Elasticsearch
    el_url="http://xx.xx.xx.xx:9200"
    el_usr="xxxxx"
    el_pws="xxxxx"
    el_idx="mprod-mcotrina-01"
    
    #conexion a base de datos
    mydb = mysql.connector.connect(
      host=myhost,
      user=myuser,
      passwd=mypws,
      database=mydb
      )
    query = myquery
    result_df = pd.read_sql(query,mydb)
    mydb.close()
    
    # Guardar el DataFrame en un archivo temporal
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as temp_file:
        result_df.to_csv(temp_file.name, index=False)
        temp_csv_path = temp_file.name
    
    # Cargar el archivo temporal usando CSVLoader
    loader = CSVLoader(file_path=temp_csv_path)
    documents = loader.load()
    #explitear el docuemento
    text_splitter = RecursiveCharacterTextSplitter(
    chunk_size = 650,
    chunk_overlap = 0
    )
    #generamos el embedding
    docs = text_splitter.split_documents(documents)
    embeddings = OpenAIEmbeddings()

    # Crear el store en Elasticsearch
    db_el = ElasticsearchStore(
        es_url=el_url,
        es_user=el_usr,
        es_password=el_pws,
        index_name=el_idx,
    )
    
    # Eliminar el índice si ya existe(esto solo se hace para  carga full en caso de Delta el proceso es diferente)
    if db_el.client.indices.exists(index=el_idx):
        db_el.client.indices.delete(index=el_idx)
        
    db = ElasticsearchStore.from_documents(
        docs,
        embeddings,
        es_url=el_url,
        es_user=el_usr,
        es_password=el_pws,
        index_name=el_idx,
    )
    db.client.indices.refresh(index=el_idx)
    return "ok"