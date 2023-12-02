#!/usr/bin/env python
# -*- coding: utf-8 -*-

__version__ = '2020.1.30'

import argparse  # process optional arguments
from tkinter import Tk
from tkinter.filedialog import askdirectory, asksaveasfilename
import csv
from splinter import Browser # http://splinter.readthedocs.io/en/latest/
import time  # used in sleep and timeout
from bs4 import BeautifulSoup  # used to parse html
import re
import geojson
from collections import OrderedDict


def main():
    """fuel.py is a tool to scrape the AIR Card website for FBO Locator
       (Contract Fuel) information, correlate to DAFIF, and output GeoJSON.
       US and CA will only be scraped when specified.
    """
    # INPUTS
    parser = argparse.ArgumentParser(
        description = 'Scrape the AIR Card website for FBO Locator (Contract Fuel) information, correlate to DAFIF, and output GeoJSON. US and CA will only be scraped when specified.',
        epilog = 'Lack of path arguments will invoke GUI elements.')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__)
    parser.add_argument('-d', metavar = 'DAFIFT', default = '',
                        help = 'full path to "DAFIFT" directory')
    parser.add_argument('-f', metavar = 'FILE', default = '',
                        help = 'full path to output file (*.geojson, *.json)')
    parser.add_argument('-c', metavar = 'COUNTRY', default = '',
                        help='filter for acceptable countries (e.g. "US CA")')
    parser.add_argument('-i0', metavar = '', default= 0, type=int,
                        help='regions list start index (int)')
    parser.add_argument('-i1', metavar = '', default= 0, type=int,
                        help='regions list end index (int)')
    args = parser.parse_args()
    d = args.d
    f_out = args.f
    country = args.c.upper()
    i0 = args.i0
    i1 = args.i1 + 1
    if len(d) < 1 or len(f_out) < 1:
        # Identify files
        # http://stackoverflow.com/a/3579625
        Tk().withdraw()  # we don't want a full GUI so hide the root window
        d = askdirectory(title='Select the folder "DAFIFT"')
        f_out = asksaveasfilename(title='Save As',
                                  filetypes=[('GeoJSON', '*.geojson'),('JSON', '*.json')],
                                  defaultextension='.geojson')
        try:
            country = input(
                'Specify a country filter (e.g. JA UK) '
                '[separated by a space]: '
                '\n>>> ').upper()
        except:
            country = ''
        try:
            i0 = int(input('Regions list start index (int): '))
        except:
            i0 = 0
        try:
            i1 = int(input('Regions list end index (int): ')) + 1
        except:
            i1 = 0
    if len(d) > 0 and len(f_out) > 0:
        # Parse ARPT.txt
        # arpt_ident = {}
        f_arpt = d + '\\ARPT\\ARPT.txt'
        arpt_name = {}
        arpt_dlat = {}
        arpt_dlon = {}
        arpt_ident2 = {}
        with open(f_arpt, 'r') as f:
            arpt_raw = csv.reader(f, delimiter='\t')
            # This skips the first row of the CSV file.
            next(arpt_raw)
            for row in arpt_raw:
                arpt_ident = (row[3] if len(row[3]) > len(row[4]) else row[4])
                arpt_name[arpt_ident] = row[1]
                arpt_dlat[arpt_ident] = row[8]
                arpt_dlon[arpt_ident] = row[10]
                arpt_ident2[row[19]] = arpt_ident # Alternate ICAO as key
        # Scrape
        regioncode = []
        icao = []
        iata = []
        name = []
        merchant = []
        fuel = []
        phone = []
        with Browser('firefox', headless=True) as browser:  # 'phantomjs'
            url = 'https://aircardsys.com/cgi-bin/usage_acceptance?AGREE=1'
            browser.visit(url)
            if browser.is_text_present('I AGREE', wait_time=1):
                #browser.find_by_text('I AGREE').click()
                browser.click_link_by_text('I AGREE')
            url = 'https://aircardsys.com/cgi-bin/fbo_locate'
            browser.visit(url)
            if browser.is_text_present('Select a Merchant'):
                while browser.is_element_not_present_by_id(
                    'MERCHANT_SUMMARY_HAS_ACTIVE_CONTRACT'):
                    #browser.find_by_id().visible
                    #element['name']
                    #wait = input('paused')
                    time.sleep(1)
                browser.find_by_text('DLA Contract Location').click()
                print('\nScraping')
                if len(country) != 0 and len(country) != 2:
                    country = ''
                optionid = 'MERCHANT_SUMMARY_COUNTRY'
                element = browser.find_by_id(optionid)
                if country == 'US' or country == 'CA':
                    element.select(country)
                    optionid = 'MERCHANT_SUMMARY_STATE'
                    element = browser.find_by_id(optionid)
                regions = []
                # http://sqa.stackexchange.com/a/11619
                for option in element.find_by_tag('option'):
                    if len(option['value']) != 2:
                        continue
                    regions.append(option['value'])
                    #regions.append(option['text'])
                if i0 < 0 or i0 > len(regions) - 1:
                    i0 = 0
                if i1 <= i0 or i1 > len(regions):
                    i1 = len(regions)
                if country and country != 'US' and country != 'CA':
                    #regions = [country]
                    i0 = regions.index(country)
                    i1 = i0 + 1
                for region in regions[i0:i1]:
                    if country == '':
                        if region == 'US' or region == 'CA':
                            continue
                    print(str(regions.index(region)), end='')
                    # http://stackoverflow.com/a/2083996
                    while True:
                        element = browser.find_by_id(optionid)
                        element.select(region)
                        browser.find_by_id('MERCHANT_SUMMARY_SEARCH_MAP_FOR_COUNTRY'
                                           '_STATE').click()
                        print('.', end='')
                        time.sleep(2)
                        try:
                            browser.get_alert().accept()
                            print(' ' + region + ' N/A')
                            break
                        except:
                            while browser.find_by_id('loading').first.visible:
                                time.sleep(1)
                            if browser.is_text_present('Merchant Name', \
                                                       wait_time=10):
                                print(' ' + region + ' ', end='')
                                table = browser.find_by_id(
                                'map_merchant_details')[0].html
                                soup = BeautifulSoup(table, 'html.parser')
                                r = 0
                                for subtable in soup.find_all('table', {'id' : re.compile('C_ROW')}):
                                    for row in subtable.find_all('tr', class_=True):
                                        col = row.find_all('td')
                                        regioncode.append(region)
                                        icao.append(col[1].text.strip())
                                        iata.append(col[2].text.strip())
                                        name.append(col[5].text.strip())
                                        merchant.append(col[0].text.strip())
                                        fuel.append(col[10].text.strip())
                                        phone.append(col[11].text.strip())
                                    r = r + 1
                                print('(' + str(r) + ')', end='')
                                print('')
                                break
                            else:
                                continue
        fc = []
        print('\n')
        if not name:
            print('No locations to correlate')
        else:
            print('Correlating')
            for n in range(0, len(name)):
                d = OrderedDict()
                query = icao[n]
                while True:
                    d['IDENT'] = query
                    d['NAME'] = name[n]
                    d['MERCHANT'] = merchant[n]
                    d['FUEL'] = fuel[n]
                    d['PHONE'] = phone[n]
                    try:
                        print(query + ' (' + regioncode[n] + '): ' +
                              arpt_dlat[query] + ', ' + arpt_dlon[query])
                        # (Lon, Lat) because https://github.com/frewsxcv/python-geojson#point)
                        p = geojson.Point((float(arpt_dlon[query]), \
                                           float(arpt_dlat[query])))
                        fc.append(geojson.Feature(geometry=p, properties=d))
                    except:
                        try:
                            query = arpt_ident2[query]
                        except:
                            try:
                                query = icao[n][1:]
                                test = arpt_name[query] # chucks error if not found
                            except:
                                query = input(icao[n] + ' (' + regioncode[n] + \
                                              ') (' + name[n] + ') not in DAFIF. ' 
                                              'Alternate ICAO? ')
                    else:
                        break
            with open(f_out, 'w', newline='', encoding='utf-8') as f:
                f.write(geojson.dumps(geojson.FeatureCollection(fc)))


if __name__ =="__main__":
    main()
