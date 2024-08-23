import streamlit as st
import pandas as pd
import numpy as np
import datetime as dt
##import IPython.display as display
from streamlit.components.v1 import html
import os
#from jinja2 import Template
import functions as func
import st_aggrid
from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, DataReturnMode, JsCode, ColumnsAutoSizeMode
from streamlit_option_menu import option_menu
import streamlit_option_menu as st_menu
import plotly.express as px
from plotly import graph_objects as go
from google.oauth2 import service_account
#from PIL import Image
#import socket
#import altair as alt
import plotly.io as pio
#import webbrowser
import base64
from datetime import datetime, timedelta
import streamlit_toggle as tog
import warnings

# Ignore warnings
warnings.filterwarnings("ignore")

os.environ["IDENTITY_USER"] = "robert.enright"

# Set Plotly default theme
pio.templates.default = "seaborn"

# Initial Streamlit Page
st.set_page_config(page_title='Onboarding Dashboard', layout='wide', initial_sidebar_state="expanded")

# Get 6m ago date
today = datetime.today()
# Calculate the date 6 months ago
six_months_ago = today - timedelta(days=30 * 6)
first_day_six_months_ago = six_months_ago.replace(day=1)

# Here we convert the image to base64 format
def get_img_as_base64(file):
    with open(file, "rb") as f:
        data=f.read()
    return base64.b64encode(data).decode("utf-8")
img = get_img_as_base64("/home/global-growth-ops/onboarding/Apps/OB Master App/Otter Logo.png")
gif = get_img_as_base64("/home/global-growth-ops/onboarding/Apps/OB Master App/OrderFood.gif")


custom_styles = f"""
    <style>
    [data-testid="stSidebar"] {{
        background-image: url(data:image/png;base64,{img});
        background-size: 100px 100px;
        background-repeat: no-repeat;
        padding-top: 30px;
        background-position: 10px 10px;
        margin-top: 0px;
    }}

    .css-16idsys p {{
        font-size: 20px;
        color: ##ffffff7e;
    }}

    div.css-j5r0tf.e1tzin5v1 {{
        background-color: #ffffff;
        border: 3px solid #6b6b6b;
        padding: 2% 2% 2% 2%;
        border-radius: 5px;
        color: #6b6b6b;
    }}

    .dataframe th {{
        background-color: #6b6b6b;
        color: #ffffff;    
        }}
    
    label.css-wvv94f {{
        color: #6b6b6b;
        font-size: 20px;
    }}

    .st-af {{
        font-size: 1.25rem;
    }}

    div[data-testid="stMetricValue"] > div {{
        overflow-wrap: break-word;
        white-space: break-spaces;
        font-size: 1.5rem;
    }}
    </style>
    <br>
    """

st.write(custom_styles, unsafe_allow_html=True)

# Here is the CSS for the custom table styles 
table_styles = [{'selector': 'th','props': [('font-size', '12.5pt'), ('color', 'white'), ('background-color', '#6b6b6b')]}, 
                {'selector': 'tr', 'props':[('background-color', 'white')]},
                {'selector': 'td','props': [('font-size', '12.5pt')]}]

if "select_backlog" not in st.session_state:
    st.session_state.select_backlog = None
if "select_location" not in st.session_state:
    st.session_state.select_location = None
if "sidebar" not in st.session_state:
    st.session_state['sidebar'] = {}
if "button_click" not in st.session_state:
    st.session_state.button_click = False

# Load in the data read
df = func.read_data()

product_criteria_dict = {
    'OM':['account_name', 'parent_account_name', 'facility_id', 'onboarding_id', 'Segment', 'is_future_foods_customer', 'ap_name', 'ap_status', 'ap_cw_date', 'activation_score', 'first_bm_event_date', 'first_confirmed_order', 'needs_om', 'first_om_event_date', 'needs_hardware', 'delivered_date', 'needs_print', 'first_printed_job', 'needs_menu_published', 'first_menu_published_date'],
    'Boost':['account_name', 'parent_account_name', 'facility_id', 'Segment', 'is_future_foods_customer', 'ap_id', 'ap_status', 'ap_cw_date', 'ap_setup_date', 'ap_active_date', 'setup_met', 'activation_met', 'first_active_campaign_day', 'first_booster_order'],
    'Direct Orders - Online Ordering':['account_name', 'parent_account_name', 'facility_id', 'Segment', 'is_future_foods_customer', 'ap_id', 'ap_status', 'ap_cw_date', 'ap_setup_date', 'ap_active_date', 'setup_met', 'activation_met', 'direct_orders_ofo_connected', 'first_d2c_menu_published_date', 'first_d2c_order'],
    'Direct Orders - Dine-in':['account_name', 'parent_account_name', 'facility_id', 'Segment', 'is_future_foods_customer', 'ap_id', 'ap_status', 'ap_cw_date', 'ap_setup_date', 'ap_active_date', 'setup_met', 'activation_met', 'direct_orders_ofo_connected', 'first_d2c_menu_published_date', 'dine_in_enabled', 'first_dine_in_order'],
    'POS Integration':['account_name', 'parent_account_name', 'facility_id', 'Segment', 'is_future_foods_customer', 'ap_id', 'ap_status', 'ap_cw_date', 'ap_setup_date', 'ap_active_date', 'setup_met', 'activation_met', 'pos_menu_bootstrapped', 'first_injected_order'],
    'Direct Orders - Google Food Ordering':['account_name', 'parent_account_name', 'facility_id', 'Segment', 'is_future_foods_customer', 'ap_id', 'ap_status', 'ap_cw_date', 'ap_setup_date', 'ap_active_date', 'setup_met', 'activation_met', 'gfo_ofo_connected', 'first_gfo_menu_published_date', 'first_gfo_order']
}

last_update_path = "/home/global-growth-ops/onboarding/Apps/OB Master App/last_update.txt"

with open(last_update_path, 'r') as f:
        last_updated_date = f.read()

date_obj = dt.datetime.strptime(last_updated_date, '%Y-%m-%d %H:%M:%S.%f')
now = dt.datetime.now()
time_diff = now - date_obj

if time_diff.days > 0:
    time_ago = f'{time_diff.days} days ago'
elif time_diff.seconds // 3600 > 0:
    time_ago = f'{time_diff.seconds // 3600} hours ago'
elif time_diff.seconds // 60 > 0:
    time_ago = f'{time_diff.seconds // 60} minutes ago'
else:
    time_ago = 'just now'

st.sidebar.markdown(f"""
    <div> 
        Last Updated: <span class="last-updated-text">{time_ago}</span>
    </div>
    """, unsafe_allow_html=True)

with st.sidebar:
    view_selected = st_menu.option_menu("Menu", ['Home', 'Onboarding Deep-Dive', 'High Level Overview', 'AppIQ'], icons=['house', 'binoculars', 'activity', 'screwdriver'], default_index=0)

    st.sidebar.info('Please view this tool in Light mode', icon="💡")
    #tog.theme(widget='checkbox', label='Light', value=True, key="theme_box")
    
# Create the dropdown for roles:
#role = st.sidebar.selectbox('Please select your view', ['High Level Overview', 'Onboarding Deep Dive'], key='role')

if view_selected=='Home':
    
    st.header("Welcome to the Otter Onboarding Master App 🦦👋!")

    st.markdown("""
    Brought to you by Global Growth Ops.

    ### What is the Master Onboarding App? 👈

    Our aim is for this app to be a one stop shop for all things onboarding. We have worked closely with the S&P team to construct a comprehensive onboarding table in Superset that contains all applicable onboarding information. The table currently contains information for various products with our goal to scale this table to all products. We will incorporate the activation criteria for each product to the table, so that we easily scale the app for new products. The existing products are:
                
    1. Order Manager
    2. POS Integration
    3. Boost
    4. Direct Orders - Online Ordering
    5. Direct Orders - Dine-in
    6. Google Food Ordering
    7. Mercury - Otter POS

    The app includes two views - Onboarding Deep Dive and High Level Overview, which include the following:

    **Onboarding Deep-Dive 🔎** - here we enable users to find specific parent accounts and view the location level onboarding data. In the case of Onboarding Specialists, they can select their name and their onboarding backlog will appear. From there, they can easily see the status of each account and the tasks required to activate accounts.

    **High Level Overview 📈** - this view provides high level statistics cohorted by week or month. Some of our key visuals include funnel movement, activation criteria analysis, onboarding times and activation rate. The aim is to provide quick digestible views that accurately show the overall performance trends within onboarding.

    **AppIQ 🧠** - this allows the user to ask questions about the app and its data sources and returns an answer to the best of ChatGPT4's ability. Here you can discover what makes this app tick.

    If you have issues or questions feel free to reach out to Robert Enright or post in the **#ob-master-app-feedback** slack channel. 
    """)

    st.markdown(f'<img src="data:image/gif;base64,{gif}" width="600" height="600" alt="order gif">', unsafe_allow_html=True)

elif view_selected=='Onboarding Deep-Dive':

    # CSS to inject contained in a string
    hide_table_row_index = """
                <style>
                thead tr th:first-child {display:none}
                tbody th {display:none}
                tbody tr {align-text:left}
                </style>
                """
    # Inject CSS with Markdown
    st.markdown(hide_table_row_index, unsafe_allow_html=True)

    col1, col2, col3, col4, col5 = st.columns(5)

    # Select view for user 
    with col1:
        selected_view = st.selectbox('Select User View', ['General Parent Search', 'Onboarding Specialist', 'New Bundle View'])
        st.session_state['view'] = selected_view
    
    if selected_view=='Onboarding Specialist':
    # Create a dropdown with unique values from the "Parent Account" column
        activation_owner_list = ['All'] + df['activation_owner'].sort_values(ascending=True).unique().tolist()
        with col2:
            selected_aa = st.selectbox('Select Onboarding Specialist', activation_owner_list)
            st.session_state['aa'] = selected_aa

        with col3:
        # Create a dropdown with unique values from the "Parent Account" column
            parent_list = ['All'] + df['parent_account_name'].loc[df['activation_owner']==selected_aa].sort_values(ascending=True).unique().tolist()
            parent_index = list(parent_list).index("All")

            selected_parent = st.selectbox('Select Parent Account', parent_list, index=parent_index)
            st.session_state['parent'] = selected_parent

        # Logic if looking at all parents
        if selected_parent=='All':
            # Here we defining the inputs for this work flow
            with col4:
                start_date = st.date_input("Start Date", value=dt.date.today() - dt.timedelta(weeks=8))
            with col5:
                end_date = st.date_input("End Date", value=dt.date.today())
            st.session_state['start_date'] = start_date
            st.session_state['end_date'] = end_date

        else:
            # Get the data for the parent selected
            parent_df = func.parent_filtering(df,selected_parent)
            p_summary = func.get_parent_summary(df,selected_parent)
            parent_dic = p_summary.to_dict()
            location_summary = func.get_location_summary(df,selected_parent)

    elif selected_view=='New Bundle View':
        selected_aa = 'All'
        bundle_list = ['All'] + df['bundle_name'].loc[df['bundle_name'].str.contains('[NEW]', na=False)].sort_values(ascending=True).unique().tolist()
        with col2:
            selected_bundle = st.selectbox('Select Bundle', bundle_list)
            st.session_state['bundle'] = selected_bundle
            bundle_df = df.loc[df['bundle_name']==selected_bundle]

        with col3:
            # Create a dropdown with unique values from the "Parent Account" column
            parent_list = ['All'] + df['parent_account_name'].loc[df['bundle_name']==selected_bundle].sort_values(ascending=True).unique().tolist()
            parent_index = list(parent_list).index("All")

            selected_parent = st.selectbox('Select Parent Account', parent_list, index=parent_index)
            st.session_state['parent'] = selected_parent

        # Logic if looking at all parents
        if selected_parent=='All':
            package_data = func.pull_package_c_data(df)
            package_dict = func.get_package_stats(package_data)

        else:
            # Get the data for the parent selected
            parent_df = func.parent_filtering(df,selected_parent)
            p_summary = func.get_parent_summary(df,selected_parent)
            parent_dic = p_summary.to_dict()
            location_summary = func.get_location_summary(df,selected_parent)

    else:
        with col2:
            parent_list = df['parent_account_name'].sort_values(ascending=True).unique().tolist()
            parent_index = list(parent_list).index("Truly Acai")
            selected_parent = st.selectbox('Select Parent Account', parent_list, index=parent_index)
            st.session_state['parent'] = selected_parent

        # Get the data for the parent selected
        parent_df = func.parent_filtering(df,selected_parent)
        p_summary = func.get_parent_summary(df,selected_parent)
        parent_dic = p_summary.to_dict()
        location_summary = func.get_location_summary(df,selected_parent)


    tabs = ["Parent Details", "Order Manager", "Boost", "Direct Orders - Online Ordering", "Dine-in", "Google Food Ordering", "POS Integration", "Mercury - Otter POS"]
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs(tabs)
    selected_tab = st.session_state.get("selected_tab", tabs[1])

    with tab1: # Parent Overview
        st.session_state.selected_tab = tabs[0]

        if (selected_parent=='All') & (selected_view=='Onboarding Specialist'):
            st.markdown("### Book of Business Details:")

            if selected_aa=='All':
                bob=df.copy() 
            else:
                bob = func.get_aa_bob(df, selected_aa)

            bob_data = func.get_product_actions(bob.loc[(bob['ap_status'].isin(['Onboarding', 'Close Won', 'Setup', 'Shipped', 'Delivered'])) & (pd.to_datetime(bob['ap_cw_date']).dt.date>=start_date)])
            aa_dict = func.get_aa_stats(bob)
            # Account URL is the column with hyperlinks
            bob_data['Account URL'] = bob_data.apply(lambda row: 'https://otr-hub.lightning.force.com/lightning/r/Account/' + str(row['account_id']) + '/view', axis=1)
            columns = ['Account Name', 'Account URL', 'Parent Account', 'Parent MRR', 'Product', 'Task List', 'CW Date', 'Onboarding Status', 'Activation Score', 'Next Steps']
            bob_data = bob_data[columns].drop_duplicates(ignore_index=True)

            # Create five columns with their applicable metrics
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.metric("Onboarding Backlog", aa_dict['ob_backlog'])
            with col2:
                st.metric("Close Won Records", aa_dict['cw'])
            with col3:
                st.metric("Setup Records", aa_dict['setup'])
            with col4:
                st.metric("Shipped Records", aa_dict['shipped'])
            with col5:
                st.metric("Delivered Records", aa_dict['delivered'])

        elif (selected_parent=='All') & (selected_view=='New Bundle View'):
            st.markdown("### New Bundle Details:")

            bob_data = func.pull_package_c_data(df)
            package_dict = func.get_package_stats(bob_data)
            # Account URL is the column with hyperlinks
            bob_data['ap_opp_id'] = bob_data.apply(lambda row: 'https://otr-hub.lightning.force.com/lightning/r/Opportunity/' + str(row['ap_opp_id']) + '/view', axis=1)

            # Create five columns with their applicable metrics
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.metric("Opportunities", package_dict['opps'])
            with col2:
                st.metric("OM Active", package_dict['om'])
            with col3:
                st.metric("POS Active", package_dict['pos'])
            with col4:
                st.metric("Boost Active", package_dict['boost'])
            with col5:
                st.metric("D2C Active", package_dict['direct_orders'])

        else:
            st.markdown("### Parent Account Details:")
            # Create five columns with their applicable metrics

            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.metric("Locations:", parent_dic['Locations Accounts:'][selected_parent])
            with col2:
                st.metric("Country:", parent_dic['Country'][selected_parent])
            with col3:
                st.metric("Segment:", parent_dic['Segment'][selected_parent])
            with col4:
                st.metric("Lead Source:", parent_dic['lead_source'][selected_parent])
            with col5:
                st.metric("FF Customer:", parent_dic['is_future_foods_customer'][selected_parent])

            col1.width = None
            col2.width = None
            col3.width = None
            col4.width = None
            col5.width = None

        if (selected_view!='General Parent Search'):

            if selected_parent=='All':

                st.markdown('### Tasks Summary')
                # Build and display the data in an AG Grid
                gb = GridOptionsBuilder.from_dataframe(bob_data, editable=True)

                # Link dictionary
                link_dict = {'Onboarding Specialist':'Account URL', 'New Bundle View':'ap_opp_id'}
                # Configure the OB Records Column to appear as a URL
                gb.configure_column(
                        f"{link_dict[selected_view]}",
                        headerName=f"{link_dict[selected_view]}",
                        cellRenderer=JsCode("""
                            class UrlCellRenderer {
                                init(params) {
                                this.eGui = document.createElement('a');
                                this.eGui.innerText = params.value;
                                this.eGui.setAttribute('href', params.value);
                                this.eGui.setAttribute('style', "text-decoration:none");
                                this.eGui.setAttribute('target', "_blank");
                                }
                                getGui() {
                                return this.eGui;
                                }
                            }
                        """)
                    )


                # Build Ag Grid
                func.build_grid(gb, bob_data, 800)

        else:
            st.markdown('### Product Summary')
            product_data = func.parent_products(parent_df).drop_duplicates(ignore_index=True).fillna("")
            product_data['Account Name'] = product_data['Account Name'] + '#' + 'https://otr-hub.lightning.force.com/lightning/r/Account/' + product_data['account_id'] + '/view'
            def make_clickable(val): 
                name, url = val.split('#')
                return f'<a target="_blank" href="{url}">{name}</a>'
            product_data['Account Name'] = product_data['Account Name'].apply(make_clickable)
            product_data = product_data.drop(columns=['account_id'])
            st.markdown(product_data.to_html(escape=False, index=True),unsafe_allow_html=True)

            #st.table(data=product_data.style.set_table_styles(table_styles))

            st.markdown('### Tasks Summary')
            task_data = func.get_product_actions(parent_df.loc[parent_df['ap_status'].isin(['Onboarding', 'Close Won', 'Setup', 'Shipped', 'Delivered']) & (parent_df['csm_status'].isin(['Active', 'Onboarding']))]).set_index('Account Name').reset_index().drop_duplicates(ignore_index=True)
            task_data['Account Name'] = task_data['Account Name'] + '#' + 'https://otr-hub.lightning.force.com/lightning/r/Account/' + task_data['account_id'] + '/view'
            task_data['Account Name'] = task_data['Account Name'].apply(make_clickable)
            task_data = task_data.drop(columns=['account_id'])
            st.markdown(task_data.to_html(escape=False, index=True),unsafe_allow_html=True)
                
    # If a parent is selected display the parent specific data
    if selected_parent!='All':
        with tab2:

            # Parent OM metric details
            om_records = func.product_filtering(parent_df, "OM")

            if len(om_records) == 0:
                st.warning("#### No records exist for this product, please refer back to parent summary page 👈")

            else:

                st.session_state.selected_tab = tabs[1]
                st.markdown('### Order Manager Onboarding Summary')

                # create 5 columns
                col1, col2, col3, col4, col5  = st.columns(5)

                om_df = om_records.copy()
                om_ob_acc = om_df.loc[(om_df['setup_met']==False) & (~om_df['ap_status'].isin(['Inactive', 'Cancelled', 'Non-OB Cancellation'])), 'account_id'].nunique()
                om_setup_backlog = om_df.loc[(om_df['setup_met']==False) & (om_df['activation_met']==0) & (om_df['ap_status'].isin(['Onboarding', 'Close Won', 'Setup', 'Delivered'])), 'account_id'].nunique()
                om_activation_backlog = om_df.loc[(om_df['setup_met']==True) & (om_df['ap_status'].isin(['Onboarding', 'Close Won', 'Setup', 'Delivered'])), 'account_id'].nunique()
                om_act_acc = om_df.loc[(om_df['ap_status']=="Active"), 'account_id'].nunique()
                om_churned_acc = om_df.loc[(om_df['ap_status'].isin(['Inactive', 'Cancelled', 'Non-OB Cancellation'])), 'account_id'].nunique()

                # Display the metric data for that parent in question
                with col1:
                    st.metric("OM Location Accounts:", len(om_records))
                with col2:
                    st.metric("Active Locations:", om_act_acc)
                with col3:
                    st.metric("Activation Backlog:", om_activation_backlog)
                with col4:
                    st.metric("Setup Backlog:", om_setup_backlog)
                with col5:
                    st.metric("Churned Locations:", om_churned_acc)

                col1.width = None
                col2.width = None
                col3.width = None
                col4.width = None
                col5.width = None

                # Pull and display the Setup Backlog data
                setup_df = func.setup_backlog(om_df, "OM")
                setup_container = st.container() 
                if not setup_df.empty:
                    setup_container.markdown('### Setup Backlog')
                    setup_container.table(data=setup_df.style.set_table_styles(table_styles))

                # Pull and display the Activaton Backlog data
                activation_df = func.activation_backlog(om_df, "OM")
                activation_container = st.container() 
                if not activation_df.empty:
                    activation_container.markdown('### Activation Backlog')
                    activation_container.table(data=activation_df.style.set_table_styles(table_styles))

                # Pull and display the Activated Records data
                activated_df = func.activation_backlog(om_df, "OM", activated=True)
                activated_container = st.container()
                if not activated_df.empty: 
                    activated_container.markdown('### Activated Records')
                    activated_container.table(data=activated_df.style.set_table_styles(table_styles))

                # Location Double Click
                st.markdown('## Location Double Click 🕵️')
                # Create a dropdown with unique location values from the "Parent Account" selected
                location_list = om_df['account_name'].sort_values(ascending=True).unique()
                selected_location = st.selectbox('Select Location:', location_list)

                # Get location details
                location_om_df = func.location_filtering(df,selected_location, "OM")

                # Warning if more than one location
                if len(location_om_df) > 1:
                    st.warning("This location has duplicate records for this product.", icon="⚠️")
                    # For those with duplicates enable users to select both records
                    record_list = location_om_df['ap_id'].sort_values(ascending=True).unique()
                    selected_record = st.selectbox('Select record: ', record_list, key='om_record_select')
                    location_om_df = location_om_df.loc[location_om_df['ap_id']==selected_record]
                    location_om_dict = location_om_df.fillna('').set_index('account_name').to_dict()
                else:
                    location_om_dict = location_om_df.fillna('').set_index('account_name').to_dict()

                # create 4 columns
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    # Create the SFDC URL for the OB record in question
                    ob_url = 'https://otr-hub.lightning.force.com/lightning/r/Onboarding__c/' + location_om_df.iloc[0]['onboarding_id'] + '/view'
                    st.markdown(f'''<a href={ob_url}><button style="color:Red;">View SFDC Record</button></a>''', unsafe_allow_html=True)

                with col2:
                    # Create the SkuSku Parent URL for the parent account selected
                    sku_url = 'https://tools.cloudkitchens.com/organizations/' + location_om_df.iloc[0]['parent_org_id'] + '/locations'
                    st.markdown(f'''<a href={sku_url}><button style="color:Red;">Sku Sku Locations</button></a>''', unsafe_allow_html=True)

                with col3:
                    # Create the SkuSku Parent URL for the parent account selected
                    invoices_url = 'https://beam.cssinternal.com/customers/' + location_om_df.iloc[0]['parent_org_id'] + '/billing/invoices'
                    st.markdown(f'''<a href={invoices_url}><button style="color:Red;">Beam Invoices</button></a>''', unsafe_allow_html=True)

                with col4:
                    # Create the SkuSku Parent URL for the parent account selected
                    subs_url = 'https://beam.cssinternal.com/customers/' + location_om_df.iloc[0]['parent_org_id'] + '/products/otter-subscriptions'
                    st.markdown(f'''<a href={subs_url}><button style="color:Red;">Beam Subscriptions</button></a>''', unsafe_allow_html=True)

                st.markdown('### OB record summary:')
                # create 5 columns and display the location record in question
                col1, col2, col3, col4, col5  = st.columns(5)

                with col1:
                    st.metric("Closed Won Date:", '' if pd.isna(location_om_dict['ap_cw_date'][selected_location]) else location_om_dict['ap_cw_date'][selected_location].strftime('%Y-%m-%d'))
                with col2:
                    st.metric("Status:", location_om_dict['ap_status'][selected_location])
                with col3:
                    st.metric("Hardware:", location_om_dict['hardware'][selected_location])
                with col4:
                    st.metric("Bundle:", location_om_dict['bundle_name'][selected_location])
                with col5:
                    st.metric("POS integration:", location_om_dict['has_pos_integration_2'][selected_location])

                col1.width = None
                col2.width = None
                col3.width = None
                col4.width = None
                col5.width = None

                # create 2 columns for the setup and activation data
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown('#### Setup details:')
                    setup_columns = ['facility_id', 'parent_org_id', 'ap_cw_date', 'first_active_storelink_date', 'activated_ofos_all_time', 
                                     'upsell_opportunity__c', 'has_pos_integration_2', 'pos_ob_status'] 
                                     #'ob_task_owner', 'internal_ob_actions', 'ob_activity_count', 'ob_last_activity']
                    location_om_df['ap_cw_date'] = location_om_df['ap_cw_date'].dt.strftime('%Y-%m-%d')
                    # Rename Output Columns and transpose the table
                    output_df = location_om_df[setup_columns].rename(columns={
                        'facility_id':'Facility ID', 'parent_org_id':'Organization ID', 'first_active_storelink_date':'First Active Storelink Date', 
                        'ap_cw_date':'Account Product CW Date', 'activated_ofos_all_time':'Activated OFOs', 'upsell_opportunity__c':'Upsell Opportunity', 
                        'has_pos_integration_2':'POS Integration', 'pos_ob_status':'POS Integration Status'}).transpose().reset_index().rename(columns={'index':'Field'})
                        # 'internal_ob_actions':'OM Actions', 'ob_activity_count':'Activity Count', 'ob_last_activity':'Last Activity Date', 'ob_task_owner':'Task Owner'
                    output_df.columns.values[-1] = 'Value'
                    output_df = output_df.fillna('')
                    st.table(output_df[['Field', 'Value']].style.set_table_styles(table_styles))

                with col2:
                    st.markdown('#### Activation details:')
                    activation_columns = ['first_om_event_date', 'last_om_event__c', 'first_bm_event_date', 'last_bm_event__c', 'first_confirmed_order', 'Orders_Last_30_Days__c', 'first_printed_job', 'Printed_Orders_Last_14_Days__c', 'delivered_date', 'first_menu_published_date', ]
                    # Format columns for final Output
                    location_om_df['delivered_date'] = location_om_df['delivered_date'].dt.strftime('%Y-%m-%d')
                    for col in ['Orders_Last_30_Days__c', 'Printed_Orders_Last_14_Days__c']:
                        location_om_df[col] = location_om_df[col].fillna(0).apply(np.int64)
                    # Rename Output Columns and transpose the table
                    output_df = location_om_df[activation_columns].rename(columns={'first_om_event_date':'First OM event 🅾️', 'last_om_event__c':'Last OM Event', 'first_bm_event_date':'First BM Event 🅱️', 'last_bm_event__c':'Last BM Event', 'first_confirmed_order':'First Order Date 📤', 'Orders_Last_30_Days__c':'Orders Last 30 Days', 'first_printed_job':'First Print 🖨️', 'Printed_Orders_Last_14_Days__c':'Printed Orders Last 14 Days', 'delivered_date':'Hardware Delivered Date 🚚', 'first_menu_published_date':'First Menu Published Date 📖'}).transpose().reset_index().rename(columns={'index':'Field'})
                    output_df.columns.values[-1] = 'Value'
                    output_df = output_df.fillna('')
                    # Write the transposed table back to Streamlit
                    st.table(output_df[['Field', 'Value']].style.set_table_styles(table_styles))

        with tab3: # Boost Tab

            # Parent OM metric details
            boost_records = func.product_filtering(parent_df, "Boost")

            if len(boost_records) == 0:
                st.warning("#### No records exist for this product, please refer back to parent summary page 👈")

            else:
                st.session_state.selected_tab = tabs[2]
                st.markdown('## Boost Onboarding Summary')

                # create 5 columns
                col1, col2, col3, col4, col5  = st.columns(5)

                # Parent OM metric details
                boost_df = boost_records.copy()
                boost_ob_acc = boost_df.loc[(boost_df['setup_met']==False) & (~boost_df['ap_status'].isin(['Inactive'])), 'account_id'].nunique()
                boost_setup_backlog = boost_df.loc[(boost_df['setup_met']==False) & (boost_df['activation_met']==0) & (boost_df['ap_status'].isin(['Onboarding', 'Close Won', 'Setup', 'Delivered'])), 'account_id'].nunique()
                boost_activation_backlog = boost_df.loc[(boost_df['setup_met']==True) & (boost_df['ap_status'].isin(['Onboarding', 'Close Won', 'Setup', 'Delivered'])), 'account_id'].nunique()
                boost_act_acc = boost_df.loc[(boost_df['ap_status']=="Active"), 'account_id'].nunique()
                boost_churned_acc = boost_df.loc[(boost_df['ap_status'].isin(['Inactive', 'Cancelled', 'Non-OB Cancellation'])), 'account_id'].nunique()

                # Display the metric data for that parent in question
                with col1:
                    st.metric("Boost Location Accounts:", len(boost_records))
                with col2:
                    st.metric("Active Locations:", boost_act_acc)
                with col3:
                    st.metric("Activation Backlog:", boost_activation_backlog)
                with col4:
                    st.metric("Setup Backlog:", boost_setup_backlog)
                with col5:
                    st.metric("Churned Locations:", boost_churned_acc)

                col1.width = None
                col2.width = None
                col3.width = None
                col4.width = None
                col5.width = None

                # Pull and display the Setup Backlog data
                setup_df = func.setup_backlog(boost_df, "Boost")
                setup_container = st.container() 
                if not setup_df.empty:
                    setup_container.markdown('### Setup Backlog')
                    setup_container.table(data=setup_df.style.set_table_styles(table_styles))

                # Pull and display the Activaton Backlog data
                activation_df = func.activation_backlog(boost_df, "Boost")
                activation_container = st.container() 
                if not activation_df.empty:
                    activation_container.markdown('### Activation Backlog')
                    activation_container.table(data=activation_df.style.set_table_styles(table_styles))

                # Pull and display the Activated Records data
                activated_df = func.activation_backlog(boost_df, "Boost", activated=True)
                activated_container = st.container()
                if not activated_df.empty: 
                    activated_container.markdown('### Activated Records')
                    activated_container.table(data=activated_df.style.set_table_styles(table_styles))

                # Location Double Click
                st.markdown('## Location Double Click 🕵️')
                # Create a dropdown with unique location values from the "Parent Account" selected
                location_list = boost_df['account_name'].sort_values(ascending=True).unique()
                selected_location = st.selectbox('Select Location: ', location_list)
                
                # Get location details
                location_boost_df = func.location_filtering(df,selected_location, 'Boost')

                # Warning if more than one location
                if len(location_boost_df) > 1:
                    st.warning("This location has duplicate records for this product.", icon="⚠️")
                    # For those with duplicates enable users to select both records
                    record_list = location_boost_df['ap_id'].sort_values(ascending=True).unique()
                    selected_record = st.selectbox('Select record:', record_list , key='boost_record_select')
                    location_boost_df = location_boost_df.loc[location_boost_df['ap_id']==selected_record]
                    location_boost_dict = location_boost_df.fillna('').set_index('account_name').to_dict()
                else:
                    location_boost_dict = location_boost_df.fillna('').set_index('account_name').to_dict()

                # create 4 columns
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    # Create the SFDC URL for the OB record in question
                    ap_url = 'https://otr-hub.lightning.force.com/lightning/r/Account_Product__c/' + str(location_boost_df.iloc[0]['ap_id']) + '/view'
                    st.markdown(f'''<a href={ap_url}><button style="color:Red;">View Boost Record</button></a>''', unsafe_allow_html=True)

                with col2:
                    # Create the SkuSku Parent URL for the parent account selected
                    sku_url = 'https://tools.cloudkitchens.com/organizations/' + location_boost_df.iloc[0]['parent_org_id'] + '/locations'
                    st.markdown(f'''<a href={sku_url}><button style="color:Red;">Sku Sku Locations</button></a>''', unsafe_allow_html=True)

                with col3:
                    # Create the SkuSku Parent URL for the parent account selected
                    invoices_url = 'https://beam.cssinternal.com/customers/' + location_boost_df.iloc[0]['parent_org_id'] + '/billing/invoices'
                    st.markdown(f'''<a href={invoices_url}><button style="color:Red;">Beam Invoices</button></a>''', unsafe_allow_html=True)

                with col4:
                    # Create the SkuSku Parent URL for the parent account selected
                    subs_url = 'https://beam.cssinternal.com/customers/' + location_boost_df.iloc[0]['parent_org_id'] + '/products/otter-subscriptions'
                    st.markdown(f'''<a href={subs_url}><button style="color:Red;">Beam Subscriptions</button></a>''', unsafe_allow_html=True)
                    
                col1.width = None
                col2.width = None
                col3.width = None
                col4.width = None

                st.markdown('### Account Product summary:')
                # create 5 columns and display the location record in question
                col1, col2, col3, col4, col5  = st.columns(5)

                with col1:
                    st.metric("Closed Won Date:", '' if pd.isna(location_boost_dict['ap_cw_date'][selected_location]) else location_boost_dict['ap_cw_date'][selected_location].strftime('%Y-%m-%d'))
                with col2:
                    st.metric("Status:", location_boost_dict['ap_status'][selected_location])
                with col3:
                    st.metric("First Campaign Date:", location_boost_dict['first_active_campaign_day'][selected_location])
                with col4:
                    st.metric("First Boosted Order Date:", location_boost_dict['first_booster_order'][selected_location])
                with col5:
                    st.metric("Boosted Orders L30D:", location_boost_dict['boosted_orders_l30d'][selected_location])

                col1.width = None
                col2.width = None
                col3.width = None
                col4.width = None
                col5.width = None

                # create 2 columns for the setup and activation data
                col1, col2 = st.columns(2)

                # create 2 columns for the setup and activation data
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown('#### Setup details:')
                    setup_columns = ['facility_id', 'parent_org_id', 'intends_to_use_product', 'first_active_storelink_date', 'ap_cw_date', 'ap_setup_date', 'upsell_opportunity__c', 'activated_ofos_all_time', 'first_active_campaign_day']
                    # Rename Output Columns and transpose the table
                    output_df = location_boost_df[setup_columns].rename(columns={'facility_id':'Facility ID', 'parent_org_id':'Organization ID', 'intends_to_use_product': 'Intends to use', 'first_active_storelink_date':'First Active Storelink Date', 'upsell_opportunity__c':'Upsell Opportunity','ap_setup_date':'Setup Date', 'activated_ofos_all_time':'Activated OFOs', 'first_active_campaign_day':'First Campaign Date'}).transpose().reset_index().rename(columns={'index':'Field'})
                    output_df.columns.values[-1] = 'Value'
                    output_df = output_df.fillna('')
                    st.table(output_df[['Field', 'Value']].style.set_table_styles(table_styles))

                with col2:
                    st.markdown('#### Activation details:')
                    activation_columns = ['first_booster_order', 'boosted_orders_l30d']
                    # Format columns for final Output
                    location_boost_df['delivered_date'] = location_boost_df['delivered_date'].dt.strftime('%Y-%m-%d')
                    for col in ['Orders_Last_30_Days__c', 'Printed_Orders_Last_14_Days__c']:
                        location_boost_df[col] = location_boost_df[col].fillna(0).apply(np.int64)
                    # Rename Output Columns and transpose the table
                    output_df = location_boost_df[activation_columns].rename(columns={'first_booster_order':'First Boosted Order Date 📤', 'boosted_orders_l30d':'Boosted Orders Last 30 Days'}).transpose().reset_index().rename(columns={'index':'Field'})
                    output_df.columns.values[-1] = 'Value'
                    output_df = output_df.fillna('')
                    # Write the transposed table back to Streamlit
                    st.table(output_df[['Field', 'Value']].style.set_table_styles(table_styles))  

        with tab4: # Direct Orders Online Ordering Tab

            # Parent OM metric details
            d2c_records = func.product_filtering(parent_df, "Direct Orders - Online Ordering")

            if len(d2c_records) == 0:
                st.warning("#### No records exist for this product, please refer back to parent summary page 👈")

            else:
                st.session_state.selected_tab = tabs[2]
                st.markdown('## Online Ordering Onboarding Summary')

                # create 5 columns
                col1, col2, col3, col4, col5  = st.columns(5)

                # Parent OM metric details
                d2c_df = d2c_records.copy()
                d2c_ob_acc = d2c_df.loc[(d2c_df['setup_met']==False) & (~d2c_df['ap_status'].isin(['Inactive'])), 'account_id'].nunique()
                d2c_setup_backlog = d2c_df.loc[(d2c_df['setup_met']==False) & (d2c_df['activation_met']==0) & (d2c_df['ap_status'].isin(['Onboarding', 'Close Won', 'Setup', 'Delivered'])), 'account_id'].nunique()
                d2c_activation_backlog = d2c_df.loc[(d2c_df['setup_met']==True) & (d2c_df['ap_status'].isin(['Onboarding', 'Close Won', 'Setup', 'Delivered'])), 'account_id'].nunique()
                d2c_act_acc = d2c_df.loc[(d2c_df['ap_status']=="Active"), 'account_id'].nunique()
                d2c_churned_acc = d2c_df.loc[(d2c_df['ap_status'].isin(['Inactive', 'Cancelled', 'Non-OB Cancellation'])), 'account_id'].nunique()

                # Display the metric data for that parent in question
                with col1:
                    st.metric("D2C Location Accounts:", len(d2c_records))
                with col2:
                    st.metric("Active Locations:", d2c_act_acc)
                with col3:
                    st.metric("Activation Backlog:", d2c_activation_backlog)
                with col4:
                    st.metric("Setup Backlog:", d2c_setup_backlog)
                with col5:
                    st.metric("Churned Locations:", d2c_churned_acc)

                col1.width = None
                col2.width = None
                col3.width = None
                col4.width = None
                col5.width = None

                # Pull and display the Setup Backlog data
                setup_df = func.setup_backlog(d2c_df, "Direct Orders - Online Ordering")
                setup_container = st.container() 
                if not setup_df.empty:
                    setup_container.markdown('### Setup Backlog')
                    setup_container.table(data=setup_df.style.set_table_styles(table_styles))

                # Pull and display the Activaton Backlog data
                activation_df = func.activation_backlog(d2c_df, "Direct Orders - Online Ordering")
                activation_container = st.container() 
                if not activation_df.empty:
                    activation_container.markdown('### Activation Backlog')
                    activation_container.table(data=activation_df.style.set_table_styles(table_styles))
            
                # Pull and display the Activated Records data
                activated_df = func.activation_backlog(d2c_df, "Direct Orders - Online Ordering", activated=True)
                activated_container = st.container()
                if not activated_df.empty: 
                    activated_container.markdown('### Activated Records')
                    activated_container.table(data=activated_df.style.set_table_styles(table_styles))

                # Location Double Click
                st.markdown('## Location Double Click 🕵️')
                # Create a dropdown with unique location values from the "Parent Account" selected
                location_list = d2c_df['account_name'].sort_values(ascending=True).unique()
                selected_location = st.selectbox('Select Location:  ', location_list)

                # Get location details
                location_d2c_df = func.location_filtering(df,selected_location, 'Direct Orders - Online Ordering')

                # Warning if more than one location
                if len(location_d2c_df) > 1:
                    st.warning("This location has duplicate records for this product.", icon="⚠️")
                    # For those with duplicates enable users to select both records
                    record_list = location_d2c_df['ap_id'].sort_values(ascending=True).unique()
                    selected_record = st.selectbox('Select record:', record_list, key='d2c_record_select')
                    location_d2c_df = location_d2c_df.loc[location_d2c_df['ap_id']==selected_record]
                    location_d2c_dict = location_d2c_df.fillna('').set_index('account_name').to_dict()
                else:
                    location_d2c_dict = location_d2c_df.fillna('').set_index('account_name').to_dict()

                # create 4 columns
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    # Create the SFDC URL for the OB record in question
                    ap_url = 'https://otr-hub.lightning.force.com/lightning/r/Account_Product__c/' + str(location_d2c_df.iloc[0]['ap_id']) + '/view'
                    st.markdown(f'''<a href={ap_url}><button style="color:Red;">View Direct Orders Record</button></a>''', unsafe_allow_html=True)

                with col2:
                    # Create the SkuSku Parent URL for the parent account selected
                    sku_url = 'https://tools.cloudkitchens.com/organizations/' + location_d2c_df.iloc[0]['parent_org_id'] + '/locations'
                    st.markdown(f'''<a href={sku_url}><button style="color:Red;">Sku Sku Locations</button></a>''', unsafe_allow_html=True)

                with col3:
                    # Create the SkuSku Parent URL for the parent account selected
                    invoices_url = 'https://beam.cssinternal.com/customers/' + location_d2c_df.iloc[0]['parent_org_id'] + '/billing/invoices'
                    st.markdown(f'''<a href={invoices_url}><button style="color:Red;">Beam Invoices</button></a>''', unsafe_allow_html=True)

                with col4:
                    # Create the SkuSku Parent URL for the parent account selected
                    subs_url = 'https://beam.cssinternal.com/customers/' + location_d2c_df.iloc[0]['parent_org_id'] + '/products/otter-subscriptions'
                    st.markdown(f'''<a href={subs_url}><button style="color:Red;">Beam Subscriptions</button></a>''', unsafe_allow_html=True)
                    
                col1.width = None
                col2.width = None
                col3.width = None
                col4.width = None

                st.markdown('### Account Product summary:')
                # create 5 columns and display the location record in question
                col1, col2, col3, col4, col5  = st.columns(5)

                with col1:
                    st.metric("Closed Won Date:", '' if pd.isna(location_d2c_dict['ap_cw_date'][selected_location]) else location_d2c_dict['ap_cw_date'][selected_location].strftime('%Y-%m-%d'))
                with col2:
                    st.metric("Status:", location_d2c_dict['ap_status'][selected_location])
                with col3:
                    st.metric("D2C Menu Published Date:", location_d2c_dict['first_d2c_menu_published_date'][selected_location])
                with col4:
                    st.metric("First D2C Order Date:", location_d2c_dict['first_d2c_order'][selected_location])
                with col5:
                    st.metric("Total D2C Orders:", location_d2c_dict['total_d2c_orders'][selected_location])

                col1.width = None
                col2.width = None
                col3.width = None
                col4.width = None
                col5.width = None

                # create 2 columns for the setup and activation data
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown('#### Setup details:')
                    setup_columns = ['facility_id', 'parent_org_id', 'intends_to_use_product', 'first_active_storelink_date', 'ap_setup_date', 'upsell_opportunity__c', 'activated_ofos_all_time', 'direct_orders_ofo_connected', 'first_d2c_menu_published_date']
                    # Rename Output Columns and transpose the table
                    output_df = location_d2c_df[setup_columns].rename(columns={'facility_id':'Facility ID', 'parent_org_id':'Organization ID', 'intends_to_use_product': 'Intends to use', 'upsell_opportunity__c':'Upsell Opportunity', 'first_active_storelink_date':'First Active Storelink Date', 'ap_setup_date':'Setup Date', 'activated_ofos_all_time':'Activated OFOs', 'direct_orders_ofo_connected':'D2C OFO Connected', 'first_d2c_menu_published_date':'D2C Menu Publish Date'}).transpose().reset_index().rename(columns={'index':'Field'})
                    output_df.columns.values[-1] = 'Value'
                    output_df = output_df.fillna('')
                    st.table(output_df[['Field', 'Value']].style.set_table_styles(table_styles))

                with col2:
                    st.markdown('#### Activation details:')
                    activation_columns = ['first_d2c_order', 'total_d2c_orders']
                    # Format columns for final Output
                    #location_d2c_df['first_d2c_order'] = location_d2c_df['first_d2c_order'].dt.strftime('%Y-%m-%d')
                    for col in ['total_d2c_orders']:
                        location_d2c_df[col] = location_d2c_df[col].fillna(0).apply(np.int64)
                    # Rename Output Columns and transpose the table
                    output_df = location_d2c_df[activation_columns].rename(columns={'first_d2c_order':'First Direct Orders Order Date 📤', 'total_d2c_orders':'Total D2C Orders 📟'}).transpose().reset_index().rename(columns={'index':'Field'})
                    output_df.columns.values[-1] = 'Value'
                    output_df = output_df.fillna('')
                    # Write the transposed table back to Streamlit
                    st.table(output_df[['Field', 'Value']].style.set_table_styles(table_styles))

        with tab5: # Dine-in Tab

            # Parent OM metric details
            dine_in_records = func.product_filtering(parent_df, "Direct Orders - Dine-in")

            if len(dine_in_records) == 0:
                st.warning("#### No records exist for this product, please refer back to parent summary page 👈")

            else:
                st.session_state.selected_tab = tabs[2]
                st.markdown('## Dine-in Onboarding Summary')

                # create 5 columns
                col1, col2, col3, col4, col5  = st.columns(5)

                # Parent OM metric details
                dine_in_df = dine_in_records.copy()
                dine_in_ob_acc = dine_in_df.loc[(dine_in_df['setup_met']==False) & (~dine_in_df['ap_status'].isin(['Inactive'])), 'account_id'].nunique()
                dine_in_setup_backlog = dine_in_df.loc[(dine_in_df['setup_met']==False) & (dine_in_df['activation_met']==0) & (dine_in_df['ap_status'].isin(['Onboarding', 'Close Won', 'Setup', 'Delivered'])), 'account_id'].nunique()
                dine_in_activation_backlog = dine_in_df.loc[(dine_in_df['setup_met']==True) & (dine_in_df['ap_status'].isin(['Onboarding', 'Close Won', 'Setup', 'Delivered'])), 'account_id'].nunique()
                dine_in_act_acc = dine_in_df.loc[(dine_in_df['ap_status']=="Active"), 'account_id'].nunique()
                dine_in_churned_acc = dine_in_df.loc[(dine_in_df['ap_status'].isin(['Inactive', 'Cancelled', 'Non-OB Cancellation'])), 'account_id'].nunique()

                # Display the metric data for that parent in question
                with col1:
                    st.metric("Dine-in Location Accounts:", len(dine_in_records))
                with col2:
                    st.metric("Active Locations:", dine_in_act_acc)
                with col3:
                    st.metric("Activation Backlog:", dine_in_activation_backlog)
                with col4:
                    st.metric("Setup Backlog:", dine_in_setup_backlog)
                with col5:
                    st.metric("Churned Locations:", dine_in_churned_acc)

                col1.width = None
                col2.width = None
                col3.width = None
                col4.width = None
                col5.width = None

                # Pull and display the Setup Backlog data
                setup_df = func.setup_backlog(dine_in_df, "Direct Orders - Dine-in")
                setup_container = st.container() 
                if not setup_df.empty:
                    setup_container.markdown('### Setup Backlog')
                    setup_container.table(data=setup_df.style.set_table_styles(table_styles))

                # Pull and display the Activaton Backlog data
                activation_df = func.activation_backlog(dine_in_df, "Direct Orders - Dine-in")
                activation_container = st.container() 
                if not activation_df.empty:
                    activation_container.markdown('### Activation Backlog')
                    activation_container.table(data=activation_df.style.set_table_styles(table_styles))

                # Pull and display the Activated Records data
                activated_df = func.activation_backlog(dine_in_df, "Direct Orders - Dine-in", activated=True)
                activated_container = st.container()
                if not activated_df.empty: 
                    activated_container.markdown('### Activated Records')
                    activated_container.table(data=activated_df.style.set_table_styles(table_styles))

                # Location Double Click
                st.markdown('## Location Double Click 🕵️')
                # Create a dropdown with unique location values from the "Parent Account" selected
                location_list = dine_in_df['account_name'].sort_values(ascending=True).unique()
                selected_location = st.selectbox('Select Location:    ', location_list)

                # Get location details
                location_dine_in_df = func.location_filtering(df,selected_location, 'Direct Orders - Dine-in')

                # Warning if more than one location
                if len(location_dine_in_df) > 1:
                    st.warning("This location has duplicate records for this product.", icon="⚠️")
                    # For those with duplicates enable users to select both records
                    record_list = location_dine_in_df['ap_id'].sort_values(ascending=True).unique()
                    selected_record = st.selectbox('Select record:', record_list, key='dine_in_record_select')
                    location_dine_in_df = location_dine_in_df.loc[location_dine_in_df['ap_id']==selected_record]
                    location_dine_in_dict = location_dine_in_df.fillna('').set_index('account_name').to_dict()
                else:
                    location_dine_in_dict = location_dine_in_df.fillna('').set_index('account_name').to_dict()

                # create 4 columns
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    # Create the SFDC URL for the OB record in question
                    ap_url = 'https://otr-hub.lightning.force.com/lightning/r/Account_Product__c/' + str(location_dine_in_df.iloc[0]['ap_id']) + '/view'
                    st.markdown(f'''<a href={ap_url}><button style="color:Red;">View Dine-in Record</button></a>''', unsafe_allow_html=True)

                with col2:
                    # Create the SkuSku Parent URL for the parent account selected
                    sku_url = 'https://tools.cloudkitchens.com/organizations/' + location_dine_in_df.iloc[0]['parent_org_id'] + '/locations'
                    st.markdown(f'''<a href={sku_url}><button style="color:Red;">Sku Sku Locations</button></a>''', unsafe_allow_html=True)

                with col3:
                    # Create the SkuSku Parent URL for the parent account selected
                    invoices_url = 'https://beam.cssinternal.com/customers/' + location_dine_in_df.iloc[0]['parent_org_id'] + '/billing/invoices'
                    st.markdown(f'''<a href={invoices_url}><button style="color:Red;">Beam Invoices</button></a>''', unsafe_allow_html=True)

                with col4:
                    # Create the SkuSku Parent URL for the parent account selected
                    subs_url = 'https://beam.cssinternal.com/customers/' + location_dine_in_df.iloc[0]['parent_org_id'] + '/products/otter-subscriptions'
                    st.markdown(f'''<a href={subs_url}><button style="color:Red;">Beam Subscriptions</button></a>''', unsafe_allow_html=True)
                    
                col1.width = None
                col2.width = None
                col3.width = None
                col4.width = None

                st.markdown('### Account Product summary:')
                # create 5 columns and display the location record in question
                col1, col2, col3, col4, col5  = st.columns(5)

                with col1:
                    st.metric("Closed Won Date:", '' if pd.isna(location_dine_in_dict['ap_cw_date'][selected_location]) else location_dine_in_dict['ap_cw_date'][selected_location].strftime('%Y-%m-%d'))
                with col2:
                    st.metric("Status:", location_dine_in_dict['ap_status'][selected_location])
                with col3:
                    st.metric("Dine-in Enabled Date:", location_dine_in_dict['dine_in_enabled_date'][selected_location])
                with col4:
                    st.metric("First Dine-in Order Date:", location_dine_in_dict['first_dine_in_order'][selected_location])
                with col5:
                    st.metric("Total Dine-in Orders:", location_dine_in_dict['total_dine_in_orders'][selected_location])

                col1.width = None
                col2.width = None
                col3.width = None
                col4.width = None
                col5.width = None

                # create 2 columns for the setup and activation data
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown('#### Setup details:')
                    setup_columns = ['facility_id', 'parent_org_id', 'intends_to_use_product', 'first_active_storelink_date', 'ap_setup_date', 'upsell_opportunity__c', 'activated_ofos_all_time', 'direct_orders_ofo_connected', 'first_d2c_menu_published_date', 'dine_in_enabled']
                    # Rename Output Columns and transpose the table
                    output_df = location_dine_in_df[setup_columns].rename(columns={'facility_id':'Facility ID', 'parent_org_id':'Organization ID', 'intends_to_use_product': 'Intends to use', 'first_active_storelink_date':'First Active Storelink Date', 'upsell_opportunity__c':'Upsell Opportunity', 'ap_setup_date':'Setup Date', 'activated_ofos_all_time':'Activated OFOs', 'direct_orders_ofo_connected':'D2C OFO Connected', 'first_d2c_menu_published_date':'D2C Menu Publish Date', 'dine_in_enabled':'Dine-in Enabled'}).transpose().reset_index().rename(columns={'index':'Field'})
                    output_df.columns.values[-1] = 'Value'
                    output_df = output_df.fillna('')
                    st.table(output_df[['Field', 'Value']].style.set_table_styles(table_styles))

                with col2:
                    st.markdown('#### Activation details:')
                    activation_columns = ['first_dine_in_order', 'total_dine_in_orders']
                    # Format columns for final Output
                    for col in ['total_dine_in_orders']:
                        location_dine_in_df[col] = location_dine_in_df[col].fillna(0).apply(np.int64)
                    # Rename Output Columns and transpose the table
                    output_df = location_dine_in_df[activation_columns].rename(columns={'first_dine_in_order':'First Dine-in Order Date 📤', 'total_dine_in_orders':'Total Dine-in Orders 📟'}).transpose().reset_index().rename(columns={'index':'Field'})
                    output_df.columns.values[-1] = 'Value'
                    output_df = output_df.fillna('')
                    # Write the transposed table back to Streamlit
                    st.table(output_df[['Field', 'Value']].style.set_table_styles(table_styles))

        with tab6: # Google Food Ordering Tab

            # Parent OM metric details
            gfo_records = func.product_filtering(parent_df, "Direct Orders - Google Food Ordering")

            if len(gfo_records) == 0:
                st.warning("#### No records exist for this product, please refer back to parent summary page 👈")

            else:
                st.session_state.selected_tab = tabs[2]
                st.markdown('## GFO Onboarding Summary')

                # create 5 columns
                col1, col2, col3, col4, col5  = st.columns(5)

                # Parent OM metric details
                gfo_df = gfo_records.copy()
                gfo_ob_acc = gfo_df.loc[(gfo_df['setup_met']==False) & (~gfo_df['ap_status'].isin(['Inactive'])), 'account_id'].nunique()
                gfo_setup_backlog = gfo_df.loc[(gfo_df['setup_met']==False) & (gfo_df['activation_met']==0) & (gfo_df['ap_status'].isin(['Onboarding', 'Close Won', 'Setup', 'Delivered'])), 'account_id'].nunique()
                gfo_activation_backlog = gfo_df.loc[(gfo_df['setup_met']==True) & (gfo_df['ap_status'].isin(['Onboarding', 'Close Won', 'Setup', 'Delivered'])), 'account_id'].nunique()
                gfo_act_acc = gfo_df.loc[(gfo_df['ap_status']=="Active"), 'account_id'].nunique()
                gfo_churned_acc = gfo_df.loc[(gfo_df['ap_status'].isin(['Inactive', 'Cancelled', 'Non-OB Cancellation'])), 'account_id'].nunique()

                # Display the metric data for that parent in question
                with col1:
                    st.metric("Boost Location Accounts:", len(gfo_records))
                with col2:
                    st.metric("Active Locations:", gfo_act_acc)
                with col3:
                    st.metric("Activation Backlog:", gfo_activation_backlog)
                with col4:
                    st.metric("Setup Backlog:", gfo_setup_backlog)
                with col5:
                    st.metric("Churned Locations:", gfo_churned_acc)

                col1.width = None
                col2.width = None
                col3.width = None
                col4.width = None
                col5.width = None

                # Pull and display the Setup Backlog data
                setup_df = func.setup_backlog(gfo_df, "Direct Orders - Google Food Ordering")
                setup_container = st.container() 
                if not setup_df.empty:
                    setup_container.markdown('### Setup Backlog')
                    setup_container.table(data=setup_df.style.set_table_styles(table_styles))

                # Pull and display the Activaton Backlog data
                activation_df = func.activation_backlog(gfo_df, "Direct Orders - Google Food Ordering")
                activation_container = st.container() 
                if not activation_df.empty:
                    activation_container.markdown('### Activation Backlog')
                    activation_container.table(data=activation_df.style.set_table_styles(table_styles))
            
                # Pull and display the Activated Records data
                activated_df = func.activation_backlog(gfo_df, "Direct Orders - Google Food Ordering", activated=True)
                activated_container = st.container()
                if not activated_df.empty: 
                    activated_container.markdown('### Activated Records')
                    activated_container.table(data=activated_df.style.set_table_styles(table_styles))

                # Location Double Click
                st.markdown('## Location Double Click 🕵️')
                # Create a dropdown with unique location values from the "Parent Account" selected
                location_list = gfo_df['account_name'].sort_values(ascending=True).unique()
                selected_location = st.selectbox('Select Location:      ', location_list)
                
                # Get location details
                location_gfo_df = func.location_filtering(df,selected_location, 'Direct Orders - Google Food Ordering')

                # Warning if more than one location
                if len(location_gfo_df) > 1:
                    st.warning("This location has duplicate records for this product.", icon="⚠️")
                    # For those with duplicates enable users to select both records
                    record_list = location_gfo_df['ap_id'].sort_values(ascending=True).unique()
                    selected_record = st.selectbox('Select record:', record_list, key='gfo_record_select')
                    location_gfo_df = location_gfo_df.loc[location_gfo_df['ap_id']==selected_record]
                    location_gfo_dict = location_gfo_df.fillna('').set_index('account_name').to_dict()
                else:
                    location_gfo_dict = location_gfo_df.fillna('').set_index('account_name').to_dict()

                # create 4 columns
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    # Create the SFDC URL for the OB record in question
                    ap_url = 'https://otr-hub.lightning.force.com/lightning/r/Account_Product__c/' + str(location_gfo_df.iloc[0]['ap_id']) + '/view'
                    st.markdown(f'''<a href={ap_url}><button style="color:Red;">View GFO Record</button></a>''', unsafe_allow_html=True)
                    
                with col2:
                    # Create the SkuSku Parent URL for the parent account selected
                    sku_url = 'https://tools.cloudkitchens.com/organizations/' + location_gfo_df.iloc[0]['parent_org_id'] + '/locations'
                    st.markdown(f'''<a href={sku_url}><button style="color:Red;">Sku Sku Locations</button></a>''', unsafe_allow_html=True)

                with col3:
                    # Create the SkuSku Parent URL for the parent account selected
                    invoices_url = 'https://beam.cssinternal.com/customers/' + location_gfo_df.iloc[0]['parent_org_id'] + '/billing/invoices'
                    st.markdown(f'''<a href={invoices_url}><button style="color:Red;">Beam Invoices</button></a>''', unsafe_allow_html=True)

                with col4:
                    # Create the SkuSku Parent URL for the parent account selected
                    subs_url = 'https://beam.cssinternal.com/customers/' + location_gfo_df.iloc[0]['parent_org_id'] + '/products/otter-subscriptions'
                    st.markdown(f'''<a href={subs_url}><button style="color:Red;">Beam Subscriptions</button></a>''', unsafe_allow_html=True)

                col1.width = None
                col2.width = None
                col3.width = None
                col4.width = None

                st.markdown('### OB record summary:')
                # create 5 columns and display the location record in question
                col1, col2, col3, col4, col5  = st.columns(5)

                with col1:
                    st.metric("Closed Won Date:", '' if pd.isna(location_gfo_dict['ap_cw_date'][selected_location]) else location_gfo_dict['ap_cw_date'][selected_location].strftime('%Y-%m-%d'))
                with col2:
                    st.metric("Status:", location_gfo_dict['ap_status'][selected_location])
                with col3:
                    st.metric("GFO Menu Published Date:", location_gfo_dict['first_gfo_menu_published_date'][selected_location])
                with col4:
                    st.metric("First GFO Order Date:", location_gfo_dict['first_gfo_order'][selected_location])
                with col5:
                    st.metric("Total GFO Orders:", location_gfo_dict['total_gfo_orders'][selected_location])

                col1.width = None
                col2.width = None
                col3.width = None
                col4.width = None
                col5.width = None

                # create 2 columns for the setup and activation data
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown('#### Setup details:')
                    setup_columns = ['facility_id', 'parent_org_id', 'intends_to_use_product', 'first_active_storelink_date', 'ap_setup_date', 'upsell_opportunity__c', 'activated_ofos_all_time', 'gfo_ofo_connected', 'first_gfo_menu_published_date']
                    # Rename Output Columns and transpose the table
                    output_df = location_gfo_df[setup_columns].rename(columns={'facility_id':'Facility ID', 'parent_org_id':'Organization ID', 'intends_to_use_product': 'Intends to use', 'upsell_opportunity__c':'Upsell Opportunity', 'first_active_storelink_date':'First Active Storelink Date', 'ap_setup_date':'Setup Date', 'activated_ofos_all_time':'Activated OFOs', 'gfo_ofo_connected':'GFO OFO Connected', 'first_gfo_menu_published_date':'GFO Menu Publish Date'}).transpose().reset_index().rename(columns={'index':'Field'})
                    output_df.columns.values[-1] = 'Value'
                    output_df = output_df.fillna('')
                    st.table(output_df[['Field', 'Value']].style.set_table_styles(table_styles))

                with col2:
                    st.markdown('#### Activation details:')
                    activation_columns = ['first_gfo_order', 'total_gfo_orders']
                    # Format columns for final Output
                    #location_gfo_df['first_gfo_order'] = location_gfo_df['first_gfo_order'].dt.strftime('%Y-%m-%d')
                    for col in ['total_gfo_orders']:
                        location_gfo_df[col] = location_gfo_df[col].fillna(0).apply(np.int64)
                    # Rename Output Columns and transpose the table
                    output_df = location_gfo_df[activation_columns].rename(columns={'first_gfo_order':'First GFO Order Date 📤', 'total_gfo_orders':'Total GFO Orders 📟'}).transpose().reset_index().rename(columns={'index':'Field'})
                    output_df.columns.values[-1] = 'Value'
                    output_df = output_df.fillna('')
                    # Write the transposed table back to Streamlit
                    st.table(output_df[['Field', 'Value']].style.set_table_styles(table_styles))
                    
        with tab7: # POS Integration Tab

            # Parent OM metric details
            pos_records = func.product_filtering(parent_df, "POS Integration")

            if len(pos_records) == 0:
                st.warning("#### No records exist for this product, please refer back to parent summary page 👈")

            else:
                st.session_state.selected_tab = tabs[2]
                st.markdown('## POS Onboarding Summary')

                # create 5 columns
                col1, col2, col3, col4, col5  = st.columns(5)

                # Parent OM metric details
                pos_df = pos_records.copy()
                pos_ob_acc = pos_df.loc[(pos_df['setup_met']==False) & (~pos_df['ap_status'].isin(['Inactive'])), 'account_id'].nunique()
                pos_setup_backlog = pos_df.loc[(pos_df['setup_met']==False) & (pos_df['activation_met']==0) & (pos_df['ap_status'].isin(['Onboarding', 'Close Won', 'Setup', 'Delivered'])), 'account_id'].nunique()
                pos_activation_backlog = pos_df.loc[(pos_df['setup_met']==True) & (pos_df['ap_status'].isin(['Onboarding', 'Close Won', 'Setup', 'Delivered'])), 'account_id'].nunique()
                pos_act_acc = pos_df.loc[(pos_df['ap_status']=="Active"), 'account_id'].nunique()
                pos_churned_acc = pos_df.loc[(pos_df['ap_status'].isin(['Inactive', 'Cancelled', 'Non-OB Cancellation'])), 'account_id'].nunique()

                # Display the metric data for that parent in question
                with col1:
                    st.metric("POS Location Accounts:", len(pos_records))
                with col2:
                    st.metric("Active Locations:", pos_act_acc)
                with col3:
                    st.metric("Activation Backlog:", pos_activation_backlog)
                with col4:
                    st.metric("Setup Backlog:", pos_setup_backlog)
                with col5:
                    st.metric("Churned Locations:", pos_churned_acc)

                col1.width = None
                col2.width = None
                col3.width = None
                col4.width = None
                col5.width = None

                # Pull and display the Activaton Backlog data
                activation_df = func.activation_backlog(pos_df, "POS Integration")
                activation_container = st.container() 
                if not activation_df.empty:
                    activation_container.markdown('### Activation Backlog')
                    activation_container.table(data=activation_df.style.set_table_styles(table_styles))

                # Pull and display the Activated Records data
                activated_df = func.activation_backlog(pos_df, "POS Integration", activated=True)
                activated_container = st.container()
                if not activated_df.empty: 
                    activated_container.markdown('### Activated Records')
                    activated_container.table(data=activated_df.style.set_table_styles(table_styles))

                # Location Double Click
                st.markdown('## Location Double Click 🕵️')
                # Create a dropdown with unique location values from the "Parent Account" selected
                location_list = pos_df['account_name'].sort_values(ascending=True).unique()
                selected_location = st.selectbox('Select Location:     ', location_list)

                # Get location details
                location_pos_df = func.location_filtering(df,selected_location, 'POS Integration')

                # Warning if more than one location
                if len(location_pos_df) > 1:
                    st.warning("This location has duplicate records for this product.", icon="⚠️")
                    # For those with duplicates enable users to select both records
                    record_list = location_pos_df['ap_id'].sort_values(ascending=True).unique()
                    selected_record = st.selectbox('Select record:', record_list, key='pos_record_select')
                    location_pos_df = location_pos_df.loc[location_pos_df['ap_id']==selected_record]
                    location_pos_dict = location_pos_df.fillna('').set_index('account_name').to_dict()
                else:
                    location_pos_dict = location_pos_df.fillna('').set_index('account_name').to_dict()

                # create 4 columns
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    # Create the SFDC URL for the OB record in question
                    ap_url = 'https://otr-hub.lightning.force.com/lightning/r/Account_Product__c/' + str(location_pos_df.iloc[0]['ap_id']) + '/view'
                    st.markdown(f'''<a href={ap_url}><button style="color:Red;">View POS Record</button></a>''', unsafe_allow_html=True)
                    
                with col2:
                    # Create the SkuSku Parent URL for the parent account selected
                    sku_url = 'https://tools.cloudkitchens.com/organizations/' + location_pos_df.iloc[0]['parent_org_id'] + '/locations'
                    st.markdown(f'''<a href={sku_url}><button style="color:Red;">Sku Sku Locations</button></a>''', unsafe_allow_html=True)

                with col3:
                    # Create the SkuSku Parent URL for the parent account selected
                    invoices_url = 'https://beam.cssinternal.com/customers/' + location_pos_df.iloc[0]['parent_org_id'] + '/billing/invoices'
                    st.markdown(f'''<a href={invoices_url}><button style="color:Red;">Beam Invoices</button></a>''', unsafe_allow_html=True)

                with col4:
                    # Create the SkuSku Parent URL for the parent account selected
                    subs_url = 'https://beam.cssinternal.com/customers/' + location_pos_df.iloc[0]['parent_org_id'] + '/products/otter-subscriptions'
                    st.markdown(f'''<a href={subs_url}><button style="color:Red;">Beam Subscriptions</button></a>''', unsafe_allow_html=True)

                col1.width = None
                col2.width = None
                col3.width = None
                col4.width = None

                st.markdown('### Account Product summary:')
                # create 5 columns and display the location record in question
                col1, col2, col3, col4, col5  = st.columns(5)

                with col1:
                    st.metric("Closed Won Date:", '' if pd.isna(location_pos_dict['ap_cw_date'][selected_location]) else location_pos_dict['ap_cw_date'][selected_location].strftime('%Y-%m-%d'))
                with col2:
                    st.metric("Status:", location_pos_dict['ap_status'][selected_location])
                with col3:
                    st.metric("POS Slug:", location_pos_dict['pos_slug'][selected_location])
                with col4:
                    st.metric("POS Menu Bootstrap Date:", location_pos_dict['pos_menu_bootstrapped_date'][selected_location])
                with col5:
                    st.metric("First Injected Order Date:", location_pos_dict['first_injected_order'][selected_location])

                col1.width = None
                col2.width = None
                col3.width = None
                col4.width = None
                col5.width = None

                # create 2 columns for the setup and activation data
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown('#### POS Slug details:')
                    setup_columns = ['facility_id', 'parent_org_id', 'intends_to_use_product', 'first_active_storelink_date', 'ap_setup_date', 'upsell_opportunity__c', 'activated_ofos_all_time', 'pos_slug', 'pos_menu_bootstrapped_date', 'pos_latest_task_subject', 'pos_latest_task_date', 'pos_task_owner', 'pos_task_status', 'pos_task_comments']
                    # Rename Output Columns and transpose the table
                    output_df = location_pos_df[setup_columns].rename(columns={
                        'facility_id':'Facility ID', 'parent_org_id':'Organization ID', 'intends_to_use_product': 'Intends to use',
                        'first_active_storelink_date':'First Active Storelink Date', 'upsell_opportunity__c':'Upsell Opportunity', 'ap_setup_date':'Setup Date',
                        'activated_ofos_all_time':'Activated OFOs', 'pos_slug':'POS OFO', 'pos_menu_bootstrapped_date':'POS Menu Bootstrap Date',
                        'pos_latest_task_subject':'POS Last Task', 'pos_latest_task_date':'Last Task Date', 'pos_task_owner':'Task Owner', 
                        'pos_task_status':'Status', 'pos_task_comments':'Comments'}).transpose().reset_index().rename(columns={'index':'Field'})
                    output_df.columns.values[-1] = 'Value'
                    output_df = output_df.fillna('')
                    st.table(output_df[['Field', 'Value']].style.set_table_styles(table_styles))

                with col2:
                    st.markdown('#### Injection details:')
                    activation_columns = ['first_injected_order', 'injected_orders_l30d']
                    # Format columns for final Output
                    for col in ['injected_orders_l30d']:
                        location_pos_df[col] = location_pos_df[col].fillna(0).apply(np.int64)
                    # Rename Output Columns and transpose the table
                    output_df = location_pos_df[activation_columns].rename(columns={'first_injected_order':'First Injected Order Date', 'injected_orders_l30d':'Injected Orders L30D'}).transpose().reset_index().rename(columns={'index':'Field'})
                    output_df.columns.values[-1] = 'Value'
                    output_df = output_df.fillna('')
                    # Write the transposed table back to Streamlit
                    st.table(output_df[['Field', 'Value']].style.set_table_styles(table_styles))
                
        with tab8: # Mercury Tab

            # Parent OM metric details
            merc_records = func.product_filtering(parent_df, "Mercury - Otter POS")

            if len(merc_records) == 0:
                st.warning("#### No records exist for this product, please refer back to parent summary page 👈")

            else:
                st.session_state.selected_tab = tabs[2]
                st.markdown('## Mercury Summary')

                # create 5 columns
                col1, col2, col3, col4, col5  = st.columns(5)

                # Parent OM metric details
                merc_df = merc_records.copy()
                merc_ob_acc = merc_df.loc[(merc_df['setup_met']==False) & (~merc_df['ap_status'].isin(['Inactive'])), 'account_id'].nunique()
                merc_setup_backlog = merc_df.loc[(merc_df['setup_met']==False) & (merc_df['activation_met']==0) & (merc_df['ap_status'].isin(['Onboarding', 'Close Won', 'Setup', 'Delivered'])), 'account_id'].nunique()
                merc_activation_backlog = merc_df.loc[(merc_df['setup_met']==True) & (merc_df['ap_status'].isin(['Onboarding', 'Close Won', 'Setup', 'Delivered'])), 'account_id'].nunique()
                merc_act_acc = merc_df.loc[(merc_df['ap_status']=="Active"), 'account_id'].nunique()
                merc_churned_acc = merc_df.loc[(merc_df['ap_status'].isin(['Inactive', 'Cancelled', 'Non-OB Cancellation'])), 'account_id'].nunique()

                # Display the metric data for that parent in question
                with col1:
                    st.metric("merc Location Accounts:", len(merc_records))
                with col2:
                    st.metric("Active Locations:", merc_act_acc)
                with col3:
                    st.metric("Activation Backlog:", merc_activation_backlog)
                with col4:
                    st.metric("Setup Backlog:", merc_setup_backlog)
                with col5:
                    st.metric("Churned Locations:", merc_churned_acc)

                col1.width = None
                col2.width = None
                col3.width = None
                col4.width = None
                col5.width = None

                # Pull and display the Activaton Backlog data
                activation_df = func.activation_backlog(merc_df, "Mercury - Otter POS")
                activation_container = st.container() 
                if not activation_df.empty:
                    activation_container.markdown('### Activation Backlog')
                    activation_container.table(data=activation_df.style.set_table_styles(table_styles))

                # Pull and display the Activated Records data
                activated_df = func.activation_backlog(merc_df, "Mercury - Otter POS", activated=True)
                activated_container = st.container()
                if not activated_df.empty: 
                    activated_container.markdown('### Activated Records')
                    activated_container.table(data=activated_df.style.set_table_styles(table_styles))

                # Location Double Click
                st.markdown('## Location Double Click 🕵️')
                # Create a dropdown with unique location values from the "Parent Account" selected
                location_list = merc_df['account_name'].sort_values(ascending=True).unique()
                selected_location = st.selectbox('Select Location:      ', location_list)

                # Get location details
                location_merc_df = func.location_filtering(df,selected_location, 'Mercury - Otter POS')

                # Warning if more than one location
                if len(location_merc_df) > 1:
                    st.warning("This location has duplicate records for this product.", icon="⚠️")
                    # For those with duplicates enable users to select both records
                    record_list = location_merc_df['ap_id'].sort_values(ascending=True).unique()
                    selected_record = st.selectbox('Select record:', record_list, key='merc_record_select')
                    location_merc_df = location_merc_df.loc[location_merc_df['ap_id']==selected_record]
                    location_merc_dict = location_merc_df.fillna('').set_index('account_name').to_dict()
                else:
                    location_merc_dict = location_merc_df.fillna('').set_index('account_name').to_dict()

                # create 4 columns
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    # Create the SFDC URL for the OB record in question
                    ap_url = 'https://otr-hub.lightning.force.com/lightning/r/Account_Product__c/' + str(location_merc_df.iloc[0]['onboarding_id']) + '/view'
                    st.markdown(f'''<a href={ap_url}><button style="color:Red;">View Mercury Record</button></a>''', unsafe_allow_html=True)
                    
                with col2:
                    # Create the SkuSku Parent URL for the parent account selected
                    sku_url = 'https://tools.cloudkitchens.com/organizations/' + location_merc_df.iloc[0]['parent_org_id'] + '/locations'
                    st.markdown(f'''<a href={sku_url}><button style="color:Red;">Sku Sku Locations</button></a>''', unsafe_allow_html=True)

                with col3:
                    # Create the SkuSku Parent URL for the parent account selected
                    invoices_url = 'https://beam.cssinternal.com/customers/' + location_merc_df.iloc[0]['parent_org_id'] + '/billing/invoices'
                    st.markdown(f'''<a href={invoices_url}><button style="color:Red;">Beam Invoices</button></a>''', unsafe_allow_html=True)

                with col4:
                    # Create the SkuSku Parent URL for the parent account selected
                    subs_url = 'https://beam.cssinternal.com/customers/' + location_merc_df.iloc[0]['parent_org_id'] + '/products/otter-subscriptions'
                    st.markdown(f'''<a href={subs_url}><button style="color:Red;">Beam Subscriptions</button></a>''', unsafe_allow_html=True)

                col1.width = None
                col2.width = None
                col3.width = None
                col4.width = None

                st.markdown('### Account Product summary:')
                # create 5 columns and display the location record in question
                col1, col2, col3, col4, col5  = st.columns(5)

                with col1:
                    st.metric("Closed Won Date:", '' if pd.isna(location_merc_dict['ap_cw_date'][selected_location]) else location_merc_dict['ap_cw_date'][selected_location].strftime('%Y-%m-%d'))
                with col2:
                    st.metric("Status:", location_merc_dict['ap_status'][selected_location])
                with col3:
                    st.metric("Storelinks Connected:", location_merc_dict['has_storelinks_setup'][selected_location])
                with col4:
                    st.metric("Mercury Menu Import Date:", location_merc_dict['first_menu_imported_at'][selected_location])
                with col5:
                    st.metric("First Mercury Order Date:", location_merc_dict['first_mercury_order'][selected_location])

                col1.width = None
                col2.width = None
                col3.width = None
                col4.width = None
                col5.width = None

                # create 2 columns for the setup and activation data
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown('#### Mercury - Otter POS:')
                    setup_columns = ['facility_id', 'parent_org_id', 'intends_to_use_product', 'first_active_storelink_date', 'ap_setup_date', 'upsell_opportunity__c', 'activated_ofos_all_time', 
                                     'has_storelinks_setup', 'first_menu_imported_at', 'sf_stripe_account_id', 'connected_accounts']
                    # Rename Output Columns and transpose the table
                    output_df = location_merc_df[setup_columns].rename(columns={
                        'facility_id':'Facility ID', 'parent_org_id':'Organization ID', 'intends_to_use_product': 'Intends to use',
                        'first_active_storelink_date':'First Active Storelink Date', 'upsell_opportunity__c':'Upsell Opportunity', 'ap_setup_date':'Setup Date',
                        'activated_ofos_all_time':'Activated OFOs', 'has_storelinks_setup':'Mercury Storelinks Setup', 'first_menu_imported_at':'Mercury Menu Import Date',
                        'sf_stripe_account_id':'Salesforce Stripe ID', 'connected_accounts':'Connected Org Level Stripe IDs (Beam)' }).transpose().reset_index().rename(columns={'index':'Field'})
                    output_df.columns.values[-1] = 'Value'
                    output_df = output_df.fillna('')
                    st.table(output_df[['Field', 'Value']].style.set_table_styles(table_styles))

                with col2:
                    st.markdown('#### Order details:')
                    activation_columns = ['first_mercury_order', 'merc_orders_l5d', 'merc_orders_l30d']
                    # Format columns for final Output
                    for col in ['merc_orders_l5d', 'merc_orders_l30d']:
                        location_merc_df[col] = location_merc_df[col].fillna(0).apply(np.int64)
                    # Rename Output Columns and transpose the table
                    output_df = location_merc_df[activation_columns].rename(columns={'first_mercury_order':'First Mercury Order Date', 'merc_orders_l5d':'Orders L5D', 'merc_orders_l30d':'Orders L30D'}).transpose().reset_index().rename(columns={'index':'Field'})
                    output_df.columns.values[-1] = 'Value'
                    output_df = output_df.fillna('')
                    # Write the transposed table back to Streamlit
                    st.table(output_df[['Field', 'Value']].style.set_table_styles(table_styles))

    else:
            with tab2:
                # Add entire backlog when all records are selected
                st.session_state.selected_tab = tabs[1]
                if selected_aa!='All':

                    st.markdown('## Order Manager Onboarding Summary')
                    # Pull the OB Specialists Book of Business
                    bob_df = func.get_entire_activation_backlog(df, selected_aa, "OM")
                
                    # AgGrid
                    gb = GridOptionsBuilder.from_dataframe(bob_df)
                    # Display the AG Grid for the BoB DataFrame
                    func.build_grid(gb, bob_df, 800)

            with tab3:
                # Add entire backlog when all records are selected
                st.session_state.selected_tab = tabs[2]
                if selected_aa!='All':

                    st.markdown('## Boost Onboarding Summary')

                    # Pull the OB Specialists Book of Business
                    bob_df = func.get_entire_activation_backlog(df, selected_aa, "Boost")

                    if bob_df.empty:
                        st.warning("#### No records exist for this product, please refer back to parent summary page 👈")

                    else:
                    # AgGrid
                        gb = GridOptionsBuilder.from_dataframe(bob_df)
                        # Display the AG Grid for the BoB DataFrame
                        func.build_grid(gb, bob_df, 800)

            with tab4:
                # Add entire backlog when all records are selected
                st.session_state.selected_tab = tabs[3]
                if selected_aa!='All':

                    st.markdown('## Direct Orders Onboarding Summary')
                    
                    # Pull the OB Specialists Book of Business
                    bob_df = func.get_entire_activation_backlog(df, selected_aa, "Direct Orders - Online Ordering")

                    if bob_df.empty:
                        st.warning("#### No records exist for this product, please refer back to parent summary page 👈")

                    else:
                    # AgGrid
                        gb = GridOptionsBuilder.from_dataframe(bob_df)
                        # Display the AG Grid for the BoB DataFrame
                        func.build_grid(gb, bob_df, 800)

            with tab5:
                # Add entire backlog when all records are selected
                st.session_state.selected_tab = tabs[4]
                if selected_aa!='All':

                    st.markdown('## Dine-in Onboarding Summary')

                    # Pull the OB Specialists Book of Business
                    bob_df = func.get_entire_activation_backlog(df, selected_aa, "Direct Orders - Dine-in")

                    if bob_df.empty:
                        st.warning("#### No records exist for this product, please refer back to parent summary page 👈")

                    else:
                    # AgGrid
                        gb = GridOptionsBuilder.from_dataframe(bob_df)
                        # Display the AG Grid for the BoB DataFrame
                        func.build_grid(gb, bob_df, 800)

            with tab6:
                # Add entire backlog when all records are selected
                st.session_state.selected_tab = tabs[5]
                if selected_aa!='All':

                    st.markdown('## GFO Onboarding Summary')

                    # Pull the OB Specialists Book of Business
                    bob_df = func.get_entire_activation_backlog(df, selected_aa, "Direct Orders - Google Food Ordering")
                    
                    if bob_df.empty:
                        st.warning("#### No records exist for this product, please refer back to parent summary page 👈")

                    else:
                    # AgGrid
                        gb = GridOptionsBuilder.from_dataframe(bob_df)
                        # Display the AG Grid for the BoB DataFrame
                        func.build_grid(gb, bob_df, 800)
                    
            with tab7:
                # Add entire backlog when all records are selected
                st.session_state.selected_tab = tabs[6]
                if selected_aa!='All':

                    st.markdown('## POS Onboarding Summary')

                    # Pull the OB Specialists Book of Business
                    bob_df = func.get_entire_activation_backlog(df, selected_aa, "POS Integration")

                    if bob_df.empty:
                        st.warning("#### No records exist for this product, please refer back to parent summary page 👈")

                    else:
                    # AgGrid
                        gb = GridOptionsBuilder.from_dataframe(bob_df)
                        # Display the AG Grid for the BoB DataFrame
                        func.build_grid(gb, bob_df, 800)

            with tab8:
                # Add entire backlog when all records are selected
                st.session_state.selected_tab = tabs[7]
                if selected_aa!='All':

                    st.markdown('## Mercury Summary')

                    # Pull the OB Specialists Book of Business
                    bob_df = func.get_entire_activation_backlog(df, selected_aa, "Mercury - Otter POS")

                    if bob_df.empty:
                        st.warning("#### No records exist for this product, please refer back to parent summary page 👈")

                    else:
                    # AgGrid
                        gb = GridOptionsBuilder.from_dataframe(bob_df)
                        # Display the AG Grid for the BoB DataFrame
                        func.build_grid(gb, bob_df, 800)

elif view_selected=='High Level Overview':
    
    col1, col2 =st.columns(2)
    with col1:
        # Select Region
        #region_list = df['Region'].sort_values(ascending=True).unique()
        region_list = ['APAC', 'EMEA', 'LATAM', 'USC']
        region_index = list(region_list).index('USC')
        region = st.selectbox('Select Region', region_list, index=region_index)
        st.session_state['region'] = region
        region_df = df.loc[df['Region']==region]
        
    with col2:
        # Select Product
        #products_list = region_df['ap_name'].sort_values(ascending=True).unique()
        products_list = ['Boost', 'Direct Orders - Dine-in', 'Direct Orders - Online Ordering', 'Direct Orders - Google Food Ordering', 'OM']
        om_index = list(products_list).index('OM')
        product = st.selectbox('Select Product', products_list, index=om_index)
        st.session_state['product'] = product
    

    with st.expander("View Filters"):
        #container = st.container()
        col1, col2, col3 = st.columns(3)
        with col1:
            # Filters for entire dataset
            # 1 - Tracking period toggle
            analysis_type = st.selectbox('Data view [weekly/ monthly]', ['Weekly', 'Monthly'])
            st.session_state['weekly_monthly'] = analysis_type
            weekly = True if analysis_type=='Weekly' else False
            # 2 - Segment filters
            segment_list = ['All', 'SMB', 'Enterprise']
            segment_index = list(segment_list).index('SMB')
            segment_toggle = st.selectbox('Segment', segment_list, index=segment_index)
            st.session_state['segment'] = segment_toggle
            segment_value =  ['', 'SMB', 'Enterprise'] if segment_toggle=='All' else [segment_toggle]

        with col2:
            # 3 - FF dataset filters
            ff_toggle = st.selectbox('Dataset - (Include FF)', ['Yes', 'No'], index=1)
            st.session_state['ff'] = ff_toggle
            ff_value = [False] if ff_toggle=='No' else [False, True] 
            # 4 - TODC inclusion y/n if EMEA then OB Rep View
            if region=="EMEA":
                emea_obs = ['All'] + df['activation_owner'].loc[df['Region']=='EMEA'].sort_values(ascending=True).unique().tolist()
                ob_value = st.selectbox('Onboarding Specialist', emea_obs, index=0)
                st.session_state['filter4'] = ob_value
                todc_value = ['XXXXXXXXXXX'] 

            else:
                ob_value = 'All'
                todc_toggle = st.selectbox('Dataset - Include "The On Demand Company"', ['Yes', 'No'], index=1)
                todc_value = ['XXXXXXXXXXX'] if todc_toggle=='Yes' else ['The On Demand Company']
                st.session_state['filter4'] = todc_toggle

        with col3:
            # 5 - Sales Source
            if region=="EMEA":
                source_value = [True, False]
                subregion_dict = {
                    'Europe': ['Portugal', 'Spain', 'France', 'Belgium', 'Netherlands', 'Luxemburg', 'Germany', 'Denmark', 'Sweden', 'Norway', 'Finland', 'Poland', 'Czechia', 'Hungary', 'Austria', 'Romania', 'Croatia', 'Serbia', 'Greece'],
                    'MENA': ['Morocco', 'Algeria', 'Tunisia', 'Libya', 'Egypt', 'Palestine', 'Isreal', 'Lebanon', 'Turkey', 'Syria', 'Jordan', 'Iran', 'Saudi Arabia', 'Qatar', 'UAE', 'Kuwait'],
                    'UK&I': ['Ireland', 'United Kingdom']
                } 
                subregion = st.selectbox('Subregion', ['All', 'Europe', 'MENA', 'UK&I'], index=0)
                st.session_state['filter5'] = subregion
                subregion_value = 'All' if subregion=='All' else subregion_dict[subregion]
            else:
                source_toggle = st.selectbox('Dataset - OTTER_OS_ONBOARDING', ['All', 'True', 'False'])
                st.session_state['filter5'] = source_toggle
                source_dict = {'All':[True, False], 'True':[True], 'False':[False]}
                source_value = source_dict[source_toggle]
                subregion_value = 'All'

            # 6 - Country select - based of selected region
            if region=="EMEA" and subregion_value!='All':
                subregion_df = region_df.loc[region_df['Country'].isin(subregion_dict[subregion])]
                country_list = ["All"] + list(subregion_df['Country'].sort_values(ascending=True).unique())
                country = st.selectbox('Country', country_list)

            else:
                country_list = ["All"] + list(region_df['Country'].sort_values(ascending=True).unique())
                country = st.selectbox('Country', country_list)

            st.session_state['country'] = country

            if region=="USC":
                # 7 - Referral Parent NOTE FOR ROB
                referral_parents_list = ["All"] + list(region_df['partner_name'].sort_values(ascending=True).unique())
                referral_parent = st.selectbox('Referral Parent', referral_parents_list)
                st.session_state['referral'] = referral_parent
            else:
                referral_parent = 'All'
            
    # Filter the dataset for those in question
    # us_df['Segment'] = df['Segment'].fillna('')
    filtered_df = func.pull_high_level_data(
        df, 
        product=product, 
        region=region,
        segment_value=segment_value,
        ff_value=ff_value,
        todc_value=todc_value, 
        ob_value=ob_value,
        country=country,
        subregion_value=subregion_value,
        source_value=source_value,
        referral_parent=referral_parent,
        start_date='2022-10-01'
    )

    filtered_df = filtered_df.drop_duplicates(ignore_index=True)
    tabs = ["Funnel Analysis", "Activation Criteria Breakdown", "North Star Metrics", "Onboarding Buckets"]
    tab1, tab2, tab3, tab4  = st.tabs(tabs)
    selected_tab = st.session_state.get("selected_tab", tabs[1])

    with tab1: # Funnel Analysis
        if len(filtered_df) == 0:
            st.warning("#### No records exist for these filters, please try and pull a different cohort ☝️")
        else:
            # Get cohorted DF
            funnel_df = func.cohorted_funnels(filtered_df, product=product, weekly=weekly)

            # Build AgGrid for the funnel data
            gb = GridOptionsBuilder.from_dataframe(funnel_df)

            # Display the AG Grid for the Funnel DataFrame
            st.write('### OB Funnel Analysis')
            func.build_grid(gb, funnel_df, 400, auto_size=True)

            # Melt the Source data for the graph
            source = funnel_df[[f'{analysis_type} Cohort', 'Actual Rate (%)', 'Expected Rate (%)']].loc[pd.to_datetime(funnel_df[f'{analysis_type} Cohort'], format='%Y-%m-%d')>=first_day_six_months_ago]
            source = pd.melt(source, id_vars=[f'{analysis_type} Cohort'], value_vars=['Actual Rate (%)', 'Expected Rate (%)'], var_name='Activation rates', value_name='Percentage', ignore_index=True)

            # Display within the app
            st.write('### Funnel Analysis Visuals')

            funnel_viz_on = tog.toggle(
                label='Show Funnel Visual',
                key="switch_1",
                value=True,
                widget='checkbox')

            if funnel_viz_on:

                # Use plotly to produce the line graph
                fig = px.line(source, x=f'{analysis_type} Cohort', y='Percentage', color='Activation rates', line_shape='spline')
                fig.update_traces(line=dict(width=3))

                # Display within the app
                st.plotly_chart(fig, use_container_width=True)

            st.write('### Funnel Analysis Double Click 🕵️')

            if product=="OM":
                query_dict = {
                    'Setup  ':['setup_met', False, ['onboarding_id', 'account_name', 'parent_account_name', 'next_steps', 'create_source', 'sales_ob_handoff', 'bundle_name', 'activation_owner', 'upsell_opportunity__c', 'onboarding_status', 'has_pos_integration_2', 'pos_intends_to_use', 'pos_ob_status', 'facility_id', 'parent_org_id', 'activated_ofos_all_time', 'ap_cw_date', 'ob_object_setup_date', 'setup_met']],
                    'Go-Live':['golive_met', False, ['onboarding_id', 'account_name', 'parent_account_name', 'next_steps','create_source', 'sales_ob_handoff', 'bundle_name', 'activation_owner', 'upsell_opportunity__c', 'onboarding_status', 'has_pos_integration_2',  'pos_intends_to_use', 'pos_ob_status', 'facility_id', 'parent_org_id', 'activated_ofos_all_time', 'ap_cw_date', 'ob_object_setup_date', 'setup_met', 'golive_met', 'last_bm_event__c', 'first_confirmed_order', 'Orders_Last_30_Days__c', 'needs_om', 'last_om_event__c', 'needs_hardware', 'delivered_date']],
                    'Activation':['activation_met', False, ['onboarding_id', 'account_name', 'parent_account_name', 'next_steps','create_source', 'sales_ob_handoff', 'bundle_name', 'activation_owner', 'upsell_opportunity__c', 'onboarding_status', 'has_pos_integration_2',  'pos_intends_to_use', 'pos_ob_status', 'facility_id', 'parent_org_id', 'activated_ofos_all_time', 'ap_cw_date', 'ob_object_setup_date', 'setup_met', 'golive_met', 'activation_met', 'last_bm_event__c', 'first_confirmed_order', 'Orders_Last_30_Days__c', 'needs_om', 'last_om_event__c', 'needs_hardware', 'delivered_date', 'needs_print', 'first_printed_job', 'Printed_Orders_Last_14_Days__c', 'needs_menu_published', 'first_menu_published_date']],
                    'Activated Records':['ob_object_active_date', True, ['onboarding_id', 'account_name', 'parent_account_name', 'next_steps','create_source', 'sales_ob_handoff', 'bundle_name', 'activation_owner', 'upsell_opportunity__c', 'onboarding_status', 'has_pos_integration_2',  'pos_intends_to_use', 'pos_ob_status', 'facility_id', 'parent_org_id', 'activated_ofos_all_time', 'ap_cw_date', 'ob_object_setup_date', 'ob_object_active_date', 'setup_met', 'golive_met', 'activation_met', 'last_bm_event__c', 'first_confirmed_order', 'Orders_Last_30_Days__c', 'needs_om', 'last_om_event__c', 'needs_hardware', 'delivered_date', 'needs_print', 'first_printed_job', 'Printed_Orders_Last_14_Days__c', 'needs_menu_published', 'first_menu_published_date']]
                    }
            else:
                core_setup_cols = ['ap_id', 'intends_to_use_product', 'account_name', 'parent_account_name', 'next_steps', 'create_source', 'sales_ob_handoff', 'bundle_name', 'activation_owner', 'upsell_opportunity__c', 'ap_status', 'ap_cw_date', 'ap_setup_date', 'setup_met', 'facility_id', 'parent_org_id', 'activated_ofos_all_time']
                core_activation_cols = ['ap_id', 'intends_to_use_product', 'account_name', 'parent_account_name', 'create_source', 'sales_ob_handoff', 'bundle_name', 'activation_owner', 'facility_id', 'parent_org_id', 'activated_ofos_all_time', 'upsell_opportunity__c', 'ap_status', 'ap_cw_date', 'ap_setup_date', 'ap_active_date', 'setup_met', 'activation_met']

                act_dict = {
                    'Boost':['first_active_campaign_day', 'first_booster_order'],
                    'Direct Orders - Online Ordering':['direct_orders_ofo_connected', 'first_d2c_menu_published_date', 'first_d2c_order'],
                    'Direct Orders - Dine-in':['direct_orders_ofo_connected', 'first_d2c_menu_published_date', 'dine_in_enabled', 'first_dine_in_order'],
                    'Direct Orders - Google Food Ordering':['gfo_ofo_connected', 'first_gfo_menu_published_date', 'first_gfo_order']
                    }

                query_dict = {
                    'Setup':['setup_met', False, core_setup_cols + act_dict[product]],
                    'Activation':['activation_met', False, core_activation_cols + act_dict[product]],
                    'Activated Records':['ap_active_date', True, core_activation_cols + act_dict[product]]
                    }

            with st.form('Pull funnel records'):
                # create 3 columns for the filters
                col1, col2, col3 = st.columns(3)
                with col1:
                    start_date_funnel = st.date_input("Start Date", value=dt.date.today() - dt.timedelta(days=7))
                with col2:
                    end_date_funnel = st.date_input("End Date", value=dt.date.today())
                with col3:
                    # Create the multi-select option for the visuals
                    if product=="OM":
                        # Only include Go-Live for OM
                        funnel_stages=['All',  'Setup', 'Go-Live', 'Activation', 'Activated Records']
                        funnel_select = st.selectbox('Select activation funnel:', funnel_stages)
                        st.session_state['funnel'] = funnel_select

                    else:
                        funnel_stages=['All', 'Setup', 'Activation', 'Activated Records']
                        funnel_select = st.selectbox('Select activation funnel:', funnel_stages)
                        st.session_state['funnel'] = funnel_select

                pull_records = st.form_submit_button('Pull Records')

                if pull_records:
                    if funnel_select=='Activated Records':
                        funnel_query = filtered_df[query_dict[funnel_select][2]].loc[(~pd.isna(filtered_df[query_dict[funnel_select][0]])) & (filtered_df['ap_cw_date'].dt.date >= start_date_funnel) & (filtered_df['ap_cw_date'].dt.date <= end_date_funnel)].reset_index(drop=True)
                    elif funnel_select=='All':
                        funnel_query = filtered_df[query_dict['Activated Records'][2]].loc[(filtered_df['ap_cw_date'].dt.date >= start_date_funnel) & (filtered_df['ap_cw_date'].dt.date <= end_date_funnel)].reset_index(drop=True)
                    else:
                        funnel_query = filtered_df[query_dict[funnel_select][2]].loc[(filtered_df[query_dict[funnel_select][0]]==query_dict[funnel_select][1]) & (filtered_df['ap_cw_date'].dt.date >= start_date_funnel) & (filtered_df['ap_cw_date'].dt.date <= end_date_funnel)].reset_index(drop=True)

                    if product=="OM":
                        funnel_query.insert(1, 'record_URL', funnel_query.apply(lambda row: 'https://otr-hub.lightning.force.com/lightning/r/Onboarding__c/' + str(row['onboarding_id']) + '/view', axis=1))
                    else:
                        funnel_query.insert(1, 'record_URL', funnel_query.apply(lambda row: 'https://otr-hub.lightning.force.com/lightning/r/Account_Product__c/' + str(row['ap_id']) + '/view', axis=1))    
                    for col in ['ap_cw_date', 'ob_object_setup_date', 'ob_object_active_date', 'delivered_date']:
                        if col in funnel_query.columns:
                            funnel_query[col] = funnel_query[col].dt.strftime('%Y-%m-%d')

                    # Build and display the data in an AG Grid
                    gb = GridOptionsBuilder.from_dataframe(funnel_query, editable=True)
                    gb.configure_column(
                        "record_URL",
                        headerName="record_URL",
                        width=100,
                        cellRenderer=JsCode("""
                            class UrlCellRenderer {
                              init(params) {
                                this.eGui = document.createElement('a');
                                this.eGui.innerText = params.value;
                                this.eGui.setAttribute('href', params.value);
                                this.eGui.setAttribute('style', "text-decoration:none");
                                this.eGui.setAttribute('target', "_blank");
                              }
                              getGui() {
                                return this.eGui;
                              }
                            }
                        """)
                    )

                    func.build_grid(gb, funnel_query, 800, pagination=True)

    with tab2: # Activation Criteria Breakdown
        if len(filtered_df) == 0:
            st.warning("#### No records exist for these filters, please try and pull a different cohort ☝️")
        else:
            #us_df = us_df.sort_values(by='ap_cw_date', ascending=False)
            # Pull activation criteria data
            ab_df = func.activation_criteria_breakdown(filtered_df, product=product, weekly=weekly)
            ab_df = ab_df.rename(columns={
                'needs_om':'OM event required',
                'needs_hardware':'Hardware required',
                'needs_print':'Print required',
                'needs_menu_published':'Menu publish required',
            })

            # Build and write back the AG Grid to display the activation criteria data
            gb = GridOptionsBuilder.from_dataframe(ab_df)
            func.build_grid(gb, ab_df, 400)

            # Create the multi-select option for the visuals
            if product=="OM":
                activation_cols=['BM Activity Rate (%)', 'Orders Rate (%)', 'OM Activity Rate (%)', 'HW Delivered Rate (%)', 'Printer Activity Rate (%)', 'Menu Publish Rate (%)']
                cols_for_dd = ['BM Event?', 'Confirmed Order?', 'OM Event?', 'Hardware Delivered?', 'Printed Order?', 'Menu Published?']
                pre_selection=activation_cols[:4]
            elif product=="Boost":
                activation_cols=['Boost Campaign Rate (%)', 'Boost Orders Rate (%)']
                cols_for_dd = ['Launched Campaign?', 'Boosted Order?']
                pre_selection=activation_cols
            elif product=="Direct Orders - Online Ordering":
                activation_cols=['D2C OFO Connected Rate (%)', 'D2C Menu Published Rate (%)', 'Direct Orders Rate (%)']
                cols_for_dd=['D2C OFO Connected?', 'D2C Menu Published?', 'Direct Order Received']
                pre_selection=activation_cols
            elif product=="Direct Orders - Dine-in":
                activation_cols=['D2C OFO Connected Rate (%)', 'D2C Menu Published Rate (%)', 'Dine-in Enabled Rate (%)', 'Dine-in Orders Rate (%)']
                cols_for_dd=['D2C OFO Connected?', 'D2C Menu Published?', 'Dine-in Enabled?', 'Dine-in Order Received']
                pre_selection=activation_cols
            elif product=="Direct Orders - Google Food Ordering":
                activation_cols=['GFO OFO Connected Rate (%)', 'GFO Menu Published Rate (%)', 'GFO Orders Rate (%)']
                cols_for_dd=['GFO OFO Connected?', 'GFO Menu Published?', 'GFO Order Received']
                pre_selection=activation_cols

            st.write('### Criteria Breakdown Visuals')
            # Create toggle fro graph visibility
            criteria_viz_on = tog.toggle(
                label='Show Criteria Visual',
                key="switch_2",
                value=True,
                widget='checkbox')

            if criteria_viz_on:

                options = st.multiselect(
                    'Select activation fields for plot:',
                    activation_cols,
                    pre_selection
                )

                # Melt the column data so that we can build the graph using Plotly
                bar_sample = ab_df.loc[pd.to_datetime(ab_df[f'{analysis_type} Cohort'], format='%Y-%m-%d')>=first_day_six_months_ago]
                bar_source = pd.melt(bar_sample, id_vars=[f'{analysis_type} Cohort'], value_vars=options, var_name='Criteria', value_name='Percentage Success (%)', ignore_index=True)
                fig = px.bar(bar_source, x=f'{analysis_type} Cohort', y='Percentage Success (%)', color='Criteria', barmode='group')
                st.plotly_chart(fig, use_container_width=True)
            # Here we are building the section to allow users to query the activation data
            st.write('#### Criteria Double Click 🕵️')

            with st.form('Pull criteria details'):
                # create 3 columns for the filters
                col1, col2, col3 = st.columns(3)
                with col1:
                    start_date_crit = st.date_input("Start Date ", value=dt.date.today() - dt.timedelta(days=7))
                with col2:
                    end_date_crit = st.date_input("End Date ", value=dt.date.today())
                with col3:
                    criteria_select = st.selectbox('Select activation criteria?:', ['All'] + cols_for_dd)

                # Create the button to trigger the analysis
                pull_criteria_data = st.form_submit_button('Pull criteria data')

                if pull_criteria_data:
                    # If all is selected, users can see all columns
                    if criteria_select=='All':
                        sample_df = filtered_df.loc[(filtered_df['ap_cw_date'].dt.date >= start_date_crit) & (filtered_df['ap_cw_date'].dt.date <= end_date_crit) & (filtered_df['activation_score'] < 1)].sort_values(by='ap_cw_date', ascending=False)
                        cols = product_criteria_dict[product]
                        sample_df = sample_df[cols]


                    # Otherwise query and individual column
                    else:
                        # Mapping the event requirements back to their fields
                        require_dict = {
                                'BM Event?':['first_bm_event_date'],
                                'Confirmed Order?':['first_confirmed_order'],
                                'OM Event?':['needs_om','first_om_event_date'],
                                'Hardware Delivered?':['needs_hardware', 'delivered_date'],
                                'Printed Order?':['needs_print', 'first_printed_job'],
                                'Menu Published?':['needs_menu_published','first_menu_published_date'],
                                'Launched Campaign?':['first_active_campaign_day'], 
                                'Boosted Order':['first_booster_order'],
                                'D2C OFO Connected?':['direct_orders_ofo_connected'], 
                                'D2C Menu Published?':['first_d2c_menu_published_date'],
                                'Direct Order Received':['first_d2c_order'],
                                'Dine-in Enabled?':['dine_in_enabled'],
                                'Dine-in Order Received':['first_dine_in_order'],
                                'GFO OFO Connected?':['gfo_ofo_connected'], 
                                'GFO Menu Published?':['first_gfo_menu_published_date'],
                                'GFO Order Received':['first_gfo_order']
                            }

                        # BM event and Orders are mandatory
                        if criteria_select in ['BM Event?', 'Confirmed Order?']:
                            cols = ['account_name', 'facility_id', 'onboarding_id', 'ap_id', 'activation_owner', 'Segment', 'is_future_foods_customer', 'ap_name', 'ap_status', 'ap_cw_date', 'activation_score', require_dict[criteria_select][0], require_dict[criteria_select][1]]
                            sample_df = filtered_df.loc[(filtered_df['ap_cw_date'].dt.date >= start_date_crit) & (filtered_df['ap_cw_date'].dt.date <= end_date_crit) & (filtered_df['activation_score'] < 1)].sort_values(by='ap_cw_date', ascending=False)
                            sample_df=sample_df[cols]

                        # The rest of the criteria are not always required, so we use the requirement dict defined above to determine the columns in question
                        else:
                            cols = ['account_name', 'facility_id', 'onboarding_id', 'ap_id', 'activation_owner', 'Segment', 'is_future_foods_customer', 'ap_name', 'ap_status', 'ap_cw_date', 'activation_score', require_dict[criteria_select][0]]
                            sample_df = filtered_df.loc[(filtered_df['ap_cw_date'].dt.date >= start_date_crit) & (filtered_df['ap_cw_date'].dt.date <= end_date_crit) & (filtered_df['activation_score'] < 1) & (filtered_df[require_dict[criteria_select][0]]==True)].sort_values(by='ap_cw_date', ascending=False)
                            sample_df=sample_df[cols]

                    # Add in the URL column so users can view the records in SFDC
                    if product=="OM":
                        sample_df.insert(3, 'record_URL', sample_df.apply(lambda row: 'https://otr-hub.lightning.force.com/lightning/r/Onboarding__c/' + str(row['onboarding_id']) + '/view', axis=1))
                    else:
                        sample_df.insert(3, 'record_URL', sample_df.apply(lambda row: 'https://otr-hub.lightning.force.com/lightning/r/Account_Product__c/' + str(row['ap_id']) + '/view', axis=1)) 
                    # Formate the date columns
                    if 'delivered_date' in sample_df.columns: 
                        date_columns = ['ap_cw_date', 'delivered_date']
                        for col in date_columns:
                            sample_df[col]=sample_df[col].dt.strftime('%Y-%m-%d')
                    else:
                        sample_df['ap_cw_date']=sample_df['ap_cw_date'].dt.strftime('%Y-%m-%d')

                    # Build and display the data in an AG Grid
                    gb = GridOptionsBuilder.from_dataframe(sample_df)

                    gb.configure_column(
                        "record_URL",
                        headerName="record_URL",
                        width=100,
                        cellRenderer=JsCode("""
                            class UrlCellRenderer {
                              init(params) {
                                this.eGui = document.createElement('a');
                                this.eGui.innerText = params.value;
                                this.eGui.setAttribute('href', params.value);
                                this.eGui.setAttribute('style', "text-decoration:none");
                                this.eGui.setAttribute('target', "_blank");
                              }
                              getGui() {
                                return this.eGui;
                              }
                            }
                        """)
                    )

                    func.build_grid(gb, sample_df, 800, pagination=True)

    with tab3: # North star metrics data
        if len(filtered_df) == 0:
            st.warning("#### No records exist for these filters, please try and pull a different cohort ☝️")
        else:
            # Add the input rolling days parameter as a slider
            col1, col2 = st.columns(2)
            with col1:
                rolling_days = st.slider('Rolling sample size', 7, 60, 30)


            # Pull the rolling median data using our funtion
            t2a=func.get_rolling_average(filtered_df, 'active_time', 'Median activation time', 'Activation rate (%)', rolling_days, weekly=weekly)
            t2s=func.get_rolling_average(filtered_df, 'setup_time', 'Median setup time', 'Setup rate (%)', rolling_days, weekly=weekly)

            # Add in weekly vs monthly logic
            if weekly==True:
                times_df = t2a.merge(t2s.drop(columns=['Period End Date', 'Period Start Date', 'Total Sample', 'Total Activated']), on=f'{analysis_type} Cohort', how='inner')
                columns = [f'{analysis_type} Cohort', 'Period End Date', 'Period Start Date', 'Median activation time', 'Median setup time', 'Total Sample', 'Total Activated', 'Activation rate (%)', 'Setup rate (%)']
                times_df = times_df[columns]
            else:
                times_df = t2a.merge(t2s.drop(columns=['Month Start', 'Month End', 'Total Sample']), on=f'{analysis_type} Cohort', how='inner')
                columns = [f'{analysis_type} Cohort', 'Month Start', 'Month End', 'Median activation time', 'Median setup time', 'Total Sample', 'Total Activated', 'Activation rate (%)','Total Setup', 'Setup rate (%)']
                times_df = times_df[columns]

            # Build the AgGrid and write back to Streamlit
            gb = GridOptionsBuilder.from_dataframe(times_df)
            func.build_grid(gb, times_df, 400)

            # Create the visuals to accompany it
            st.write('### Onboarding Time Visuals')
            # North Star Visual togel
            ns_viz_on = tog.toggle(
                label='Show Metric Visual',
                key="switch_3",
                value=True,
                widget='checkbox')

            if ns_viz_on:
                # Create the multi-select option for the visuals
                ns_cols=['Median activation time', 'Median setup time', 'Activation rate (%)', 'Setup rate (%)']
                ns_options = st.multiselect(
                    'Select columns to plot:',
                    ns_cols,
                    ns_cols[:2]
                )
                # Melt data to format the data for the line plot
                times_source = pd.melt(times_df.loc[pd.to_datetime(times_df[f'{analysis_type} Cohort'], format='%Y-%m-%d')>=first_day_six_months_ago], id_vars=[f'{analysis_type} Cohort'], value_vars=ns_options, var_name='Metric', value_name='Days', ignore_index=True)
                fig = px.line(times_source, x=f'{analysis_type} Cohort', y='Days', color='Metric', line_shape='spline')
                fig.update_traces(line=dict(width=3))
                st.plotly_chart(fig, use_container_width=True)

            # Here we are building the section to allow users to query the activation data
            st.write('### Cohort Double Click 🕵️')

            with st.form('Pull cohort details'):

                # create 3 columns for the filters
                col1, col2, col3 = st.columns(3)
                with col1:
                    start_date_crit = st.date_input("CW Start Date", value=dt.date.today() - dt.timedelta(days=7))
                with col2:
                    end_date_crit = st.date_input("CW End Date", value=dt.date.today())
                with col3:
                    metric_select = st.selectbox('Select metric:', ['Active', 'Setup'])

                pull_cohort_details = st.form_submit_button('Pull Cohort Data')

                # Create the button to trigger the analysis
                if pull_cohort_details:

                    metric_dict = {'Active':'active_time', 'Setup':'setup_time'}
                    metric = metric_dict[metric_select]
                    if product == 'OM':
                        columns = ['account_name', 'parent_account_name', 'facility_id', 'onboarding_id', 'activation_owner', 'onboarding_status', 'ap_cw_date', 'ob_object_setup_date', 'setup_time', 'setup_met', 'ob_object_active_date',  'active_time', 'activation_met']
                        ns_df = filtered_df[columns].loc[(filtered_df['ap_cw_date'].dt.date>=start_date_crit) & (filtered_df['ap_cw_date'].dt.date<=end_date_crit) & (~pd.isna(filtered_df[metric])) & (filtered_df['ob_object_active_date'].dt.date<=end_date_crit)]
                        for col in ['ap_cw_date', 'ob_object_setup_date', 'ob_object_active_date']:
                            ns_df[col]=ns_df[col].dt.strftime('%Y-%m-%d')
                    else:
                        columns = ['account_name', 'parent_account_name', 'facility_id', 'ap_id', 'activation_owner', 'ap_status', 'ap_cw_date', 'ap_setup_date', 'setup_time', 'setup_met', 'ap_active_date',  'active_time', 'activation_met']    
                        ns_df = filtered_df[columns].loc[(pd.to_datetime(filtered_df['ap_cw_date']).dt.date>=start_date_crit) & (pd.to_datetime(filtered_df['ap_cw_date']).dt.date<=end_date_crit) & (~pd.isna(filtered_df[metric])) & (pd.to_datetime(filtered_df['ap_active_date']).dt.date<=end_date_crit)]            
                        for col in ['ap_cw_date', 'ap_setup_date', 'ap_active_date']:
                            ns_df[col]=pd.to_datetime(ns_df[col]).dt.strftime('%Y-%m-%d')

                    # Build the AgGrid and write back to Streamlit
                    gb = GridOptionsBuilder.from_dataframe(ns_df)
                    func.build_grid(gb, ns_df, 800, pagination=True)

    with tab4: # Onboarding Buckets
        if len(filtered_df) == 0:
            st.warning("#### No records exist for these filters, please try and pull a different cohort ☝️")
        else:
            # Pull the data using our functions
            st.write('### Activation Bucket Analysis')
            bucket_2 = func.get_buckets_2(filtered_df, weekly=weekly)

            # Build the AgGrid and write back to Streamlit
            gb = GridOptionsBuilder.from_dataframe(bucket_2)
            func.build_grid(gb, bucket_2, 800)

elif view_selected=='AppIQ':

    st.markdown("### Any questions about the app, please ask below 🦜")

    #question = st.text_input("Ask me anything! 👈")
    #submit = st.button("Submit question")

    #documents = func.load_docs()
    #embeddings = func.initialize_embeddings()

    #if submit==True:
    #    result, docs = func.app_iq_answer_question(documents=documents, embeddings=embeddings, question=question)

    #    st.markdown(result)