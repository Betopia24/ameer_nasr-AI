#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup
import time
import random
from datetime import datetime, timedelta
import urllib.parse
import re

class TravelAIAgent:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })

    def scrape_flights(self, origin, destination, departure_date, return_date, travelers):
        print(f"🔍 Scraping flights from {origin} to {destination}...")
        
        flights_found = {
            'outbound': None,
            'return': None,
            'sources_tried': []
        }
        
        # Try multiple flight search engines
        search_engines = [
            {
                'name': 'Kayak',
                'url_template': 'https://www.kayak.com/flights/{origin}-{destination}/{departure_formatted}/{return_formatted}/{travelers}adults',
                'selectors': [
                    '[data-resultid] .price',
                    '.resultsPrice',
                    '.price-text',
                    '[class*="price"]',
                    '[class*="flight"]'
                ]
            },
            {
                'name': 'Expedia',
                'url_template': 'https://www.expedia.com/Flights-Search?trip=roundtrip&leg1=from:{origin},to:{destination},departure:{departure_date}&leg2=from:{destination},to:{origin},departure:{return_date}&passengers=adults:{travelers}',
                'selectors': [
                    '[data-test-id*="price"]',
                    '.price-amount',
                    '[class*="flight-info"]',
                    '[class*="airline"]'
                ]
            },
            {
                'name': 'Skyscanner',
                'url_template': 'https://www.skyscanner.com/transport/flights/{origin}/{destination}/{departure_formatted}/{return_formatted}/?adults={travelers}&children=0&adultsv2={travelers}&childrenv2=&infants=0&cabinclass=economy&rtn=1&preferdirects=false&outboundaltsenabled=false&inboundaltsenabled=false',
                'selectors': [
                    '[data-testid*="price"]',
                    '.Price_mainPriceContainer',
                    '[class*="flight"]',
                    '[class*="airline"]'
                ]
            }
        ]
        
        departure_formatted = departure_date.replace('-', '')
        return_formatted = return_date.replace('-', '')
        
        for engine in search_engines:
            try:
                url = engine['url_template'].format(
                    origin=origin,
                    destination=destination,
                    departure_date=departure_date,
                    return_date=return_date,
                    departure_formatted=departure_formatted,
                    return_formatted=return_formatted,
                    travelers=travelers
                )
                
                print(f"📱 Trying {engine['name']}: {url[:100]}...")
                flights_found['sources_tried'].append(f"{engine['name']}: {url}")
                
                response = self.session.get(url, timeout=15)
                print(f"   Status: {response.status_code}")
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Look for actual flight data
                    flight_data = self.extract_flight_info(soup, engine['selectors'])
                    
                    if flight_data['flights_found']:
                        print(f"✅ Found {len(flight_data['flights_found'])} flights on {engine['name']}")
                        for flight in flight_data['flights_found']:
                            print(f"   - {flight}")
                        
                        # Use first valid flight found
                        if not flights_found['outbound']:
                            flights_found['outbound'] = {
                                'raw_data': flight_data['flights_found'],
                                'source': engine['name'],
                                'url': url
                            }
                        break
                    else:
                        print(f"⚠️ No flight data extracted from {engine['name']}")
                else:
                    print(f"⚠️ {engine['name']} returned status {response.status_code}")
                    
            except Exception as e:
                print(f"⚠️ {engine['name']} failed: {str(e)[:100]}")
            
            time.sleep(3)  # Be respectful to servers
        
        return flights_found

    def extract_flight_info(self, soup, selectors):
        flights_found = []
        
        # Try different selectors to find flight information
        for selector in selectors:
            try:
                elements = soup.select(selector)
                for elem in elements[:10]:  # Limit to first 10 results
                    text = elem.get_text(strip=True)
                    if text and len(text) > 2:
                        # Look for patterns that might indicate flights
                        if any(keyword in text.lower() for keyword in ['$', 'flight', 'airline', 'price', 'am', 'pm']):
                            flights_found.append(text)
            except:
                continue
        
        # Also look for airline names and flight numbers in the page
        airline_patterns = [
            r'(American|Delta|United|Southwest|JetBlue|Alaska|Spirit|Frontier|Allegiant)\s*(Airlines?)?',
            r'[A-Z]{2}\s*\d{3,4}',  # Flight number pattern
            r'\$\d{2,4}',  # Price pattern
        ]
        
        page_text = soup.get_text()
        for pattern in airline_patterns:
            matches = re.findall(pattern, page_text, re.IGNORECASE)
            flights_found.extend([match[0] if isinstance(match, tuple) else match for match in matches[:5]])
        
        return {
            'flights_found': list(set(flights_found)),  # Remove duplicates
            'total_elements_checked': len(soup.find_all(['div', 'span', 'p']))
        }

    def scrape_hotels(self, destination, check_in, check_out, travelers, accommodation_type, budget):
        print(f"🏨 Scraping hotels in {destination}...")
        
        hotels_found = {
            'hotels': [],
            'sources_tried': []
        }
        
        search_engines = [
            {
                'name': 'Booking.com',
                'url_template': 'https://www.booking.com/searchresults.html?ss={destination}&checkin={check_in}&checkout={check_out}&group_adults={travelers}&no_rooms=1',
                'selectors': [
                    '[data-testid="title"]',
                    '.sr-hotel__name',
                    '[data-testid="property-card-name"]',
                    'h3[data-testid="title"]',
                    '.fcab3ed991.a23c043802'
                ]
            },
            {
                'name': 'Hotels.com',
                'url_template': 'https://www.hotels.com/search.do?resolved-location=CITY:{destination}&q-destination={destination}&q-check-in={check_in}&q-check-out={check_out}&q-rooms=1&q-room-0-adults={travelers}&q-room-0-children=0',
                'selectors': [
                    '[data-stid="content-hotel-title"]',
                    '.hotel-name',
                    'h3[class*="name"]'
                ]
            },
            {
                'name': 'Expedia Hotels',
                'url_template': 'https://www.expedia.com/Hotel-Search?destination={destination}&startDate={check_in}&endDate={check_out}&rooms=1&adults={travelers}',
                'selectors': [
                    '[data-stid="content-hotel-title"]',
                    '.hotel-name',
                    'h3[data-testid="property-name"]'
                ]
            }
        ]
        
        destination_encoded = urllib.parse.quote(destination)
        
        for engine in search_engines:
            try:
                url = engine['url_template'].format(
                    destination=destination_encoded,
                    check_in=check_in,
                    check_out=check_out,
                    travelers=travelers
                )
                
                print(f"📱 Trying {engine['name']}: {url[:100]}...")
                hotels_found['sources_tried'].append(f"{engine['name']}: {url}")
                
                response = self.session.get(url, timeout=15)
                print(f"   Status: {response.status_code}")
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    hotel_data = self.extract_hotel_info(soup, engine['selectors'])
                    
                    if hotel_data['hotels_found']:
                        print(f"✅ Found {len(hotel_data['hotels_found'])} hotels on {engine['name']}")
                        for hotel in hotel_data['hotels_found'][:5]:
                            print(f"   - {hotel}")
                        
                        hotels_found['hotels'].extend([{
                            'name': hotel,
                            'source': engine['name'],
                            'url': url
                        } for hotel in hotel_data['hotels_found'][:3]])
                        
                        if len(hotels_found['hotels']) >= 3:
                            break
                    else:
                        print(f"⚠️ No hotel data extracted from {engine['name']}")
                else:
                    print(f"⚠️ {engine['name']} returned status {response.status_code}")
                    
            except Exception as e:
                print(f"⚠️ {engine['name']} failed: {str(e)[:100]}")
            
            time.sleep(3)
        
        return hotels_found

    def extract_hotel_info(self, soup, selectors):
        hotels_found = []
        
        for selector in selectors:
            try:
                elements = soup.select(selector)
                for elem in elements[:10]:
                    text = elem.get_text(strip=True)
                    if text and len(text) > 5 and len(text) < 100:
                        # Filter out obvious non-hotel names
                        if not any(skip in text.lower() for skip in ['book now', 'search', 'filter', 'sort', 'map', 'list']):
                            hotels_found.append(text)
            except:
                continue
        
        # Also search for hotel-like terms in the page
        hotel_patterns = [
            r'([A-Z][a-z]+\s+)*(Hotel|Resort|Inn|Suites?|Lodge|Motel)(\s+[A-Z][a-z]+)*',
            r'([A-Z][a-z]+\s+)*\b(Grand|Luxury|Premium|Boutique|Historic)\s+\w+',
        ]
        
        page_text = soup.get_text()
        for pattern in hotel_patterns:
            matches = re.findall(pattern, page_text)
            for match in matches[:5]:
                hotel_name = match[0] + match[1] + match[2] if isinstance(match, tuple) else match
                if len(hotel_name.strip()) > 5:
                    hotels_found.append(hotel_name.strip())
        
        return {
            'hotels_found': list(set(hotels_found))[:10],  # Remove duplicates, limit to 10
        }

    def scrape_activities(self, destination, interests, budget):
        print(f"🎯 Scraping activities in {destination}...")
        
        activities_found = {
            'activities': [],
            'sources_tried': []
        }
        
        search_engines = [
            {
                'name': 'TripAdvisor',
                'url_template': 'https://www.tripadvisor.com/Attractions-g{location_id}-Activities-{destination}.html',
                'selectors': [
                    '[data-test-target="attraction-review-title"]',
                    '.listing_title',
                    '.attraction_name'
                ]
            },
            {
                'name': 'Viator',
                'url_template': 'https://www.viator.com/{destination}/tours',
                'selectors': [
                    '[data-testid="product-title"]',
                    '.product-title',
                    'h3[class*="title"]'
                ]
            }
        ]
        
        destination_encoded = urllib.parse.quote(destination.replace(' ', '-'))
        
        for engine in search_engines:
            try:
                url = engine['url_template'].format(
                    destination=destination_encoded,
                    location_id=random.randint(100000, 999999)  # Placeholder for location ID
                )
                
                print(f"📱 Trying {engine['name']}: {url[:100]}...")
                activities_found['sources_tried'].append(f"{engine['name']}: {url}")
                
                response = self.session.get(url, timeout=15)
                print(f"   Status: {response.status_code}")
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    activity_data = self.extract_activity_info(soup, engine['selectors'])
                    
                    if activity_data['activities_found']:
                        print(f"✅ Found {len(activity_data['activities_found'])} activities on {engine['name']}")
                        for activity in activity_data['activities_found'][:5]:
                            print(f"   - {activity}")
                        
                        activities_found['activities'].extend([{
                            'name': activity,
                            'source': engine['name'],
                            'url': url
                        } for activity in activity_data['activities_found'][:5]])
                        
                        if len(activities_found['activities']) >= 5:
                            break
                    else:
                        print(f"⚠️ No activity data extracted from {engine['name']}")
                        
            except Exception as e:
                print(f"⚠️ {engine['name']} failed: {str(e)[:100]}")
            
            time.sleep(3)
        
        return activities_found

    def extract_activity_info(self, soup, selectors):
        activities_found = []
        
        for selector in selectors:
            try:
                elements = soup.select(selector)
                for elem in elements[:15]:
                    text = elem.get_text(strip=True)
                    if text and len(text) > 5 and len(text) < 100:
                        activities_found.append(text)
            except:
                continue
        
        return {
            'activities_found': list(set(activities_found))[:10]
        }

    def generate_itinerary(self, questionnaire):
        print('\n🤖 Starting real-time web scraping for your trip...')
        print('=' * 60)
        
        destination = questionnaire['destination']
        origin = questionnaire['origin']
        departure_date = questionnaire['departure_date']
        return_date = questionnaire['return_date']
        duration = questionnaire['duration']
        travelers = questionnaire['travelers']
        interests = questionnaire['interests']
        budget = questionnaire['budget']
        accommodation_type = questionnaire['accommodation_type']

        print(f"\n🌐 Scraping live data from travel websites...")
        
        # Scrape real data only
        flights = self.scrape_flights(origin, destination, departure_date, return_date, travelers)
        hotels = self.scrape_hotels(destination, departure_date, return_date, travelers, accommodation_type, budget)
        activities = self.scrape_activities(destination, interests, budget)

        print("\n" + "="*60)
        print("🔍 SCRAPING RESULTS - REAL DATA ONLY")
        print("="*60)
        
        # Display only what was actually found
        print("\n✈️ FLIGHTS FOUND:")
        if flights['outbound'] and flights['outbound']['raw_data']:
            print(f"   Source: {flights['outbound']['source']}")
            for flight_info in flights['outbound']['raw_data'][:10]:
                print(f"   - {flight_info}")
            print(f"   🔗 {flights['outbound']['url']}")
        else:
            print("   ❌ No flight data successfully scraped")
        
        print(f"\n   Sources attempted:")
        for source in flights['sources_tried']:
            print(f"   - {source}")
        
        print("\n🏨 HOTELS FOUND:")
        if hotels['hotels']:
            for hotel in hotels['hotels'][:5]:
                print(f"   - {hotel['name']} (from {hotel['source']})")
            if hotels['hotels']:
                print(f"   🔗 {hotels['hotels'][0]['url']}")
        else:
            print("   ❌ No hotel data successfully scraped")
            
        print(f"\n   Sources attempted:")
        for source in hotels['sources_tried']:
            print(f"   - {source}")
        
        print("\n🎯 ACTIVITIES FOUND:")
        if activities['activities']:
            for activity in activities['activities'][:8]:
                print(f"   - {activity['name']} (from {activity['source']})")
            if activities['activities']:
                print(f"   🔗 {activities['activities'][0]['url']}")
        else:
            print("   ❌ No activity data successfully scraped")
            
        print(f"\n   Sources attempted:")
        for source in activities['sources_tried']:
            print(f"   - {source}")

        print('\n' + '=' * 60)
        print('⚠️  NOTE: Modern travel websites use anti-bot protection')
        print('🤖 Consider using official APIs for production applications')
        print('📊 This shows actual scraping attempts and real results only')
        
        return {
            'flights': flights,
            'hotels': hotels,
            'activities': activities,
            'questionnaire': questionnaire
        }


class QuestionnaireInterface:
    def __init__(self):
        self.agent = TravelAIAgent()

    def collect_questionnaire(self):
        print('🌴 AI Travel Agent - Real Web Scraping Only')
        print('=' * 60)
        print('I\'ll show you ONLY the real data scraped from travel websites\n')

        questionnaire = {}
        
        questionnaire['destination'] = input('Where do you want to go? ')
        questionnaire['origin'] = input('What city are you flying from? ')
        questionnaire['duration'] = input('How many days? ')
        questionnaire['departure_date'] = input('Departure date (YYYY-MM-DD)? ')
        questionnaire['return_date'] = input('Return date (YYYY-MM-DD)? ')
        questionnaire['adults'] = input('Number of adults? ')
        questionnaire['children'] = input('Number of children (0 if none)? ')
        questionnaire['interests'] = input('Your interests (beach, culture, food, nightlife, adventure, nature)? ')
        questionnaire['budget'] = int(input('Budget per person ($)? '))
        questionnaire['accommodation_type'] = input('Accommodation preference (hotel/airbnb/resort)? ')

        questionnaire['travelers'] = int(questionnaire['adults']) + int(questionnaire['children'] or 0)

        return questionnaire

    def run(self):
        try:
            questionnaire = self.collect_questionnaire()
            
            print('\n🚀 Starting live web scraping - NO FALLBACK DATA...')
            results = self.agent.generate_itinerary(questionnaire)
            
        except Exception as e:
            print(f'Error occurred: {str(e)}')


if __name__ == "__main__":
    app = QuestionnaireInterface()
    app.run()