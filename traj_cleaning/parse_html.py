import os
from playwright.sync_api import Playwright, sync_playwright, expect
from tqdm import tqdm

import json
import re
import zipfile


def parse_tracefile(tracefilepath, outpath):
    parsed_data = []
    before = ""
    with open(tracefilepath, 'r') as file:
        for line in file:
            try:
                json_line = json.loads(line)

                if json_line.get("type") == "before" and "apiName" in json_line:
                    before = json_line["apiName"]
                    

                elif json_line.get("type") == "after" and "log" in json_line:
                    entry = json_line["log"][0]
                    match = re.search(r'waiting for (.*)', entry)
                    if match:
                        parsed_data.append((before, match.group(1)))
            except json.JSONDecodeError:
                continue  
    with open(outpath, 'w') as file2:
        json.dump(parsed_data, file2)

def run(playwright: Playwright, filename) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://trace.playwright.dev/")
    with page.expect_file_chooser() as fc_info:
        page.get_by_role("button", name="Select file(s)").click()
    file_chooser = fc_info.value
    file_chooser.set_files(filename)

    return page, browser

def save_html(page, outpath):
    with page.expect_popup() as page1_info:
        page.get_by_role("button", name="").click()
    page1 = page1_info.value
    html = page1.content()
    with open(outpath, "w") as file:
        file.write(html)
    page1.close()

def load_actions(playwright: Playwright, page, actions_file, trace_file_dir, html_dir) -> None:

    with open(actions_file, 'r') as file:
        actions = json.load(file)
        page.locator(".list-view-entry > .codicon").first.click()
        htmlpath = os.path.join(html_dir, f"{trace_file_dir}_0.html")
        save_html(page, htmlpath)
        for ind, action in enumerate(actions[1:]):
            page.get_by_text(f"{action[0]}{action[1]}").click()
            htmlpath = os.path.join(html_dir, f"{trace_file_dir}_{ind}.html")
            save_html(page, htmlpath)
    

if __name__ == "__main__":
    traj_dir = "/Users/guozhitong/Desktop/WebArena/z_human-trajectories/trajectories"
    html_dir = "/Users/guozhitong/Desktop/WebArena/z_human-trajectories/cleaned_htmls"
    action_dir = "/Users/guozhitong/Desktop/WebArena/z_human-trajectories/cleaned_actions"
    os.makedirs(html_dir, exist_ok=True)
    os.makedirs(action_dir, exist_ok=True)

    success_list = []

    for traj_file in tqdm(os.listdir(traj_dir)):
        # unzip file
        # read trace file, extract the list of actions, save as file in 
        # open browser, load trace file
            # for each action, click the corresponding element, save the html
        
        parsed_data = []
    
        if traj_file.endswith('.trace.zip'):
            #unzip file
            traj_file_path = os.path.join(traj_dir, traj_file)

            with zipfile.ZipFile(traj_file_path, 'r') as zip_ref:
                zip_ref.extractall(traj_file)

            os.remove(traj_file_path)
            
            # read trace file, extract the list of actions, save as file in
            trace_file_dir = traj_file.replace('.zip', '')
            tracefile = os.path.join(traj_file, 'trace.trace')
            actionfile = os.path.join(action_dir, f"{trace_file_dir}.json")

            parse_tracefile(tracefile, actionfile)

            # open browser, load trace file
            with sync_playwright() as playwright:
                page, browser = run(playwright, traj_file_path)

                # for each action, click the corresponding element, save the html
                try:
                    load_actions(playwright, page, actionfile, trace_file_dir, html_dir)
                    # write to a success list
                    success_list.append(traj_file)
                    
                    browser.close()
                except:
                    browser.close()
                    continue

        json.dump(success_list, open("success_list.json", "w"))

