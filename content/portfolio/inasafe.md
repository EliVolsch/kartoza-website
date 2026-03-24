---
title: "InaSAFE Disaster Scenario Contingency Planning"
description: "An open-source disaster planning tool that helps governments quickly model potential impacts of floods, earthquakes, and natural hazards."
thumbnail: "/img/portfolio/inasafe.png"
tags:
  - Disaster Management
  - QGIS Plugin
  - Web GIS
  - Indonesia
client: "Government of Indonesia / Australian Government"
date: 2014-05-01
endDate: 2015-06-01
services:
  - Development
  - Training
  - Support
  - Maintenance
related_plugins:
  - inasafe
reviewedBy: "Jeff Osundwa"
reviewedDate: "2026-03-19"
---

{{< block
    title="InaSAFE"
    subtitle="Open-source disaster contingency planning for governments"
    class="is-primary"
    sub-block-side="bottom"
>}}
Helping governments model potential impacts of natural disasters to enable evidence-based response.
{{< /block >}}

## Overview

InaSAFE is a free, open-source tool used to model and plan for natural disasters such as floods, earthquakes, volcanic eruptions, tsunamis, fires, and hurricanes. Initially supported by the Indonesian government with funding from Australia, InaSAFE combines hazard and exposure data to estimate the potential impact of disaster events and produce actionable reports. Kartoza has played a key role in designing, building, and maintaining the InaSAFE ecosystem, including the QGIS plugin, documentation, and supporting interfaces. The software generates clear maps, impact summaries, and recommended actions, helping disaster managers plan responses, allocate resources, and communicate risk to stakeholders.

![InaSAFE](/img/portfolio/inasafe.png)

## Components

### InaSAFE Plugin
A QGIS desktop plugin co-developed with DMInnovation enabling rapid scenario assessments. Users can run simulations locally, create impact maps, and export PDF reports detailing affected areas and estimated consequences.

### InaSAFE Realtime
An automated server-side system delivering near real-time impact estimates following major disaster events. Built on top of InaSAFE libraries and enhancements to core QGIS functionality, the system ingests rapidly updating hazard data (such as earthquake shake maps or flood forecasts), runs automated impact calculations, and generates authoritative cartographic outputs within minutes. During this work, Kartoza contributed major improvements to the QGIS ecosystem, including raster rendering, Web Coverage Service (WCS) support, print composition, and Python bindings, to support fast, reliable automated map generation.

![InaSAFE Realtime](/img/portfolio/inasafe-realtime.png)

### GeoSAFE
A web-based interface built on GeoNode allowing users to conduct analyses via browsers without desktop GIS software. Supports collaborative scenario planning across agencies.

![GeoSAFE](/img/portfolio/inasafe-geosafe.png)

## Technology

- QGIS Desktop and Server
- GeoNode
- Docker
- Web Coverage Service (WCS)

## Services Provided

- Capacity building and training
- Support and maintenance
- Software development and enhancement
- Governance and sustainability
