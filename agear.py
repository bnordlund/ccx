#!/usr/bin/env python
# -*- coding: utf-8 -*-

__version__ = '2020.1.30'

import argparse  # process optional arguments
import csv
from tkinter import Tk
from tkinter.filedialog import askdirectory, asksaveasfilename
import math
import geojson
from collections import OrderedDict


def main():
    """ agear.py parses the NGA's DAFIF for Arresting Gear information.
        Downloads at https://dbgia.geointel.nga.mil/
        Map at www.robertnordlund.com/ccx/
    """
    # INPUTS
    parser = argparse.ArgumentParser(
        description = 'Parses the NGA\'s DAFIF for Arresting Gear information.',
        epilog = 'Lack of path arguments will invoke GUI elements.')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__)
    parser.add_argument('-d', metavar = 'DAFIFT', default = '',
                        help = 'full path to "DAFIFT" directory')
    parser.add_argument('-f', metavar = 'FILE', default = '',
                        help = 'full path to output file (*.geojson, *.json)')
    parser.add_argument('-c', metavar = 'COUNTRY', default = '',
                        help='filter for acceptable countries (e.g. "US CA")')
    parser.add_argument('-t', metavar = 'TYPE', default= '',
                        help='filter for acceptable system type (e.g. "MA-1 BAK-15")')
    args = parser.parse_args()
    d = args.d
    f_out = args.f
    country_filter = args.c
    type_filter = args.t
    if len(d) < 1 or len(f_out) < 1:
        # Identify files
        # http://stackoverflow.com/a/3579625
        Tk().withdraw()  # we don't want a full GUI so hide the root window
        # show an "Open" dialog box and return the path to the selected file
        # f_agear = askopenfilename(title='Select AGEAR.txt',
        #                           filetypes=[('Text Documents','*.txt')])
        # f_arpt = askopenfilename(title='Select ARPT.txt',
        #                          filetypes=[('Text Documents','*.txt')])
        d = askdirectory(title='Select the folder "DAFIFT"')
        if len(d) > 0:
            f_out = asksaveasfilename(title='Save As',
                                      filetypes=[('GeoJSON', '*.geojson'),('JSON', '*.json')],
                                      defaultextension='.geojson')
                                    # ('CSV (Comma delimited)', '*.csv')
            if len(f_out) > 0:
                try:
                    country_filter = input(
                        'Filter for acceptable countries (e.g. US CA) '
                        '[separated by a space]: '
                        '\n>>> ')
                except:
                    country_filter = ''
                try:
                    type_filter = input(
                        'Filter for acceptable system type (e.g. MA-1 BAK-15) '
                        '[separated by a space]: '
                        '\n>>> ')
                except:
                    type_filter = ''
    if len(d) > 0 and len(f_out) > 0:
        f_agear = d + '\\ARPT\\AGEAR.txt'
        f_arpt = d + '\\ARPT\\ARPT.txt'
        f_appc_ab = d + '\\APPC\\APPC_ABSORBING_SYS.txt'
        f_appc_en = d + '\\APPC\\APPC_ENGAGING_DEV.txt'
        # Parse APPC_ABSORBING_SYS.txt
        ab_type = {}
        with open(f_appc_ab, 'r') as f:
            for row in csv.reader(f, delimiter='\t'):
                ab_type[row[0]] = row[1]
        # Parse APPC_ENGAGING_DEV.txt
        en_type = {}
        with open(f_appc_en, 'r') as f:
            for row in csv.reader(f, delimiter='\t'):
                en_type[row[0]] = row[1]
        # Parse ARPT.txt
        arpt = {}
        with open(f_arpt, 'r') as csvfile:
            reader = csv.DictReader(csvfile, delimiter='\t')
            # https://www.idiotinside.com/2015/09/18/csv-json-pretty-print-python/
            title = reader.fieldnames
            for row in reader:
                row_dict = ({title[i]:row[title[i]] for i in range(len(title))})
                arpt[row_dict['ARPT_IDENT']] = {}
                arpt[row_dict['ARPT_IDENT']]['NAME'] = row_dict['NAME']
                arpt[row_dict['ARPT_IDENT']]['ICAO'] = row_dict['ICAO'] if len(row_dict['ICAO']) > len(row_dict['FAA_HOST_ID']) else row_dict['FAA_HOST_ID']
                arpt[row_dict['ARPT_IDENT']]['WGS_DLAT'] = row_dict['WGS_DLAT']
                arpt[row_dict['ARPT_IDENT']]['WGS_DLONG'] = row_dict['WGS_DLONG']
        # Parse AGEAR.txt
        agear = []
        with open(f_agear, 'r') as csvfile:
            reader = csv.DictReader(csvfile, delimiter='\t')
            # https://www.idiotinside.com/2015/09/18/csv-json-pretty-print-python/
            title = reader.fieldnames
            for i, row in enumerate(reader):
                row_dict = ({title[i]:row[title[i]] for i in range(len(title))})
                agear.append({})
                agear[i]['ARPT_IDENT'] = row_dict['ARPT_IDENT']
                agear[i]['RWY_IDENT'] = row_dict['RWY_IDENT']
                agear[i]['LOCATION'] = str(int(row_dict['LOCATION']))
                agear[i]['TYPE'] = row_dict['TYPE']
        # Filter airports
        for i in range(len(agear)-1,-1,-1):
            if country_filter != '':
                if agear[i]['ARPT_IDENT'][0:2] not in country_filter.upper():
                    del agear[i]
                    continue
            if type_filter != '':
                # https://stackoverflow.com/a/25102099
                if len([s for s in [ab_type[agear[i]['TYPE'][:-2]],en_type[agear[i]['TYPE'][-2:]]] if any(xs in s for xs in type_filter.upper().split())]) == 0:
                    del agear[i]
                    continue
        # Build GeoJSON
        ARPT_IDENT = ''
        rwy = {}
        r = 0
        fc = []
        #print(agear)
        #agear.update({len(agear) + 1: {'ARPT_IDENT': ''}})
        agear.append(agear[0])
        #print(agear)
        for i in range(0,len(agear)):
            if (agear[i]['ARPT_IDENT'] != ARPT_IDENT and len(rwy) > 0) or i == len(agear)-1:
                d = OrderedDict()
                d['IDENT'] = arpt[agear[i-1]['ARPT_IDENT']]['ICAO']
                d['NAME'] = arpt[agear[i-1]['ARPT_IDENT']]['NAME']
                # The RWY separator character is called an "interpunct"·
                d['RWY'] = ' · '.join('<span class=\'details\' title=\'' +
                                      str(value[0]) + '\'>' + str(key)  +
                                      '</span>' for key, value in rwy.items())
                # (Lon, Lat) because https://github.com/frewsxcv/python-geojson#point)
                p = geojson.Point((float(arpt[agear[i-1]['ARPT_IDENT']]['WGS_DLONG']),
                                   float(arpt[agear[i-1]['ARPT_IDENT']]['WGS_DLAT'])))
                fc.append(geojson.Feature(geometry=p, properties=d))
                ARPT_IDENT = agear[i]['ARPT_IDENT']
                rwy = {}
                r = 0
            if rwy == {}:
                rwy[agear[i]['RWY_IDENT']] = [agear[i]['LOCATION'] + '&#8242 (' +
                                              ab_type[agear[i]['TYPE'][:-2]] + '/' + 
                                              en_type[agear[i]['TYPE'][-2:]] + ')']
                ARPT_IDENT = agear[i]['ARPT_IDENT']
                continue
            if agear[i]['RWY_IDENT'] != agear[i-1]['RWY_IDENT']:
                rwy[agear[i]['RWY_IDENT']] = [agear[i]['LOCATION'] + '&#8242 (' +
                                              ab_type[agear[i]['TYPE'][:-2]] + '/' + 
                                              en_type[agear[i]['TYPE'][-2:]] + ')']
            else:
                rwy[agear[i]['RWY_IDENT']] = [rwy[agear[i]['RWY_IDENT']][0] + '&#10;' +
                          agear[i]['LOCATION'] + '&#8242 (' +
                          ab_type[agear[i]['TYPE'][:-2]] + '/' + 
                          en_type[agear[i]['TYPE'][-2:]] + ')']
        with open(f_out, 'w', newline='', encoding='utf-8') as f:
            f.write(geojson.dumps(geojson.FeatureCollection(fc)))


if __name__ == "__main__":
    main()
