#!/usr/bin/env python3
"""
OpenSeaMap AIS Service Diagnostic Tool

This script investigates why the OpenSeaMap AIS tracking service has stopped working.
It tests various data sources and endpoints to help identify the failure point.

Based on investigation of:
- github.com/openseamap/online_chart
- Historical MarineTraffic integration
- Alternative AIS data sources mentioned in Issue #63
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import time

class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_status(status: str, message: str):
    """Print formatted status message"""
    color = Colors.GREEN if status == "OK" else Colors.RED if status == "FAIL" else Colors.YELLOW
    print(f"{color}{status:>6}{Colors.RESET} | {message}")

def print_section(title: str):
    """Print section header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{title.center(70)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}\n")

def test_marinetraffic_tiles(lat: float = 51.5, lon: float = -0.1, zoom: int = 10) -> Tuple[bool, str]:
    """
    Test the MarineTraffic tile service that OpenSeaMap historically used.
    
    From online_chart/index.php, the old endpoint was:
    https://tiles.marinetraffic.com/ais_helpers/shiptilesingle.aspx
    """
    # Calculate tile coordinates from lat/lon/zoom
    import math
    n = 2.0 ** zoom
    x = int((lon + 180.0) / 360.0 * n)
    y = int((1.0 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2.0 * n)
    
    url = (f"https://tiles.marinetraffic.com/ais_helpers/shiptilesingle.aspx"
           f"?output=png&sat=1&grouping=shiptype&tile_size=512&legends=1"
           f"&zoom={zoom}&X={x}&Y={y}")
    
    try:
        response = requests.get(url, timeout=10, headers={
            'User-Agent': 'OpenSeaMap-Diagnostic/1.0'
        })
        
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', '')
            if 'image' in content_type:
                return True, f"Tile service responding (HTTP {response.status_code}, {len(response.content)} bytes)"
            else:
                return False, f"Unexpected content type: {content_type}"
        elif response.status_code == 403:
            return False, "Access denied (HTTP 403) - API likely commercialized"
        elif response.status_code == 401:
            return False, "Authentication required (HTTP 401) - API key needed"
        else:
            return False, f"HTTP {response.status_code}: {response.text[:200]}"
    except requests.exceptions.Timeout:
        return False, "Request timeout (10s)"
    except requests.exceptions.ConnectionError as e:
        return False, f"Connection error: {str(e)[:100]}"
    except Exception as e:
        return False, f"Error: {str(e)[:100]}"

def test_marinetraffic_api_simple() -> Tuple[bool, str]:
    """Test if MarineTraffic API is accessible without authentication"""
    # Try a simple public endpoint
    url = "https://www.marinetraffic.com/en/data/?asset_type=vessels"
    
    try:
        response = requests.get(url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0'
        })
        
        if response.status_code == 200:
            return True, f"MarineTraffic website accessible (HTTP {response.status_code})"
        else:
            return False, f"HTTP {response.status_code}"
    except Exception as e:
        return False, f"Error: {str(e)[:100]}"

def test_aishub_api(mmsi: Optional[int] = None) -> Tuple[bool, str]:
    """
    Test AISHub.net API (mentioned in OpenSeaMap Issue #63 as alternative)
    AISHub provides free access to AIS data for contributors.
    """
    # Try to get vessels in a bounding box (requires registration but can test endpoint)
    url = "https://data.aishub.net/ws.php"
    params = {
        'username': 'DEMO',  # Demo account for testing
        'format': '1',  # JSON
        'output': 'json',
        'compress': '0'
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            try:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    return True, f"AISHub API responding with data ({len(data)} entries)"
                elif 'ERROR' in str(data):
                    return False, f"API error: {data}"
                else:
                    return True, "AISHub endpoint accessible (authentication likely required)"
            except json.JSONDecodeError:
                return False, f"Invalid JSON response: {response.text[:200]}"
        elif response.status_code == 401:
            return False, "Authentication required - valid credentials needed"
        else:
            return False, f"HTTP {response.status_code}"
    except Exception as e:
        return False, f"Error: {str(e)[:100]}"

def test_aisstream_websocket() -> Tuple[bool, str]:
    """
    Test AISstream.io (modern AIS data provider with WebSocket API)
    """
    # url = "https://stream.aisstream.io/v0/stream"   # note url not used
    
    try:
        # Just test if the endpoint exists (full WebSocket test would be more complex)
        response = requests.get("https://aisstream.io", timeout=10)
        if response.status_code == 200:
            return True, "AISstream.io website accessible (WebSocket API available)"
        else:
            return False, f"HTTP {response.status_code}"
    except Exception as e:
        return False, f"Error: {str(e)[:100]}"

def test_openseamap_api_endpoints() -> Dict[str, Tuple[bool, str]]:
    """Test OpenSeaMap's own API endpoints"""
    base_url = "https://map.openseamap.org"
    
    results = {}
    
    # Test main map page
    try:
        response = requests.get(base_url, timeout=10)
        results['main_page'] = (
            response.status_code == 200,
            f"HTTP {response.status_code}"
        )
    except Exception as e:
        results['main_page'] = (False, f"Error: {str(e)[:100]}")
    
    # Test API directory
    api_url = f"{base_url}/api/"
    try:
        response = requests.get(api_url, timeout=10)
        results['api_directory'] = (
            response.status_code in [200, 403],  # 403 might mean it exists but is restricted
            f"HTTP {response.status_code}"
        )
    except Exception as e:
        results['api_directory'] = (False, f"Error: {str(e)[:100]}")
    
    # Test getAIS.php endpoint (from the GitHub code)
    # This endpoint expects bbox parameters but we can test if it exists
    ais_url = f"{base_url}/api/getAIS.php"
    try:
        response = requests.get(ais_url, timeout=10, params={
            'bbox': '0,0,1,1'
        })
        results['getAIS_endpoint'] = (
            response.status_code in [200, 400],  # 400 might mean bad params but endpoint exists
            f"HTTP {response.status_code}"
        )
    except Exception as e:
        results['getAIS_endpoint'] = (False, f"Error: {str(e)[:100]}")
    
    return results

def check_dns_resolution(domains: List[str]) -> Dict[str, Tuple[bool, str]]:
    """Check if critical domains resolve properly"""
    import socket
    results = {}
    
    for domain in domains:
        try:
            ip = socket.gethostbyname(domain)
            results[domain] = (True, f"Resolves to {ip}")
        except socket.gaierror:
            results[domain] = (False, "DNS resolution failed")
        except Exception as e:
            results[domain] = (False, f"Error: {str(e)[:100]}")
    
    return results

def analyze_github_issues() -> Tuple[bool, str]:
    """
    Check the GitHub repository for recent issues about AIS
    """
    url = "https://api.github.com/repos/OpenSeaMap/online_chart/issues"
    
    try:
        response = requests.get(url, timeout=10, params={
            'state': 'all',
            'per_page': 30
        })
        
        if response.status_code == 200:
            issues = response.json()
            ais_issues = [
                issue for issue in issues 
                if 'ais' in issue.get('title', '').lower() or 
                   'marine' in issue.get('title', '').lower() or
                   'traffic' in issue.get('title', '').lower()
            ]
            
            if ais_issues:
                recent = ais_issues[0]
                return True, (f"Found {len(ais_issues)} AIS-related issues. "
                            f"Most recent: '{recent['title']}' "
                            f"(#{recent['number']}, {recent['state']})")
            else:
                return True, f"No AIS-specific issues found in recent {len(issues)} issues"
        else:
            return False, f"HTTP {response.status_code}"
    except Exception as e:
        return False, f"Error: {str(e)[:100]}"

def generate_recommendations(test_results: Dict) -> List[str]:
    """Generate recommendations based on test results"""
    recommendations = []
    
    if not test_results['marinetraffic_tiles'][0]:
        recommendations.append(
            "MarineTraffic tile service is not accessible. This was the primary AIS data source. "
            "MarineTraffic has commercialized their API (requires paid subscription)."
        )
    
    if test_results['aishub_api'][0]:
        recommendations.append(
            "AISHub.net API is accessible and was mentioned as an alternative in Issue #63. "
            "Consider migrating to AISHub (requires registration and data sharing)."
        )
    
    if test_results['aisstream'][0]:
        recommendations.append(
            "AISstream.io is accessible. This is a modern WebSocket-based AIS provider. "
            "Consider this as a potential alternative data source."
        )
    
    if not any(test_results['openseamap_endpoints'].values()):
        recommendations.append(
            "OpenSeaMap API endpoints are not responding. This could indicate server issues."
        )
    
    if not recommendations:
        recommendations.append(
            "All services appear accessible. The issue may be in the client-side JavaScript "
            "or in API authentication/credentials."
        )
    
    return recommendations

def main():
    """Main diagnostic routine"""
    print(f"\n{Colors.BOLD}OpenSeaMap AIS Service Diagnostic Tool{Colors.RESET}")
    print(f"Run at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python: {sys.version.split()[0]}\n")
    
    test_results = {}
    
    # Test 1: DNS Resolution
    print_section("DNS Resolution Check")
    critical_domains = [
        'map.openseamap.org',
        'tiles.marinetraffic.com',
        'data.aishub.net',
        'aisstream.io'
    ]
    
    dns_results = check_dns_resolution(critical_domains)
    for domain, (success, message) in dns_results.items():
        print_status("OK" if success else "FAIL", f"{domain}: {message}")
    
    # Test 2: MarineTraffic (Historical Data Source)
    print_section("MarineTraffic Service (Historical Provider)")
    success, message = test_marinetraffic_tiles(51.5074, -0.1278, 10)  # London
    test_results['marinetraffic_tiles'] = (success, message)
    print_status("OK" if success else "FAIL", f"Tile service: {message}")
    
    success, message = test_marinetraffic_api_simple()
    test_results['marinetraffic_web'] = (success, message)
    print_status("OK" if success else "FAIL", f"Website: {message}")
    
    # Test 3: Alternative AIS Sources
    print_section("Alternative AIS Data Sources")
    
    success, message = test_aishub_api()
    test_results['aishub_api'] = (success, message)
    print_status("OK" if success else "FAIL", f"AISHub.net: {message}")
    
    success, message = test_aisstream_websocket()
    test_results['aisstream'] = (success, message)
    print_status("OK" if success else "FAIL", f"AISstream.io: {message}")
    
    # Test 4: OpenSeaMap Infrastructure
    print_section("OpenSeaMap Infrastructure")
    osm_results = test_openseamap_api_endpoints()
    test_results['openseamap_endpoints'] = osm_results
    
    for endpoint, (success, message) in osm_results.items():
        print_status("OK" if success else "FAIL", f"{endpoint}: {message}")
    
    # Test 5: GitHub Issues
    print_section("GitHub Repository Analysis")
    success, message = analyze_github_issues()
    test_results['github_issues'] = (success, message)
    print_status("INFO", message)
    
    # Generate Report
    print_section("Diagnostic Summary & Recommendations")
    
    recommendations = generate_recommendations(test_results)
    
    for i, rec in enumerate(recommendations, 1):
        print(f"\n{Colors.YELLOW}{i}.{Colors.RESET} {rec}")
    
    # Next Steps
    print_section("Suggested Next Steps")
    print(f"""
1. {Colors.BOLD}Verify the root cause:{Colors.RESET}
   - MarineTraffic tile service appears to be the primary issue
   - The service has moved to a paid API model
   
2. {Colors.BOLD}Check OpenSeaMap GitHub:{Colors.RESET}
   - Review Issue #63: "Investigate alternative AIS layer"
   - Check for recent commits about AIS implementation
   - URL: https://github.com/OpenSeaMap/online_chart/issues/63

3. {Colors.BOLD}Test alternative data sources:{Colors.RESET}
   - Register for AISHub.net account (requires sharing AIS data)
   - Investigate AISstream.io API
   - Check if other free AIS APIs are available

4. {Colors.BOLD}Examine client-side code:{Colors.RESET}
   - Inspect the map page's JavaScript console for errors
   - Check network tab for failed API requests
   - Look at index.php for hardcoded endpoints

5. {Colors.BOLD}Contact maintainers:{Colors.RESET}
   - Email support with diagnostic results
   - Post in the forum: https://forum.openseamap.org
   - Open a GitHub issue if none exists

6. {Colors.BOLD}Consider contributing:{Colors.RESET}
   - Propose a pull request with alternative AIS source
   - Help migrate to AISHub or another provider
    """)
    
    # Save detailed report
    report_file = f"ais_diagnostic_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'test_results': {
                k: {'success': v[0], 'message': v[1]} 
                for k, v in test_results.items() 
                if not isinstance(v, dict)
            },
            'openseamap_endpoints': {
                k: {'success': v[0], 'message': v[1]}
                for k, v in test_results['openseamap_endpoints'].items()
            },
            'recommendations': recommendations
        }, f, indent=2)
    
    print(f"\n{Colors.GREEN}Detailed report saved to: {report_file}{Colors.RESET}\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Diagnostic interrupted by user{Colors.RESET}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.RED}Fatal error: {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
