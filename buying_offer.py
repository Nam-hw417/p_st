import streamlit as st
import pandas as pd
import numpy as np
import pyodbc

# sql을 통한 데이터 추출

sql = '''
select 기업ID, 기업사업자등록번호, 상품시리얼번호, 기업명_한글, 기업명_영문, 상품명, 상품키워드,
--lower(replace(상품명,' ','_')) 상품명수정1,
--replace(replace(상품명,' ','_'),',','_') 상품명수정2--,
'https://origin.buykorea.org/bk/byr/product/'|| (replace(replace(lower(상품명),' ','_'),',','_'))||'-'||상품시리얼번호||'.do' as 상품정보URL
from (
SELECT 
distinct
CD.coid "기업ID",
CD.BSNO "기업사업자등록번호", 
CD.coname "기업명_한글",
CD.coname_en "기업명_영문",
B.GOODS_SN "상품시리얼번호",
NVL(b.GOODS_NM_ENG,'UDV')  AS "상품명",
b.goods_kwrd "상품키워드"
--b.UPDDE_DT,b.RGSDE_DT AS "업데이트날짜",
--NVL(b.GOODS_EXPSR_AT, 'UDV') AS "노출여부" 
FROM 
bkuser2.BK_GO_MNG_T b,
(select c.coid, d.bsno, c.webuserid, d.coname, d.coname_en
from bkuser2.crm_cm_cust c, bkuser2.crm_cm_corp d
where c.coid = d.coid
) CD
WHERE 
b.REGISTER_ID = CD.webuserid(+)
and B.CONFM_STTUS = '02'
AND NVL(B.DELETE_AT, 'N') = 'N'
)
order by 1,2;
'''

# 데이터 추출함수

def collect(sql):
    conn = pyodbc.connect('DSN=BP_DB;UID=bpuser;PWD=kotrabp')
    conn.setdecoding(pyodbc.SQL_CHAR, encoding='utf-8')
    conn.setdecoding(pyodbc.SQL_WCHAR, encoding='utf-8')
    conn.setdecoding(pyodbc.SQL_WMETADATA, encoding='utf-32le')
    conn.setencoding(encoding='utf-8')
    data= pd.read_sql_query(sql, conn)
    conn.close()
    return data


# data = collect(sql)
# df = data.copy()

data = pd.read_csv('BK_CORE_S200.csv')
df = data.copy()

# 데이터 정제 함수

def make_df_clean(df):
    df.columns = ['ID', 'BSNO', 'ITEM_NO', 'CONAME_KO', 'CONAME_EN', 'ITEM', 'ITEM_KWD', 'URL'] # 컬럼명 변경
    df = df[df['BSNO'].notnull()]
    df = df.drop_duplicates('ITEM_NO')
    df = df[df['BSNO'] != '1208200275']
    df = df[df['ITEM_KWD'].notnull()]
    df['ITEM'] = df['ITEM'].str.replace('[^A-Za-z0-9]+', ' ')
    df['ITEM_KWD'] =  df['ITEM_KWD'].apply(lambda x: x.lower())
    return df


df = make_df_clean(df)


# streamlit 적용 코드

if 'kwd1' not in st.session_state:
    st.session_state.kwd1 = ''

if 'kwd2' not in st.session_state:
    st.session_state.kwd2 = ''

if 'kwd3' not in st.session_state:
    st.session_state.kwd3 = ''


st.title('Buying Offer Matching Companies')
st.subheader('by BigData Team / TriBIG')

st.write("Input 1st Keyword")
st.text_input(label = 'keyword1 (Required / ENG, lowercase)',
	max_chars = 30,
	key = 'kwd1')


st.write("Input 2nd Keyword")
st.text_input(label = 'keyword2 (Option / ENG, lowercase)',
	max_chars = 30,
	key = 'kwd2')


st.write("Input 3rd Keyword")
st.text_input(label = 'keyword3 (Option /ENG, lowercase)',
	max_chars = 30,
	key = 'kwd3')


# 추천함수

@st.cache
@st.cache
def recommand_kr_company(kwd1 = None, kwd2 = None, kwd3 = None):
    global df
    try:
        df_result = df[df['ITEM_KWD'].str.contains(kwd1)]
        if kwd2:
            df_result = df_result[df_result['ITEM_KWD'].str.contains(kwd2)]
            if kwd3:
                df_result = df_result[df_result['ITEM_KWD'].str.contains(kwd3)]
        try:
            df_result = df_result[['BSNO', 'CONAME_EN', 'ITEM', 'URL']].drop_duplicates('BSNO').sample(30).reset_index().drop('index', axis = 1)
        except:
            df_result = df_result[['BSNO', 'CONAME_KO','CONAME_EN', 'ITEM', 'URL']].drop_duplicates('BSNO').head(30).reset_index().drop('index', axis = 1)
    except:
        print('조건에 맞는 데이터가 없습니다')
        
    return df_result


result = recommand_kr_company(st.session_state.kwd1, st.session_state.kwd2, st.session_state.kwd3)


st.write('Matching Korean Companies: ')
st.dataframe(result, width =700, height =800)


@st.cache(allow_output_mutation=True)
def convert_df(df):
    return df.to_csv(index = False).encode('utf-8')

csv = convert_df(result)


st.download_button(
	label= 'Download Data as CSV',
	data = csv,
	file_name = 'Matching_Companies.csv', 
	mime = 'text/csv')


## 추가코드 반영: csv 업로드시 매칭데이터 일괄  return ('22.11.28')


st.sidebar.title('Lead Marketing Matching KR Companies')
bk_data = data.copy()
bk_data = make_df_clean(bk_data)
bk_data['items'] = bk_data['ITEM_KWD'].str.lower()
bk_data['items'].fillna(' ', inplace = True)


columns = ['BUYER_ID', 'BUYER_ITEMS', 'BSNO', 'CONAME_KO', 'CONAME_EN', 'ITEM', 'URL', 'ITEM_KWD']
df_result = pd.DataFrame(columns = columns)



st.sidebar.subheader("Input csv format: BUYER_ID / BUYER_NAME / BUYER_ITEMS")
file = st.sidebar.file_uploader("Choose a csv file", key = 'csv')


def return_kr_company(text):
    try:
        result = bk_data[bk_data['items'].str.contains(text)].drop_duplicates(['BSNO']).sample(5)
    except:
        result = bk_data[bk_data['items'].str.contains(text)].drop_duplicates(['BSNO']).head(5)
    result['KEYWORD'] = text
    result = result[['BSNO', 'CONAME_KO', 'CONAME_EN', 'ITEM', 'URL', 'ITEM_KWD']]
    return result
    

if file:
    lead = pd.read_csv(st.session_state.csv, encoding = 'cp949')
    st.sidebar.write('Check Your Input Dataset Sample')
    st.sidebar.dataframe(lead.head())
    lead['items'] = lead['BUYER_ITEMS'].str.lower() 
    
    item_cleaned = []
    
    for item in lead['items']:
        item_split = item.split()
        item_cleaned.append(item_split[0]) 
        
    lead['KEYWORD']= item_cleaned
    lead_df = lead[['BUYER_ID', 'BUYER_NAME', 'BUYER_ITEMS', 'KEYWORD']]
    lead_df['KEYWORD'] = lead_df['KEYWORD'].str.replace('[^a-z]+', ' ')
    
    
    for i in range(len(lead_df)):
        keyword = lead_df['KEYWORD'][i]  
        temp_df = return_kr_company(keyword)
        temp_df['BUYER_ID'] = lead_df['BUYER_ID'][i]
        temp_df['BUYER_ITEMS'] = lead_df['BUYER_ITEMS'][i]
        df_result = pd.concat([df_result, temp_df])
        
    st.sidebar.write("Check Your Result Dataset Sample")
    st.sidebar.dataframe(df_result.head())
    
    st.sidebar.write("Download Your Result Dataset")
    df_csv = convert_df(df_result)
    st.sidebar.download_button(
     label = 'Download Data as CSV', 
     data =df_csv,
     file_name = 'Lead Marketing Dataset.csv',
     mime = 'text/csv')

st.caption('#E.O.P / Nam.H.W.')

# E.O.P / Nam.H.W.

