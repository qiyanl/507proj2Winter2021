#################################
##### Name: QIYAN LIU
##### Uniqname: qiyanl
#################################

from bs4 import BeautifulSoup
import requests
import json
import secrets # file that contains your API key

CACHE_FILENAME = "NationalSite.json"
SITE_DICT = {}
base_url = 'https://www.nps.gov'

# Part 0: Caching
def open_cache():
    ''' Opens the cache file if it exists and loads the JSON into
    the CACHE_DICT dictionary.
    if the cache file doesn't exist, creates a new cache dictionary
    
    Parameters
    ----------
    None
    
    Returns
    -------
    The opened cache: dict
    '''
    try:
        cache_file = open(CACHE_FILENAME, 'r')
        cache_contents = cache_file.read()
        cache_dict = json.loads(cache_contents)
        cache_file.close()
    except:
        cache_dict = {}
    return cache_dict

SITE_CACHE = open_cache()

def save_cache(cache_dict):
    ''' Saves the current state of the cache to disk
    
    Parameters
    ----------
    cache_dict: dict
        The dictionary to save
    
    Returns
    -------
    None
    '''
    dumped_json_cache = json.dumps(cache_dict)
    fw = open(CACHE_FILENAME,"w")
    fw.write(dumped_json_cache)
    fw.close() 

def make_request_with_cache(baseurl,cache):
    '''Check the cache for a saved result for this baseurl. 
    If the result is found, return it. Otherwise send a new 
    request, save it, then return it.
    Parameters
    ----------
    baseurl: string
        The URL for the API endpoint
    cache: dict
        The cache that make request with
    
    Returns
    -------
    dict
        the results of the query as a dictionary loaded from cache
        JSON
    '''
    if baseurl in cache.keys():
        print("Using cache")
        return cache[baseurl]
    else:
        print("Fetching")
        cache[baseurl] = requests.get(baseurl).text
        save_cache(cache)
        return cache[baseurl]
        
class NationalSite:
    '''a national site

    Instance Attributes
    -------------------
    category: string
        the category of a national site (e.g. 'National Park', '')
        some sites have blank category.
    
    name: string
        the name of a national site (e.g. 'Isle Royale')

    address: string
        the city and state of a national site (e.g. 'Houghton, MI')

    zipcode: string
        the zip-code of a national site (e.g. '49931', '82190-0168')

    phone: string
        the phone of a national site (e.g. '(616) 319-7906', '307-344-7381')
    '''
    def __init__(self,category,name,address,zipcode,phone):
        self.category = category
        self.name = name
        self.address = address
        self.zipcode = zipcode
        self.phone = phone
    
    def info(self):
        return f"{self.name} ({self.category}): {self.address} {self.zipcode}"



def build_state_url_dict():
    ''' Make a dictionary that maps state name to state page url from "https://www.nps.gov"

    Parameters
    ----------
    None

    Returns
    -------
    dict
        key is a state name and value is the url
        e.g. {'michigan':'https://www.nps.gov/state/mi/index.htm', ...}
    '''
    
    url = 'https://www.nps.gov/index.htm'
    page = make_request_with_cache(url,SITE_CACHE)
    soup = BeautifulSoup(page, 'html.parser')
    a = soup.find(class_="dropdown-menu SearchBar-keywordSearch")
    raw_data = a.find_all('a')
    state_dict = {}
    for state in raw_data:
        temp = state.string.lower()
        state_dict[temp] = 'https://www.nps.gov' + state['href']
            
    save_cache(SITE_CACHE)
    return state_dict   

def get_site_instance(site_url):
    '''Make an instances from a national site URL.
    
    Parameters
    ----------
    site_url: string
        The URL for a national site page in nps.gov
    
    Returns
    -------
    instance
        a national site instance
    '''
    
    url = site_url
    page = make_request_with_cache(url,SITE_CACHE)
    soup = BeautifulSoup(page, 'html.parser')
    a = soup.find(class_="ParkFooter-contact")

    
    code_raw = a.find(class_="postal-code")
    if code_raw != None:
        code = code_raw.text
        code = code.strip()
    else:
        code = ''
    address_1 = a.find(itemprop="addressLocality")
    address_2 = a.find(itemprop="addressRegion")
    if address_1 != None:
        addr_1 = address_1.text.strip()
    else:
        addr_1 = ''
    if address_2 != None:
        addr_2 = address_2.text.strip()
    else:
        addr_2 = ''
    address = addr_1 + ', '+ addr_2
    phone_raw = a.find( class_="tel")
    if phone_raw != None:
        phone = phone_raw.text.strip()
        
    else:
        phone = ''

    b = soup.find(id='HeroBanner')
    name_raw = b.find(class_="Hero-title")
    if name_raw != None:
        name = name_raw.text.strip()
    else:
        name =''
    type_raw = b.find(class_="Hero-designation")
    if type_raw != None:
        park_type = type_raw.text.strip()
    else:
        park_type =''
    instance = NationalSite(category=park_type,name=name,address=address,zipcode=code,phone=phone)
    
    save_cache(SITE_CACHE)

    return instance



def get_sites_for_state(state_url):
    '''Make a list of national site instances from a state URL.
    
    Parameters



    ----------
    state_url: string
        The URL for a state page in nps.gov
    
    Returns
    -------
    list
        a list of national site instances
    '''
    
    state_uri = state_url
    page = make_request_with_cache(state_uri,SITE_CACHE)
    soup = BeautifulSoup(page, 'html.parser')
    a = soup.find(id='list_parks')
    raw_data = a.find_all(class_='clearfix')
    
    park_list = []
    for i in range(len(raw_data)):
        temp =raw_data[i].find('a')
        park_url = 'https://www.nps.gov' + temp['href'] + 'index.htm'
        park_instance = get_site_instance(park_url)
        park_list.append(park_instance)
            
    
    save_cache(SITE_CACHE)
    return park_list


def get_nearby_places(site_object):
    '''Obtain API data from MapQuest API.
    
    Parameters
    ----------
    site_object: object
        an instance of a national site
    
    Returns
    -------
    dict
        a converted API return from MapQuest API
    '''
    code = site_object.zipcode
    if not code:
        return {}
    else:
        url = 'http://www.mapquestapi.com/search/v2/radius?key='+secrets.API_KEY+'&origin='+code+\
        '&radius=10&maxMatches=10&ambiguities=ignore&outFormat=json'
        page = make_request_with_cache(url,SITE_CACHE)
        api_dict = json.loads(page)
        
        for site in api_dict["searchResults"]:
            fields = site['fields']
            site_name = site['name']
            site_type = fields['group_sic_code_name']
            site_addr = fields['address']
            site_city = fields['city']
            if not site_addr:
                site_addr = 'no address'
            if not site_type:
                site_type = 'no category'
            if not site_city:
                site_city = 'no city'
            print(f"- {site_name} ({site_type}): {site_addr}, {site_city}")
        
        save_cache(SITE_CACHE)
        return api_dict


if __name__ == "__main__":
    
    SITE_CACHE = open_cache()
    states_dict = build_state_url_dict()
    state_name_enter = True
    while True:
        if state_name_enter:
            state_name = input("Please input a state name or exit: ").lower()
            if state_name == 'exit':
                break
            elif state_name in states_dict.keys():
                state_uri = states_dict[state_name]
                parklist = get_sites_for_state(state_uri)
                headers_1 = 'List of national sites in '+ state_name
                print('-'*len(headers_1))
                print(headers_1)
                print('-'*len(headers_1))
                for i in range(len(parklist)):
                    print(f"[{i+1}] {parklist[i].info()}")
            else:
                print("[ERROR] Please enter a proper state name.")
                continue
            
        state_name_enter = False
        number_enter = input("Choose a number for detail search or exit or back: ")
        if number_enter == 'exit':
            break
        elif number_enter == 'back':
            state_name_enter = True
        else:
            num = int(number_enter)
            if num > len(parklist):
                print("[ERROR] Please enter a valid number.")
                continue
            else:
                temp = parklist[num-1]
                headers_2 = 'Places near '+ temp.name
                print('-'*len(headers_2))
                print(headers_2)
                print('-'*len(headers_2))
                get_nearby_places(temp)

    

    
    

    

    
    
    
    
    

    
    
