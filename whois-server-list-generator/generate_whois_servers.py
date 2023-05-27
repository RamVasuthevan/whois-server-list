import csv
import os
import time
import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass
from typing import Optional, Union, List

@dataclass
class Result:
    tld_punycode: str
    whois_server_url: str
    tld_unicode: Optional[Union[None,str]] = None    


def create_csv(results:List[Result]):
    HEADERS = ['Domain', 'WHOIS Server URL']
    FILENAME = 'whois-servers.csv'

    with open(FILENAME, 'w', newline='', encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(HEADERS)
        writer.writerows(((result.tld_punycode,result.whois_server_url) for result in results))


def create_markdown(results:List[Result]):
    FILENAME = 'whois-servers.md'

    with open(FILENAME, 'w', newline='', encoding="utf-8") as file:
        file.write("| Domain   | WHOIS Server URL          |\n")
        file.write("|----------|--------------------------|\n")
        for result in results:
            file.write(f"| {result.tld_punycode} | {result.whois_server_url} |\n")           


def create_README(results:List[Result]):
    BEFORE_FILENAME = 'whois-server-list-generator/README/before.md'
    AFTER_FILENAME = 'whois-server-list-generator/README/after.md'
    README_FILENAME = 'README.md'

    with open(BEFORE_FILENAME, 'r', encoding="utf-8") as before_file:
        before_content = before_file.read()

    markdown_content = "| Domain   | WHOIS Server URL          |\n"
    markdown_content += "|----------|--------------------------|\n"
    for result in results:
        if result.tld_punycode == result.tld_unicode.lower():
            markdown_content+=(f"| .{result.tld_punycode} | https://{result.whois_server_url} |\n")
        else:
            markdown_content+=(f"| .{result.tld_punycode} (.{result.tld_unicode}) | https://{result.whois_server_url} |\n")

    with open(AFTER_FILENAME, 'r', encoding="utf-8") as after_file:
        after_content = after_file.read()

    readme_content = before_content + markdown_content + after_content

    with open(README_FILENAME, 'w', encoding="utf-8") as readme_file:
        readme_file.write(readme_content)


if __name__ == "__main__":
    MAX_RETRIES = 3
    TIMEOUT = 10
    SLEEP = 1

    BASE_IANA_URL = 'https://www.iana.org'
    ROOT_ZONE_DATABASE_URL = BASE_IANA_URL + '/domains/root/db'

    retry_count = 0

    while retry_count < MAX_RETRIES:
        try:
            response = requests.get(ROOT_ZONE_DATABASE_URL, timeout=TIMEOUT)
            response.raise_for_status()
            break
        except requests.exceptions.RequestException:
            print("Error occurred while fetching root zone database. Retrying...")
            retry_count += 1
            time.sleep(SLEEP)

    if response and response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        table = soup.find('table', id='tld-table')
        results = []

        for tr in table.tbody.find_all('tr'):
            relative_tld_url = tr.td.span.a.get('href')
            tld_punycode = os.path.splitext(os.path.basename(relative_tld_url))[0]
            print(tld_punycode)

            retry_count = 0

            while retry_count < MAX_RETRIES:
                try:
                    response = requests.get(BASE_IANA_URL + relative_tld_url, timeout=TIMEOUT)
                    response.raise_for_status()
                    break
                except requests.exceptions.RequestException:
                    print(f"Error occurred while fetching {tld_punycode}. Retrying...")
                    retry_count += 1
                    time.sleep(SLEEP)

            if response and response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                tld_unicode=soup.find('h1').text.split('.')[-1].strip()
                registry_information = soup.find('h2', string='Registry Information').find_next('p')

                if registry_information.find('b', string='WHOIS Server:'):
                    whois_url = registry_information.find('b', string='WHOIS Server:').next_sibling.strip()
                    results.append(Result(tld_punycode,whois_url,tld_unicode))
            else:
                print(
                    f"Error occurred while fetching {tld_punycode}. Status Code: {response.status_code}")
                response.raise_for_status()

            time.sleep(SLEEP)

    create_csv(results)
    create_markdown(results)
    create_README(results)
