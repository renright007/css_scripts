import pandas as pd
from ds.utilities.io import ds_trino
import datetime
from ds.utilities.secrets import secrets
from google.oauth2 import service_account
import pygsheets
import tam_functions as tf
from googleapiclient.discovery import build

SCOPES = (
"https://www.googleapis.com/auth/spreadsheets",
"https://www.googleapis.com/auth/drive",
)
bot_creds = secrets.Secrets().get_secret("global_growth_ops_service_account")
my_credentials = service_account.Credentials.from_service_account_info(
bot_creds,
scopes=SCOPES,
)
gc= pygsheets.authorize(custom_credentials=my_credentials)
client = build('drive', 'v3', credentials=my_credentials)

def get_table(sql_str: str) -> pd.DataFrame:
    return ds_trino.fetch_data(
        sql_str = sql_str,
        conn = ds_trino.create_trino_connection(user = 'robert.enright'),
        use_cache=False
    ).reset_index(drop=True)

def connect_to_sheets(sheet_id):
    
    # Point your notebook to sheets. Remember to share it with the service account email!
    ss = gc.open_by_key(sheet_id)
    
def create_open_gsheet(email,filename):

    name = email.split('@')[0]

    sheet = gc.sheet.create(filename)
    wks = gc.open(filename)

    #wks[0].set_dataframe(df.fillna(''), (1,1), extend = True, copy_head = True, fit = False, copy_index = False)
    wks.share(email, role='writer')
    link = sheet.get('spreadsheetUrl')
    wks_id = sheet.get('spreadsheetId')
    return wks_id,link
    
def copy_template_file(email):
    
    copied_file = client.files().copy(
        fileId='1j-_YFjxNCraJx4Ys-qj0X-9NN4Ted0DmUTyOvq6aYHk',
        body={"name": f"Copy of TAM Analysis Template"}
    ).execute()

    ss = gc.open_by_key(copied_file['id'])
    ss.share(email, role='writer')

    return copied_file['id']
    
def dd_cancellations(input_df, folder_name, uuid, start_date):
    
    # Pull the DD store ids using the UUID
    stores_df = tf.get_dd_store_ids(uuid, errors=False)
    org_list = [[folder_name, stores_df]]
    
    # Transform the merchant reports
    cancels_df = input_df.copy()
    # Format key columns
    cancels_df['Store ID'] = cancels_df['Store ID'].astype(str)
    cancels_df["Order Placed Date"] = pd.to_datetime(cancels_df["Order Placed Date"])
    cancels_df = cancels_df[cancels_df['Order Placed Date'] > pd.to_datetime(start_date)]    
    cancels_df['month_year'] = cancels_df['Order Placed Date'].dt.to_period('M')
    
    # Create Summary View
    org_cancels_df, total_tam_df, total_wins_df = tf.run_all_orgs(cancels_df, org_list, folder_name)
    
    # Use pivot function to aggregate cancellation and winback data
    # 1 Org cancelled orders subtotal by Month
    tam_pivot_table = total_tam_df.pivot_table(
        values='Order Subtotal',
        index='org_name',
        columns='month_year',
        aggfunc='sum',
        fill_value=0
    )
    # 2 Store cancelled orders subtotal by Month
    tam_by_store_pivot_table = total_tam_df.pivot_table(
        values='Order Subtotal',
        index=['org_name', 'Store Name', 'Store ID'],
        columns='month_year',
        aggfunc='sum',
        fill_value=0
    )
    # 3 Org winback data by Month
    wins_pivot_table = total_wins_df.pivot_table(
        values='Net Payout',
        index='org_name',
        columns='month_year',
        aggfunc='sum',
        fill_value=0
    )
    # 4 Store winback data by Month
    wins_by_store_pivot_table = total_wins_df.pivot_table(
        values='Net Payout',
        index=['org_name', 'Store Name', 'Store ID'],
        columns='month_year',
        aggfunc='sum',
        fill_value=0
    )

    # Pull aggregated cancellation reason data
    all_orgs_cancel_reasons_df, all_orgs_cancel_reasons_tam_df, all_orgs_cancel_reasons_wins_df = tf.create_all_org_cancel_reason(cancels_df, org_list)
    # 5 Org cancelled orders data grouped by reason
    cancel_reasons_tam_pivot_table = all_orgs_cancel_reasons_tam_df.pivot_table(
        values='Order Subtotal',
        index=['org_name', 'Cancellation Category - Short'],
        columns='month_year',
        aggfunc='sum',
        fill_value=0
    )
    # 5 Org winback data grouped by reason
    cancel_reasons_wins_pivot_table = all_orgs_cancel_reasons_wins_df.pivot_table(
        values='Net Payout',
        index=['org_name', 'Cancellation Category - Short'],
        columns='month_year',
        aggfunc='sum',
        fill_value=0
    )
    
    return org_cancels_df, tam_pivot_table, tam_by_store_pivot_table, wins_by_store_pivot_table, wins_pivot_table, cancel_reasons_tam_pivot_table, cancel_reasons_wins_pivot_table

def dd_errors(input_df, folder_name, uuid, start_date):
    
    # Pull the DD store ids using the UUID
    stores_df = tf.get_dd_store_ids(uuid)
    org_list = [[folder_name, stores_df]]
    
    # Transform the merchant reports
    errors_df = input_df.copy()
    errors_df['Organization Name'] = folder_name
    # Format key columns
    errors_df["Timestamp Local Date"] = pd.to_datetime(errors_df["Timestamp Local Date"])
    errors_df = errors_df[errors_df['Timestamp Local Date'] > pd.to_datetime(start_date)]
    errors_df['month_year'] = errors_df['Timestamp Local Date'].dt.to_period('M')
    errors_df['total_tam'] = errors_df['Error Charge'] + errors_df['Adjustment']
    
    # Results DF
    dd_tam = errors_df['total_tam'].sum()
    dd_winbacks = errors_df['Adjustment'].sum()
    dd_wb_perc = dd_winbacks/dd_tam
    # Combine the two for the results
    results_df = pd.DataFrame({
        'org_name':[folder_name],
        'tam':[dd_tam],
        'wins':[dd_winbacks],
        'win_perc':[dd_wb_perc]
        })
    #unique_tam_store_count
    #unique_wins_store_count
    
    total_tam_df, total_wins_df, results_df_2 = tf.get_month_values(folder_name, errors_df, org_list)

    # Format TAM df columns
    total_tam_df["Timestamp Local Date"] = pd.to_datetime(total_tam_df["Timestamp Local Date"])
    total_tam_df['month_year'] = total_tam_df['Timestamp Local Date'].dt.to_period('M')
    total_tam_df['total_tam'] = total_tam_df['Error Charge'] + total_tam_df['Adjustment']
    # Format winback df columns
    total_wins_df["Timestamp Local Date"] = pd.to_datetime(total_wins_df["Timestamp Local Date"])
    total_wins_df['month_year'] = total_wins_df['Timestamp Local Date'].dt.to_period('M')

    # Create summary pivot table views
    # 1 Org errors TAM value agg by month
    tam_pivot_table = errors_df.pivot_table(
        values='total_tam',
        index='Organization Name',
        columns='month_year',
        aggfunc='sum',
        fill_value=0
    )
    # 2 Stores errors TAM value agg by month
    tam_by_store_pivot_table = errors_df.pivot_table(
        values='total_tam',
        index=['Organization Name', 'Store Name', 'Store ID'],
        columns='month_year',
        aggfunc='sum',
        fill_value=0
    )
    # 3 Org errors winback value agg by month
    wins_pivot_table = errors_df.pivot_table(
        values='Adjustment',
        index='Organization Name',
        columns='month_year',
        aggfunc='sum',
        fill_value=0
    )
    # 4 Store errors winback value agg by month
    wins_by_store_pivot_table = errors_df.pivot_table(
        values='Adjustment',
        index=['Organization Name', 'Store Name', 'Store ID'],
        columns='month_year',
        aggfunc='sum',
        fill_value=0
    )
    
    return total_tam_df, total_wins_df, results_df, tam_pivot_table, tam_by_store_pivot_table, wins_pivot_table, wins_by_store_pivot_table 

def ubereats_cancellations(org_name, uuid):

    # Get the UE orders via query 
    complete_ue_orders_df = tf.get_complete_ue_orders_df_2(org_name, '2024-01-01', uuid)
    
    # Get the TAM data
    ue_tam, ue_tam_df = tf.get_ue_tam(complete_ue_orders_df)
    
    # Get the winbacks data
    ue_winbacks, ue_winbacks_df = tf.get_ue_winbacks(complete_ue_orders_df)
    
    # Winback Percentage
    win_perc = ue_winbacks / ue_tam
    
    return ue_tam, ue_winbacks, win_perc

def ubereats_errors(input_df, org_name, uuid, start_date):

    # Pull in and transform the merchant report
    ue_errors_df = input_df.copy()
    
    # Get the UE orders via query
    start_date_str = start_date.strftime('%Y-%m-%d')
    complete_ue_errors_df = tf.get_complete_ue_orders_df_2(ue_errors_df, start_date_str, uuid)
    complete_ue_errors_df['time_customer_ordered'] = pd.to_datetime(complete_ue_errors_df["time_customer_ordered"])
    complete_ue_errors_df['month_year'] = complete_ue_errors_df['time_customer_ordered'].dt.to_period('M')
    
    # Get the TAM data
    ue_tam, ue_tam_df = tf.get_ue_tam(complete_ue_errors_df)

    # Store Count
    distinct_tam_store_count = complete_ue_errors_df['store_id'].nunique()
    
    # Group the DF by Org and rename columns
    grouped_complete_ue_errors_df = complete_ue_errors_df.groupby('org_name').agg(
        {'customer_refunded': 'sum',
         'refund_not_covered_by_merchant': 'sum'
        })
    grouped_complete_ue_errors_df = grouped_complete_ue_errors_df.rename(columns={"refund_not_covered_by_merchant": "Winbacks", "customer_refunded": "TAM"})

    # Aggregate out by month
    distinct_value_counts = ue_tam_df['store_id'].value_counts()

    # Create summary pivot tables
    # 1 Org errors TAM value agg by month
    tam_pivot_table = ue_tam_df.pivot_table(
        values='customer_refunded',
        index='org_name',
        columns='month_year',
        aggfunc='sum',
        fill_value=0
    )

    # 2 Store errors TAM value agg by month    
    tam_by_store_pivot_table = complete_ue_errors_df.pivot_table(
        values='customer_refunded',
        index=['org_name', 'facility_name', 'store_id'],
        columns='month_year',
        aggfunc='sum',
        fill_value=0
    )

    return ue_tam, complete_ue_errors_df, grouped_complete_ue_errors_df, tam_pivot_table, tam_by_store_pivot_table

def ubereats_payments(input_df, org_name, start_date):

    # Pull in and transform the merchant report
    ue_payments_df = input_df.copy()
    ue_payments_df.columns = ue_payments_df.columns.str.strip()
    ue_payments_df['org_name'] = org_name

    # Ensure we are only looking at restaurant refunds & refund disputes
    winbacks_df = ue_payments_df.loc[(ue_payments_df['Order Status']=='Refund Disputed') | (ue_payments_df['Other payments description']=='Restaurant refunds')]

    # Winbacks are the refund dispute payment transactions
    winbacks_df["Order Date"] = pd.to_datetime(winbacks_df["Order Date"], format='%m/%d/%y')
    winbacks_df = winbacks_df[winbacks_df['Order Date'] > pd.to_datetime(start_date)]
    winbacks_df['month_year'] = winbacks_df['Order Date'].dt.to_period('M')
    winbacks_df['Winbacks'] = winbacks_df['Total payout'].astype(int)
    winbacks = winbacks_df['Winbacks'].sum()

    # Store Count
    distinct_winback_store_count = winbacks_df['Store ID'].nunique()
    
    # Create summary pivot tables
    # 1 Org errors winbacks value agg by month
    wins_pivot_table = winbacks_df.pivot_table(
        values='Winbacks',
        index='org_name',
        columns='month_year',
        aggfunc='sum',
        fill_value=0
    )
    
    # 2 Store winback value agg by month
    wins_by_store_pivot_table = winbacks_df.pivot_table(
        values='Winbacks',
        index=['org_name', 'Store Name', 'Store ID'],
        columns='month_year',
        aggfunc='sum',
        fill_value=0
    )
    
    return winbacks, winbacks_df, wins_pivot_table, wins_by_store_pivot_table

def ue_link_payments_and_errors(df1, df2):
    
    df_errors = df1.copy()
    df_refunds = df2.copy()

    # For the errors group by the Order ID to return the concenated order list and the sum of the errors
    df_errors_ss = df_errors[['Order ID', 'Order Issue', 'Inaccurate Items', 'Inaccurate Customizations', 'Customer Refunded']]
    
    # Define a function that processes each cell
    def process_string(s):
        if isinstance(s, str) and s.startswith('#'):
            return s[1:]  # Return the string after the first character
        return s  # Return the original string if it doesn't start with '#'

    # Apply the function to the column
    df_refunds['Order ID'] = df_refunds['Order ID'].apply(process_string)

    # Join the DFs back on the Order ID
    output_df = df_refunds.merge(df_errors_ss, on='Order ID', how='left')
    items_df = output_df[['Order ID', 'Inaccurate Items']].loc[~pd.isna(output_df['Inaccurate Items']) & output_df['Order Issue'].isin(['MISSING_ITEMS', 'PARTIAL_MISSING_ITEMS'])]
    
    # Get the refunded order frequency
    items_df['Inaccurate Items'] = items_df['Inaccurate Items'].astype(str)
    items_df['Inaccurate Items'] = items_df['Inaccurate Items'].str.split('|').apply(lambda x: [item.strip() for item in x])
    # Explode the lists into individual rows
    items_exploded = items_df.explode('Inaccurate Items')
    # Get the frequency counts
    value_counts = items_exploded['Inaccurate Items'].value_counts()
    item_issues_df = value_counts.reset_index()
    item_issues_df.columns = ['Inaccurate Items', 'count']
    
    return output_df, item_issues_df

def transform_pivot_to_df(df, output_col):
    # Transform to dict
    original_dict = df.to_dict()
    customer_name = df.first_valid_index() 

    # Remove the org name
    try:
        transformed_dict = {k: v[f'{customer_name}'] for k, v in original_dict.items()}
    except:
        transformed_dict = {k: v[f'{customer_name}'] for k, v in original_dict.items()}

    
    return pd.DataFrame(list(transformed_dict.items()), columns=['month_year', f'{output_col}'])

def transform_multiindex_to_df(df):

    #customer_name = df.index.levels[0][0]
    
    try:
        new_df = df.droplevel('org_name').reset_index()
    except:
        new_df = df.droplevel('Organization Name').reset_index()

    json = new_df.to_json(orient='records')
    output_df = pd.read_json(json, orient='records')

    return output_df