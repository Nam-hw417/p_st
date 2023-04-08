import streamlit as st
import pandas as pd
import numpy as np


# 전처리된 데이터 호출

df_ana = pd.read_csv('../Data/PRE_PROCED_v1.csv', dtype = {'HSCD':'object'})
df_ana['HSCD'] = df_ana['HSCD'].astype(str)

# hscd 가 5자리일 경우 '0'을 붙여서 6자리로

hscds = []
for hscd in df_ana['HSCD']:
    if len(hscd) ==5:
        hscds.append('0' + hscd)
    else:
        hscds.append(hscd)

df_ana['HSCD'] = hscds


# 필요한 함수 작성

if 'hscd' not in st.session_state:
    st.session_state.hscd = '330499'

if 'con' not in st.session_state:
    st.session_state.con = '중국'

    
st.title('Related Market by HS-CODE')

# hscd_list = df_ana['HSCD'].unique().tolist()
# hscd_list = [hscd for hscd in hscd_list if hscd is not np.NaN]
# hscd_list.sort()

st.write('Input HS-CODE(6 unit)')
st.text_input(label = 'HSCD', 
              max_chars = 6,
              key = 'hscd')

# selectbox로 변경

country_list = df_ana['COUNTRY'].unique().tolist()
country_list = [con for con in country_list if con is not np.nan]
country_list.sort()

st.write('Select Country (Korean)')
st.selectbox(label = 'Country(KOR)',
             options = country_list,
             key = 'con')

@st.cache
def return_cor(hscd, con):
    target_hscd = df_ana[df_ana['HSCD'] == hscd]
    target_wide = target_hscd.pivot_table(values = 'LOG_AMT', 
                                          index = 'BSNO', columns = 'COUNTRY',
                                          fill_value =0)
    target_cor = target_wide.corr()
    target_value = target_cor[con].sort_values(ascending = False)[0:6]
    return target_value


target_value = return_cor(st.session_state.hscd, st.session_state.con)
related_con = target_value.index.tolist()

target_df = target_value.to_frame()[1:]

st.write('Related Market Top5: ', related_con)



@st.cache                   
def return_company(hscd, con_list):
    target_company = df_ana[(df_ana['HSCD'] == hscd) & (df_ana['COUNTRY'].isin(con_list))].pivot_table(
    index = 'BSNO', columns = 'COUNTRY', values = 'EXP_AMT', fill_value =0)
    return target_company

target_company = return_company(st.session_state.hscd, related_con)

# 기업명이 있는 데이터 로드

coname_df = pd.read_csv('../Data/BSNO_NAME.csv')
df_name = coname_df.merge(target_company, how='right', left_on ='BSNO_DECRYPT', right_on='BSNO')
                        

@st.cache
def convert_df(df):
    return df.to_csv().encode('utf-8')

csv = convert_df(df_name)

st.write('Target Company List: 2021 Export Amount($)') 

text = '<span style ="color: red">Export amount data for each company is a trade secret and external leakage is prohibited</span>'

st.write(text, unsafe_allow_html = True)

df_name.rename({'BSNO_DECRYPT':'BSNO'}, inplace = True)


st.dataframe(df_name, width = 1000)

st.download_button(
    label = 'Download Data as CSV',
    data = csv,
    file_name ='target_company.csv',
    mime = 'text/csv')

# st.bar_chart
# check box를 넣고 check box 클릭시 나오도록

vis = st.checkbox("Visualize Corr")

if vis:
    st.write('Related Country Corr by HSCD')
    st.bar_chart(target_df)

# E.O.P
