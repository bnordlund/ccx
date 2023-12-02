#!/usr/bin/env python
# -*- coding: utf-8 -*-

__version__ = '2023.1.13'

import argparse  # process optional arguments
from tkinter import Tk
from tkinter.filedialog import askdirectory, asksaveasfilename
import os


def main():
    """ ccx.py uses the NGA's DAFIF to update CCX GeoJSON.
        Map at www.robertnordlund.com/ccx/
    """
    # INPUTS
    parser = argparse.ArgumentParser(
        description = 'Uses the NGA\'s DAFIF to update CCX GeoJSON.',
        epilog = 'Lack of path arguments will invoke GUI elements.')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__)
    parser.add_argument('-d', metavar = 'DAFIFT', default = '',
                        help = 'full path to "DAFIFT" directory')
    parser.add_argument('-p', metavar = 'PYTHON', default = '',
                        help = 'full path to Python script directory')
    parser.add_argument('-s', metavar = 'PATH', default = '',
                        help = 'full path to save directory')
    args = parser.parse_args()
    d_dafift = args.d
    d_python = args.p
    d_save = args.s
    if len(d_dafift) < 1 or len(d_save) < 1:
        # http://stackoverflow.com/a/3579625
        Tk().withdraw()  # we don't want a full GUI so hide the root window
        d_dafift = askdirectory(title='Select the folder "DAFIFT"')
        d_python = askdirectory(title='Select the folder with Python scripts')
        if len(d_python) < 1:
            # https://stackoverflow.com/a/9350788
            d_python = os.path.dirname(os.path.realpath(__file__))
        if len(d_dafift) > 0:
            d_save = askdirectory(title='Select output folder')
    if len(d_dafift) > 0 and len(d_save) > 0:
        d_dafift = d_dafift.replace('/','\\')
        d_python = d_python.replace('/','\\')
        d_save = d_save.replace('/','\\')
        c1 = 'py -3 "' + d_python + '\\'
        c2 = '" -d "' + d_dafift + '" -f "' + d_save + '\\'
        def runthejewels(script, fname, args):
            """ runthejewels streamlines the script-running process.
            """
            if args != '':
                os.system(c1 + script + c2 + fname + '" ' + args)
            else:
                os.system(c1 + script + c2 + fname + '"')
            print('Updated ' + fname)
        #script = 'agear.py'
        #fname = 'agear.geojson'
        #os.system(c1 + script + c2 + fname + '"')
        #print('Updated ' + fname)
        runthejewels('agear.py', 'agear.geojson', '')
        runthejewels('agear.py', 'barrier.geojson', '-t "MA-1 BAK-15"')
        runthejewels('suas.py', 'suas.geojson', '-c "US CA JA KS"')
        runthejewels('suas.py', 'suas everything.geojson', '')
        runthejewels('mtr.py', 'mtr.geojson', '')
        runthejewels('mtr_label.py', 'mtr_label.geojson', '')
        runthejewels('iap.py', 'tacan.geojson', '-l 6000 -w 100 -t T')
        inputs = ['fueld00.json','fueld26.json',
                'fueli000.json','fueli050.json',
                'fueli100.json','fueli150.json',
                'fueli200.json']
        runthejewels('fuel.py', 'fuel[0]', '-i1 25 -c US')
        runthejewels('fuel.py', 'fuel[1]', '-i0 26 -c US')
        runthejewels('fuel.py', 'fuel[2]', '-i0 0 -i1 49')
        runthejewels('fuel.py', 'fuel[3]', '-i0 50 -i1 99')
        runthejewels('fuel.py', 'fuel[4]', '-i0 100 -i1 149')
        runthejewels('fuel.py', 'fuel[5]', '-i0 150 -i1 199')
        runthejewels('fuel.py', 'fuel[6]', '-i0 200')
        #runthejewels('fuel.py', 'fuelc.json', '-c CA')
        script = 'merge-geojson.py'
        fname = 'fuel.geojson'
        inputs = ['fuel[0]', 'fuel[1]', 'fuel[2]', 'fuel[3]', 'fuel[4]', 'fuel[5]', 'fuel[6]']
        # https://stackoverflow.com/a/12008055
        # https://stackoverflow.com/a/2050649
        os.system(c1 + script + '" -o "' + d_save + '\\' + fname + '" -i ' +
                  '"{}"'.format('" "'.join([d_save + '\\' + s for s in inputs])))

if __name__ == "__main__":
    main()
