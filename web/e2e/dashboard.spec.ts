import { test, expect } from "@playwright/test";

test.describe("Dashboard", () => {
  test("loads login page", async ({ page }) => {
    await page.goto("/login");
    await expect(page.locator("h1")).toContainText("Delhi Metro Digital Twin");
  });

  test("login page has form", async ({ page }) => {
    await page.goto("/login");
    await expect(page.locator('input[id="username"]')).toBeVisible();
    await expect(page.locator('input[id="password"]')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toContainText("Sign In");
  });

  test("main page loads with map container", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator("aside")).toBeVisible();
  });

  test("sidebar navigation items are present", async ({ page }) => {
    await page.goto("/");
    const sidebar = page.locator("aside");
    await expect(sidebar.locator("text=Live Map")).toBeVisible();
    await expect(sidebar.locator("text=Timetable")).toBeVisible();
    await expect(sidebar.locator("text=ETA Prediction")).toBeVisible();
  });
});
