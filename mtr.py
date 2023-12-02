#!/usr/bin/env python
# -*- coding: utf-8 -*-

__version__ = '2020.1.30'

import argparse  # process optional arguments
import csv, json
from geojson import Feature, FeatureCollection, LineString
from tkinter import Tk
from tkinter.filedialog import askdirectory, asksaveasfilename

def main():
    """ mtr.py parses the NGA's DAFIF for Military Training Routes.
        Downloads at https://dbgia.geointel.nga.mil/
        Map at www.robertnordlund.com/ccx/
    """
    # INPUTS
    parser = argparse.ArgumentParser(
        description = 'Parses the NGA\'s DAFIF for Military Training Routes.',
        epilog = 'Lack of path arguments will invoke GUI elements.')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__)
    parser.add_argument('-d', metavar = 'DAFIFT', default = '',
                        help = 'full path to "DAFIFT" directory')
    parser.add_argument('-f', metavar = 'FILE', default = '',
                        help = 'full path to output file (*.geojson, *.json)')
    args = parser.parse_args()
    d = args.d
    f_out = args.f
    if len(d) < 1 or len(f_out) < 1:
        # Identify CSV
        # http://stackoverflow.com/a/3579625
        Tk().withdraw()  # we don't want a full GUI so hide the root window
        # show an "Open" dialog box and return the path to the selected file
        d = askdirectory(title='Select the folder "DAFIFT"')
        f_out = asksaveasfilename(title='Save As',
                                  filetypes=[('GeoJSON', '*.geojson'),('JSON', '*.json')],
                                  defaultextension='.geojson')
    if len(d) > 0 and len(f_out) > 0:
        # Read CSV
        f_in = d + '\\MTR\\MTR_OV.txt'
        with open(f_in) as csvfile:
            csv_rows = []
            featuresSegments = []
            reader = csv.DictReader(csvfile, delimiter='\t')
            # https://www.idiotinside.com/2015/09/18/csv-json-pretty-print-python/
            title = reader.fieldnames
            for row in reader:
                #csv_rows.extend([{title[i]:row[title[i]] for i in range(len(title))}])
                row_dict = ({title[i]:row[title[i]] for i in range(len(title))})
                if row_dict['MTR_IDENT'][:2] == 'SR':
                    continue
                # https://stackoverflow.com/a/48586799
                featuresSegments.append(
                    Feature(
                        geometry = LineString([
                            (round(float(row_dict['PT_DLONG']), 4), round(float(row_dict['PT_DLAT']), 4)),
                            (round(float(row_dict['NX_DLONG']), 4), round(float(row_dict['NX_DLAT']), 4))
                            ]),
                        properties = {
                            'MTR': row_dict['MTR_IDENT'],
                            'Type': row_dict['MTR_IDENT'][:2],
                            'From': row_dict['PT_IDENT'],
                            'To': row_dict['NX_POINT'],
                        }
                    )
                )
            collection = FeatureCollection(featuresSegments)
            with open(f_out, 'w', newline='', encoding='utf-8') as f:
                #print(json.dumps(collection, sort_keys=False, indent=4, separators=(',', ': '),ensure_ascii=False))
                f.write(json.dumps(collection))

if __name__ == "__main__":
    main()
