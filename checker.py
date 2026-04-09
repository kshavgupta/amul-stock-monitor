import logging
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

logger = logging.getLogger(__name__)

PRODUCTS = [
    {
        "name": "Amul High Protein Rose Lassi 200ml (Pack of 30)",
        "url": "https://shop.amul.com/en/product/amul-high-protein-rose-lassi-200-ml-or-pack-of-30",
    },
    {
        "name": "Amul High Protein Plain Lassi 200ml (Pack of 30)",
        "url": "https://shop.amul.com/en/product/amul-high-protein-plain-lassi-200-ml-or-pack-of-30",
    },
]


def check_stock() -> list[dict]:
    """
    Returns a list of products that are currently IN STOCK.
    Each item: {"name": ..., "url": ...}
    """
    in_stock = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        )

        for product in PRODUCTS:
            page = context.new_page()
            try:
                logger.info(f"Checking: {product['name']}")
                page.goto(product["url"], wait_until="domcontentloaded", timeout=120000)

                # Handle pincode popup if it appears
                try:
                    pincode_input = page.wait_for_selector(
                        "input[placeholder*='pincode'], input[placeholder*='Pincode'], input[name='pincode']",
                        timeout=10000
                    )
                    if pincode_input:
                        logger.info("Pincode popup detected, entering pincode...")
                        pincode_input.fill("560103")
                        page.wait_for_timeout(1000)
                        # Try clicking a submit/check button first, fallback to Enter
                        try:
                            submit_btn = page.query_selector(
                                "button[type='submit'], button:has-text('Check'), button:has-text('Submit'), button:has-text('Proceed'), .pincode-submit, .btn-pincode"
                            )
                            if submit_btn:
                                submit_btn.click()
                            else:
                                page.keyboard.press("Enter")
                        except Exception:
                            page.keyboard.press("Enter")
                        page.wait_for_timeout(5000)
                except Exception:
                    pass  # No pincode popup, continue normally

                # Wait for Vue.js to render the product section
                page.wait_for_selector(".product-detail, .product-grid-item", timeout=60000)

                # Stock is available if "Add to Cart" button exists and is NOT disabled
                add_to_cart = page.query_selector("a[title='Add to Cart']")

                if add_to_cart:
                    is_disabled = "disabled" in (add_to_cart.get_attribute("class") or "")
                    if not is_disabled:
                        logger.info(f"IN STOCK: {product['name']}")
                        in_stock.append(product)
                    else:
                        logger.info(f"Out of stock: {product['name']}")
                else:
                    # Fallback: check if "Notify Me" button is present (means out of stock)
                    notify_me = page.query_selector(".product-grid-enquiry-wrap, .product-enquiry-wrap")
                    if notify_me:
                        logger.info(f"Out of stock (Notify Me shown): {product['name']}")
                    else:
                        logger.warning(f"Could not determine stock status for: {product['name']}")

            except PlaywrightTimeout:
                logger.error(f"Timeout loading: {product['url']}")
            except Exception as e:
                logger.error(f"Error checking {product['name']}: {e}")
            finally:
                page.close()

        browser.close()

    return in_stock
