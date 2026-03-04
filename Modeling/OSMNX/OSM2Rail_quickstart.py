# -*- coding: utf-8 -*-
"""
Created on Mon Feb 16 12:54:38 2026

@author: evert
"""

import osm2rail as orl
subarea_name = 'Rotterdam'
download_dir = './osmfile'



osm_file=orl.download_osm_data_from_overpass(subarea_names=subarea_name,download_dir = download_dir,ret_download_path=True)


