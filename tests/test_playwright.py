import time

import pytest
from playwright.sync_api import Page


@pytest.mark.playwright
def test_integration(page: Page):
    # Go to http://localhost:5000/conda-store/
    page.goto("http://localhost:5000/conda-store/")

    # Click text=Login
    page.locator("text=Login").click()
    # expect(page).to_have_url("http://localhost:5000/conda-store/login/")

    # Click [placeholder="Username"]
    page.locator("[placeholder=\"Username\"]").click()

    # Fill [placeholder="Username"]
    page.locator("[placeholder=\"Username\"]").fill("username")

    # Press Tab
    page.locator("[placeholder=\"Username\"]").press("Tab")

    # Fill [placeholder="Password"]
    page.locator("[placeholder=\"Password\"]").fill("password")

    # Click button:has-text("Sign In")
    # with page.expect_navigation(url="http://localhost:5000/conda-store/"):
    with page.expect_navigation():
        page.locator("button:has-text(\"Sign In\")").click()

    # Click [placeholder="Search"]
    page.locator("[placeholder=\"Search\"]").click()

    # Fill [placeholder="Search"]
    page.locator("[placeholder=\"Search\"]").fill("python")

    # Press Enter
    page.locator("[placeholder=\"Search\"]").press("Enter")
    # expect(page).to_have_url("http://localhost:5000/conda-store/?search=python")

    # Click text=filesystem/python-flask-env
    page.locator("text=filesystem / python-flask-env").click()
    # expect(page).to_have_url("http://localhost:5000/conda-store/environment/filesystem/python-flask-env/")

    # polling for build to complete
    for i in range(10):
        if page.locator("#build-status", has_text="COMPLETED"):
            break
        time.sleep(10)
    else:
        raise Exception("Error waiting for build to complete when polling")

    page.goto("http://localhost:5000/conda-store/")
