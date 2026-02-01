import os
import sys
import json
import threading
import importlib.util
from pathlib import Path
from django.apps import apps
from django.conf import settings
from django.utils import timezone


# Spiders are now in the scanner app directory
SPIDERS_DIR = Path(__file__).resolve().parent / 'spiders'


def get_available_spiders():

    spiders = []
    
    if SPIDERS_DIR.exists():
        for file in SPIDERS_DIR.glob('*.py'):
            if file.name != '__init__.py' and not file.name.startswith('_'):
                spiders.append(file.stem)
    
    return sorted(spiders)


def get_spider_class(spider_module_name):

    spider_file = SPIDERS_DIR / f'{spider_module_name}.py'
    
    if not spider_file.exists():
        return None
    
    try:
        # Load module from file path
        spec = importlib.util.spec_from_file_location(spider_module_name, spider_file)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spider_module_name] = module
        spec.loader.exec_module(module)
        
        # Find the spider class in the module
        for name in dir(module):
            obj = getattr(module, name)
            if isinstance(obj, type) and hasattr(obj, 'name') and hasattr(obj, 'parse'):
                # Check if it's a Spider subclass (has 'start_requests' or inherits from Spider)
                if 'Spider' in name or hasattr(obj, 'start_requests'):
                    return obj
    except Exception as e:
        print(f"Error loading spider {spider_module_name}: {e}")
    
    return None


def run_all_spiders_async(name_query, job_id, app_label, model_name, spider_names=None):

    
    def run_in_thread():
        # Get the job model dynamically
        try:
             JobModel = apps.get_model(app_label, model_name)
             scan_job = JobModel.objects.get(id=job_id)
        except LookupError:
             print(f"Model {app_label}.{model_name} not found.")
             return
        except JobModel.DoesNotExist:
             print(f"Job {job_id} not found.")
             return

        # Determine the Result Model
        try:
            ScanResultModel = scan_job.get_result_model()
        except AttributeError:
             # Fallback if get_result_model is missing (shouldn't happen with correct inheritence)
             return

        # Get spiders to run
        spiders_to_run = spider_names or get_available_spiders()
        scan_job.total_spiders = len(spiders_to_run)
        scan_job.status = 'running'
        scan_job.save()
        
        # Run each spider and collect results
        for spider_module_name in spiders_to_run:
            try:
                spider_file = SPIDERS_DIR / f'{spider_module_name}.py'
                if not spider_file.exists():
                    scan_job.refresh_from_db()
                    scan_job.completed_spiders += 1
                    scan_job.save()
                    continue
                
                # Get spider class to get the website name
                spider_class = get_spider_class(spider_module_name)
                website_name = spider_class.name if spider_class and hasattr(spider_class, 'name') else spider_module_name
                
                # Run spider in subprocess to avoid Twisted reactor issues
                import subprocess
                
                spider_code = f'''
import sys
import json
sys.path.insert(0, r"{SPIDERS_DIR.parent}")

from scrapy.crawler import CrawlerProcess
import importlib.util

# Load spider module
spec = importlib.util.spec_from_file_location("spider", r"{spider_file}")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

# Find spider class
spider_cls = None
for name in dir(module):
    obj = getattr(module, name)
    if isinstance(obj, type) and hasattr(obj, "name") and hasattr(obj, "parse"):
        if "Spider" in name or hasattr(obj, "start_requests"):
            spider_cls = obj
            break

if spider_cls:
    collected = {{
        "images": [], 
        "videos": [], 
        "page_urls": [],
        "emails": getattr(spider_cls, "emails", [])
    }}
    
    class Collector:
        def process_item(self, item, spider):
            # Collect Images
            if item.get("image"):
                if isinstance(item["image"], list):
                    collected["images"].extend(item["image"])
                else:
                    collected["images"].append(item["image"])
            
            # Collect Videos
            if item.get("video"):
                if isinstance(item["video"], list):
                    collected["videos"].extend(item["video"])
                else:
                    collected["videos"].append(item["video"])
            
            # Collect Page URLs
            if item.get("page_url"):
                if isinstance(item["page_url"], list):
                    collected["page_urls"].extend(item["page_url"])
                else:
                    collected["page_urls"].append(item["page_url"])
                    
            return item
    
    process = CrawlerProcess({{
        "LOG_ENABLED": False,
        "LOG_LEVEL": "ERROR",
        "ROBOTSTXT_OBEY": False,
        "ITEM_PIPELINES": {{Collector: 300}},
    }})
    process.crawl(spider_cls, name_query="{name_query}")
    process.start()
    print("RESULT:" + json.dumps(collected))
else:
    print("RESULT:" + json.dumps({{"images": [], "videos": [], "page_urls": [], "emails": []}}))
'''
                
                result = subprocess.run(
                    [sys.executable, '-c', spider_code],
                    capture_output=True,
                    text=True,
                    timeout=120,  # 2 minute timeout per spider
                    cwd=str(SPIDERS_DIR.parent)
                )
                
                # Parse results
                collected_items = {'images': [], 'videos': []}
                if result.stdout:
                    for line in result.stdout.strip().split('\n'):
                        if line.startswith('RESULT:'):
                            try:
                                collected_items = json.loads(line[7:])
                            except json.JSONDecodeError:
                                pass
                            break
                
                # Process results with S3 upload
                from .utils import download_file, upload_to_s3
                
                final_images = []
                final_videos = collected_items.get('videos', [])
                
                original_images = collected_items.get('images', [])
                page_urls = collected_items.get('page_urls', [])
                profile_url = page_urls[0] if page_urls else None
                
                for img_url in original_images:
                    # Download and upload to S3
                    content, content_type = download_file(img_url)
                    s3_url = None
                    if content:
                        filename = img_url.split('/')[-1]
                        if len(filename) > 50: filename = filename[-50:]
                        if not filename: filename = "image.jpg"
                        
                        s3_url = upload_to_s3(content, filename, content_type)
                    
                    final_images.append({
                        'original': img_url,
                        's3': s3_url
                    })
                
                
                ScanResultModel.objects.update_or_create(
                    scan_job=scan_job,
                    website=website_name,
                    defaults={
                        'images': final_images,
                        'videos': final_videos,
                        'page_urls': page_urls,
                        'profile_url': profile_url,
                        'contact_emails': collected_items.get('emails', []),
                        'status': 'pending'
                    }
                )
                
            except subprocess.TimeoutExpired:
                print(f"Spider {spider_module_name} timed out")
            except Exception as e:
                print(f"Error running spider {spider_module_name}: {e}")
            
            # Update progress
            scan_job.refresh_from_db()
            scan_job.completed_spiders += 1
            scan_job.save()
        
        # Mark job as completed
        scan_job.refresh_from_db()
        scan_job.status = 'completed'
        scan_job.completed_at = timezone.now()
        scan_job.save()
    
    # Start background thread
    thread = threading.Thread(target=run_in_thread, daemon=True)
    thread.start()
    return thread

