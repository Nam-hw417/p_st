import pandas as pd
import numpy as np
import streamlit as st
import streamlit.components.v1 as components
from scipy import stats
from dateutil.relativedelta import relativedelta
from PIL import Image
from scipy.stats import wilcoxon
import plotly.figure_factory as ff
import plotly.express as px


# <페이지 설정>
st.set_page_config(page_title='KOTRA Performance Measurement',
                   page_icon='kotra_character.jpg',
                   layout ='wide')

# <데이터 불러오기>
data = pd.read_csv('biz_data.csv', low_memory = False, dtype ={'사업시작월':str, '참가기업사업자번호':str})
exp_df = pd.read_csv('expamt_data.csv', low_memory = False, dtype ={'BSNO':str})
rec_df = pd.read_csv('biz_rec_30.csv', dtype ={'사업시작월':str, '참가기업사업자번호':str})


# <사용 함수>
def show_biz_sample(topic: str):

    if not topic:
        st.session_state.text_error = 'Please enter a topic'
        return
    
    df = rec_df[rec_df['사업명'].str.contains(topic)]
    df = df[df['사업시작월'].str.contains('2019|2020|2021')]
    df = df[['사업명', '사업시작월']].set_index('사업시작월').sort_index(ascending = False)
    if len(df) > 15:
        df = df.head(15)
    return df 


def ext_date(mon_base, bf_yn, month_num):
    '''
    Args)
    mon_base : 기준 년월  
    bf_yn : 사업참가 전 여부(1-사업참가전, 0-사업참가후)
    month_num : 비교기간
    '''
    if bf_yn==1:
        pre_str_mon = mon_base - relativedelta(months = month_num)
        pre_str_mon = pre_str_mon.strftime("%Y%m")  
    else:
        pre_str_mon = mon_base + relativedelta(months = month_num)
        pre_str_mon = pre_str_mon.strftime("%Y%m") 
    return pre_str_mon


def make_basis_months(mon, basis = 12):
    '''
    Args)
    mon : 기준 년월  
    basis : 비교기간
    '''
    mon_base = pd.to_datetime(mon + '01')
    end_month = 1
    
    # 사업참가전 시작/종료 년, 월 반환
    pre_str_mon = ext_date(mon_base, 1, basis)
    pre_end_mon = ext_date(mon_base, 1, end_month)
    
    # 사업참가후 시작/종료 년, 월 반환
    post_str_mon = ext_date(mon_base, 0, end_month)
    post_end_mon = ext_date(mon_base, 0, basis)
    
    return pre_str_mon, pre_end_mon, post_str_mon, post_end_mon
    
   
    
def eval_kotra_biz_re(biz_name, basis_month, period):
    '''
    사업실적 평가 함수 
    Args)
    biz_name : 선택한 사업명 
    basis_month : 사업시작 년월
    period : 비교기간
    '''
    try:
        pre_str_mon, pre_end_mon, post_str_mon, post_end_mon = make_basis_months(basis_month, period)
        idx = data[(data['사업명'] == biz_name) & (data['사업시작월'] == basis_month)]['참가기업사업자번호'].unique().tolist()
        if idx is None:
            st.write('입력값이 유효하지 않습니다.')
            pass
        result_df = exp_df[exp_df['BSNO'].isin(idx)]
        result_df.set_index('BSNO', inplace = True)
        pre_df = result_df.loc[:,  pre_str_mon:pre_end_mon]
        post_df = result_df.loc[:, post_str_mon:post_end_mon]
        
        pre = pre_df.mean(axis =1)
        post = post_df.mean(axis =1)
        dist = post - pre
        diff = post.mean() - pre.mean()
        w, p_value = wilcoxon(dist, alternative = 'greater')
        num_company = len(result_df)
        
        return num_company, pre_str_mon, pre_end_mon, pre.mean(), post_str_mon, post_end_mon, post.mean(), diff, p_value, pre_df, post_df
    except:
        st.write('입력값이 유효하지 않습니다.')
        return

    
# <화면 구현>
st.title('KOTRA Performance Measurement\n')
st.header('')

topic = None
topic = st.text_input(label='검색(키워드)',
                      max_chars = 55,
                      key = 'biz_cat',
                      help = '사업명의 키워드를 입력하세요')
    


if 'biz_cat' not in st.session_state:
    st.session_state['biz_cat'] = 'None'
    df = show_biz_sample(st.session_state.biz_cat)
else:
    
    df = show_biz_sample(st.session_state.biz_cat)
    

try:
    
    df_li = df['사업명'].tolist()

    col3, col4, col5 = st.columns([2.0, 0.9, 0.9])

    with col3:

        st.selectbox('사업 선택', df_li,
                     key = 'biz_name')

    with col4:
        biz_month = rec_df[rec_df['사업명']==st.session_state.biz_name]['사업시작월']
        st.selectbox('사업 시작연월 선택', biz_month,
                     key = 'biz_month')

    with col5:

        st.selectbox('사업전후 비교기간 선택', [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
                     key = 'period', index=11)


    num_company, pre_str_mon, pre_end_mon, pre_mean, post_str_mon, post_end_mon, post_mean, diff, p_value, pre_df, post_df = eval_kotra_biz_re(st.session_state.biz_name, 
                      st.session_state.biz_month, int(st.session_state.period))
    
    st.write('')
    st.write('')
    st.write('')
    st.write('')

    c = st.expander('RESULT', expanded=True)
    c.write('')
    c.markdown('### 사업 성과 :page_facing_up:')
    c.write('')
    c.write('')

    c.markdown('##### 사업 정보')
    c.info(f' * 사업명  :  {st.session_state.biz_name} ')
    c.info(f' * 사업시작연월  :  {st.session_state.biz_month[:4]}년 {st.session_state.biz_month[4:]}월')
    c.info(f" * 사업 참가 기업수  :  {format(int(num_company), ',')} 개사")
    c.write('')


    c.markdown('##### 사업 참가 전 수출금액')
    col6, col7 = c.columns([1.5, 1.5])

    col6.info(f" * 비교기간  :  {pre_str_mon[:4]}년 {pre_str_mon[4:]}월 ~ {pre_end_mon[:4]}년 {pre_end_mon[4:]}월")
    col7.info(f" * 월평균 수출금액 평균  :  $ {format(int(pre_mean), ',')}")


    c.markdown('##### 사업 참가 후 수출금액')
    col8, col9 = c.columns([1.5, 1.5])
    col8.info(f" * 비교기간  :  {post_str_mon[:4]}년 {post_str_mon[4:]}월 ~ {post_end_mon[:4]}년 {post_end_mon[4:]}월")
    col9.info(f" * 월평균 수출금액 평균  :  $ {format(int(post_mean),',')}")
    c.write('')
    c.write('')
    
    c.markdown('##### 사업 참가 전후의 월별 평균수출금액')
    
    pre_monly = pre_df.mean().round().rename(index=lambda x: x[:4]+'/'+x[4:])
    post_monly = post_df.mean().round().rename(index=lambda x: x[:4]+'/'+x[4:])
    
    pre_monly_df = pre_monly.to_frame(name='평균수출금액')
    pre_monly_df['사업참여상태'] = '사업 참여 전'
    post_monly_df = post_monly.to_frame(name='평균수출금액')
    post_monly_df['사업참여상태'] = '사업 참여 후'
    
    monthly_df = pd.concat([pre_monly_df, post_monly_df], axis=0)
    max_value = monthly_df['평균수출금액'].max()
    
    fig = px.line(monthly_df, x=monthly_df.index, y='평균수출금액', color='사업참여상태', markers=True, range_y = ([0, max_value*1.1]), labels={'index':f'사업 시작 {st.session_state.period}개월 전후'})
    fig.update_layout(showlegend=True)
    

    c.plotly_chart(fig, use_container_width=True)
    


    
    if p_value < 0.05:
        if diff > 0:
            res2 = '해당사업은 통계적으로 유효성이 입증됩니다.'
            res3 = f'해당사업의 {st.session_state.period} 개월간 총효과는 $ {format(int(diff) * int(st.session_state.period) * num_company, ",")} 로 추정됩니다.'
            
        else:
            res2 = '해당사업은 통계적으로 유효성이 입증되지 않습니다.'
            res3 = ''

    else:
        res2 = '해당사업은 통계적으로 유효성이 입증되지 않습니다.'
        res3 = ''

    c.markdown('##### 성과 측정 결과')
    c.text_area('', f"""사업참가 전후 월평균수출금액차이: ${format(int(diff), ',')} 이며 해당사업 Wilcoxon 순위합 검정의 p_value: {np.round(p_value, 4)} 으로, {res2}
{res3}""")
    c.caption('(총효과 추정식: 사업참가 기업수 x 사업전후 비교기간 x 월평균수출금액차이)')

    c.write('')
    c.write('')
    c.write('')
    c.write('')
    c.subheader('<성과측정원리: Wilcoxon 부호순위 검정>')
    image = Image.open('wilcoxon.png')
    c.image(image, caption='측정되지 않는 것은 관리되지 않는다 - 피터드러커')
    
    
except TypeError:
    pass


    
st.write('')
st.caption('E.O.P / Nam H.W.')


