import time
from crawler.crawler import get_links, rank_urls, get_links_parallel

WEBSITE_URL = "https://www.microsoft.com/en-in"
TOP_N = 10

start_time = time.time()
all_content = {}

links = get_links(WEBSITE_URL)
print(f"\nTotal Links Found: {len(links)}")

ranked_links = rank_urls(links)
top_urls = [url for score, url in ranked_links[:TOP_N]]

print("\nTop Ranked URLs:\n")
for score, url in ranked_links[:TOP_N]:
    print(f"Score: {score} | {url}")

print(f"\n--- Spawning parallel downloads for top {TOP_N} pages ---")
parallel_results = get_links_parallel(top_urls, max_workers=10)

print("\n--- Summary of Discovered Structures ---")
for parent_url, child_links in parallel_results.items():
    print(f"-> {parent_url} contained {len(child_links)} links.")



end_time = time.time()
print(f"\nDiscovery Time: {end_time - start_time:.2f} seconds")