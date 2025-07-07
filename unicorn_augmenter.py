import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime
from typing import List, Dict

class UnicornDataAugmenter:
    def __init__(self, existing_json_file='funding_data.json'):
        self.existing_json_file = existing_json_file
        self.unicorn_url = "https://techcrunch.com/2025/07/06/at-least-36-new-tech-unicorns-were-minted-in-2025-so-far/"
        self.unicorn_data = []
        
    def parse_unicorn_content(self, content: str) -> List[Dict]:
        """Parse the unicorn content and extract structured data"""
        unicorns = []
        
        # Split content by months
        months = ['June', 'May', 'April', 'March', 'February', 'January']
        
        for month in months:
            # Find the section for each month
            month_pattern = rf"## {month}(.*?)(?=## |$)"
            month_match = re.search(month_pattern, content, re.DOTALL)
            
            if month_match:
                month_content = month_match.group(1)
                
                # Extract individual company entries
                company_pattern = r'\*\*(.*?)\*\* --- \$([\d.]+) billion: (.*?)(?=\*\*|$)'
                companies = re.findall(company_pattern, month_content, re.DOTALL)
                
                for company_name, valuation, description in companies:
                    # Extract funding amount from description
                    funding_match = re.search(r'raised.*?\$(\d+(?:\.\d+)?)\s*million', description)
                    funding_amount = f"${funding_match.group(1)} million" if funding_match else None
                    
                    # Extract series information
                    series_match = re.search(r'Series ([A-Z])', description)
                    series = f"Series {series_match.group(1)}" if series_match else None
                    
                    # Extract founding year
                    founded_match = re.search(r'founded in (\d{4})', description)
                    founded_year = founded_match.group(1) if founded_match else None
                    
                    # Extract total funding
                    total_funding_match = re.search(r'raised more than \$(\d+(?:\.\d+)?)\s*million', description)
                    total_funding = f"${total_funding_match.group(1)} million" if total_funding_match else None
                    
                    # Extract investors
                    investors_match = re.search(r'investors.*?including (.*?)\.', description)
                    investors = investors_match.group(1) if investors_match else None
                    
                    # Clean up description
                    clean_description = re.sub(r'\[.*?\]\(.*?\)', '', description)  # Remove markdown links
                    clean_description = re.sub(r'\s+', ' ', clean_description).strip()
                    
                    unicorn_entry = {
                        'source': 'TechCrunch Unicorns 2025',
                        'title': f"{company_name} becomes unicorn with ${valuation} billion valuation",
                        'url': self.unicorn_url,
                        'date': f"2025-{self._month_to_number(month):02d}-01T00:00:00-00:00",
                        'scraped_at': datetime.now().isoformat(),
                        'company_name': company_name,
                        'funding_amount': funding_amount,
                        'valuation': f"${valuation} billion",
                        'series': series,
                        'founded_year': founded_year,
                        'total_funding': total_funding,
                        'investors': investors,
                        'description': clean_description[:200] + "..." if len(clean_description) > 200 else clean_description,
                        'is_recent': True,
                        'is_unicorn': True,
                        'unicorn_month': month,
                        'unicorn_year': '2025'
                    }
                    
                    unicorns.append(unicorn_entry)
        
        return unicorns
    
    def _month_to_number(self, month: str) -> int:
        """Convert month name to number"""
        months = {
            'January': 1, 'February': 2, 'March': 3, 'April': 4,
            'May': 5, 'June': 6, 'July': 7, 'August': 8,
            'September': 9, 'October': 10, 'November': 11, 'December': 12
        }
        return months.get(month, 1)
    
    def scrape_unicorn_data(self) -> List[Dict]:
        """Scrape unicorn data from the provided content"""
        # Since we have the content provided, we'll use it directly
        content = """
        ## June

**Linear** --- $1.25 billion: This [software development product
management tool](https://linear.app/) last raised an $82 million Series
C, valuing the company at $1.25 billion, according to PitchBook. The
company, founded in 2019, has raised more than $130 million in funding
to date from investors, including Accel and Sequoia Capital. 

**Gecko** --- $1.62 billion: This company [makes data-gathering
robotics](https://www.geckorobotics.com/) that climb, crawl, swim, and
fly. Founded in 2013, the company last raised a $121 million Series D,
valuing it at $1.6 billion, according to PitchBook. Gecko has raised
more than $340 million in funding to date from investors, including Cox
Enterprises and Drive Capital. 

**Meter** --- $1.25 billion: This company, which offers [managed
internet infrastructure](https://www.meter.com/) service to enterprises,
last raised a $170 million Series C, valuing the company at $1.25
billion, according to PitchBook. The company, founded in 2015, has
raised more than $250 in funding to date, from investors including
General Catalyst, Sequoia Capital, Sam Altman, and Lachy Groom. 

**Teamworks** --- $1.25 billion: This [sports
software](https://teamworks.com/) company last raised a $247 million
Series F, valuing the company at $1.25 billion, according to PitchBook.
The company, founded in 2006, has raised more than $400 million in
funding to date from investors, including Seaport Capital and General
Catalyst.  

**Thinking Machines** --- $10 billion: This [AI research
company,](https://thinkingmachines.ai/) founded just last year by OpenAI
alum Mira Murati, raised a $2 billion seed round, valuing the company
at $10 billion, according to PitchBook. The company's investors include
a16z and Nvidia. 

**Kalshi** --- $2 billion: The popular [prediction markets
company,](https://kalshi.com/) founded in 2018, last raised a $185
million Series C, valuing the company at $2 billion, according to
PitchBook. The company has raised more than $290 million in funding to
date, from investors including Sequoia and Global Founders Capital. 

**Decagon** --- $1.5 billion: This [customer service AI agent
company](https://decagon.ai/), founded in 2023, last raised a $131
million Series C, valuing the company at $1.5 billion, according to
PitchBook. The company has raised more than $231 million in funding to
date from investors, including a16z and Accel. 

## May

**Pathos** --- $1.6 billion: This [drug development
company](https://pathos.com/), founded in 2020, last raised a $365
million Series D, valuing the company at $1.6 billion, according to
PitchBook. The company has raised more than $460 million to date from
investors, including General Catalyst and Altimeter Capital Management. 

**Statsig** --- $1.1 billion: This [product development
platform](https://www.statsig.com/), founded in 2021, last raised a
$100 million Series C, valuing the company at $1.1 billion, according
to PitchBook. The company has raised around $153 million to date from
investors, including Sequoia, Madrona, and ICONIQ Growth. 

**SpreeAI** --- $1.5 billion: This [shopping tech
company](https://www.spreeai.com/) last raised an undisclosed round,
according to PitchBook, that valued the company at $1.5 billion. The
company, founded in 2020, has raised more than $20 million to date from
investors, including the Davidson Group. 

**Function** --- $2.5 billion: This [health tech
company](https://www.functionhealth.com/), founded in 2020, last raised
a $200 million round, according to PitchBook, valuing the company at
$2.5 billion. The company has raised more than $250 million in funding
to date from investors, including a16z. 

**Owner** --- $1 billion: This [restaurant marketing software
company](https://www.owner.com/), founded in 2018, last raised a $120
million Series C, valuing the company at $1 billion, per PitchBook. The
company has raised more than $180 million in funding to date from
investors, including Headline, Redpoint Ventures, SaaStr Fund, and
Meritech Capital. 

**Awardco** --- $1 billion: This [employee engagement
platform](https://www.awardco.com/) last raised a $165 million Series
B, valuing the company at $1 billion, per PitchBook. The company,
founded in 2012, has raised more than $230 million in funding to date
from investors, including General Catalyst. 

## April

**Nourish** --- $1 billion: This [dietitian telehealth
company](https://www.usenourish.com/) last raised a $70 million Series
B, according to PitchBook, valuing the company at $1 billion. The
company, founded in 2020, has raised more than $100 million in funding
to date from investors, including Index Ventures and Thrive Capital. 

**Chapter** --- $1.38 billion: This [Medicare guide health tech
company,](https://askchapter.org/) founded in 2013, last raised a $75
million Series D, valuing it at $1.38 billion, according to PitchBook.
The company has raised $186 million in funding to date, with investors
including XYZ Venture Capital and Narya. 

**Threatlocker** --- $1.2 billion: This Orlando-based [data protection
company](https://www.threatlocker.com/) last raised a $60 million
Series E, valuing the company at $1.2 billion, according to PitchBook.
The company, founded in 2017, has raised more than $200 million in
funding to date from investors, including General Atlantic and StepStone
Group. 

**Cyberhaven** --- $1 billion: This [data detection
company](https://www.cyberhaven.com/) last raised a $100 million Series
D in April, according to PitchBook, valuing the company at $1 billion.
The company, launched in 2015, has raised more than $200 million in
funding to date, with investors including Khosla Ventures and Redpoint
Ventures.

## March 

**Fleetio** --- $1.5 billion: This Alabama-based startup creates
software to help make fleet operations easier. It last raised a $454
million Series D at a $1.5 billion valuation, according to PitchBook.
It was launched in 2012 and has raised $624 million in funding to date,
with investors including Elephant and Growth Equity at Goldman Sachs
Alternatives.

**The Bot Company** --- $2 billion: This robotics platform last raised
a $150 million early-stage round, valuing it at $2 billion, according
to PitchBook. The company, which was founded in 2024, has raised $300
million to date in funding. 

**Celestial AI** --- $2.5 billion: The AI company raised a $250
million Series C led by Fidelity that valued the company at $2.5
billion, per Crunchbase. The company, based in California, was launched
in 2020 and counts BlackRock and Engine Ventures as investors. It has
raised more than $580 million in capital to date, per PitchBook. 

**Underdog Fantasy** --- $1.3 billion: The sports gaming company last
raised a $70 million Series C valuing the company at $1.3 billion,
according to Crunchbase. The company, founded in 2020, has raised more
than $100 million in capital to date, per PitchBook. Investors include
Spark Capital. 

**Build Ops** --- $1 billion: This software company last raised a
$122.6 million Series C, valuing it at $1 billion. Build Ops, which
was launched in 2018, has raised $273 million in total, according to
PitchBook, with investors including Founders Fund and Fika Ventures. 

**Insilico Medicine** --- $1 billion: The drug research company raised
a $110 million Series E valuing the company at $1 billion, per
Crunchbase. It launched in 2014, has raised more than $500 million to
date in capital, and counts Lilly Ventures and Value Partners Group as
investors. 

**Olipop** --- $2 billion: This popular probiotic soda company last
raised a $137.9 million Series C at a $1.96 billion valuation. It was
founded in 2018 and has raised $243 million to date, with investors
including Scoop Ventures and J.P. Morgan Growth Equity Partners. 

**Peregrine** --- $2.5 billion: This data analysis and integration
platform, launched in 2017, last raised a $190 million Series C with a
valuation of $2.5 billion. It has raised more than $250 million in
funding to date, according to PitchBook, with investors including
Sequoia and Fifth Down Capital. 

**Assured** --- $1 billion: The AI company helps process claims and
last raised a $23 million Series B, valuing the company at $1 billion.
It was launched in 2019 and has raised a little more than $26 million
to date, with investors including ICONIQ Capital and Kleiner Perkins. 

## February 

**Abridge** --- $2.8 billion: This medtech company, founded in 2018,
last raised a $250 million Series D at a $2.75 billion valuation, per
PitchBook. The company has raised more than $460 million to date in
funding and counts Elad Gil and IVP as investors. 

**OpenEvidence** --- $1 billion: This medtech company, founded in 2017,
last raised a $75 million Series A at a $1 billion valuation, per
PitchBook. The company has raised $135 million to date in funding and
counts Sequoia Capital as an investor. 

**Hightouch** --- $1.2 billion: The data platform, founded in 2018,
last raised an $80 million Series C at a $1.2 billion valuation, per
PitchBook. The company has raised $171 million to date in funding and
counts Sapphire Ventures and Bain Capital Ventures as investors.

## January

**Kikoff** --- $1 billion: This personal finance platform last raised
an undisclosed amount that valued it at $1 billion, according to
PitchBook. The company, founded in 2019, has raised $42.5 million to
date and counts Female Founders Fund, Lightspeed Venture Partners, and
basketballer Steph Curry as investors. 

**Netradyne** --- $1.35 billion: Founded in 2015, this computer vision
startup raised a $90 million Series D valuing it at $1.35 billion, according to Crunchbase. The round was led
by Point72 Ventures.

**Hippocratic AI** --- $1.6 billion: This startup, founded in 2023,
creates healthcare models. It raised a $141 million Series B, valuing it at $1.64 billion, according to Crunchbase. The round was led
by Kleiner Perkins. 

**Truveta** --- $1 billion: This genetic research company raised a $320 million round valuing it at $1 billion, according to
Crunchbase. Founded in 2020, its investors include the CVCs from
Microsoft and Regeneron Pharmaceuticals. 

**Clay** --- $1.25 billion: Founded in 2017, Clay is an AI sales
platform. The company raised a $40 million Series B, valuing it at
$1.25 billion, according to PitchBook. It has raised more than $100
million to date and counts Sequoia, First Round, Boldstar, and Box Group
as investors.  

**Mercor** --- $2 billion: This contract recruiting startup raised a $100 million Series B valuing it at $2 billion. The company, founded
in 2022, counts Felicis, Menlo Ventures, Jack Dorsey, Peter Thiel, and
Anthology Fund as investors. 

**Loft Orbital** --- $1 billion: Founded in 2017, the satellite company raised a $170 million Series C valuing the company at $1 billion,
according to Crunchbase. Investors in the round included Temasek and
Tikehau Capital. 
        """
        
        return self.parse_unicorn_content(content)
    
    def load_existing_data(self) -> List[Dict]:
        """Load existing JSON data"""
        try:
            with open(self.existing_json_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"File {self.existing_json_file} not found. Creating new data.")
            return []
        except json.JSONDecodeError:
            print(f"Error reading {self.existing_json_file}. Creating new data.")
            return []
    
    def augment_data(self) -> List[Dict]:
        """Augment existing data with unicorn data"""
        print("Scraping unicorn data...")
        unicorn_data = self.scrape_unicorn_data()
        print(f"Found {len(unicorn_data)} unicorn companies")
        
        print("Loading existing data...")
        existing_data = self.load_existing_data()
        print(f"Loaded {len(existing_data)} existing records")
        
        # Combine data
        combined_data = existing_data + unicorn_data
        
        print(f"Combined data: {len(combined_data)} total records")
        return combined_data
    
    def save_augmented_data(self, output_file='funding_data_augmented.json'):
        """Save the augmented data to a new JSON file"""
        augmented_data = self.augment_data()
        
        with open(output_file, 'w') as f:
            json.dump(augmented_data, f, indent=2)
        
        print(f"Augmented data saved to {output_file}")
        
        # Also update the original file
        with open(self.existing_json_file, 'w') as f:
            json.dump(augmented_data, f, indent=2)
        
        print(f"Original file {self.existing_json_file} updated")
        
        return augmented_data
    
    def print_summary(self):
        """Print a summary of the unicorn data"""
        unicorn_data = self.scrape_unicorn_data()
        
        print("\n=== UNICORN DATA SUMMARY ===")
        print(f"Total unicorns found: {len(unicorn_data)}")
        
        # Group by month
        by_month = {}
        for unicorn in unicorn_data:
            month = unicorn['unicorn_month']
            if month not in by_month:
                by_month[month] = []
            by_month[month].append(unicorn)
        
        for month in ['June', 'May', 'April', 'March', 'February', 'January']:
            if month in by_month:
                print(f"\n{month} 2025: {len(by_month[month])} unicorns")
                for unicorn in by_month[month]:
                    print(f"  • {unicorn['company_name']}: {unicorn['valuation']} valuation")
        
        # Top valuations
        print("\n=== TOP VALUATIONS ===")
        sorted_unicorns = sorted(unicorn_data, key=lambda x: float(x['valuation'].replace('$', '').replace(' billion', '')), reverse=True)
        for unicorn in sorted_unicorns[:5]:
            print(f"  • {unicorn['company_name']}: {unicorn['valuation']}")

def main():
    """Main function to run the augmentation"""
    augmenter = UnicornDataAugmenter()
    
    # Print summary first
    augmenter.print_summary()
    
    # Save augmented data
    print("\n" + "="*50)
    augmented_data = augmenter.save_augmented_data()
    
    print(f"\nAugmentation complete!")
    print(f"Total records in augmented file: {len(augmented_data)}")

if __name__ == "__main__":
    main()
