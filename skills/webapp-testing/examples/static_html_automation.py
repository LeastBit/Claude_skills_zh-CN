from playwright.sync_api import sync_playwright
import os

# 示例：使用 file:// URL 自动化与静态 HTML 文件的交互

html_file_path = os.path.abspath('path/to/your/file.html')
file_url = f'file://{html_file_path}'

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1920, 'height': 1080})

    # 导航到本地 HTML 文件
    page.goto(file_url)

    # 截图
    page.screenshot(path='/mnt/user-data/outputs/static_page.png', full_page=True)

    # 与元素交互
    page.click('text=点击我')
    page.fill('#name', 'John Doe')
    page.fill('#email', 'john@example.com')

    # 提交表单
    page.click('button[type="submit"]')
    page.wait_for_timeout(500)

    # 截取最终截图
    page.screenshot(path='/mnt/user-data/outputs/after_submit.png', full_page=True)

    browser.close()

print("静态 HTML 自动化已完成！")
