"""
HEMAGON Profile Scraper
"""
import os
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from playwright.sync_api import sync_playwright

WEAPON_NAMES = [
    'Dussak - Women', 'Katana', 'Longsword - Women', 'Longsword & Rondel',
    'Rapier - Women', 'Rapier & Dagger', 'Rapier & Dagger - Women',
    'Saber - Woman', 'Spear', 'Sword & Buckler - Women'
]


def save_tournament_with_links(page, output_dir: str, filename: str) -> dict:
    """Save tournament page with all links and extract VK links."""
    filepath = os.path.join(output_dir, filename)
    content = {
        'text': page.inner_text('body'),
        'links': []
    }
    all_links = page.query_selector_all('a[href]')
    for link in all_links:
        href = link.get_attribute('href')
        text = link.inner_text().strip()
        if href and text:
            content['links'].append({'text': text, 'href': href})
    
    os.makedirs(output_dir, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(content, f, ensure_ascii=False, indent=2)
    
    vk_links = [l for l in content['links'] if 'vk.com' in l['href']]
    for vk in vk_links:
        vk_filename = f"vk_{vk['href'].split('/')[-1].replace('?from=groups', '')}.json"
        vk_filepath = os.path.join(output_dir, vk_filename)
        with open(vk_filepath, "w", encoding="utf-8") as f:
            json.dump({
                'source_tournament': filename,
                'vk_link': vk['href'],
                'vk_name': vk['text']
            }, f, ensure_ascii=False, indent=2)
    
    return content


def set_fights_per_page(page, count=50):
    """Set number of fights shown per page."""
    page.wait_for_timeout(1000)
    parent_div = page.query_selector('text=Per page')
    if parent_div:
        btn_group = parent_div.query_selector('xpath=../div[contains(@class, "btn-group")]')
        if btn_group:
            buttons = btn_group.query_selector_all('button')
            for btn in buttons:
                if btn.inner_text().strip() == str(count):
                    btn.click()
                    page.wait_for_timeout(2000)
                    return


def load_user_profile(profile_link: str, target_dir: str) -> dict:
    """
    Load a HEMA fighter's profile from hemagon.com and save to target directory.
    
    Args:
        profile_link: Full URL to profile (e.g., 'https://hemagon.com/users/nekrasova')
        target_dir: Directory to save output files
    
    Returns:
        Dictionary with profile data and file paths
    """
    os.makedirs(target_dir, exist_ok=True)
    
    result = {
        'profile_link': profile_link,
        'target_dir': target_dir,
        'files_saved': [],
        'tournaments': [],
        'weapons': []
    }
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            viewport={'width': 1920, 'height': 1080},
        )
        page = context.new_page()
        
        # Load profile page
        page.goto(profile_link, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(3000)
        
        # Handle cookie consent
        btn = page.query_selector('button:has-text("YES, I AGREE")')
        if btn:
            btn.click()
            page.wait_for_timeout(1000)
        
        # Save profile page
        profile_path = os.path.join(target_dir, "profile.txt")
        with open(profile_path, "w", encoding="utf-8") as f:
            f.write(page.inner_text('body'))
        result['files_saved'].append("profile.txt")
        
        # Navigate to stats page
        page.goto(profile_link + "/stats", wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(3000)
        
        processed_tournaments = set()
        
        for weapon_name in WEAPON_NAMES:
            links = page.query_selector_all('a')
            weapon_link = None
            for link in links:
                if link.inner_text().strip() == weapon_name:
                    weapon_link = link
                    break
            
            if not weapon_link:
                continue
            
            weapon_link.click()
            page.wait_for_timeout(2000)
            
            # Save weapon stats page
            weapon_filename = f"weapon_{weapon_name.replace(' ', '_').replace('&', 'and')}.txt"
            weapon_path = os.path.join(target_dir, weapon_filename)
            with open(weapon_path, "w", encoding="utf-8") as f:
                f.write(page.inner_text('body'))
            result['files_saved'].append(weapon_filename)
            result['weapons'].append(weapon_name)
            
            # Parse tournaments from weapon page
            tournament_links = page.query_selector_all('a[href*="/tournament/"]')
            weapon_tournaments = set()
            for link in tournament_links:
                href = link.get_attribute('href')
                if href and '/tournament/' in href and '/nomination/' not in href:
                    slug = href.split('/')[-1]
                    if slug and slug not in processed_tournaments:
                        weapon_tournaments.add(slug)
            
            # Save tournament pages
            for slug in weapon_tournaments:
                processed_tournaments.add(slug)
                page.goto(f"https://hemagon.com/tournament/{slug}", wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(2000)
                save_tournament_with_links(page, target_dir, f"tournament_{slug}.json")
                result['files_saved'].append(f"tournament_{slug}.json")
                result['tournaments'].append(slug)
            
            # Go back to stats page
            page.goto(profile_link + "/stats", wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(2000)
            
            # Handle SHOW FIGHTS WITH ME button
            show_fights_btn = page.query_selector('button:has-text("SHOW FIGHTS WITH ME")')
            if show_fights_btn:
                show_fights_btn.click()
                page.wait_for_timeout(2000)
                
                page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                page.wait_for_timeout(1000)
                set_fights_per_page(page, 50)
                
                fights_filename = f"weapon_{weapon_name.replace(' ', '_').replace('&', 'and')}_fights.txt"
                fights_path = os.path.join(target_dir, fights_filename)
                with open(fights_path, "w", encoding="utf-8") as f:
                    f.write(page.inner_text('body'))
                result['files_saved'].append(fights_filename)
        
        browser.close()
    
    return result


def _load_user_profile_sync(profile_link: str, target_dir: str) -> dict:
    """Synchronous wrapper for load_user_profile."""
    return load_user_profile(profile_link, target_dir)


async def load_user_profile_async(profile_link: str, target_dir: str) -> dict:
    """Async version of load_user_profile that runs in a thread."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        partial(_load_user_profile_sync, profile_link, target_dir)
    )