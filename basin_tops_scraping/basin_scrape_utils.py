import os
import requests
from bs4 import BeautifulSoup
import pandas as pd


def get_topsdf_from_basin(url, seq_num, author=None):
    s = requests.session()
    s.get(url + seq_num)
    r2 = s.get('http://basin.gdr.nrcan.gc.ca/excel_e.php?t=1&export=txt')
    tops_text = r2.text.split('\n')
    # hack to deal with commas in author field
    headers = tops_text[3].strip().split(', ')
    rows = tops_text[4:]
    listlike = [row.strip().replace(', U', ',U').split(', ') for row in rows if row.strip()]
    
    try:
        tops_df = pd.DataFrame(listlike, columns=headers)

    except AssertionError:
        print('7 columns passed, data had 8 columns')
        print(headers)
        for row in listlike:
            print(row)
        tops_df = pd.DataFrame(listlike, columns=headers.append('unknown'))
    
    if author:
        tops_df = tops_df[tops_df['Author'] == author]   
    
    return tops_df

    
    


def get_well_header_table(url, seq_num):
    well_url = url + seq_num
    out = requests.get(well_url)
    soup = BeautifulSoup(out.text, features='lxml')
    tables = soup.find_all('table')
    return tables[1]


def get_well_header_row(table, heading):
    column_one =  table.find('td', text=heading)
    return column_one.nextSibling.nextSibling.text.replace(u'\xa0', u' ').strip()


def get_well_full_name(well_info_table):
    return well_info_table.find('th').text.replace(u'\xa0', u' ')


def well_header_dict(well_info_table, meta_params, meta_field_descrip):
    well_header_dict = {}
    well_header_dict['Full Name'] = get_well_full_name(well_info_table)
    for param in meta_params:
        
        well_header_dict[meta_field_descrip[param]] = get_well_header_row(well_info_table, param).strip()
    return well_header_dict


def make_well_seq_lookup(data_dir, wells_wanted):

    with open(os.path.join(data_dir, wells_wanted), 'r') as f:
        wells = f.readlines()

    well_sequence_numbers = {}
    for well in wells:
        num, name = well.split(',')
        well_sequence_numbers[num.replace('"','')] = name.strip().replace('"','')
    return well_sequence_numbers


def make_locations_dict(fname, wellname=None):
    """
    Takes a filename of a well locations file and 
    returns a dictionary whose key is the well name, and
    location is the value
    """
    with open(fname, 'r') as f:
        keys = f.readline()
        lines = f.readlines()
        wells = {}
        keys = keys.strip().split(', ')
        for line in lines:
            d = line.split(',')
            try:
                wells[d[0]] = {
                               keys[1]: d[1].strip(),
                               keys[2]: d[2].strip(),
                               keys[3]: float(d[3].strip()),  # Lat (NAD27)
                               keys[4]: float(d[4].strip()),  # Long (NAD27)
                               keys[5]: float(d[5].strip()),  # Northing (NAD27)
                               keys[6]: float(d[6].strip()),  # Easting (NAD27)
                               keys[7]: float(d[7].strip()),  # Lat (NAD83)
                               keys[8]: float(d[8].strip()),  # Long (NAD83)
                               keys[9]: float(d[9].strip()),  # Northing (NAD 83)
                               keys[10]: float(d[10].strip()),   # Easting (NAD 83)
                               keys[11]: int(d[11].strip()),  # Zone (UTM)
                              }
            except:
                pass
    
    if wellname:
        wells[wellname]['Common Name'] = wellname
        return wells[wellname]
    else:
        return wells


def make_header_text(header_dict):
    text = ''
    for k, v in header_dict.items():
        text += f'# {k} : {v} \n'
    return text


def load_meta_params():
    params = ['RT:', 'WD:', 'Unique Well ID:', 'GSC#:', 'Spud Date:', 'TD:']
    return params


def load_meta_field_descriptions():
    meta_field_descrip = {'RT:': 'Rotary Table', 
                      'WD:': 'Water Depth', 
                      'Unique Well ID:': 'UWI',
                      'GSC#:': 'Regulator Sequence Number', 
                      'Spud Date:': 'Spud Date', 
                      'TD:': 'Total Depth'
                     }
    return meta_field_descrip


def text_header(delim='#', *args):
    text = ''
    for t in args:
        text += t
    return text


def convert(list, delim=', '): 
    # Converting list to string list 
    s = [str(i) for i in list] 
    # Join list items using join() 
    res = str(delim.join(s)) 
    return res


def format_column_names(columns, head_flag='# '):
    return head_flag + str(list(columns)).replace('[','').replace(']','').replace("'",'')


def write_tops_file(fname, text_head, body_df, ):
    with open(fname, 'w') as f:
        f.write(text_head)
        f.write(format_column_names(body_df.columns) + '\n')
        for row in body_df.values:
            f.write(convert(row) + '\n')
    return


