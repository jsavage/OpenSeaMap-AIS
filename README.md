# OpenSeaMap-AIS
Investigating the AIS feed because it seems to have stopped working

To run these tests:
./test1.sh:
uv run --with requests ais_diagnostic.py

./test2.sh
uv run --with selenium ais_browser_test.py



Claude AI Prompt:
map.openseamap.org is an open source maritime charting service that displays AIS data. 
High level instructions for this are here: https://openseamap.org/index.php?id=schiffstracking&L=1.   
The code for the underlying AIS functionality is on github.com/openseamap.  
The online service is not currently displaying AIS tracks and I have had no response to emails sent to support channels.  
What I would like to do is create a script (eg python) that I can run that will help me investigate and demonstrate why this service has stopped running.  
Either starting from the source of the underlying data downwards or starting from existing tests that may have already been created by others to help monitor and support this service.

I'll help you investigate why the OpenSeaMap AIS tracking service has stopped working. Let me start by examining the documentation and GitHub repositories to understand the architecture.Fetched OpenSeaMap - The free nautical chartopenseamap.orggithub openseamap AIS10 resultsGitHub - OpenSeaMap/android-ais-openseamap-plotter: Android app to display AIS-data on OpenSeaMapgithub.comonline_chart/api/getAIS.php at master · OpenSeaMap/online_chartgithub.comandroid-ais-openseamap-plotter/src/com/klein/downloaders/OsmTileDownloader.java at master · OpenSeaMap/android-ais-openseamap-plottergithub.comandroid-ais-openseamap-plotter/res/values/strings.xml at master · OpenSeaMap/android-ais-openseamap-plottergithub.comInvestigate alternative AIS layer. · Issue #63 · OpenSeaMap/online_chartgithub.comonline_chart/index.php at master · OpenSeaMap/online_chartgithub.comOpenSeaMap-dev:GitHub – OpenSeaMap-devopenseamap.orgOpenSeaMap - the free nautical chart · GitHubgithub.comMainpage:en – OpenSeaMap-devopenseamap.orgOpenSeaMap - OpenStreetMap Wikiopenstreetmap.orgNow let me look at the online_chart repository more closely to understand the AIS implementation:Failed to fetch https://github.com/OpenSeaMap/online_chartOpenSeaMap online_chart repository AIS implementation10 resultsonline_chart/api/getAIS.php at master · OpenSeaMap/online_chartgithub.comOpenSeaMap - OpenStreetMap Wikiopenstreetmap.orgOpenSeaMap - Wikipediawikipedia.orgOpenSeaMap: Mainpageopenseamap.orgonline_chart/index.php at master · OpenSeaMap/online_chartgithub.comOpenSeaMap - the free nautical chart · GitHubgithub.comOpenSeaMap: Our resourcesopenseamap.orgMain Page – OpenSeaMap-devopenseamap.orgInvestigate alternative AIS layer. · Issue #63 · OpenSeaMap/online_chartgithub.comGitHub - OpenSeaMap/online_chart_ol3: OpenSeaMap chart framework - an interative online chartgithub.comLet me check what the current AIS endpoint is and test it:marinetraffic.com tiles API AIS10 resultsAIS API Documentation | AIS Marine Trafficmarinetraffic.comAccess ship and position data via the API | AIS Marine Trafficmarinetraffic.comAIS API Servicesmarinetraffic.comAPI Services | MarineTrafficmarinetraffic.comAIS data API Documentationmarinetraffic.comMarineTraffic Real-time Ship Data Scraper · Apifyapify.comContainer Tracking API Documentationmarinetraffic.comMarine-Traffic-API · PyPIpypi.orgAPI Services – MarineTraffic Helpmarinetraffic.comSet-up your API Services – MarineTraffic Helpmarinetraffic.comNow let me check the actual OpenSeaMap map to see what's happening:Fetched OpenSeaMapopenseamap.orgBased on my investigation, I can see that OpenSeaMap previously used MarineTraffic's tile service for AIS data, but MarineTraffic has commercialized their API (requiring paid access). I've found the critical information in the GitHub code showing the old endpoint and the issue discussing alternatives.
Let me create a comprehensive Python diagnostic script for you:OpenSeaMap AIS Diagnostic ScriptCode #!/usr/bin/env python3
"""
OpenSeaMap AIS Service Diagnostic Tool

This script investigates why the OpenSeaMap AIS tracking service has stopped working.
It tests various data sources and endpoints to help identify the failure point.

Based on investiNow let me create an additional script that can actually test the live map and extract more detailed information:OpenSeaMap Browser-Based AIS TestCode #!/usr/bin/env python3
"""
OpenSeaMap Browser-Based AIS Test Script

This script uses Selenium to load the actual OpenSeaMap interface,
enable the AIS layer, and monitor network requests to identify failures.

Requirements:
    pip install selenium 
    
I've created two comprehensive Python scripts to help you investigate the OpenSeaMap AIS service failure. Here's what I found and what these scripts do:
Key Findings from Investigation
Based on my research of the OpenSeaMap GitHub repository and related sources:

Root Cause: OpenSeaMap historically used MarineTraffic's tile service for AIS data, but MarineTraffic has commercialized their API and now requires paid access GitHub
Known Issue: There's an existing GitHub Issue #63 titled "Investigate alternative AIS layer" where maintainers discuss the problem and alternatives like AISHub.net
Code Evidence: The source code in online_chart/index.php shows commented-out MarineTraffic endpoints that were previously used
----

The Two Scripts I've Created
Script 1: ais_diagnostic.py - API Endpoint Testing
This script tests the service from a network/API perspective:

Tests MarineTraffic's tile service (the old data source)
Checks alternative AIS providers (AISHub.net, AISstream.io)
Verifies OpenSeaMap's own API endpoints
Checks DNS resolution
Analyzes GitHub issues
Generates a comprehensive JSON report

Usage:
bashpip install requests
python ais_diagnostic.py
Script 2: ais_browser_test.py - Browser Automation Testing
This script uses Selenium to test the actual web interface:

Loads the real OpenSeaMap website in a browser
Attempts to enable the AIS layer checkbox
Monitors all network requests
Captures JavaScript errors
Takes screenshots for evidence
Identifies exactly which requests are failing

Usage:
bashpip install selenium
# Install Chrome/Chromium and chromedriver
python ais_browser_test.py
# Or headless: python ais_browser_test.py --headless
What These Scripts Will Show
They'll help you demonstrate:

Whether MarineTraffic is returning 403 Forbidden (proving commercialization)
Which alternative AIS sources are accessible
Whether OpenSeaMap's backend is functioning
Any JavaScript errors preventing layer activation
The exact failure point in the data pipeline

Next Steps
After running these scripts, you'll have concrete evidence to:

Share with the OpenSeaMap maintainers
Post in the forum or GitHub issues
Propose switching to an alternative provider
Possibly contribute a fix yourself (the GitHub issue mentions AISHub as a viable alternative)

Both scripts generate detailed reports that you can attach to support emails or GitHub issues to help demonstrate the problem clearly.
