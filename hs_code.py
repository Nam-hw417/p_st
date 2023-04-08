import pandas as pd
import numpy as np
import streamlit as st


hscd = pd.read_csv('1028_HSCD.csv', dtype = {'HSCD':'object', 'MTICD':'object'})
df_mti = pd.read_csv('1028_MTI.csv', dtype ={'MTICD':'object'})


st.title('MTI Code Return (Korean)')
st.subheader('by Big Data Team / TriBIG')


if 'text1' not in st.session_state:
    st.session_state.text1 = '화장품'

if 'text2' not in st.session_state:
    st.session_state.text2 = ''

if 'text3' not in st.session_state:
    st.session_state.text3 = ''


col1, col2, col3 = st.columns(3)

with col1:
    st.write('Input 1st Item Keyword')
    st.text_input(label = 'Keyword 1 (Korean, Required)', 
              max_chars = 15,
              key = 'text1')

with col2:
    st.write('Input 2nd Item Keyword')
    st.text_input(label = '& Keyword 2 (Korean, Option)', 
              max_chars = 15,
              key = 'text2')

with col3:
    st.write('Input 3rd Item Keyword')
    st.text_input(label = '& Keyword 3 (Korean, Option)', 
              max_chars = 15,
              key = 'text3')
    
@st.cache
def return_mticd(text1, text2 = None, text3 = None):
    df_result = df_mti[df_mti['HS_DESC'].str.contains(text1)][['MTICD', 'MTI_NAME']]
    if text2:
        df_result = df_result[df_mti['HS_DESC'].str.contains(text2)][['MTICD', 'MTI_NAME']]
        if text3:
            df_result = df_result[df_mti['HS_DESC'].str.contains(text3)][['MTICD', 'MTI_NAME']]
    return  df_result


result = return_mticd(st.session_state.text1, st.session_state.text2, st.session_state.text3)
st.text('Related MTI Code (6 digit)')
st.dataframe(result, width = 700)

@st.cache
def return_hscd(text1, text2 = None, text3 = None):
    hs_result = hscd[hscd['HS_MTI_DESC'].str.contains(text1)][['MTICD', 'HSCD', 'HS_MTI_DESC']]
    if text2:
        hs_result = hs_result[hs_result['HS_MTI_DESC'].str.contains(text2)][['MTICD', 'HSCD', 'HS_MTI_DESC']]
        if text3:
            hs_result = hs_result[hs_result['HS_MTI_DESC'].str.contains(text3)][['MTICD', 'HSCD', 'HS_MTI_DESC']]
    return hs_result

hs_df = return_hscd(st.session_state.text1, st.session_state.text2, st.session_state.text3)
st.text('Related HS Code (10 digit)')
st.dataframe(hs_df, width = 700)


st.caption('P.O.C./Nam.H.W')

