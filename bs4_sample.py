from bs4 import BeautifulSoup as bs
from selenium import webdriver
import urllib.request, urllib.error, urllib.parse
import re
import ssl
import pandas as pd
import numpy as np

class SoupMaker():
    """
    A class that scrapes indeed's Job ads
    """
    def __init__(self, _url, _driver):
        self.base_url = "https://www.indeed.com.ph"
        self.home_url = self.base_url + _url
        self.job_links = []
        self.driver = _driver
        self.job_datas = []
        self.job_table = []
        
    def read_page(self):        
        self.ctx = ssl.create_default_context()
        self.ctx.check_hostname = False
        self.ctx.verify_mode = ssl.CERT_NONE
        print("Parsing: ", self.home_url)
        self.url = urllib.request.urlopen(self.home_url,
                              context = self.ctx).read()
        _soup1 = bs(self.url, "html.parser")
        self.a_tags = _soup1('a')
        
    def get_job_url(self):
        for link in self.a_tags:
            link = link.get("href", None)
            if link != None:
                cmp_url = re.search("^/.+/.+/jobs/.+", link)
                rc_url = re.search("^/rc.+", link)
                if cmp_url or rc_url:
                    self.job_links.append(self.base_url + link.strip())
                    
    def get_job_info(self):
        for link in self.job_links:
            print("    Scraping: ", link)
            self.driver.get(link)
            self.driver.implicitly_wait(2750)
            _soup2 = bs(self.driver.page_source, "lxml")
            self.title = _soup2.find("title").get_text()
            self.job_descs = _soup2.find_all('div', 'jobsearch-JobComponent-description icl-u-xs-mt--md')
            self.job_origins = _soup2.find_all('div', 'jobsearch-JobMetadataFooter')
            
            self.job_title = re.findall("(.+) - .+ - .+", self.title)[0]
            self.job_location = re.findall(".+ - (.+) - .+", self.title)[0]
            self.description = ''
            for d in self.job_descs:
                self.description += d.get_text("|", strip = True) 
            self.origin = re.findall("^.+ ago", self.job_origins[0].get_text())[0]    
            self.job_datas.append(self.job_title)
            self.job_datas.append(self.job_location)
            self.job_datas.append(self.description)
            self.job_datas.append(self.origin)
            
        self.x = np.array(self.job_datas).reshape((10,4))
        df = pd.DataFrame(data=self.x, columns=['Job Title', 'Job Location',
                                    'Job Description', 'Job Origin'])
        return df
        
if __name__ == '__main__':
    n = int(input("Enter no. of pages to scrape: "))
    n = n*10
    file_name = input("Enter CSV filename: ")
    
    driver = webdriver.Chrome(r"C:\chromedriver\chromedriver.exe")
    writer = pd.ExcelWriter('{0}.xlsx'.format(file_name), engine='xlsxwriter')
    df = []
    
    for i in range(10, n+10, 10):
        ext = "/jobs?q=&l=Philippines&start={0}".format(i-10)
        if n == 10:
            ext = "/jobs-in-Philippines"
        s = SoupMaker(ext, driver)
        s.read_page()
        s.get_job_url()
        df.append(s.get_job_info())
        
    result = pd.concat(df)
    result.to_excel(writer, index=False)
    writer.save()
    driver.close()
