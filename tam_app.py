from datetime import datetime, timedelta
import streamlit_toggle as tog
import streamlit as st
import pandas as pd
import numpy as np
import datetime as dt
##import IPython.display as display
from streamlit.components.v1 import html
import webbrowser
from st_aggrid import JsCode
from streamlit_option_menu import option_menu
import st_aggrid
from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, DataReturnMode, ColumnsAutoSizeMode
import os
import base64
#import streamlit_shadcn_ui as ui
import time
import output_data_transformations as odt
import pygsheets
from google.oauth2 import service_account
from ds.utilities.secrets import secrets
import tam_functions as tf

os.environ["IDENTITY_USER"] = "robert.enright"

#st.set_page_config(layout="wide")

SCOPES = (
"https://www.googleapis.com/auth/spreadsheets",
"https://www.googleapis.com/auth/drive",
)

bot_creds = secrets.Secrets().get_secret("growth_ops_service_account")
my_credentials = service_account.Credentials.from_service_account_info(
bot_creds,
scopes=SCOPES,
)
gc= pygsheets.authorize(custom_credentials=my_credentials)

# Initial Streamlit Page
st.set_page_config(
    page_title='TAM Analysis App'
    , page_icon = ":flag-ta:"
    , initial_sidebar_state="collapsed") #, layout='wide' , initial_sidebar_state="expanded"

# Define the tooltip style
tooltip_css = """
<style>
.tooltip {
  position: relative;
  display: inline-block;
  cursor: pointer;
}

.tooltip .tooltiptext {
  visibility: hidden;
  width: 120px;
  background-color: black;
  color: #fff;
  text-align: center;
  border-radius: 6px;
  padding: 5px 0;
  position: absolute;
  z-index: 1;
  bottom: 100%;
  left: 50%;
  margin-left: -60px;
  opacity: 0;
  transition: opacity 0.3s;
}

.tooltip:hover .tooltiptext {
  visibility: visible;
  opacity: 1;
}
</style>
"""

# Insert CSS for the tooltip
st.markdown(tooltip_css, unsafe_allow_html=True)

# Get 6m ago date
today = datetime.today()
# Calculate the date 6 months ago
six_months_ago = today - timedelta(days=30 * 6)
first_day_six_months_ago = six_months_ago.replace(day=1)

# Here we convert the image to base64 format
def get_img_as_base64(file):
    with open(file, "rb") as f:
        data=f.read()
    return base64.b64encode(data).decode()
#img = get_img_as_base64('Otter Logo.png')
#gif = get_img_as_base64('OrderFood.gif')

#st.markdown(f'<img src="data:image/png;base64,{img}" width="100" height="100" alt="otter logo">', unsafe_allow_html=True)

st.markdown("""
### TAM Analysis App 👈

Here we provide an automated solution for Total Addressable Market data for Revenue Recapture customers. 

**Instructions**:
1. Go to the merchant portals, download the Doordash and Ubereats errors and cancellation reports.
2. Select the customer in question within the app. Make sure the UUID is correct.
3. Choose the user to share the report with.
4. Upload the reports to the file drop.
5. Generate the output file and the app shall do the rest! 
   
If you have issues or questions feel free to reach out to Robert Enright or post in the **#tam_analysis_app** slack channel. 
""")

# Pull in the org list
orgs = pd.read_csv('org_list.csv')
orgs_list = orgs['output_org'].to_list()
default_org = orgs_list.index('Panda Restaurant Group (31d2cf2c-08c9-4b4a-82fa-a1165baaf1da)')
# Create the select box
selected_org = st.selectbox("Type organization name:", options=orgs_list, index=default_org)
st.session_state['org'] = selected_org
org_name = orgs.loc[orgs['output_org']==selected_org, 'org_name'].iloc[0]
uuid = '{:g}'.format(orgs.loc[orgs['output_org']==selected_org, 'uuid'].iloc[0])
# OrgID to use to pull the rest of the data
output_org_id = orgs['organization_id'].loc[orgs['output_org']==selected_org]
st.markdown('Customer UUID: ' + str(uuid))

# Pull in the org list
users = pd.read_csv('user_list.csv')
users_list = users['output_name'].to_list()
default_user = users_list.index('robert.enright@cloudkitchens.com (Robert Enright)')
# Create the select box
selected_user = st.selectbox("Select user:", options=users_list, index=default_user)
st.session_state['org'] = selected_user
# Email to use to share and send with end user
output_email = str(users.loc[users['output_name']==selected_user, 'email'].iloc[0])
st.markdown('User email: ' + output_email)

# Analysis Start Date
default_date = dt.date(2024, 1, 1)
start_date = st.date_input("Analysis Start Date", value=default_date, format="YYYY-MM-DD")
st.session_state['start_date'] = start_date

# Streamlit file uploader for Merchant reports
st.markdown("""
<div class="tooltip"><strong>Upload Doordash Reports</strong>
    <span class="tooltiptext">Find reports here: <a href="https://www.doordash.com/merchant" style="color: #ffffff;">DD Portal</a></span>
</div>
""", unsafe_allow_html=True)
col1, col2 = st.columns(2)
dd_errors_df, dd_canc_df, ue_errors_df, ue_payments_df = pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

with col1:
    uploaded_files_1 = st.file_uploader("Doordash Cancellations report", accept_multiple_files=True)
    if len(uploaded_files_1) > 0:
        for uploaded_file in uploaded_files_1:
            file_name = uploaded_file.name
            if uploaded_file  == uploaded_files_1[0]:
                dd_canc_df = pd.read_csv(uploaded_file)
            else:
                extra_dd_canc_df = pd.read_csv(uploaded_file)
                dd_canc_df = pd.concat(dd_canc_df, extra_dd_canc_df, ignore_index=True)

    if len(dd_canc_df) > 0:
        st.success('Doordash cancellations data loaded', icon="✅")
        dd_can = True
    else:
        st.warning('Doordash cancellations data missing', icon="⚠️")
        dd_can = False  
        
with col2:
    uploaded_files_2 = st.file_uploader("Doordash Errors report", accept_multiple_files=True)
    if len(uploaded_files_2) > 0:
        for uploaded_file in uploaded_files_2:
            file_name = uploaded_file.name
            if uploaded_file  == uploaded_files_2[0]:
                dd_errors_df = pd.read_csv(uploaded_file)
            else:
                extra_dd_errors_df = pd.read_csv(uploaded_file)
                dd_errors_df = pd.concat(dd_errors_df, extra_dd_errors_df, ignore_index=True)
        
    if len(dd_errors_df) > 0:
        st.success('Doordash errors data loaded', icon="✅")
        dd_err = True
    else:
        st.warning('Doordash errors data missing', icon="⚠️")    
        dd_err = False 

st.markdown("""
<div class="tooltip"><strong>Upload Ubereats Reports</strong>
    <span class="tooltiptext">Find reports here: <a href="https://merchants.ubereats.com/manager" style="color: #ffffff;">UE Portal</a></span>
</div>
""", unsafe_allow_html=True)
col1, col2 = st.columns(2)
with col1:
    uploaded_files_3 = st.file_uploader("Ubereats Errors report", accept_multiple_files=True)
    if len(uploaded_files_3) > 0:
        for uploaded_file in uploaded_files_3:
            file_name = uploaded_file.name
            if uploaded_file  == uploaded_files_3[0]:
                ue_errors_df = pd.read_csv(uploaded_file)
            else:
                extra_ue_errors_df = pd.read_csv(uploaded_file)
                ue_errors_df = pd.concat(ue_errors_df, extra_ue_errors_df, ignore_index=True)

    if len(ue_errors_df) > 0:
        st.success('Ubereats errors data loaded', icon="✅")
        ue_err = True
    else:
        st.warning('Ubereats errors data missing', icon="⚠️")
        ue_err = False      

with col2:
    uploaded_files_4 = st.file_uploader("Ubereats Payments report", accept_multiple_files=True)
    if len(uploaded_files_4) > 0:
        for uploaded_file in uploaded_files_4:
            file_name = uploaded_file.name
            if uploaded_file  == uploaded_files_4[0]:
                ue_payments_df = pd.read_csv(uploaded_file)
            else:
                extra_ue_payments_df = pd.read_csv(uploaded_file)
                ue_payments_df = pd.concat(ue_payments_df, extra_ue_payments_df, ignore_index=True)

    if len(ue_payments_df) > 0:
        st.success('Ubereats payments data loaded', icon="✅")
        ue_pay = True
    else:
        st.warning('Ubereats payments data missing', icon="⚠️")
        ue_pay = False   

file_status = [dd_err, dd_can, ue_err, ue_pay]
true_count = sum(file_status)
progress_complete = true_count/4
percentage = str(round(progress_complete * 100, 2)) + "%"

progress_text = f"Operation in progress - the merchant data load is {percentage} complete."
my_bar = st.progress(0, text=progress_text)

for percent_complete in range(100):
    time.sleep(0.01)
    my_bar.progress(progress_complete, text=progress_text)
time.sleep(1)
#my_bar.empty()

with st.form('Trigger TAM Analysis Output File'):
    pull_data = st.form_submit_button('Pull data')
    if pull_data:
        if progress_complete <= 0:
            st.error("There are insufficient files to perform this transformation, please add and resubmit...", icon="🚨")
        else:
            with st.spinner('Data transformation in progress... 🤖'):
                # Sample Data
                org_name = str(org_name)
                #st.markdown(f"Organization Name: {org_name}")
                uuid = str(uuid)
                #st.markdown(f"UUID: {uuid}")

                output_file = odt.copy_template_file(output_email)
                st.markdown('Here is the link to the newly created Gsheet: https://docs.google.com/spreadsheets/d/' + output_file)
                ss = gc.open_by_key(output_file)
                
                # 1. DD Cancellations Data Dump
                ws = ss.worksheet("title", "dd_cancellations_data_input")
                ws.clear("A3","F3")
                ws.clear("A6","S15")
                ws.clear("V6","AH15")
                ws.clear("A18","N")                
                ws.clear("Q18","AD")
                
                if len(dd_canc_df)>0:

                    cancels_df = dd_canc_df.copy()
                    try:
                        org_cancels_df, tam_pivot_table, tam_by_store_pivot_table, wins_by_store_pivot_table, wins_pivot_table, cancel_reasons_tam_pivot_table, cancel_reasons_wins_pivot_table = odt.dd_cancellations(cancels_df, org_name, uuid, start_date)
                        st.success("Doordash cancellations data was successfully pulled", icon="✅" )

                        # paste the dataframe into sheets
                        ws.set_dataframe(
                            org_cancels_df.fillna(0), (2, 1), extend=True, copy_head=True, fit=False, copy_index=False
                        )

                        tam_table = odt.transform_pivot_to_df(tam_pivot_table, "dd_tam_cancellations")
                        # paste the dataframe into sheets
                        ws.set_dataframe(
                            tam_table, (6, 1), extend=True, copy_head=True, fit=False, copy_index=False
                        )

                        wins_table = odt.transform_pivot_to_df(wins_pivot_table, 'dd_cancelled_winbacks')
                        # paste the dataframe into sheets
                        ws.set_dataframe(
                            wins_table, (6, 4), extend=True, copy_head=True, fit=False, copy_index=False
                        )

                        tam_by_store_df = odt.transform_multiindex_to_df(tam_by_store_pivot_table)
                        # paste the dataframe into sheets
                        ws.set_dataframe(
                            tam_by_store_df, (18, 1), extend=True, copy_head=True, fit=False, copy_index=False
                        )

                        wins_by_store_df = odt.transform_multiindex_to_df(wins_by_store_pivot_table)
                        # paste the dataframe into sheets
                        ws.set_dataframe(
                            wins_by_store_df, (18, 17), extend=True, copy_head=True, fit=False, copy_index=False
                        )

                        tam_reasons_df = odt.transform_multiindex_to_df(cancel_reasons_tam_pivot_table)
                        # paste the dataframe into sheets
                        ws.set_dataframe(
                            tam_reasons_df, (6, 7), extend=True, copy_head=True, fit=False, copy_index=False
                        )

                        win_reasons_df = odt.transform_multiindex_to_df(cancel_reasons_wins_pivot_table)
                        # paste the dataframe into sheets
                        ws.set_dataframe(
                            win_reasons_df, (6, 22), extend=True, copy_head=True, fit=False, copy_index=False
                        )

                    except Exception as dd_canc_e:
                        st.error(f"An error occurred pulling DD cancellations data: {dd_canc_e}", icon="🚨")
                        #org_cancels_df, tam_pivot_table, tam_by_store_pivot_table, wins_by_store_pivot_table, wins_pivot_table, cancel_reasons_tam_pivot_table, cancel_reasons_wins_pivot_table = 
 

                # 2. DD Errors Data Dump
                ws = ss.worksheet("title", "dd_errors_data")
                ws.clear("A3","F3")
                ws.clear("A6","15")
                ws.clear("A18","N")     
                ws.clear("Q18","AD")

                if len(dd_errors_df)>0:
                    # Transform the data into summary tables
                    errors_df = dd_errors_df.copy()
                    try:
                        total_tam_df, total_wins_df, results_df, tam_pivot_table, tam_by_store_pivot_table, wins_pivot_table, wins_by_store_pivot_table = odt.dd_errors(errors_df, org_name, uuid, start_date)       
                        st.success("Doordash errors data was successfully pulled", icon="✅" )

                        # paste the dataframe into sheets
                        ws.set_dataframe(
                            results_df.fillna(0), (2, 1), extend=True, copy_head=True, fit=False, copy_index=False
                        )

                        tam_table = odt.transform_pivot_to_df(tam_pivot_table, "dd_errors_tam")
                        # paste the dataframe into sheets
                        ws.set_dataframe(
                            tam_table.fillna(0), (6, 1), extend=True, copy_head=True, fit=False, copy_index=False
                        )

                        winbacks_table = odt.transform_pivot_to_df(wins_pivot_table, "dd_error_winbacks")
                        # paste the dataframe into sheets
                        ws.set_dataframe(
                            winbacks_table.fillna(0), (6, 4), extend=True, copy_head=True, fit=False, copy_index=False
                        )

                        tam_by_store = odt.transform_multiindex_to_df(tam_by_store_pivot_table)
                        # paste the dataframe into sheets
                        ws.set_dataframe(
                            tam_by_store.fillna(0), (18, 0), extend=True, copy_head=True, fit=False, copy_index=False
                        )

                        wins_by_store = odt.transform_multiindex_to_df(wins_by_store_pivot_table)
                        # paste the dataframe into sheets
                        ws.set_dataframe(
                            wins_by_store.fillna(0), (18, 17), extend=True, copy_head=True, fit=False, copy_index=False
                        )
                        
                    except Exception as dd_err_e:
                        st.error(f"An error occurred pulling DD errors data: {dd_err_e}", icon="🚨")

                # 3. Ubereats Cancellations data ingestion
                ws = ss.worksheet("title", "ubereats_data")
                ws.clear("A3","F3")
                ws.clear("A6","15")
                ws.clear("A18","N")
                ws.clear("Q18","AD")

                with st.spinner('Pulling HOI orders for Ubereats, this may take a moment... ⌛'):
                # Pull the Ubereats TAM errors data
                    if len(ue_errors_df)>0:
                        try:
                            ue_tam, complete_ue_errors_df, grouped_complete_ue_errors_df, tam_pivot_table, tam_by_store_pivot_table = odt.ubereats_errors(ue_errors_df, org_name, uuid, start_date)
                            st.success("Ubereats errors data was successfully pulled", icon="✅" )

                            tam_table = odt.transform_pivot_to_df(tam_pivot_table, "ue_errors_tam")
                            # paste the dataframe into sheets
                            ws.set_dataframe(
                                tam_table.fillna(0), (6, 1), extend=True, copy_head=True, fit=False, copy_index=False
                            )

                            tam_by_store = odt.transform_multiindex_to_df(tam_by_store_pivot_table)
                            # paste the dataframe into sheets
                            ws.set_dataframe(
                                tam_by_store.fillna(0), (18, 0), extend=True, copy_head=True, fit=False, copy_index=False
                            )

                        except Exception as ue_errs_e:
                            st.error(f"An error occurred pulling the UE errors data: {ue_errs_e}", icon="🚨")
                            ue_tam = 0

                    # Pull the Ubereats Winbacks data
                    if len(ue_payments_df)>0:
                        try:
                            ue_winbacks, winbacks_df, wins_pivot_table, wins_by_store_pivot_table = odt.ubereats_payments(ue_payments_df, org_name, start_date)
                            winback_rate = ue_winbacks/ue_tam
                            st.success("Ubereats payments data was successfully pulled", icon="✅" )

                            wins_table = odt.transform_pivot_to_df(wins_pivot_table, "ue_error_winbacks")
                            # paste the dataframe into sheets
                            ws.set_dataframe(
                                wins_table.fillna(0), (6, 4), extend=True, copy_head=True, fit=False, copy_index=False
                            )

                            wins_by_store = odt.transform_multiindex_to_df(wins_by_store_pivot_table)
                            # paste the dataframe into sheets
                            ws.set_dataframe(
                                wins_by_store.fillna(0), (18, 17), extend=True, copy_head=True, fit=False, copy_index=False
                            )

                        except Exception as payouts_e:
                            st.error(f"An error occurred pulling the UE payments data: {payouts_e}", icon="🚨")
                            ue_winbacks = 0
                            winback_rate = 0
                            winbacks_df = pd.Da

                        # Combine the two for the results
                        results_df = pd.DataFrame({
                            'org_name':[org_name],
                            'tam':[ue_tam],
                            'wins':[ue_winbacks],
                            'win_perc':[winback_rate]
                            })

                        # Paste in results
                        ws.set_dataframe(
                            results_df, (2, 1), extend=True, copy_head=True, fit=False, copy_index=False
                        )

                    # 4. Pull the ubereats items errors list
                    if (len(ue_errors_df)>0) and (len(winbacks_df)>0):
                        ws = ss.worksheet("title", "ubereats_menu_performance")
                        ws.clear("A2","B")

                        try:
                            output_df, item_issues_df = odt.ue_link_payments_and_errors(ue_errors_df, winbacks_df)
                            st.success("Ubereats refunds and menu data merged", icon="✅" )

                            # paste the dataframe into sheets
                            ws.set_dataframe(
                                item_issues_df.fillna(0), (0, 0), extend=True, copy_head=True, fit=False, copy_index=False
                            )

                        except Exception as menu_e:
                            st.error(f"An error occurred while merging menu data: {menu_e}", icon="🚨")
                            

                st.markdown('Data transformation complete!')

                #ue_merchant_store_ids = complete_ue_errors_df[['facility_name', 'store_id', 'external_store_id', 'uuid']].drop_duplicates(ignore_index=True)
                #st.dataframe(ue_merchant_store_ids)
                #push_data = st.form_submit_button('Push Ubereats Merchant Store IDs to table')
                #if push_data:
                #    
                #    data_push = tf.push_ue_ids_to_superset(ue_merchant_store_ids, append=False)
                #    st.markdown(data_push)

                #try:
                #    ue_tam, ue_winbacks, win_perc = odt.ubereats_cancellations(ue_errors_df, org_name, uuid)
                #    st.success("Ubereats cancellations data was successfully pulled", icon="✅" )
                #except Exception as e:
                #    st.error(f"An error occurred: {e}", icon="🚨")

                #results_df = pd.DataFrame({
                #'org_name':[folder_name],
                #'tam':[ue_tam],
                #'wins':[ue_winbacks],
                #'win_perc':[win_perc]
                #})

                # paste the dataframe into sheets
                #ws.set_dataframe(
                #    results_df.fillna(0), (2, 1), extend=True, copy_head=True, fit=False, copy_index=False
                #)




