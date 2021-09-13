from django.shortcuts import render,get_object_or_404
from django.http import HttpResponse,HttpResponseRedirect,Http404,JsonResponse
from django.template import loader
from django.utils import timezone
from django.http import HttpResponse,HttpResponseRedirect,Http404,JsonResponse
from django.urls import reverse
from django.views import generic
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from uuid import uuid4
from urllib.parse import urlparse
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from django.views.decorators.http import require_POST, require_http_methods
from django.views.decorators.csrf import csrf_exempt
from scrapyd_api import ScrapydAPI
from scrapy import signals
from scrapy.crawler import Crawler, CrawlerProcess,CrawlerRunner
# from web_scraper.web_scraper.spiders.paytm_crawler import PaytmCrawlerSpider
from twisted.internet import reactor
from web_interface.models import ScrapyItem
import scrapy,time
import logging
from django.contrib.auth.models import User
from autoscraper import AutoScraper
# Create your views here.

scrapyd = ScrapydAPI('http://localhost:8000')

def searchdata(request):
    url = 'https://stackoverflow.com/questions/2081586/web-scraping-with-python'
    # We can add one or multiple candidates here.
    # You can also put urls here to retrieve urls.
    wanted_list = [""]

    scraper = AutoScraper()
    result = scraper.build(url, wanted_list)
    if 'q' in request.GET:
        querystring = request.GET.get('q').strip()

        print(querystring)
        
        if len(querystring) == 0:
            return redirect('/search/')

        results= []
        url = request.GET.get('q', None)
        #page = request.GET.get('page')
        unique_id = str(uuid4())
        settings = {
            'unique_id': unique_id
        }
        #if url!=None and page==None:
        task = scrapyd.schedule('default','paytm_crawler',
                                settings=settings, search_data=querystring)
        task1 = scrapyd.schedule('default','snapdeal_crawler',
                                 settings=settings, search_data=querystring)
        time.sleep(20)
        status = scrapyd.job_status('default', task)
        status1 = scrapyd.job_status('default', task1)
        obj=ScrapyItem.objects.get(unique_id=unique_id)
        for i in obj.paytm_data.values():
            results.append(i)
        for i in obj.snapdeal_data.values():
            results.append(i)
        print(results[0])
        # paginator = Paginator(results, 5)
        # products = paginator.get_page(page)
        return render (request, 'web_interface/results.html', {
            'querystring': querystring,
            'results': results,
        })

    else:
        return render(request, 'web_interface/search.html', {})

def viewdata(request):
    import requests
    from bs4 import BeautifulSoup
    import pandas as pd
    if request.method =='GET':
        url = 'https://etherscan.io/txs?p=2'
        requests.get(url)
        # page = requests.get(url)
        # soup = BeautifulSoup(page.text, 'lxml')
        # table_data = soup.find('table', class_ = 'table table-hover')

        scraper = AutoScraper()
        soup = scraper._get_soup(url)
        table_data = soup.find('table', class_ = 'table table-hover')
        headers = []
        for i in table_data.find_all('th'):
            title = i.text
            headers.append(title)
        print(headers)
        # df = pd.DataFrame(columns = headers)


        for j in table_data.find_all('tr')[1:]:
            row_data = j.find_all('td')
            row = [tr.text for tr in row_data]
            length = len(df)
            df.loc[length] = row

        return render(request,'web_interface/results.html',{'results' : table_data})

