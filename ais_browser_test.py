#!/usr/bin/env python3
"""
OpenSeaMap Browser-Based AIS Test Script

This script uses Selenium to load the actual OpenSeaMap interface,
enable the AIS layer, and monitor network requests to identify failures.

Requirements:
    pip install selenium requests beautifulsoup4
    
Also requires Chrome/Chromium and chromedriver installed.
"""

import sys
import json
import time
from datetime import datetime
from typing import List, Dict, Optional

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
except ImportError:
    print("ERROR: Selenium not installed. Install with: pip install selenium")
    sys.exit(1)

class OpenSeaMapAISMonitor:
    """Monitor OpenSeaMap's AIS layer functionality"""
    
    def __init__(self, headless: bool = False, verbose: bool = True):
        self.headless = headless
        self.verbose = verbose
        self.driver = None
        self.network_logs = []
        
    def setup_driver(self):
        """Initialize Chrome driver with logging capabilities"""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument('--headless')
        
        # Enable performance logging to capture network requests
        chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            if self.verbose:
                print("✓ Chrome WebDriver initialized successfully")
            return True
        except Exception as e:
            print(f"✗ Failed to initialize Chrome WebDriver: {e}")
            print("\nPlease ensure you have:")
            print("  1. Chrome or Chromium browser installed")
            print("  2. ChromeDriver installed (matching your Chrome version)")
            print("     Download from: https://chromedriver.chromium.org/")
            return False
    
    def load_openseamap(self, url: str = "https://map.openseamap.org") -> bool:
        """Load the OpenSeaMap website"""
        try:
            if self.verbose:
                print(f"\n→ Loading {url}...")
            
            self.driver.get(url)
            
            # Wait for map to initialize
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.ID, "map"))
            )
            
            if self.verbose:
                print("✓ Map container loaded")
            
            time.sleep(3)  # Give JavaScript time to initialize
            return True
            
        except TimeoutException:
            print("✗ Timeout waiting for map to load")
            return False
        except Exception as e:
            print(f"✗ Error loading OpenSeaMap: {e}")
            return False
    
    def find_ais_checkbox(self) -> Optional[object]:
        """Locate the AIS layer checkbox"""
        possible_selectors = [
            ("ID", "checkLayerAis"),
            ("CSS", "input[id='checkLayerAis']"),
            ("XPATH", "//input[@type='checkbox' and contains(@id, 'Ais')]"),
            ("XPATH", "//label[contains(text(), 'Marine Traffic')]/../input"),
            ("XPATH", "//label[contains(text(), 'AIS')]/../input"),
        ]
        
        for selector_type, selector in possible_selectors:
            try:
                if selector_type == "ID":
                    element = self.driver.find_element(By.ID, selector)
                elif selector_type == "CSS":
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                elif selector_type == "XPATH":
                    element = self.driver.find_element(By.XPATH, selector)
                
                if element:
                    if self.verbose:
                        print(f"✓ Found AIS checkbox using {selector_type}: {selector}")
                    return element
            except NoSuchElementException:
                continue
        
        return None
    
    def enable_ais_layer(self) -> bool:
        """Enable the AIS tracking layer"""
        try:
            # First, try to find and click the View menu
            try:
                view_menu = self.driver.find_element(By.XPATH, 
                    "//img[@alt='view']/..")
                if self.verbose:
                    print("→ Opening View menu...")
                view_menu.click()
                time.sleep(1)
            except:
                if self.verbose:
                    print("→ View menu not found or already open")
            
            # Find the AIS checkbox
            ais_checkbox = self.find_ais_checkbox()
            
            if not ais_checkbox:
                print("✗ Could not locate AIS checkbox")
                return False
            
            # Check if already enabled
            if ais_checkbox.is_selected():
                if self.verbose:
                    print("→ AIS layer already enabled")
            else:
                if self.verbose:
                    print("→ Enabling AIS layer...")
                ais_checkbox.click()
                time.sleep(2)
            
            return True
            
        except Exception as e:
            print(f"✗ Error enabling AIS layer: {e}")
            return False
    
    def capture_network_logs(self, duration: int = 10) -> List[Dict]:
        """Capture network activity for specified duration"""
        if self.verbose:
            print(f"\n→ Monitoring network traffic for {duration} seconds...")
        
        start_time = time.time()
        relevant_requests = []
        
        while time.time() - start_time < duration:
            logs = self.driver.get_log('performance')
            
            for log in logs:
                try:
                    log_data = json.loads(log['message'])
                    message = log_data.get('message', {})
                    method = message.get('method', '')
                    
                    if method == 'Network.requestWillBeSent':
                        params = message.get('params', {})
                        request = params.get('request', {})
                        url = request.get('url', '')
                        
                        # Filter for AIS-related requests
                        if any(keyword in url.lower() for keyword in [
                            'ais', 'marine', 'traffic', 'ship', 'vessel', 
                            'getais', 'marinetraffic', 'aishub', 'aisstream'
                        ]):
                            relevant_requests.append({
                                'timestamp': datetime.now().isoformat(),
                                'url': url,
                                'method': request.get('method', ''),
                                'requestId': params.get('requestId', '')
                            })
                            
                            if self.verbose:
                                print(f"  → Request: {url[:80]}...")
                    
                    elif method == 'Network.responseReceived':
                        params = message.get('params', {})
                        response = params.get('response', {})
                        url = response.get('url', '')
                        
                        if any(keyword in url.lower() for keyword in [
                            'ais', 'marine', 'traffic', 'ship', 'vessel'
                        ]):
                            status = response.get('status', 0)
                            status_text = response.get('statusText', '')
                            
                            # Update the matching request with response info
                            request_id = params.get('requestId', '')
                            for req in relevant_requests:
                                if req.get('requestId') == request_id:
                                    req['status'] = status
                                    req['status_text'] = status_text
                                    req['content_type'] = response.get('mimeType', '')
                                    
                                    if self.verbose:
                                        symbol = "✓" if 200 <= status < 300 else "✗"
                                        print(f"  {symbol} Response: {status} {status_text}")
                    
                    elif method == 'Network.loadingFailed':
                        params = message.get('params', {})
                        request_id = params.get('requestId', '')
                        error_text = params.get('errorText', '')
                        
                        for req in relevant_requests:
                            if req.get('requestId') == request_id:
                                req['failed'] = True
                                req['error'] = error_text
                                
                                if self.verbose:
                                    print(f"  ✗ Request failed: {error_text}")
                
                except json.JSONDecodeError:
                    continue
                except Exception as e:
                    if self.verbose:
                        print(f"  Warning: Error parsing log: {e}")
            
            time.sleep(0.5)
        
        return relevant_requests
    
    def check_javascript_errors(self) -> List[str]:
        """Check for JavaScript errors in the browser console"""
        try:
            logs = self.driver.get_log('browser')
            errors = []
            
            for log in logs:
                if log['level'] in ['SEVERE', 'ERROR']:
                    errors.append(f"{log['level']}: {log['message']}")
            
            if errors and self.verbose:
                print(f"\n✗ Found {len(errors)} JavaScript errors:")
                for error in errors[:5]:  # Show first 5
                    print(f"  - {error[:150]}...")
            elif self.verbose:
                print("\n✓ No JavaScript errors detected")
            
            return errors
            
        except Exception as e:
            print(f"Warning: Could not retrieve browser logs: {e}")
            return []
    
    def take_screenshot(self, filename: str = None):
        """Save a screenshot of the current state"""
        if not filename:
            filename = f"openseamap_ais_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        
        try:
            self.driver.save_screenshot(filename)
            if self.verbose:
                print(f"✓ Screenshot saved: {filename}")
            return filename
        except Exception as e:
            print(f"✗ Failed to save screenshot: {e}")
            return None
    
    def analyze_results(self, network_requests: List[Dict], js_errors: List[str]) -> Dict:
        """Analyze collected data and generate findings"""
        analysis = {
            'timestamp': datetime.now().isoformat(),
            'ais_requests_found': len(network_requests),
            'successful_requests': 0,
            'failed_requests': 0,
            'blocked_requests': 0,
            'javascript_errors': len(js_errors),
            'findings': [],
            'raw_requests': network_requests,
            'raw_errors': js_errors
        }
        
        # Analyze network requests
        for req in network_requests:
            if req.get('failed'):
                analysis['failed_requests'] += 1
                analysis['findings'].append(
                    f"FAILED REQUEST: {req['url']} - {req.get('error', 'Unknown error')}"
                )
            elif 'status' in req:
                if 200 <= req['status'] < 300:
                    analysis['successful_requests'] += 1
                elif req['status'] in [401, 403]:
                    analysis['blocked_requests'] += 1
                    analysis['findings'].append(
                        f"BLOCKED REQUEST: {req['url']} - HTTP {req['status']} {req.get('status_text')}"
                    )
                else:
                    analysis['failed_requests'] += 1
                    analysis['findings'].append(
                        f"HTTP ERROR: {req['url']} - {req['status']} {req.get('status_text')}"
                    )
        
        # Determine root cause
        if analysis['ais_requests_found'] == 0:
            analysis['root_cause'] = "No AIS requests detected - layer may not be implemented or checkbox not functioning"
        elif analysis['blocked_requests'] > 0:
            analysis['root_cause'] = "AIS requests are being blocked (401/403) - API likely requires authentication"
        elif analysis['failed_requests'] > 0:
            analysis['root_cause'] = "AIS requests are failing - check network connectivity or API endpoint changes"
        elif analysis['successful_requests'] > 0:
            analysis['root_cause'] = "AIS requests successful - issue may be in data rendering/display"
        else:
            analysis['root_cause'] = "Unable to determine - requests made but no responses captured"
        
        return analysis
    
    def run_full_diagnostic(self) -> Dict:
        """Run complete diagnostic test"""
        print("\n" + "="*70)
        print("OpenSeaMap AIS Browser-Based Diagnostic".center(70))
        print("="*70 + "\n")
        
        if not self.setup_driver():
            return {'error': 'Failed to initialize WebDriver'}
        
        try:
            # Load the map
            if not self.load_openseamap():
                return {'error': 'Failed to load OpenSeaMap'}
            
            # Enable AIS layer
            if not self.enable_ais_layer():
                print("\nNote: Could not enable AIS layer via checkbox")
                print("Continuing to monitor for any AIS-related activity...")
            
            # Capture network activity
            network_requests = self.capture_network_logs(duration=15)
            
            # Check for JavaScript errors
            js_errors = self.check_javascript_errors()
            
            # Take screenshot
            screenshot = self.take_screenshot()
            
            # Analyze results
            analysis = self.analyze_results(network_requests, js_errors)
            analysis['screenshot'] = screenshot
            
            # Print summary
            print("\n" + "="*70)
            print("DIAGNOSTIC SUMMARY".center(70))
            print("="*70)
            print(f"\nAIS Requests Detected: {analysis['ais_requests_found']}")
            print(f"Successful Responses:  {analysis['successful_requests']}")
            print(f"Failed Requests:       {analysis['failed_requests']}")
            print(f"Blocked Requests:      {analysis['blocked_requests']}")
            print(f"JavaScript Errors:     {analysis['javascript_errors']}")
            print(f"\nRoot Cause Assessment:")
            print(f"  {analysis['root_cause']}")
            
            if analysis['findings']:
                print(f"\nKey Findings:")
                for finding in analysis['findings'][:5]:
                    print(f"  - {finding}")
            
            # Save detailed report
            report_file = f"browser_diagnostic_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w') as f:
                json.dump(analysis, f, indent=2)
            print(f"\nDetailed report saved: {report_file}")
            
            return analysis
            
        finally:
            if self.driver:
                self.driver.quit()
                if self.verbose:
                    print("\n✓ Browser closed")

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Test OpenSeaMap AIS functionality using browser automation'
    )
    parser.add_argument('--headless', action='store_true',
                       help='Run browser in headless mode')
    parser.add_argument('--quiet', action='store_true',
                       help='Reduce output verbosity')
    
    args = parser.parse_args()
    
    monitor = OpenSeaMapAISMonitor(
        headless=args.headless,
        verbose=not args.quiet
    )
    
    try:
        results = monitor.run_full_diagnostic()
        
        # Exit with appropriate code
        if 'error' in results:
            sys.exit(1)
        elif results.get('failed_requests', 0) > 0 or results.get('blocked_requests', 0) > 0:
            sys.exit(2)  # Tests ran but issues detected
        else:
            sys.exit(0)  # Success
            
    except KeyboardInterrupt:
        print("\n\nDiagnostic interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()