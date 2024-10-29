###############################################
# DOL Office of Data Governance (odg@dol.gov) #
###############################################

# Import libraries.
import streamlit as st
import requests
import pandas as pd
import io
import urllib.parse
import json 


### Page configuration ###
st.set_page_config(
    page_title="DOL API Explorer",
    page_icon="rocket",
    layout="wide",
)

### CSS styling ###
st.markdown('''
            <style>
            [data-testid="stExpander"]{
                border: 1.5px solid;
                border-radius: 10px;
                border-color: #ff4b4b;                
            }
                        
            .stExpander {
            color: #ff4b4b;  
            font-family: Arial;  
            font-size: 18px;  
            font-weight: bold;
            }
                        
            [data-testid="baseButton-secondary"]{
                background-color: #17157a;
                color: white
            }            
            </style>
            
            ''', unsafe_allow_html=True)

############
# Side bar # 
############  
st.sidebar.header('About the API Explorer')
                   
st.sidebar.markdown('''
    The **DOL API** is a web service that provides on-demand access to machine readable metadata and data. This tool was developed to educate and train new users on the API's structure and operation. 

    To get official DOL data, visit the [Open Data Portal](https://www.dataportal.dol.gov).
                
    **Resources:**
    ''')

st.sidebar.markdown('''
                    - [Register for an API key](https://www.dataportal.dol.gov/registration)
                    - [API User Guide](https://www.dataportal.dol.gov/pdf/dol-api-user-guide.pdf)
                    - [Video Tutorials](https://www.dataportal.dol.gov/video-tutorials)
                    - [API Examples](https://www.dataportal.dol.gov/api-examples)
                    '''
                    , unsafe_allow_html=True)

st.sidebar.markdown(':incoming_envelope: [**Contact us**](mailto:odg@dol.gov) for questions or assistance.', unsafe_allow_html=True)        
    

##############
# Main Panel # 
##############
st.header('Department of Labor API Explorer', divider='rainbow')

### API URL Structure ### 
col1, col2, col3, col4 = st.columns([.33, .10, .17, .40])

#--- server & method ---#
with col1:
    base_url = st.text_input('Server URL', value='https://apiprod.dol.gov/v4', disabled=True)

with col2:
    method = st.text_input('Method', value='get', disabled=True)

#--- agency & endpoint ---#
def get_datasets(agency=None, number_of_pages=100):
    collect = []
    for page in range(1, number_of_pages + 1):
        url = f"https://apiprod.dol.gov/v4/datasets?page={page}"
        response = requests.get(url)
        if response.status_code != 200:
            raise Exception(
                f"Request failed with status code {response.status_code}")
        datasets_api_json = response.json()['datasets']
        if not datasets_api_json:
            break
        datasets_api = pd.DataFrame(datasets_api_json)
        collect.append(datasets_api)
    datasets = pd.concat(collect)
    if agency is not None:
        mask = datasets['agency'].apply(lambda x: x['abbr'] == agency.upper())
        datasets = datasets[mask]
    return datasets

@st.cache_data
def create_agency_endpoint_table(agency=None):
    datasets = get_datasets(agency=agency)
    datasets = datasets[['agency', 'api_url']]
    datasets['api_url'] = datasets['api_url'].str.lower()
    agency_name = []
    agency_abbr = []
    for idx, row in datasets['agency'].items():
        l = row.keys()
        if 'name' in l:
            agency_name.append(row['name'].lower())
        if 'abbr' in l:
            agency_abbr.append(row['abbr'].lower())
        else:
            agency_name.append(None)
            agency_abbr.append(None)
    datasets['agency'] = agency_name
    datasets['agency_abbr'] = agency_abbr
    datasets = datasets[['agency', 'agency_abbr', 'api_url']]
    return datasets

datasets = create_agency_endpoint_table()

with col3:
    options_agency = datasets.agency_abbr.sort_values().unique().tolist()
    agency = st.selectbox('Agency', (options_agency), index=0)

with col4:
    if agency != '':
        datasets_filter = datasets.query(f"agency_abbr=='{agency}'")['api_url'].to_list()
        dataset = st.selectbox('Dataset', datasets_filter)

#--- format ---#
col5, col6 = st.columns([.25, .75])

with col5:
    options_format = ['json', 'xml', 'csv']
    formats = st.selectbox('Format', options_format, index=2)

#--- API key ---#
with col6:
    api_key = st.text_input('Demo API Key', value='cmYH7_DdqtL1We6LrKBZc3C54VG19gTOrNmWwWXiXxc', help='Register for an API key at https://www.dataportal.dol.gov/registration. If you are already registered, sign-in to the open data portal first and then get your key at https://www.dataportal.dol.gov/api-keys.')

basic_api = f'{base_url}/{method}/{agency}/{dataset}/{formats}?X-API-KEY={api_key}'
basic_meta_api = f'{base_url}/{method}/{agency}/{dataset}/{formats}/metadata?X-API-KEY={api_key}'

st.write('')

if api_key=='YOUR_API_KEY':
    st.markdown(
    """
    <style>
    .warning-box {
        background-color: #ffcccb;
        border: 1px solid #ff0000;
        padding: 10px;
        border-radius: 5px;
    }
    </style>
    """, 
    unsafe_allow_html=True
)
    st.markdown('<div class="warning-box">⚠️ <strong>Warning:</strong> You are missing your API key! Register for an API key to use the DOL API Explorer. </div>', unsafe_allow_html=True)
    st.write('')
    st.write('')

st.markdown(f'''            
            **Metadata:** :point_right:
            {basic_meta_api}
         ''')
         
st.markdown(f'''            
            **Data:** :point_right: 
            {basic_api}
         ''')

st.text('')

################################
# Customize your data request  #
################################         
st.markdown('''
            **Customize your data request:** 
            Select which fields and records you want. Choose how records are formatted and sorted.
         ''')

@st.cache_data
def get_metadata(agency, endpoint, format='csv', api_key=None):
    metadata_url = f"https://apiprod.dol.gov/v4/get/{agency}/{endpoint}/{format}/metadata?X-API-KEY={api_key}"
    if format not in ['csv', 'json']:
        raise ValueError("Invalid format specified. Use 'csv' or 'json'.")
    if api_key is None:
        raise ValueError("API key must be provided.")
    try:
        response = requests.get(metadata_url)
        response.raise_for_status()  # Raises HTTPError for bad responses (4xx or 5xx)
        if format == 'json':
            metadata_json = response.json()
            metadata = pd.DataFrame(metadata_json)
        elif format == 'csv':
            metadata = pd.read_csv(io.StringIO(
                response.content.decode('utf-8')))
    except requests.RequestException as e:
        raise Exception(f"Request failed: {e}")
    except ValueError as e:
        raise Exception(f"ValueError: {e}")
    except Exception as e:
        raise Exception(f"Error processing data: {e}")

    return metadata    

metadata = get_metadata(agency=agency, endpoint=dataset, api_key=api_key)     

### Fields ###
with st.expander('Reduce the number of fields returned.'):
    st.markdown(
       "<p style='font-family: Arial; font-size: 16px; color: #001F3F;'>"
        "Select the <b>fields</b> you want to include in your API request. "
        "By default, all fields are returned. You can choose specific fields "
        "to reduce the size of the response and improve performance."
        "</p>",
        unsafe_allow_html=True            
   )
    
    if agency == '' or dataset == '':
        pass

    else:
        endpoint = datasets.query(f'(agency_abbr == "{agency}") & (api_url == "{dataset}")')['api_url'].values[0]
        abbr = datasets.query(f'(agency_abbr == "{agency}") & (api_url == "{dataset}")')['agency_abbr'].values[0]

        ### Create field drop down ###
        field_options = metadata.sort_values(by=['variable_id'])['short_name'].to_list()
        fields = st.multiselect("Fields:", (field_options), key='multiselect_fields')

    show_url_fields = st.toggle(
        'Show request url with fields parameter', value=False)

    if show_url_fields:
        if fields == []:
            st.markdown(f'''
                        [{basic_api}]({basic_api})
                     ''')
        else:
            st.markdown(f'''
                        [{basic_api}&fields={','.join(fields)}]({basic_api}&fields={','.join(fields)})
                     ''')

            if fields == ''.join(metadata['short_name'].sort_values().to_list()):
                all_fields = "yes"

### Sort ###
with st.expander('Sort your records.'):
    st.markdown(
       "<p style='font-family: Arial; font-size: 16px; color: #001F3F;'>"
        "Apply a <b>sort</b> direction to the records of a dataset and / or <b>sort by</b> a specific field. By default records are sorted in ascending (asc) order."
        "</p>",
        unsafe_allow_html=True            
   )
    
    options_sort_order = ['', 'asc', 'desc']
    sort_order = st.selectbox('Sort:', options_sort_order, index=0)
    
    options_sort_by = [''] + metadata['short_name'].sort_values().to_list()
    sort_by = st.selectbox('Sort By:', (options_sort_by))
    
    show_url_sort = st.toggle('Show request url with sort / sort by parameters', value=False)

    if show_url_sort:
        if sort_order != '' and sort_by != '':
            st.markdown(f'''
                        [{basic_api}&sort={sort_order}&sort_by={sort_by}]({basic_api}&sort={sort_order}&sort_by={sort_by})
                     ''')
        elif sort_order != '' and sort_by == '':
            st.markdown(f'''
                        [{basic_api}&sort={sort_order}]({basic_api}&sort={sort_order})
                     ''')
        elif sort_order == '' and sort_by != '':
            st.markdown(f'''
                        [{basic_api}&sort_by={sort_by}]({basic_api}&sort_by={sort_by})
                     ''')
        elif sort_order == '' and sort_by == '':
            st.markdown(f'''
                        [{basic_api}]({basic_api})
                     ''')

### Filter Object ###
def create_filter_condition(filter_idx):
    col_a, col_b, col_c = st.columns([.35, .15, .50])
    
    with col_a:
        filter_by = st.selectbox(f'Filter by {filter_idx}', ([''] + metadata['short_name'].sort_values().to_list()))
    
    with col_b:
        operator = st.selectbox(f'Operator {filter_idx}', ('', 'eq', 'neq', 'gt', 'lt', 'in', 'not_in', 'like'))
    
    with col_c:
        if operator in ['in', 'not_in']:
            value_input = st.text_input(f'Values {filter_idx} (comma-separated)', value="value1,value2,value3")
            value = [v.strip() for v in value_input.split(',')] if value_input else []
        elif operator == 'like':
            value = st.text_input(f'Value {filter_idx} (use % for wildcards)', value='%value%')
        else:
            value = st.text_input(f'Value {filter_idx}')

    # Return a tuple including all relevant variables, with default values if not defined
    return filter_by, operator, value

with st.expander('Filter your records.'):
    st.markdown(
       "<p style='font-family: Arial; font-size: 16px; color: #001F3F;'>"
        "Create 1 or more <b>filter</b> conditions to subset the records of a dataset."
        "</p>",
        unsafe_allow_html=True            
   )

    conditions = []
    for i in range(1,4):  # Up to 5 conditions
        filter_by, operator, value = create_filter_condition(i)
        if filter_by:
            conditions.append({"field":filter_by,"operator":operator,"value":value})

    if conditions:        
        if len(conditions) > 1:            
            operator = st.radio("Select the operator for combining filter conditions:", ("and", "or"), index=0)
            filters = {f'{operator}': conditions} if len(conditions) > 1 else conditions
            filters_json = json.dumps(filters)        

        else:            
            filters_json = json.dumps(conditions[0])

        ### Write JSON Filter Object String ###            
        st.markdown(
        "<p style='font-family: Arial; font-size: 18px; color: #007BFF;'>"
        "<b>filter_object</b><br>"
        f"{filters_json}"
        "</p>",
        unsafe_allow_html=True            
        )            

        ### Encode Filter Object ###
        encoded_filter = urllib.parse.quote(filters_json)

        ### Explain URL Encoding ###                                               
        show_url_filter = st.toggle('Show request url with filter object parameter', value=False)

        if show_url_filter:        
            st.markdown(
               "<p style='font-family: Arial; font-size: 16px; color: #001F3F;'>"
               "<b>Encoding:</b> There are certain reserved characters that cannot be used in a URL so we have to encode (translate) the filter object as follows:"
                "</p>",
                unsafe_allow_html=True            
           )        
        
        
            encode_df = pd.DataFrame({'{': ['%7B'], '"': ['%22'], ',': ['%2C'], 'Space': ['%20'], ':': ['%3A'], '}': ['%7D'], '[': ['%5B'], ']': ['%5D']})
            encode_df.index = ['Replace with:']
            st.dataframe(encode_df)
        
            if 'encoded_filter' in locals():
                st.markdown(f'*Data:* :point_right: [{basic_api}&filter_object={encoded_filter}]({basic_api}&filter_object={encoded_filter})')
                
            else:
                st.markdown('''**>>> Please make filter selections to create a request URL.**''')
    
    else:
        st.write('No filter conditions created.')


with st.expander('Limit the number of records returned.'):
    st.markdown(
       "<p style='font-family: Arial; font-size: 16px; color: #001F3F;'>"
       "The maximum number of records to be returned by the API. The <b>limit</b> is 5MB of data, not exceeding 10000 records per request."
        "</p>",
        unsafe_allow_html=True            
   )
    
    limit = st.text_input('Limit:', value='10')
    show_url_limit = st.toggle('Show request url with limit parameter', value=False)

    if show_url_limit:
        st.markdown(f'''
                    [{basic_api}&limit={limit}]({basic_api}&limit={limit})
                 ''')

with st.expander('Skip a set number of records before retrieving data.'):
    st.markdown(
       "<p style='font-family: Arial; font-size: 16px; color: #001F3F;'>"
       "The <b>offset</b> parameter can be used in conjunction with the limit parameter when you are requesting more than the maximum record limit for a dataset. For example, if you need 20,000 records you would get the first chunk of 10,000 records by setting the limit to 10000 and offset to 0, and the second chunk of 10,000 records by setting the limit to 10000 and offset to 10000."
        "</p>",
        unsafe_allow_html=True            
   )
    
    offset = st.text_input('Offset:', value='0')
    show_url_offset = st.toggle('Show request url with offset parameter', value=False)

    if show_url_offset:
        st.markdown(f'''
                    [{basic_api}&offset={offset}&limit={limit}]({basic_api}&offset={offset}&limit={limit})
                 ''')

st.text('')
#--- Review ---#

if fields == []:
    fields_review = "Fields: all fields"
else:
    fields_review = f"Selected fields: {fields}".replace(
        "[", "").replace("]", "")

if sort_order != '' and sort_by != '':
    sort_review = f'Sorting: Sort order = {sort_order} and Sort by = {sort_by}'

elif sort_order != '' and sort_by == '':
    sort_review = f'Sorting: Sort order = {sort_order}'

elif sort_order == '' and sort_by != '':
    sort_review = f'Sorting: Sort by = {sort_by}'

elif sort_order == '' and sort_by == '':
    sort_review = 'Sorting: default'

if conditions == []:
    filter_review = 'Filters: records not subset'

else:
    filter_review = 'Filters: ' + filters_json 

agencyabbr_agency = dict(zip(datasets['agency_abbr'], datasets['agency']))
agency_name = agencyabbr_agency[f'{agency}']

st.markdown(f'''
            **Review your customization:**
            
                - Agency: {agency_name} 
                - Dataset: {dataset}               
                - {fields_review}
                - {sort_review}
                - {filter_review}
                - Limit: {limit} records per request
                - Offset: skip {offset} records before retrieving data.
         ''')

#--- Submit ---#
if conditions == []:
    encoded_filter = ''

parameters = {'limit': f'{limit}','offset':f'{offset}','fields': f'{",".join(fields)}','sort': f'{sort_order}',
              'sort_by': f'{sort_by}', 'filter_object': f'{encoded_filter}'}

customization = []
for k, v in parameters.items():
    if v == '':
        pass
    else:
        customization.append(f'&{k}={v}')

st.markdown('**Custom Data Download:**')
url = f'{basic_api}' + ''.join(customization).replace('"', '')
st.write(url)

st.text('')

#--- API Code Snippets ---#
st.markdown('**Code Snippets:**')

code_url = f'{basic_api}'.replace('csv?', 'json?') + ''.join(customization).replace('"', '')


def create_data_python_snippet(code_url=code_url):
    code = f'''
    # Import libraries
    import requests, pandas as pd
    
    # Get data
    url = "{code_url}"
    request = requests.get(url, verify=False)
    data_json = request.json()['data']
    data = pd.DataFrame(data_json)
    '''
    return st.code(code, language='python', line_numbers=True)


def create_data_r_snippet(code_url=code_url):
    code = f'''
    # Import libraries
    library(httr)
    library(jsonlite)
    
    # Get data
    url <- "{code_url}"
    request <- GET(url)
    data <- as.data.frame(fromJSON(content(request,"text")))
    '''
    return st.code(code, language='r', line_numbers=True)

tab1, tab2 = st.tabs(["python", "r"])

with tab1:
    data_python_snippet = create_data_python_snippet()

with tab2:
    data_r_snippet = create_data_r_snippet()
