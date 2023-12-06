from playwright.sync_api import Playwright, sync_playwright, expect


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://trace.playwright.dev/")
    page.get_by_role("button", name="Select file(s)").click()
    page.goto("https://trace.playwright.dev/?trace=blob%3Ahttps%3A%2F%2Ftrace.playwright.dev%2F0151f016-36a8-42b5-972f-7f0666234148&traceFileName=23.trace.zip")
    page.locator(".list-view-entry > .codicon").first.click()
    page.locator("div:nth-child(2) > .codicon").click(click_count=5)
    page.get_by_text("frame.clickget_by_role(\"link\", name=\"12 Reviews\")102ms").click()
    page.locator("div").filter(has_text=re.compile(r"^frame\.clickget_by_role\(\"link\", name=\"12 Reviews\"\)102ms$")).locator("span").click()
    page.locator("div:nth-child(3) > .codicon").click()
    page.locator("div:nth-child(3) > .codicon").click(click_count=7)
    page.close()

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
