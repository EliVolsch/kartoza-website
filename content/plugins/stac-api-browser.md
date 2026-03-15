---
title: "STAC API Browser"
description: "A QGIS plugin for browsing and accessing SpatioTemporal Asset Catalogs (STAC) to discover and load remote sensing data."
thumbnail: "/img/plugins/stac-api-browser.png"
plugin_type: "client"
client: "Microsoft Planetary Computer"
client_url: "https://planetarycomputer.microsoft.com/"
downloads: "44,832+"
version: "1.1.2"
rating: "4.5"
votes: 63
repository: "https://github.com/kartoza/qgis-stac-plugin"
plugin_url: "https://plugins.qgis.org/plugins/qgis_stac_plugin/"
homepage: "https://github.com/kartoza/qgis-stac-plugin"
qgis_min: "3.18.0"
qgis_max: "3.99.0"
tags:
  - STAC
  - Remote Sensing
  - Cloud Native
  - Satellite
related_portfolio:
  - microsoft-stac
  - planet-labs
weight: 120
---

## Overview

The STAC API Browser is a Kartoza plugin developed with funding from Microsoft Planetary Computer that brings cloud-native geospatial data discovery to QGIS. STAC (SpatioTemporal Asset Catalog) is a specification for describing geospatial information, making it easier to search and discover satellite imagery and other earth observation data.

With over 44,000 downloads, this is one of Kartoza's most popular plugins.

## Key Features

- **Catalog Browser**: Browse multiple STAC catalogs
- **Search Interface**: Search by area, date, and collection
- **Preview**: Preview assets before downloading
- **Direct Loading**: Load COG and other cloud-optimised formats
- **Catalog Management**: Save and organise favourite catalogs
- **Asset Selection**: Choose specific bands or assets to load

## Supported STAC Catalogs

The plugin works with any STAC-compliant API, including:

- Microsoft Planetary Computer
- AWS Earth Search
- Google Earth Engine (via STAC)
- Element 84 Earth Search
- Digital Earth Africa
- Radiant Earth MLHub

## Cloud-Native Formats

Directly load cloud-native formats including:

- Cloud Optimized GeoTIFF (COG)
- Zarr
- NetCDF
- GeoParquet

## Use Cases

- Satellite imagery discovery
- Time series analysis
- Environmental monitoring
- Agricultural assessment
- Urban change detection
- Climate research

## Installation

1. Open QGIS and go to **Plugins → Manage and Install Plugins**
2. Search for "STAC"
3. Click **Install Plugin**
4. Access from the Web menu or toolbar

## Documentation

Full documentation is available on the [GitHub repository](https://github.com/kartoza/qgis-stac-plugin).
