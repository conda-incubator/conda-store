import time

import pytest
from playwright.sync_api import Page


@pytest.mark.playwright
def test_integration(page: Page, server_port):
    # Go to http://localhost:{server_port}/conda-store/admin/
    page.goto(f"http://localhost:{server_port}/conda-store/admin/", wait_until="domcontentloaded")
    page.screenshot(path="test-results/conda-store-unauthenticated.png")

    # Click text=Login
    page.locator("text=Login").click()
    # expect(page).to_have_url(f"http://localhost:{server_port}/conda-store/login/")

    # Click [placeholder="Username"]
    page.locator('[placeholder="Username"]').click()

    # Fill [placeholder="Username"]
    page.locator('[placeholder="Username"]').fill("username")

    # Press Tab
    page.locator('[placeholder="Username"]').press("Tab")

    # Fill [placeholder="Password"]
    page.locator('[placeholder="Password"]').fill("password")

    # Click button:has-text("Sign In")
    # with page.expect_navigation(url=f"http://localhost:{server_port}/conda-store/"):
    with page.expect_navigation():
        page.locator('button:has-text("Sign In")').click()

    page.screenshot(path="test-results/conda-store-authenticated.png")

    # Click [placeholder="Search"]
    page.locator('[placeholder="Search"]').click()

    # Fill [placeholder="Search"]
    page.locator('[placeholder="Search"]').fill("python")

    # Press Enter
    page.locator('[placeholder="Search"]').press("Enter")
    # expect(page).to_have_url(f"http://localhost:{server_port}/conda-store/?search=python")

    # Click text=filesystem/python-flask-env
    page.locator("text=filesystem / python-flask-env").click()
    # expect(page).to_have_url(f"http://localhost:{server_port}/conda-store/environment/filesystem/python-flask-env/")

    page.locator("a", has_text="Build").click()

    # polling for build to complete
    for i in range(10):
        locator = page.locator('#build-status:has-text("COMPLETED")')
        if locator.count() == 1:
            break
        page.reload()
        time.sleep(10)
    else:
        raise Exception("Error waiting for build to complete when polling")

    page.screenshot(path="test-results/conda-store-build-complete.png")

    page.goto(f"http://localhost:{server_port}/conda-store/admin/")

    page.goto(f"http://localhost:{server_port}/conda-store/")
    time.sleep(5)
