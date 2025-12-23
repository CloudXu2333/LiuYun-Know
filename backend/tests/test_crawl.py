from firecrawl import Firecrawl
from tavily import TavilyClient
import json
from datetime import datetime
import concurrent.futures
import threading

# 初始化客户端
firecrawl = Firecrawl(api_key="fc-ba93bcedb1434a6c95291425c0ed0ad6")
tavily_client = TavilyClient("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")

# 搜索配置
query = "人工智能最新进展"
max_results = 5  # 每个源的最大结果数
use_search_and_scrape = False  # 是否使用 Firecrawl 的一体化搜索+抓取功能

# Crawl 爬取配置
enable_deep_crawl = False  # 是否对搜索结果进行深度爬取(爬取整站)
max_crawl_sites = 2  # 最多爬取几个网站
crawl_page_limit = 20  # 每个网站最多爬取多少页

print(f"=" * 60)
print(f"搜索查询: {query}")
print(f"最大结果数: {max_results}")
print(f"一体化模式: {'开启' if use_search_and_scrape else '关闭'}")
print(f"=" * 60)

all_urls = {}
lock = threading.Lock()

# 搜索函数
def tavily_search(query):
    results = []
    try:
        response = tavily_client.search(query=query, max_results=5)
        for result in response.get('results', []):
            results.append({
                'url': result.get('url'),
                'title': result.get('title', 'No title'),
                'snippet': result.get('content', ''),
                'source': 'tavily'
            })
        print(f"✓ Tavily 找到 {len(results)} 个结果")
    except Exception as e:
        print(f"✗ Tavily 搜索失败: {str(e)}")
    return results

def firecrawl_search(query, limit=5):
    """Firecrawl 搜索（仅搜索，不抓取内容）"""
    results = []
    try:
        # 使用官方推荐的参数
        response = firecrawl.search(
            query=query,
            limit=limit,
            # sources=["web", "news"],  # 可选：指定搜索源类型
            # tbs="qdr:w",  # 可选：过去一周的结果
            # location="China",  # 可选：地理位置
        )
        
        # 正确的响应结构：response.web / response.news（直接在 response 对象上）
        # 处理 web 结果
        if hasattr(response, 'web') and response.web:
            for idx, item in enumerate(response.web, 1):
                # SearchResultWeb 对象，直接访问属性
                results.append({
                    'url': item.url if hasattr(item, 'url') else '',
                    'title': item.title if hasattr(item, 'title') else 'No title',
                    'snippet': item.description if hasattr(item, 'description') else '',
                    'source': 'firecrawl-web',
                    'position': idx
                })
        
        # 处理 news 结果
        if hasattr(response, 'news') and response.news:
            for idx, item in enumerate(response.news, 1):
                results.append({
                    'url': item.url if hasattr(item, 'url') else '',
                    'title': item.title if hasattr(item, 'title') else 'No title',
                    'snippet': item.snippet if hasattr(item, 'snippet') else '',
                    'source': 'firecrawl-news',
                    'date': item.date if hasattr(item, 'date') else ''
                })
        
        print(f"✓ Firecrawl 找到 {len(results)} 个结果")
    except Exception as e:
        print(f"✗ Firecrawl 搜索失败: {str(e)}")
        import traceback
        print(f"  详细错误: {traceback.format_exc()}")
    return results

def firecrawl_search_and_scrape(query, limit=3):
    """Firecrawl 一体化搜索+抓取（一次调用完成搜索和内容抓取）"""
    results = []
    try:
        print(f"使用 Firecrawl 一体化模式（搜索+抓取）...")
        response = firecrawl.search(
            query=query,
            limit=limit,
            scrape_options={
                "formats": ["markdown", "links"],  # 获取 markdown 和链接
                # "timeout": 30000,  # 可选：30秒超时
            }
        )
        
        # 处理已包含内容的搜索结果
        if hasattr(response, 'data'):
            data = response.data if not isinstance(response.data, dict) else [response.data]
            for item in data:
                result = {
                    'url': item.get('url') if isinstance(item, dict) else getattr(item, 'url', None),
                    'title': item.get('title', 'No title') if isinstance(item, dict) else getattr(item, 'title', 'No title'),
                    'snippet': item.get('description', '') if isinstance(item, dict) else getattr(item, 'description', ''),
                    'markdown': item.get('markdown', '') if isinstance(item, dict) else getattr(item, 'markdown', ''),
                    'links': item.get('links', []) if isinstance(item, dict) else getattr(item, 'links', []),
                    'source': 'firecrawl-scrape',
                    'scraped_at': datetime.now().isoformat()
                }
                results.append(result)
                print(f"  ✓ {result['title'][:40]}... ({len(result['markdown'])} 字符)")
        
        print(f"✓ Firecrawl 一体化模式完成，获得 {len(results)} 个结果")
    except Exception as e:
        print(f"✗ Firecrawl 一体化模式失败: {str(e)}")
        import traceback
        print(f"  详细错误: {traceback.format_exc()}")
    return results

def deep_crawl_site(base_url, limit=20, site_name=""):
    """深度爬取整个网站（Crawl 功能）"""
    print(f"\n{'='*60}")
    print(f"🕷️  开始深度爬取: {site_name or base_url}")
    print(f"📄 页面限制: {limit} 页")
    print(f"{'='*60}")
    
    try:
        # 使用 Firecrawl Crawl API 爬取整站
        crawl_result = firecrawl.crawl(
            url=base_url,
            limit=limit,
            scrape_options={
                "formats": ["markdown", "links"],
            },
            poll_interval=5  # 每5秒检查一次状态
        )
        
        pages = []
        if hasattr(crawl_result, 'data') and crawl_result.data:
            for idx, doc in enumerate(crawl_result.data, 1):
                page_data = {
                    'page_number': idx,
                    'url': doc.metadata.get('sourceURL') if hasattr(doc, 'metadata') else '',
                    'title': doc.metadata.get('title', 'No title') if hasattr(doc, 'metadata') else 'No title',
                    'markdown': doc.markdown if hasattr(doc, 'markdown') else '',
                    'status_code': doc.metadata.get('statusCode') if hasattr(doc, 'metadata') else None,
                }
                pages.append(page_data)
                print(f"  [{idx}/{len(crawl_result.data)}] ✓ {page_data['title'][:50]}... ({len(page_data['markdown'])} 字符)")
        
        summary = {
            'base_url': base_url,
            'site_name': site_name,
            'status': crawl_result.status if hasattr(crawl_result, 'status') else 'unknown',
            'total_pages': len(pages),
            'completed': crawl_result.completed if hasattr(crawl_result, 'completed') else len(pages),
            'credits_used': crawl_result.creditsUsed if hasattr(crawl_result, 'creditsUsed') else 0,
            'crawled_at': datetime.now().isoformat(),
            'pages': pages
        }
        
        print(f"\n✓ 爬取完成！")
        print(f"  总页数: {summary['total_pages']}")
        print(f"  消耗积分: {summary['credits_used']}")
        print(f"  状态: {summary['status']}")
        
        return summary
        
    except Exception as e:
        print(f"✗ 深度爬取失败: {str(e)}")
        import traceback
        print(f"  详细错误: {traceback.format_exc()}")
        return {
            'base_url': base_url,
            'site_name': site_name,
            'status': 'failed',
            'error': str(e),
            'crawled_at': datetime.now().isoformat(),
            'pages': []
        }

# 第一步：并行搜索
print("\n【并行搜索】")
print("-" * 60)

# 初始化结果列表
final_results = []

if use_search_and_scrape:
    # 使用 Firecrawl 一体化模式，直接返回带内容的结果
    print("使用 Firecrawl 一体化搜索+抓取模式...")
    final_results = firecrawl_search_and_scrape(query, limit=max_results)
    
    # Tavily 仍需单独搜索
    tavily_results = tavily_search(query)
    
    # 跳过后续的单独抓取步骤
    skip_scraping = True
else:
    # 传统模式：先搜索，后抓取
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        tavily_future = executor.submit(tavily_search, query)
        firecrawl_future = executor.submit(firecrawl_search, query, max_results)
        
        tavily_results = tavily_future.result()
        firecrawl_results = firecrawl_future.result()
    
    skip_scraping = False

# 合并去重
if not use_search_and_scrape:
    for item in tavily_results + firecrawl_results:
        url = item['url']
        if url and url not in all_urls:
            all_urls[url] = item
    
    print(f"\n合并去重后共 {len(all_urls)} 个唯一网页")
else:
    # 一体化模式下，Firecrawl 结果已包含内容
    for item in tavily_results:
        url = item['url']
        if url and url not in all_urls:
            all_urls[url] = item
    
    print(f"\nTavily 搜索到 {len(all_urls)} 个网页")

# 爬取函数
def scrape_url(url, info, idx, total):
    print(f"[{idx}/{total}] 开始爬取: {info['title'][:30]}...")
    try:
        scraped = firecrawl.scrape(url=url, formats=['markdown'])
        markdown = scraped.markdown if hasattr(scraped, 'markdown') else scraped.get('markdown', '')
        
        print(f"[{idx}/{total}] ✓ 成功，{len(markdown)} 字符")
        return {
            'title': info['title'],
            'url': url,
            'source': info['source'],
            'snippet': info['snippet'],
            'markdown': markdown,
            'scraped_at': datetime.now().isoformat()
        }
    except Exception as e:
        print(f"[{idx}/{total}] ✗ 失败: {str(e)}")
        return {
            'title': info['title'],
            'url': url,
            'source': info['source'],
            'snippet': info['snippet'],
            'error': str(e)
        }

# 第二步：并行爬取（仅在传统模式下执行）
if not use_search_and_scrape:
    print("\n" + "=" * 60)
    print("【并行爬取单页】")
    print("=" * 60)
    
    temp_results = []
    max_crawl = 5
    urls_to_crawl = list(all_urls.items())[:max_crawl]
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(scrape_url, url, info, idx, len(urls_to_crawl)): url
            for idx, (url, info) in enumerate(urls_to_crawl, 1)
        }
        
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            temp_results.append(result)
    
    final_results.extend(temp_results)
else:
    print("\n" + "=" * 60)
    print("【一体化模式：已包含内容，跳过单独爬取】")
    print("=" * 60)

# 第三步：深度爬取（Crawl 整站）
crawled_sites = []
if enable_deep_crawl and len(all_urls) > 0:
    print("\n" + "=" * 60)
    print("【深度爬取模式：Crawl 整站】")
    print("=" * 60)
    
    # 从搜索结果中提取根域名，选择最相关的网站进行深度爬取
    from urllib.parse import urlparse
    
    sites_to_crawl = []
    seen_domains = set()
    
    # 选择不同域名的网站
    for url, info in list(all_urls.items())[:max_crawl_sites * 3]:
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        domain = parsed.netloc
        
        if domain not in seen_domains:
            sites_to_crawl.append({
                'base_url': base_url,
                'domain': domain,
                'title': info['title'],
                'original_url': url
            })
            seen_domains.add(domain)
            
            if len(sites_to_crawl) >= max_crawl_sites:
                break
    
    print(f"\n将深度爬取以下 {len(sites_to_crawl)} 个网站：")
    for idx, site in enumerate(sites_to_crawl, 1):
        print(f"  {idx}. {site['title'][:50]} ({site['domain']})")
    
    # 依次爬取每个网站（避免并发导致的速率限制）
    for idx, site in enumerate(sites_to_crawl, 1):
        print(f"\n进度: [{idx}/{len(sites_to_crawl)}]")
        crawl_result = deep_crawl_site(
            base_url=site['base_url'],
            limit=crawl_page_limit,
            site_name=site['title']
        )
        crawled_sites.append(crawl_result)
else:
    if not enable_deep_crawl:
        print("\n" + "=" * 60)
        print("【深度爬取已禁用】")
        print("=" * 60)

# 保存结果
mode_suffix = "integrated" if use_search_and_scrape else "traditional"
if enable_deep_crawl:
    mode_suffix += "_with_crawl"

output_file = f"combined_results_{mode_suffix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

summary = {
    'query': query,
    'mode': '一体化搜索+抓取' if use_search_and_scrape else '传统搜索后抓取',
    'deep_crawl_enabled': enable_deep_crawl,
    'search_time': datetime.now().isoformat(),
    'search_results': {
        'total': len(final_results),
        'successful': len([r for r in final_results if 'error' not in r and r.get('markdown')]),
        'sources': {
            'tavily': len([r for r in final_results if r.get('source', '').startswith('tavily')]),
            'firecrawl': len([r for r in final_results if r.get('source', '').startswith('firecrawl')])
        },
        'data': final_results
    },
    'crawled_sites': {
        'total_sites': len(crawled_sites),
        'total_pages': sum(site.get('total_pages', 0) for site in crawled_sites),
        'successful_sites': len([s for s in crawled_sites if s.get('status') == 'completed']),
        'data': crawled_sites
    }
}

with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)

print(f"\n" + "=" * 60)
print(f"📊 最终统计")
print(f"=" * 60)
print(f"✓ 保存文件: {output_file}")
print(f"\n🔍 搜索结果:")
print(f"  - 总结果数: {summary['search_results']['total']}")
print(f"  - 成功获取内容: {summary['search_results']['successful']} 个")
print(f"  - 来源: Tavily={summary['search_results']['sources']['tavily']}, Firecrawl={summary['search_results']['sources']['firecrawl']}")

if enable_deep_crawl:
    print(f"\n🕷️  深度爬取:")
    print(f"  - 爬取网站数: {summary['crawled_sites']['total_sites']}")
    print(f"  - 总页面数: {summary['crawled_sites']['total_pages']}")
    print(f"  - 成功网站: {summary['crawled_sites']['successful_sites']}")

print(f"=" * 60)
