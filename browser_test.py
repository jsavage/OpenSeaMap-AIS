
[1mOpenSeaMap AIS Service Diagnostic Tool[0m
Run at: 2025-12-09 10:36:19
Python: 3.12.3


[1m[94m======================================================================[0m
[1m[94m                         DNS Resolution Check                         [0m
[1m[94m======================================================================[0m

[92m    OK[0m | map.openseamap.org: Resolves to 195.37.132.70
[91m  FAIL[0m | tiles.marinetraffic.com: DNS resolution failed
[92m    OK[0m | data.aishub.net: Resolves to 144.76.105.244
[92m    OK[0m | aisstream.io: Resolves to 172.67.183.244

[1m[94m======================================================================[0m
[1m[94m             MarineTraffic Service (Historical Provider)              [0m
[1m[94m======================================================================[0m

[91m  FAIL[0m | Tile service: Connection error: HTTPSConnectionPool(host='tiles.marinetraffic.com', port=443): Max retries exceeded with url: /ais_h
[91m  FAIL[0m | Website: HTTP 403

[1m[94m======================================================================[0m
[1m[94m                     Alternative AIS Data Sources                     [0m
[1m[94m======================================================================[0m

[91m  FAIL[0m | AISHub.net: Invalid JSON response: 
[92m    OK[0m | AISstream.io: AISstream.io website accessible (WebSocket API available)

[1m[94m======================================================================[0m
[1m[94m                      OpenSeaMap Infrastructure                       [0m
[1m[94m======================================================================[0m

[92m    OK[0m | main_page: HTTP 200
[92m    OK[0m | api_directory: HTTP 403
[91m  FAIL[0m | getAIS_endpoint: Error: HTTPSConnectionPool(host='map.openseamap.org', port=443): Read timed out. (read timeout=10)

[1m[94m======================================================================[0m
[1m[94m                      GitHub Repository Analysis                      [0m
[1m[94m======================================================================[0m

[93m  INFO[0m | Found 2 AIS-related issues. Most recent: 'Marine Traffic (AIS) layer no longer working' (#192, open)

[1m[94m======================================================================[0m
[1m[94m                 Diagnostic Summary & Recommendations                 [0m
[1m[94m======================================================================[0m


[93m1.[0m MarineTraffic tile service is not accessible. This was the primary AIS data source. MarineTraffic has commercialized their API (requires paid subscription).

[93m2.[0m AISstream.io is accessible. This is a modern WebSocket-based AIS provider. Consider this as a potential alternative data source.

[1m[94m======================================================================[0m
[1m[94m                         Suggested Next Steps                         [0m
[1m[94m======================================================================[0m


1. [1mVerify the root cause:[0m
   - MarineTraffic tile service appears to be the primary issue
   - The service has moved to a paid API model
   
2. [1mCheck OpenSeaMap GitHub:[0m
   - Review Issue #63: "Investigate alternative AIS layer"
   - Check for recent commits about AIS implementation
   - URL: https://github.com/OpenSeaMap/online_chart/issues/63

3. [1mTest alternative data sources:[0m
   - Register for AISHub.net account (requires sharing AIS data)
   - Investigate AISstream.io API
   - Check if other free AIS APIs are available

4. [1mExamine client-side code:[0m
   - Inspect the map page's JavaScript console for errors
   - Check network tab for failed API requests
   - Look at index.php for hardcoded endpoints

5. [1mContact maintainers:[0m
   - Email support with diagnostic results
   - Post in the forum: https://forum.openseamap.org
   - Open a GitHub issue if none exists

6. [1mConsider contributing:[0m
   - Propose a pull request with alternative AIS source
   - Help migrate to AISHub or another provider
    

[92mDetailed report saved to: ais_diagnostic_report_20251209_103632.json[0m

