#!/usr/bin/env python

__version__ = '2020.1.30'

from json import load, JSONEncoder
import argparse
from re import compile
from tkinter import Tk
from tkinter.filedialog import askopenfilenames, asksaveasfilename
import sys

def main():
    """ merge-geojson.py merges multiple GeoJSON files.
        Forked from https://gist.github.com/themiurgo/8687883.js
    """
    float_pat = compile(r'^-?\d+\.\d+(e-?\d+)?$')
    charfloat_pat = compile(r'^[\[,\,]-?\d+\.\d+(e-?\d+)?$')
    parser = argparse.ArgumentParser(
        description= 'Merge multiple GeoJSON files.',
        epilog = 'Lack of path arguments will invoke GUI elements.')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__)
    parser.add_argument('-i', metavar = 'INFILE', default = '',
                      help='full path of files to be merged (*.geojson, *.json)', nargs='+')
    parser.add_argument('-o', metavar = 'OUTFILE', default = '',
                      help='full path of output file (*.geojson, *.json)')
    parser.add_argument('-p', metavar = 'PRECISION', type=int, default = 6, 
                      help='digits of precision (int)')
    args = parser.parse_args()
    infiles = list(args.i)
    outfile = args.o
    p = args.p
    if len(infiles) < 1 or len(outfile) < 1:
        # Identify files
        # http://stackoverflow.com/a/3579625
        Tk().withdraw()  # we don't want a full GUI so hide the root window
        # show an "Open" dialog box and return the path to the selected file
        infiles = askopenfilenames(title='Select GeoJSON files',
                                   filetypes=[('GeoJSON','*.geojson'),('JSON','*.json')])
        if len(infiles) > 0:
            outfile = asksaveasfilename(title='Save As',
                                        filetypes=[('GeoJSON', '*.geojson'),('JSON', '*.json')],
                                        defaultextension='.geojson')
    if len(infiles) > 0 and len(outfile) > 0:
        outjson = dict(type='FeatureCollection', features=[])
        for infile in infiles:
            with open(infile, 'r') as f:
                injson = load(f)
            if injson.get('type', None) != 'FeatureCollection':
                raise Exception('Sorry, "%s" does not look like GeoJSON' % infile)
            if type(injson.get('features', None)) != list:
                raise Exception('Sorry, "%s" does not look like GeoJSON' % infile)
            try:    
                outjson['features'] += injson['features']
            except:
                outjson['features'] += injson
        encoder = JSONEncoder(separators=(',', ':'))
        encoded = encoder.iterencode(outjson)
        format = '%.' + str(p) + 'f'
        output = outfile
        with open(output, 'w', newline='', encoding='utf-8') as f:
            for token in encoded:
                if charfloat_pat.match(token):
                    # in python 2.7, we see a character followed by a float literal
                    f.write(token[0] + format % float(token[1:]))

                elif float_pat.match(token):
                    # in python 2.6, we see a simple float literal
                    f.write(format % float(token))

                else:
                    f.write(token)


if __name__ == "__main__":
    main()
