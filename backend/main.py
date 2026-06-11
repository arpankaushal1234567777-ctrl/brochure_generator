from crawler.crawler import crawl

visited = set()

crawl("https://www.ril.com", visited)

print("\nTotal Pages Visited:", len(visited))
