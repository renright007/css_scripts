import pandas as pd
from ds.utilities.io import ds_trino
import datetime
from ds.utilities.secrets import secrets
from google.oauth2 import service_account
import pygsheets
from db_connection import DatabaseConnection
from superset import Superset


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

def get_table(sql_str: str) -> pd.DataFrame:
    return ds_trino.fetch_data(
        sql_str = sql_str,
        conn = ds_trino.create_trino_connection(user = 'robert.enright'),
        use_cache=False
    ).reset_index(drop=True)

def connect_to_sheets(sheet_id):
    
    # Point your notebook to sheets. Remember to share it with the service account email!
    return gc.open_by_key(sheet_id)

def push_ue_ids_to_superset(df, append=True):
   
    # Connect to Superset
    db_conn = DatabaseConnection()
    # Connect to Superset Engine
    db_engine = db_conn.get_engine()
    
    schema_name = 'early_life_cyle'
    TABLE = 'ubereats_external_store_ids'
    
    if append:
        append_value='append'
    else:
        append_value='replace'
    
    try:
        df.to_sql(f"{TABLE}", con=db_engine, schema=schema_name, if_exists=f"{append_value}", index=False)
        message = "Push "
    except Exception as e:
        message = f"Failed to update {TABLE} data into Superset. Error: {e}"
        
    return message
    
def get_user_list():
    
    query = f"""
    SELECT DISTINCT
      CONCAT(firstname,' ',lastname) user_name
      , email
      , CONCAT(email, ' (', firstname,' ',lastname, ')') output_name
    FROM hudi_ingest.salesforce_otter.user
    WHERE 1=1
      AND isactive=True
    ORDER BY 1 ASC"""
    
    return get_table(query)

def get_org_list():
    
    query = f"""
    SELECT 
      organization_id
      , ent_orgs.org_name
      , CONCAT(ent_orgs.org_name, ' (', ent_orgs.organization_id, ')') output_org
      , sot.uuid
    FROM iceberg.globalsp_iceberg.us_enterprise_orgs ent_orgs
    LEFT JOIN hudi_ingest.operations.dolodex_sot_agreement sot ON sot.org_id = ent_orgs.organization_id
    WHERE 1=1
      AND is_demo_org=False
      AND is_deleted=False
    ORDER BY 2 ASC
    """
    return get_table(query)

#### UBER EATS
    
def get_complete_ue_orders_df(org_name, uuid):
    
    query = f"""
    select
      puo.workflow_uuid,
      puo.time_customer_ordered,
      puo.customer_refunded,
      puo.refunded_covered_by_merchant,
      puo.refund_not_covered_by_merchant,
      puo.item_issue_details,
      -- hoi.external_order_id,
      hoi.store_id,
      drs.uuid,
      dsa.org_name,
      dsa.brand_name
    from iceberg.scratch.{org_name}_ue_orders as puo
    inner join hudi_ingest.api_orders.customer_orders as hoi
      on puo.workflow_uuid = hoi.external_order_id
    left join hudi_ingest.operations.dolodex_rr_stores as drs
      on drs.store_id = hoi.store_id
    left join hudi_ingest.operations.dolodex_sot_agreement as dsa
      on drs.uuid = dsa.uuid
    where 1=1
      and day_partition >= '2023-10-01'
      and drs.uuid is not null
      and drs.uuid != '-1'
      and drs.uuid = '{uuid}'"""
    
    return get_table(query)

def get_complete_ue_orders_df_2(df, input_date, uuid):
    
    df1 = df.copy()
    df1 = df1.rename(columns={
        'Workflow UUID':'workflow_uuid',
        'Time Customer Ordered':'time_customer_ordered',
        'Customer Refunded':'customer_refunded',
        'Refund Covered by Merchant':'refund_covered_by_merchant',
        'Refund Not Covered by Merchant':'refund_not_covered_by_merchant',
        'Item Issue Details':'item_issue_details',
        'External Store ID':'external_store_id'
    })
    
    query = f"""
    select
      hoi.external_order_id as workflow_uuid,
      hoi.store_id,
      hoi.facility_name,
      drs.uuid,
      dsa.org_name,
      dsa.brand_name
    FROM hudi_ingest.api_orders.customer_orders as hoi
    left join hudi_ingest.operations.dolodex_rr_stores as drs
      on drs.store_id = hoi.store_id
    left join hudi_ingest.operations.dolodex_sot_agreement as dsa
      on drs.uuid = dsa.uuid
    where 1=1
      and day_partition >= '{input_date}'
      and drs.uuid is not null
      and drs.uuid != '-1'
      and drs.uuid = '{uuid}'"""
    
    df2 = get_table(query)
    
    output_df = df1.merge(df2, how='inner', on='workflow_uuid')
    output_cols = [
        'workflow_uuid','time_customer_ordered','customer_refunded',
        'refund_covered_by_merchant','refund_not_covered_by_merchant',
        'item_issue_details','store_id','facility_name','uuid','org_name',
        'brand_name', 'external_store_id'
    ]
    
    return output_df[output_cols]

def get_ue_tam(df):
    # tam = df['Customer Refunded'].sum()
    tam_df = df.copy()
    tam_df['item_issue_details'] = tam_df['item_issue_details'].fillna('')
    # tam_df = tam_df[tam_df['item_issue_details'].str.contains('MISCELLANEOUS')]
    tam = tam_df['customer_refunded'].sum()
    print(tam)

    return tam, tam_df

def get_ue_winbacks(df):
    # type ='MISC' and o.notes = 'Restaurant refunds'
    # external_order_status = 'Refund Disputed'

    # per Joao, winbacks will be the column 'Refund Not Covered by The Merchant'
    # TAM will be the column 'Customer Refunded'
    # Workflow UUID is the external_order_id, we should be able to match to our submissions without issue

    # winbacks = df['Refund Not Covered by Merchant'].sum()
    df['item_issue_details'] = df['item_issue_details'].fillna('')
    winbacks_df = df.copy()
    # winbacks_df = df[df['item_issue_details'].str.contains('MISCELLANEOUS')]
    winbacks_df = winbacks_df[winbacks_df['refund_not_covered_by_merchant'] != 0.00]

    winbacks = winbacks_df['refund_not_covered_by_merchant'].sum()
    print(winbacks)

    return winbacks, winbacks_df

def create_files(errors_df, folder_name):
    org_names = errors_df['org_name'].unique()
    print(len(org_names))

    for org_name in org_names:
        print(org_name)
        org_df = errors_df[errors_df['org_name'] == org_name]
        print('Org Only Filter: ' + str(len(org_df)))

        org_ue_tam, org_ue_tam_df = get_ue_tam(org_df)
        org_ue_winbacks, org_ue_winbacks_df = get_ue_winbacks(org_df)

        print('TAM Only Filter: ' + str(len(org_ue_tam_df)))
        print('Wins Only Filter: ' + str(len(org_ue_winbacks_df)))

        org_ue_tam_df.to_csv(folder_name + '/results/ubereats/cancels_tam_files/' + org_name + '.csv')
        org_ue_winbacks_df.to_csv(folder_name + '/results/ubereats/cancels_winback_files/' + org_name + '.csv')

    return

def format_df(df):

    df.columns = [col.lower().replace(' ', '_') for col in df.columns]

    df['external_store_id'] = df['external_store_id'].astype(str).apply(lambda x: x.replace('.0', '') if x != 'nan' else x)

    df['time_customer_ordered'] = pd.to_datetime(df['time_customer_ordered'])
    df['time_customer_ordered'] = df['time_customer_ordered'].apply(lambda x: x.to_pydatetime())

    df['time_merchant_accepted'] = pd.to_datetime(df['time_merchant_accepted'])
    df['time_merchant_accepted'] = df['time_merchant_accepted'].apply(lambda x: x.to_pydatetime())

    df['time_customer_was_refunded'] = pd.to_datetime(df['time_customer_was_refunded'])
    df['time_customer_was_refunded'] = df['time_customer_was_refunded'].apply(lambda x: x.to_pydatetime())

    return df

def get_dd_store_ids(uuid, errors=True):
    
    query = f"""
    select
      drs.store_id,
      drs.dd_store_id_3
    from hudi_ingest.operations.dolodex_rr_stores as drs
    where 1=1
      and drs.status = 'Live'
      and drs.uuid = '{uuid}'"""
    
    df = get_table(query)
    df = df.fillna(0)
    
    if errors:
        df['dd_store_id_3'] = df['dd_store_id_3'].astype(int)
    
    return df

def filter_for_dd_error_charges(df, org_df):
    filtered_df = df[df['Transaction Type'] == 'ERROR_CHARGE']
    filtered_df = filtered_df.copy()
    filtered_df.reset_index(drop=True, inplace=True)
    # print(filtered_df)
    # filtered_df['Store ID'] = filtered_df['Store ID'].astype(str)

    store_ids = org_df['dd_store_id_3'].unique()
    # print(type(store_ids))
    stores_filtered_df = filtered_df[filtered_df['Store ID'].isin(store_ids)]
    stores_filtered_df.reset_index(drop=True, inplace=True)
    # print(stores_filtered_df)

    tam_amount = stores_filtered_df['Error Charge'].sum()

    unique_merchant_delivery_ids = stores_filtered_df['Merchant Delivery ID'].unique()

    return tam_amount, unique_merchant_delivery_ids, stores_filtered_df

def get_dd_error_charges_winbacks(df, org_df, unique_ids):

    # only get adjustments that had a corresponding error charge
    # so lets get the unique values in Merchant Delivery ID column for all our Errors
    # then filter down to only those in our Adjustments

    filtered_df = df[df['Transaction Type'] == 'ADJUSTMENT']
    filtered_df = filtered_df[filtered_df['Description'] == 'merchant_payment_adjustment']
    filtered_df = filtered_df.copy()
    filtered_df.reset_index(drop=True, inplace=True)
    # filtered_df['Store ID'] = filtered_df['Store ID'].astype(str)


    store_ids = org_df['dd_store_id_3'].unique()
    stores_filtered_df = filtered_df[filtered_df['Store ID'].isin(store_ids)]
    stores_filtered_df.reset_index(drop=True, inplace=True)

    adj_with_matching_errors_df = stores_filtered_df[stores_filtered_df['Merchant Delivery ID'].isin(unique_ids)]
    adj_with_matching_errors_sum = adj_with_matching_errors_df['Adjustment'].sum()

    only_adjustment_df = stores_filtered_df[~stores_filtered_df['Merchant Delivery ID'].isin(unique_ids)]
    only_adjustment_sum = only_adjustment_df['Adjustment'].sum()

    return adj_with_matching_errors_sum, only_adjustment_sum, adj_with_matching_errors_df, only_adjustment_df

def get_tam_wins_win_perc(df, org_input_pair):
    org_name = org_input_pair[0]
    # org_input = org_input_pair[1]
    org_df = org_input_pair[1]

    errors_amt, unique_merchant_delivery_ids, dd_errors_df = filter_for_dd_error_charges(df, org_df)
    adj_with_errors_amount, only_adjustment_sum, adj_with_errors_df, only_adjustment_df = get_dd_error_charges_winbacks(df, org_df, unique_merchant_delivery_ids)

    new_tam_df = pd.concat([dd_errors_df, only_adjustment_df])
    winbacks_df = pd.concat([adj_with_errors_df, only_adjustment_df])

    new_tam_df['Organization Name'] = org_name
    winbacks_df['Organization Name'] = org_name

    new_tam = errors_amt + only_adjustment_sum
    total_won = adj_with_errors_amount + only_adjustment_sum
    winback_perc = total_won / new_tam

    return new_tam, total_won, winback_perc, new_tam_df, winbacks_df

def get_month_values(folder_name, df, org_list):
    total_tam_df = pd.DataFrame()
    total_wins_df = pd.DataFrame()
    final_results_list = []

    for org_pair in org_list:
        print(org_pair[0])
        # print(org_input_pair[1])
        org_tam, org_wins, org_win_perc, org_tam_df, org_wins_df = get_tam_wins_win_perc(df, org_pair)
        print(org_tam, org_wins, org_win_perc)

        # Change file path
        #org_tam_df.to_csv(folder_name + '/results/doordash/errors_tam_files/' + str(org_pair[0]) + '.csv')
        #org_wins_df.to_csv(folder_name + '/results/doordash/errors_winback_files/' + str(org_pair[0]) + '.csv')

        unique_tam_store_count = count_store_ids(org_tam_df)
        unique_wins_store_count = count_store_ids(org_wins_df)

        total_tam_df = pd.concat([total_tam_df, org_tam_df])
        total_wins_df = pd.concat([total_wins_df, org_wins_df])

        org_results_list = [str(org_pair[0]), org_tam, org_wins, org_win_perc,
                            unique_tam_store_count, unique_wins_store_count]
        final_results_list.append(org_results_list)

    final_results_df = pd.DataFrame(final_results_list, columns =['org_name', 'tam', 'wins', 'win_perc',
                                                                 'unique_tam_store_count', 'unique_wins_store_count'])

    return total_tam_df, total_wins_df, final_results_df

def setup_org_dd_store_id_list(stores_df):
    popeyes_org_data_list = []

    org_names = stores_df['org_name'].unique()
    # print(type(org_names))
    print(len(org_names))
    # print(org_names)

    for org_name in org_names:
        print(org_name)
        single_org_df = stores_df[stores_df['org_name'] == org_name]
        popeyes_org_pair = [org_name, single_org_df]
        popeyes_org_data_list.append(popeyes_org_pair)

    return popeyes_org_data_list

def count_store_ids(df):
    unique_store_ids = df['Store ID'].nunique()
    print(unique_store_ids)

    return unique_store_ids

def filter_for_dd_cancels_tam(df, org_df):

    store_ids = org_df['dd_store_id_3'].unique()

    stores_filtered_df = df[df['Store ID'].isin(store_ids)]
    stores_filtered_df.reset_index(drop=True, inplace=True)

    tam_amount = stores_filtered_df['Order Subtotal'].sum()

    return tam_amount, stores_filtered_df


def filter_for_dd_cancels_wins(df, org_df):

    filtered_df = df[df['Paid'] == True]
    filtered_df = filtered_df.copy()
    filtered_df.reset_index(drop=True, inplace=True)

    store_ids = org_df['dd_store_id_3'].unique()

    stores_filtered_df = filtered_df[filtered_df['Store ID'].isin(store_ids)]
    stores_filtered_df.reset_index(drop=True, inplace=True)

    win_amount = stores_filtered_df['Net Payout'].sum()

    return win_amount, stores_filtered_df

def run_all_orgs(cancels_df, org_list, folder_name):
    total_tam_df = pd.DataFrame()
    total_wins_df = pd.DataFrame()
    final_results_list = []

    for org_pair in org_list:
        print(org_pair[0])
        # print(org_input_pair[1])
        org_tam_amt, org_tam_df = filter_for_dd_cancels_tam(cancels_df, org_pair[1])
        org_cancels_amt, org_cancels_df = filter_for_dd_cancels_wins(cancels_df, org_pair[1])

        org_win_perc = org_cancels_amt / org_tam_amt

        print("TAM: " + str(org_tam_amt) + "   Winbacks: " + str(org_cancels_amt) + "   Win Perc: " + str(org_win_perc))

        org_tam_df['org_name'] = str(org_pair[0])
        org_cancels_df['org_name'] = str(org_pair[0])

        #org_tam_df.to_csv(folder_name + '/results/doordash/cancels_tam_files/' + str(org_pair[0]) + '.csv')
        #org_cancels_df.to_csv(folder_name + '/results/doordash/cancels_winback_files/' + str(org_pair[0]) + '.csv')

        unique_tam_store_count = count_store_ids(org_tam_df)
        unique_wins_store_count = count_store_ids(org_cancels_df)

        total_tam_df = pd.concat([total_tam_df, org_tam_df])
        total_wins_df = pd.concat([total_wins_df, org_cancels_df])

        org_results_list = [str(org_pair[0]), org_tam_amt, org_cancels_amt,
                            org_win_perc, unique_tam_store_count, unique_wins_store_count]
        final_results_list.append(org_results_list)

    final_results_df = pd.DataFrame(final_results_list, columns =['org_name', 'tam', 'wins', 'win_perc',
                                                                 'unique_tam_store_count', 'unique_wins_store_count'])

    return final_results_df, total_tam_df, total_wins_df

def create_win_perc_by_cancel_reason(df, org_df):
    df['Cancellation Category - Short'].fillna('Blank', inplace=True)
    df['Cancellation Category - Description'].fillna('Blank', inplace=True)

    unique_cancel_reasons = list(df['Cancellation Category - Short'].unique())
    # unique_cancel_reasons_desc = list(df['Cancellation Category - Description'].unique())
    # unique_pairs_df = df[['Cancellation Category - Short', 'Cancellation Category - Description']].drop_duplicates()
    
    stores_df = org_df[1]

    cancel_reason_df = pd.DataFrame()
    results_list = []
    total_tam_df = pd.DataFrame()
    total_wins_df = pd.DataFrame()

    for reason in unique_cancel_reasons:
        # print(type(pair_row))
        print(reason)
        cancel_short_val = reason
        # cancel_desc_val = pair_row['Cancellation Category - Description']
        # cancel_reason_df = df[(df['Cancellation Category - Short'] == cancel_short_val) & (df['Cancellation Category - Description'] == cancel_desc_val)]
        cancel_reason_df = df[(df['Cancellation Category - Short'] == cancel_short_val)]

        wins_amt, wins_df = filter_for_dd_cancels_wins(cancel_reason_df, stores_df)
        tam_amt, tam_df = filter_for_dd_cancels_tam(cancel_reason_df, stores_df)

        total_tam_df = pd.concat([total_tam_df, tam_df])
        total_wins_df = pd.concat([total_wins_df, wins_df])

        win_perc = wins_amt / tam_amt

        print("TAM: " + str(tam_amt) + "   Winbacks: " + str(wins_amt) + "   Win Perc: " + str(win_perc))

        results_list.append([cancel_short_val, tam_amt, wins_amt, win_perc])


    results_df = pd.DataFrame(results_list, columns=['cancel_category_short',
                                                    'tam_amt','wins_amt','win_percentage'])

    return results_df, total_tam_df, total_wins_df

def create_all_org_cancel_reason(cancels_df, org_list):
    total_results_df = pd.DataFrame()
    total_tam_df = pd.DataFrame()
    total_wins_df = pd.DataFrame()

    for org_pair in org_list:
        org_results_df, org_tam_df, org_wins_df = create_win_perc_by_cancel_reason(cancels_df, org_pair)
        org_results_df['org_name'] = str(org_pair[0])
        org_tam_df['org_name'] = str(org_pair[0])
        org_wins_df['org_name'] = str(org_pair[0])
        total_results_df = pd.concat([total_results_df, org_results_df])
        total_tam_df = pd.concat([total_tam_df, org_tam_df])
        total_wins_df = pd.concat([total_wins_df, org_wins_df])

    return total_results_df, total_tam_df, total_wins_df