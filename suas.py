#!/usr/bin/env python
# -*- coding: utf-8 -*-

__version__ = '2022.5.31'

import argparse  # process optional arguments
import csv, json
from geojson import Feature, FeatureCollection, Polygon
from tkinter import Tk
from tkinter.filedialog import askdirectory, asksaveasfilename
import math
from xml.etree import ElementTree as et # append2drx

def main():
    """ suas.py parses the NGA's DAFIF for Special Use Airspace.
        Downloads at https://dbgia.geointel.nga.mil/
    """
    xml_handler = ('.drx', '.xml') # extensions for special consideration
    # INPUTS
    parser = argparse.ArgumentParser(
        description = 'Parses the NGA\'s DAFIF for Special Use Airspace.',
        epilog = 'Absence of path arguments will invoke GUI elements (discarding filter arguments).')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__)
    parser.add_argument('-d', metavar = 'DAFIFT', default = '',
                        help = 'full path to "DAFIFT" directory')
    parser.add_argument('-f', metavar = 'file', default = '',
                        help = 'full path to output file (*.geojson, *.json)')
    parser.add_argument('-c', metavar = 'countries', default = '',
                        help='filter for acceptable countries (e.g. US JA)')
    parser.add_argument('-a', metavar = 'area', default= '90 -180 -90 180',
                        help='filter area by NW & SE corners if applicable (lat lng lat lng) (e.g. 50 -131 23 -66)')
    args = parser.parse_args()
    d = args.d
    f_out = args.f
    ctry_filter = args.c
    area_filter = list(map(float, args.a.split()))
    gui = False
    # http://stackoverflow.com/a/3579625
    Tk().withdraw() # we don't want a full GUI so hide the root window
    if len(d) < 1:
        # show an "Open" dialog box and return the path to the selected file
        d = askdirectory(title='Select the folder "DAFIFT"')
        gui = True
    if d and len(f_out) < 1:
        f_out = asksaveasfilename(title='Save As',
                                  filetypes=[('GeoJSON', '*.geojson'),
                                             ('JSON', '*.json'),
                                             ('Drawing Object', '*.drx'),
                                             ('XML', '*.xml')],
                                  defaultextension='.geojson')
        gui = True
    # Confirm filters once GUI invoked
    if d and f_out and gui:
        print('[Command line filter arguments discarded after GUI invoked]\n')
        try:
            ctry_filter = input(
                'Specify a country filter if applicable (e.g. \'US JA\') '
                '[just the letters]: ')
        except:
            ctry_filter = ''
        try:
            area_filter = input(
                'Specify NW & SE corners if applicable (lat lng lat lng) [just the numbers]\n(e.g. \'50 -131 23 -66\'): ')
            area_filter = list(map(float, area_filter.split()))
            if (len(area_filter) != 4 or
                area_filter[2] >= area_filter[0] or
                area_filter[3] <= area_filter[1]):
                area_filter = list(map(float, '90 -180 -90 180'.split()))
        except:
            area_filter = list(map(float, '90 -180 -90 180'.split()))
    if d and f_out:
        # Read CSV (CTRY)
        f_in = d + '\\SUAS\\SUAS_CTRY.TXT'
        ctry_dict = {}
        with open(f_in) as csvfile:
            reader = csv.DictReader(csvfile, delimiter='\t')
            title = reader.fieldnames
            for row in reader:
                row_dict = ({title[i]:row[title[i]] for i in range(len(title))})
                ctry_dict[row_dict['SUAS_IDENT']] = row_dict['CTRY_1']
        # Read CSV (SUAS)
        f_in = d + '\\SUAS\\SUAS.TXT'
        with open(f_in) as csvfile:
            featuresPolygons = []
            drawing = et.Element('Objects') # Create SVG XML element
            nm2ft = 6076.12
            SUAS_IDENT = ''
            coordinates = []
            valid = False
            reader = csv.DictReader(csvfile, delimiter='\t')
            # https://www.idiotinside.com/2015/09/18/csv-json-pretty-print-python/
            title = reader.fieldnames
            for row in reader:
                row_dict = ({title[i]:row[title[i]] for i in range(len(title))})
                ctry_dict[row_dict['SUAS_IDENT']][:2]
                if ctry_dict[row_dict['SUAS_IDENT']][:2] not in ctry_filter.upper().split() and ctry_filter != '':
                    continue
                # append2drx color_pen_fore argument
                if row_dict['TYPE'] == 'T' or row_dict['TYPE'] == 'R':
                    color_xml = [255, 0, 0] # red
                elif row_dict['TYPE'] == 'M':
                    color_xml = [128, 0, 128] # purple
                elif row_dict['TYPE'] == 'A':
                    color_xml = [255, 0, 128] # magenta
                elif row_dict['TYPE'] == 'W':
                    color_xml = [0, 64, 128] # blue
                else:
                    color_xml = [0, 0, 0] # black
                    #color_xml = [0, 128, 0] # dark green
                # Write completed geometry
                if row_dict['SUAS_IDENT'] != SUAS_IDENT and len(coordinates) > 3:
                    if coordinates[0] != coordinates[-1]:
                        coordinates.append(coordinates[0])
                    # https://stackoverflow.com/a/48586799
                    if valid == True:
                        featuresPolygons.append(
                            Feature(
                                geometry = Polygon([coordinates]),
                                properties = properties
                            )
                        )
                        coordinates.pop()
                        drawing = append2drx(drawing, coordinates,
                                             polygon=True,
                                             color_pen_fore=color_xml,
                                             tooltip=SUAS_IDENT)
                    coordinates = []
                    valid = False
                # Abort invalid geometry
                if row_dict['SUAS_IDENT'] != SUAS_IDENT and valid == False:
                    coordinates = []
                # Handle Circles
                if row_dict['SHAP'] == 'C' or row_dict['SHAP'] == 'A':
                    if f_out.endswith(xml_handler):
                        point = (float(row_dict['WGS_DLONG0']), float(row_dict['WGS_DLAT0']))
                        if (point[1] <= area_filter[0] and                            
                            point[1] >= area_filter[2] and
                            point[0] >= area_filter[1] and
                            point[0] <= area_filter[3]):
                            coordinates.append(point)
                            drawing = append2drx(drawing, coordinates,
                                                 obj = 'ellipse',
                                                 vRadius = float(row_dict['RADIUS1']) * nm2ft,
                                                 hRadius = float(row_dict['RADIUS1']) * nm2ft, 
                                                 color_pen_fore=color_xml,
                                                 tooltip=SUAS_IDENT)
                            coordinates = []
                            if row_dict['RADIUS2'] != '':
                                coordinates.append(point)
                                drawing = append2drx(drawing, coordinates,
                                                     obj = 'ellipse',
                                                     vRadius = float(row_dict['RADIUS2']) * nm2ft,
                                                     hRadius = float(row_dict['RADIUS2']) * nm2ft, 
                                                     color_pen_fore=color_xml,
                                                     tooltip=SUAS_IDENT)
                                coordinates = []
                    else:
                        n = 36
                        circle = []
                        for i in range(n):
                            theta = 360 / n * i
                            point = projection(
                                float(row_dict['WGS_DLAT0']),
                                float(row_dict['WGS_DLONG0']),
                                float(row_dict['RADIUS1']),
                                theta)
                            if (point[1] <= area_filter[0] and
                                point[1] >= area_filter[2] and
                                point[0] >= area_filter[1] and
                                point[0] <= area_filter[3]):
                                valid = True
                            circle.append(point)
                        circle.append(circle[0])
                        coordinates.extend(circle)
                        if row_dict['RADIUS2'] != '':
                            circle = []
                            for i in range(n):
                                theta = 360 / n * i
                                point = projection(
                                    float(row_dict['WGS_DLAT0']),
                                    float(row_dict['WGS_DLONG0']),
                                    float(row_dict['RADIUS2']),
                                    theta)
                                if (point[1] <= area_filter[0] and
                                    point[1] >= area_filter[2] and
                                    point[0] >= area_filter[1] and
                                    point[0] <= area_filter[3]):
                                    valid = True
                                circle.append(point)
                            circle.append(circle[0])
                            coordinates.extend(circle)
                # Handle Arcs
                elif row_dict['SHAP'] == 'R' or row_dict['SHAP'] == 'L':
                    theta1 = bearing(
                        float(row_dict['WGS_DLAT0']),
                        float(row_dict['WGS_DLONG0']),
                        float(row_dict['WGS_DLAT1']),
                        float(row_dict['WGS_DLONG1']))
                    theta2 = bearing(
                        float(row_dict['WGS_DLAT0']),
                        float(row_dict['WGS_DLONG0']),
                        float(row_dict['WGS_DLAT2']),
                        float(row_dict['WGS_DLONG2']))
                    angdiff = theta2 - theta1
                    direction = 1 if row_dict['SHAP'] == 'R' else -1
                    if angdiff * direction < 0:
                        angdiff = angdiff + direction * 360
                    n = 36
                    for i in range(math.ceil(abs(angdiff) / (360 / n))):
                        theta = theta1 + direction * i * 360 / n
                        point = projection(
                            float(row_dict['WGS_DLAT0']),
                            float(row_dict['WGS_DLONG0']),
                            float(row_dict['RADIUS1']),
                            theta)
                        if (point[1] <= area_filter[0] and
                            point[1] >= area_filter[2] and
                            point[0] >= area_filter[1] and
                            point[0] <= area_filter[3]):
                            valid = True
                        coordinates.append(point)
                    coordinates.extend([
                        (round(float(row_dict['WGS_DLONG2']), 4), round(float(row_dict['WGS_DLAT2']), 4))
                        ])
                # Handle Polygons
                else:
                    point = (round(float(row_dict['WGS_DLONG1']), 4), round(float(row_dict['WGS_DLAT1']), 4))
                    if (point[1] <= area_filter[0] and
                        point[1] >= area_filter[2] and
                        point[0] >= area_filter[1] and
                        point[0] <= area_filter[3]):
                        valid = True
                    coordinates.extend([
                        (round(float(row_dict['WGS_DLONG1']), 4), round(float(row_dict['WGS_DLAT1']), 4)),
                        (round(float(row_dict['WGS_DLONG2']), 4), round(float(row_dict['WGS_DLAT2']), 4))
                        ])
                if len(coordinates) > 2 and coordinates[-2] == coordinates[-3]:
                    del coordinates[-3]
                properties = {
                        'SUAS': row_dict['SUAS_IDENT'],
                        'Name': row_dict['NAME'],
                        'ICAO': row_dict['ICAO'],
                        'TYPE': row_dict['TYPE'],
                    }
                SUAS_IDENT = row_dict['SUAS_IDENT']
            # Write final geometry
            if coordinates[0] != coordinates[-1]:
                coordinates.append(coordinates[0])
            if valid == True:
                featuresPolygons.append(
                    Feature(
                        geometry = Polygon([coordinates]),
                        properties = properties
                    )
                )
                coordinates.pop()
                drawing = append2drx(drawing, coordinates,
                                     polygon=True,
                                     color_pen_fore=color_xml,
                                     tooltip=SUAS_IDENT)
            collection = FeatureCollection(featuresPolygons)
            if f_out.endswith(xml_handler):
                with open(f_out, 'wb') as f:
                    bstr = et.tostring(drawing, encoding='ISO-8859-1', method='xml')
                    f.write(bstr)
            else:
                with open(f_out, 'w', newline='', encoding='utf-8') as f:
                    #print(json.dumps(collection, sort_keys=False, indent=4, separators=(',', ': '),ensure_ascii=False))
                    f.write(json.dumps(collection))

def projection(lat, lng, d, theta):
    """ projection returns coordinates from bearing (deg true) and range (NM).
        http://www.movable-type.co.uk/scripts/latlong.html
    """
    R = 3438.1451 # Earth's radius (NM)
    lat = lat * math.pi / 180
    lng = lng * math.pi / 180
    theta = theta * math.pi / 180
    lat2 = math.asin(math.sin(lat) * math.cos(d / R) + math.cos(lat) * math.sin(d / R) * math.cos(theta))
    lng2 = lng + math.atan2(math.sin(theta) * math.sin(d / R) * math.cos(lat), math.cos(d / R) - math.sin(lat) * math.sin(lat2))
    return (round((lng2 * 180 / math.pi + 540) % 360 - 180, 5), round(lat2 * 180 / math.pi, 4)) # lng2 normalized +/-180

def bearing(lat1, lng1, lat2, lng2):
    """ bearing returns bearing (deg true) between two points.
        http://www.movable-type.co.uk/scripts/latlong.html
    """
    lat1 = lat1 * math.pi / 180;
    lng1 = lng1 * math.pi / 180;
    lat2 = lat2 * math.pi / 180;
    lng2 = lng2 * math.pi / 180;
    y = math.sin(lng2 - lng1) * math.cos(lat2);
    x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(lng2 - lng1);
    brng = (math.atan2(y, x) * 180 / math.pi + 360) % 360
    return brng

def append2drx(drawing, coordinates, 
               # Default object
               obj = 'line', # 'line' or 'ellipse' or 'text'
               tooltip = '', 
               line_width = '4',
               line_style = 'solid', 
               color_pen_fore = [255, 255, 255], 
               color_pen_back = [255, 0, 0],  # applies when Fill style not "none"
               fill_style = 'none', 
               # Default label/Text (anchored to first point)
               string_label = '',
               display_label = False, # not used in Text
               color_label_fore = [0, 0, 0], 
               color_label_back = [255, 255, 255], 
               font_size_label = '12', 
               font_name_label = 'Arial', 
               backtype_label = 'none',  # 'shadow' (for Text) or 'none' or 'rect'
               # Ellipse / Text
               rotation = '0', # deg clockwise
               # Ellipse only
               vRadius = 6076, # ft
               hRadius = 6076, # ft
               # Text only
               text_rotate = False, # Rotate with map
               text_scale = True, # Scale to map
               text_anchor = 'center_center', # 'center_center' or 'upper_left' etc.
               text_max = '72', 
               # Line only
               polygon = False,
               line_type = 'rhumb', # 'rhumb' or 'simple'
               string_embed = '', 
               color_embed_fore = [0, 0, 0], 
               color_embed_back = [255, 255, 255],  # applies when Embedded Font backtype not "none"
               font_size_embed = '12', 
               font_name_embed = 'Arial', 
               backtype_embed = 'none'): # 'none' or 'rect'
    """append2drx appends to JMPS/FalconView Drawing Object XML (*.drx)

    Args:
        drawing: ElementTree element e.g. et.Element('Objects')
        coordinates: array of (dlon, dlat) tuples or arrays
        polygon (optional): boolean e.g. True
        line_width (optional): string integer e.g. '4'
        color_pen_fore (optional): RGB tuple or array e.g. [255, 255, 255]
        (and many more optional arguments)

    Returns:
        drawing: ElementTree element (with updated Next element attribute)
    """
    def rgb2dict(rgb):
        """rgb2dict returns a dict from RGB tuple or array
        Args:
            tuple or array of RGB values e.g. [255, 255, 255]

        Returns:
            dict e.g. {'red':'0', 'green':'0', 'blue':'0'}
        """
        color = {'red':str(rgb[0])}
        color['green'] = str(rgb[1])
        color['blue'] = str(rgb[2])
        return color
    # Setup
    drawing.set('xmlns', 'urn:JMPS/JMPS')
    color_pen_fore = rgb2dict(color_pen_fore)
    color_pen_back = rgb2dict(color_pen_back)
    color_label_fore = rgb2dict(color_label_fore)
    color_label_back = rgb2dict(color_label_back)
    color_embed_fore = rgb2dict(color_embed_fore)
    color_embed_back = rgb2dict(color_embed_back)
    try:
        n = int(drawing.attrib['Next'])
    except:
        n = 0
    # Create SVG XML element
    # https://nick.onetwenty.org/index.php/2010/04/07/creating-svg-files-with-python/
    obj_et = et.SubElement(drawing, 'Object', ID=str(n))
    # Detail
    obj_detail = et.SubElement(obj_et, 'Detail')
    detail_comment = et.SubElement(obj_detail, 'Comment')
    detail_status = et.SubElement(obj_detail, 'Status')
    detail_tooltip = et.SubElement(obj_detail, 'Tooltip')
    detail_tooltip.text = tooltip
    # Ellipse / Text / Line
    if obj.lower() == 'ellipse':
        thing = et.SubElement(obj_et, 'Ellipse', style=line_style,
                              rotate=rotation)
    elif obj.lower() == 'text':
        thing = et.SubElement(obj_et, 'Text', rotate=rotation,
                              fixed_degrees='0', 
                              rotatewithmap=str(text_rotate).lower(),
                              fixed=str(not(text_scale)).lower(),
                              anchor=text_anchor,
                              maxsize=text_max)
    else:
        thing = et.SubElement(obj_et, 'Line', style=line_style,
                              linetype=line_type,
                              polygon=str(polygon).lower())
    pen = et.SubElement(thing, 'Pen', width=line_width)
    if obj.lower() in ('ellipse', 'line'):
        c = color_pen_fore
        c.update({'type':'fore'})
        color = et.SubElement(pen, 'Color', c)
        c = color_pen_back
        c.update({'type':'back'})
        color = et.SubElement(pen, 'Color', c) # applies when Fill style not "none"
        fill = et.SubElement(thing, 'Fill', style=fill_style) # uses Pen Color type "back"
    if obj.lower() == 'ellipse':
        radius = et.SubElement(thing, 'VRadius')
        radius.text = str(round(vRadius))
        radius = et.SubElement(thing, 'HRadius')
        radius.text = str(round(hRadius))
    if obj.lower() in ('ellipse', 'text'):
        point = et.SubElement(thing, 'Point', type='center')
        latitude = et.SubElement(point, 'LATITUDE')
        latitude.text = str(coordinates[-1][1])
        longitude = et.SubElement(point, 'LONGITUDE')
        longitude.text = str(coordinates[-1][0])
    if obj.lower() == 'text':
        font = et.SubElement(thing, 'Font', size=font_size_label, attributes='0',
                              backtype=backtype_label)
        string = et.SubElement(thing, 'String')
    else:
        label = et.SubElement(thing, 'Label', Display=str(display_label).lower()) # anchored to first point
        font = et.SubElement(label, 'Font', size=font_size_label, attributes='0',
                             backtype=backtype_label)
        string = et.SubElement(label, 'String')
    name = et.SubElement(font, 'Name')
    name.text = font_name_label
    c = color_label_fore
    c.update({'type':'fore'})
    color = et.SubElement(font, 'Color', c)
    c = color_label_back
    c.update({'type':'back'})
    color = et.SubElement(font, 'Color', c)
    string.text =  string_label
    if obj.lower() == 'line':
        for p in coordinates:
            point = et.SubElement(thing, 'Point')
            latitude = et.SubElement(point, 'LATITUDE')
            latitude.text = str(p[1])
            longitude = et.SubElement(point, 'LONGITUDE')
            longitude.text = str(p[0])
        embed = et.SubElement(thing, 'Embedded', text_position='center')
        font = et.SubElement(embed, 'Font', size=font_size_embed, attributes='0',
                             backtype=backtype_embed)
        name = et.SubElement(font, 'Name')
        name.text = font_name_embed
        c = color_embed_fore
        c.update({'type':'fore'})
        color = et.SubElement(font, 'Color', c)
        c = color_embed_back
        c.update({'type':'back'})
        color = et.SubElement(font, 'Color', c) # applies when Embedded Font backtype not "none"
        string = et.SubElement(embed, 'String')
        string.text =  string_embed
    drawing.set('Next', str(n+1))
    return drawing

if __name__ == "__main__":
    main()
