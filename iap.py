#!/usr/bin/env python
# -*- coding: utf-8 -*-

__version__ = '2020.1.30'

import argparse  # process optional arguments
import csv
from tkinter import Tk
from tkinter.filedialog import askdirectory, asksaveasfilename
import re
import math
import geojson
from collections import OrderedDict


def main():
    """ iap.py parses the NGA's DAFIF for IAP minima.
        Downloads at https://dbgia.geointel.nga.mil/
        Map at www.robertnordlund.com/ccx/
    """
    # INPUTS
    parser = argparse.ArgumentParser(
        description = 'Parses the NGA\'s DAFIF for IAP minima.',
        epilog = 'Lack of path arguments will invoke GUI elements.')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__)
    parser.add_argument('-d', metavar = 'DAFIFT', default = '',
                        help = 'full path to "DAFIFT" directory')
    parser.add_argument('-f', metavar = 'FILE', default = '',
                        help = 'full path to output file (*.geojson, *.json)')
    parser.add_argument('-l', metavar = 'LENGTH', default= 0, type=int,
                        help='minimum runway length (ft) (int)')
    parser.add_argument('-w', metavar = 'WIDTH', default= 0, type=int,
                        help='minimum runway width (ft) (int)')
    parser.add_argument('-t', metavar = 'TYPE', default= '',
                        help='filter for IAP type (e.g. \'T\' for TACAN) [just the letter]')
    args = parser.parse_args()
    d = args.d
    f_out = args.f
    filter_rwy_len = args.l
    filter_rwy_wid = args.w
    filter_trm_type = args.t
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
                # Filter RWY
                try:
                    filter_rwy_len = input(
                        'Specify minimum runway length (ft): '
                        '\n>>> ')
                    filter_rwy_len = int(filter_rwy_len)
                except:
                    filter_rwy_len = 0
                try:
                    filter_rwy_wid = input(
                        'Specify minimum runway width (ft): '
                        '\n>>> ')
                    filter_rwy_wid = int(filter_rwy_wid)
                except:
                    filter_rwy_wid = 0
                # Filter type
                try:
                    filter_trm_type = input(
                        'Specify an IAP filter (e.g. \'T\' for TACAN) [just the letter]: '
                        '\n>>> ')
                except:
                    filter_trm_type = ''
    if len(d) > 0 and len(f_out) > 0:
        # Parse ARPT.txt
        f_rwy = d + '\\ARPT\\RWY.txt'
        f_trm = d + '\\TRM\\TRM_MIN.txt'
        f_arpt = d + '\\ARPT\\ARPT.txt'
        arpt_ident = {}
        arpt_name = {}
        arpt_dlat = {}
        arpt_dlon = {}
        with open(f_arpt, 'r') as f:
            arpt_raw = csv.reader(f, delimiter='\t')
            # This skips the first row of the CSV file.
            next(arpt_raw)
            for row in arpt_raw:
                arpt_ident[row[0]] = (row[3] if len(row[3]) > len(row[4])
                                      else row[4])
                arpt_name[row[0]] = row[1]
                arpt_dlat[row[0]] = row[8]
                arpt_dlon[row[0]] = row[10]
        # Parse RWY.txt
        rwy_arpt_raw = []
        rwy_rwy_raw = []
        rwy_len_raw = []
        rwy_wid_raw = []
        with open(f_rwy, 'r') as f:
            rwy_raw = csv.reader(f, delimiter='\t')
            next(rwy_raw)
            for row in rwy_raw:
                rwy_arpt_raw.append(row[0])
                rwy_rwy_raw.append(row[1])
                rwy_len_raw.append(int(row[5]))
                rwy_wid_raw.append(int(row[6]))
                rwy_arpt_raw.append(row[0])
                rwy_rwy_raw.append(row[2])
                rwy_len_raw.append(int(row[5]))
                rwy_wid_raw.append(int(row[6]))
        rwy_arpt_filter = []
        rwy_rwy_filter = []
        rwy_len_filter = []
        rwy_wid_filter = []
        for i, a in enumerate(rwy_arpt_raw):
            if (rwy_len_raw[i] >= filter_rwy_len
                and rwy_wid_raw[i] >= filter_rwy_wid):
                rwy_arpt_filter.append(a)
                rwy_rwy_filter.append(rwy_rwy_raw[i])
                rwy_len_filter.append(rwy_len_raw[i])
                rwy_wid_filter.append(rwy_wid_raw[i])
        rwy_arpt_raw = rwy_arpt_filter
        rwy_rwy_raw = rwy_rwy_filter
        rwy_len_raw = rwy_len_filter
        rwy_wid_raw = rwy_wid_filter
        # Parse TRM_MIN.txt
        circling = '&copy;'
        trm_arpt_raw = []
        trm_ident_raw = []
        trm_catcdh_raw = []
        trm_catcha_raw = []
        trm_catcwc_raw = []
        trm_catcwv_raw = []
        with open(f_trm, 'r') as f:
            trm_raw = csv.reader(f, delimiter='\t')
            next(trm_raw)
            for row in trm_raw:
                trm_arpt_raw.append(row[0])
                trm_ident_raw.append(row[2])
                trm_catcdh_raw.append(row[15])
                trm_catcha_raw.append(row[17])
                trm_catcwc_raw.append(row[18])
                trm_catcwv_raw.append(row[19])
        # Filter IAP
        trm_arpt_filter = []
        trm_ident_filter = []
        trm_catcdh_filter = []
        trm_catcha_filter = []
        trm_catcwc_filter = []
        trm_catcwv_filter = []
        for i, a in enumerate(trm_arpt_raw):
            if (filter_trm_type in trm_ident_raw[i][0]
                    and 'COPTER' not in trm_ident_raw[i]
                    and a in rwy_arpt_raw):
                trm_arpt_filter.append(a)
                trm_ident_filter.append(trm_ident_raw[i])
                trm_catcdh_filter.append(trm_catcdh_raw[i])
                trm_catcha_filter.append(trm_catcha_raw[i])
                trm_catcwc_filter.append(trm_catcwc_raw[i])
                trm_catcwv_filter.append(trm_catcwv_raw[i])
        trm_arpt_raw = trm_arpt_filter
        trm_ident_raw = trm_ident_filter
        trm_catcdh_raw = trm_catcdh_filter
        trm_catcha_raw = trm_catcha_filter
        trm_catcwc_raw = trm_catcwc_filter
        trm_catcwv_raw = trm_catcwv_filter
        # Get indices of first instances of ARPT in RWY
        i_rwy = []
        for a in rwy_arpt_raw:
            i_rwy.append(rwy_arpt_raw.index(a))
        i_rwy = list(set(i_rwy))
        i_rwy.sort()
        i_rwy.append(len(rwy_arpt_raw) + 1)
        # Get indices of first instances of ARPT in TRM
        i_trm = []
        for a in trm_arpt_raw:
            i_trm.append(trm_arpt_raw.index(a))
        i_trm = list(set(i_trm))
        i_trm.sort()
        i_trm.append(len(trm_arpt_raw) + 1)
        # Create final lists corresponding to ARPT
        trm_arpt = []
        trm_rwy = []
        trm_iap = []
        for j_trm, k in enumerate(i_trm[:-1]):
            j_rwy = i_rwy.index(rwy_arpt_raw.index(trm_arpt_raw[k]))
            rwy_arpt = rwy_arpt_raw[i_rwy[j_rwy]:i_rwy[j_rwy+1]]
            rwy_rwy = rwy_rwy_raw[i_rwy[j_rwy]:i_rwy[j_rwy+1]]
            rwy_len = rwy_len_raw[i_rwy[j_rwy]:i_rwy[j_rwy+1]]
            rwy_wid = rwy_wid_raw[i_rwy[j_rwy]:i_rwy[j_rwy+1]]
            trm_ident = trm_ident_raw[i_trm[j_trm]:i_trm[j_trm+1]]
            trm_catcdh = trm_catcdh_raw[i_trm[j_trm]:i_trm[j_trm+1]]
            trm_catcha = trm_catcha_raw[i_trm[j_trm]:i_trm[j_trm+1]]
            trm_catcwc = trm_catcwc_raw[i_trm[j_trm]:i_trm[j_trm+1]]
            trm_catcwv = trm_catcwv_raw[i_trm[j_trm]:i_trm[j_trm+1]]
            # Get IDENT_RWY and IDENT_TRM from IDENT
            trm_ident_rwy = []
            trm_ident_trm = []
            for b, a in enumerate(trm_ident):
                try:
                    trm_ident_rwy.append(re.search('[0-9]{2}[LRC]?', a).group(0))
                except:
                    # https://xkcd.com/1171/
                    trm_ident_rwy.append(circling)
                trm_ident_trm.append(a.split(' ', maxsplit = 1)[1]
                                     .replace('RW','RWY ').strip())
            # Get index list of IAP with lowest HAT
            ii_trm = sorted(range(len(trm_catcha)), key=lambda x:trm_catcha[x])
            rwy = ''
            iii = 0
            while rwy == '' and iii < len(ii_trm):
                if ((trm_ident_rwy[ii_trm[iii]] == circling
                        or trm_ident_rwy[ii_trm[iii]] in rwy_rwy)
                        and trm_catcha[ii_trm[iii]] != ''):
                    if trm_ident_rwy[ii_trm[iii]] == circling:
                        r = rwy_len.index(max(rwy_len))
                        c = circling + ' '
                    else:
                        r = rwy_rwy.index(trm_ident_rwy[ii_trm[iii]])
                        c = ''
                    trm_arpt.append(trm_arpt_raw[k])
                    rwy = (c + str(rwy_rwy[r]) + ' (' + str(rwy_len[r]) +
                               '&prime;&times;' + str(rwy_wid[r]) + '&prime;)')
                    trm_rwy.append(rwy)
                    
                    iap = (str(trm_ident_trm[ii_trm[iii]]) +
                           ': <span class=\'details\' title=\'Class C\'>' +
                           str(trm_catcdh[ii_trm[iii]]) + '&prime; [' +
                           str(trm_catcha[ii_trm[iii]]) + '&prime;] (' +
                           str(trm_catcwc[ii_trm[iii]].lstrip('0')) + '/' +
                           str(trm_catcwv[ii_trm[iii]]) + ')' + '</span>')
                    trm_iap.append(iap)
                else:
                    iii = iii + 1
        # Write CSV
    ##    with open(f_out, 'w', newline='', encoding='utf-8') as f:
    ##        wr = csv.writer(f, dialect=csv.excel, delimiter=',')
    ##        # Excel chucks a wobbly if the first two characters are "ID",
    ##        # hence "ICAO" instead of "IDENT"
    ##        wr.writerow(['ICAO', 'NAME', 'IAP', 'RWY', 'dlat', 'dlon'])
    ##        for i, a in enumerate(trm_arpt):
    ##            wr.writerow([arpt_ident[a], arpt_name[a],
    ##                         trm_iap[i], trm_rwy[i], 
    ##                         arpt_dlat[a], arpt_dlon[a]])
        fc = []
        for i, a in enumerate(trm_arpt):
            d = OrderedDict()
            d['IDENT'] = arpt_ident[a]
            d['NAME'] = arpt_name[a]
            d['IAP'] = trm_iap[i]
            d['RWY'] = trm_rwy[i]
            # (Lon, Lat) because https://github.com/frewsxcv/python-geojson#point)
            p = geojson.Point((float(arpt_dlon[a]), float(arpt_dlat[a])))
            fc.append(geojson.Feature(geometry=p, properties=d))
        with open(f_out, 'w', newline='', encoding='utf-8') as f:
            f.write(geojson.dumps(geojson.FeatureCollection(fc)))


if __name__ == "__main__":
    main()
