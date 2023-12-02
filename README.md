# ccx
CCX Map (Arresting Gear, Contract Fuel, TACAN IAP, WW/SIGMETS, TFR, MTR, SUAS, etc.) for flight planning
Several tools are provided for parsing the National Geospatial-Intelligence Agency's (NGA) Defense Aeronautical Flight Information File (DAFIF) into GeoJSON (*.json):
* agear.py: airports with arresting gear
* iap.py: Instrument Approach Procedures (IAP), specifically TACtical Air Navigation (TACAN) 
* mtr.py: Military Training Routes (MTR)
* suas.py: Special Use Airspace (SUAS)

Additionally, tools are provided for scraping the AIR Card website for FBO Locator (Contract Fuel) information, correlating to DAFIF, and outputting GeoJSON (*.json). 
* fuel.py: US and CA will only be scraped when specified.
* merge-geojson.py: combine multiple *.json files

These tools are used programmatically in the following script:
* ccx.py

Requires DAFIF: https://aerodata.nga.mil/AeroDownload/
