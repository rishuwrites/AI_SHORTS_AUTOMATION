import io
import time

from PIL import Image


_DEEPAI_URL = "https://deepai.org/machine-learning-model/text2img"
_DEEPAI_IMAGE_PREFIX = "https://api.deepai.org/job-view-file/"
_MIN_GENERATION_INTERVAL = 5


class DeepAIUnavailableError(RuntimeError):
    pass


class DeepAIImageGenerator:
    def __init__(self):
        self._playwright = None
        self._browser = None
        self._page = None
        self._last_generation = 0
        self._disabled_reason = None

    def close(self):
        try:
            if self._browser and self._browser.is_connected():
                self._browser.close()
        finally:
            if self._playwright:
                self._playwright.stop()
            self._playwright = None
            self._browser = None
            self._page = None

    def _check_restriction(self, page):
        text = page.locator("body").inner_text(timeout=10_000).lower()
        markers = (
            "verify you are human",
            "are you a human",
            "captcha",
            "unusual traffic",
            "rate limit",
            "too many requests",
        )
        restriction = next((marker for marker in markers if marker in text), None)
        if restriction:
            self._disabled_reason = f"DeepAI displayed a {restriction} restriction"
            raise DeepAIUnavailableError(self._disabled_reason)

    def _page_for_generation(self):
        if self._disabled_reason:
            raise DeepAIUnavailableError(self._disabled_reason)
        if self._browser and self._browser.is_connected() and self._page:
            return self._page

        try:
            from playwright.sync_api import sync_playwright

            self._playwright = sync_playwright().start()
            self._browser = self._playwright.chromium.launch(headless=True)
            self._page = self._browser.new_page()
            response = self._page.goto(
                _DEEPAI_URL,
                wait_until="domcontentloaded",
                timeout=60_000,
            )
            if response is None or response.status >= 400:
                status = response.status if response else "no response"
                raise DeepAIUnavailableError(
                    f"DeepAI image page failed to load ({status})"
                )
            self._check_restriction(self._page)
            self._page.locator("#generate-textarea").wait_for(timeout=30_000)
        except DeepAIUnavailableError as exc:
            self._disabled_reason = str(exc)
            raise
        except Exception as exc:
            self._disabled_reason = (
                f"DeepAI browser or generator page is unavailable "
                f"({type(exc).__name__})"
            )
            raise DeepAIUnavailableError(self._disabled_reason) from exc
        return self._page

    def generate(self, prompt):
        try:
            return self._generate(prompt)
        except DeepAIUnavailableError:
            raise
        except Exception as exc:
            self._disabled_reason = (
                f"DeepAI generation failed ({type(exc).__name__})"
            )
            raise DeepAIUnavailableError(self._disabled_reason) from exc

    def _generate(self, prompt):
        page = self._page_for_generation()
        self._check_restriction(page)
        if self._last_generation:
            wait = _MIN_GENERATION_INTERVAL - (
                time.monotonic() - self._last_generation
            )
            if wait > 0:
                time.sleep(wait)

        previous_urls = set(
            page.locator("main img").evaluate_all(
                """(images, prefix) =>
                    images.map(image => image.currentSrc || image.src)
                        .filter(src => src.startsWith(prefix))""",
                _DEEPAI_IMAGE_PREFIX,
            )
        )
        try:
            page.locator("#generate-textarea").fill(prompt[:2000])
            submit = page.locator("#modelSubmitButton")
            submit.wait_for(state="visible", timeout=10_000)
            page.wait_for_function(
                "() => !document.querySelector('#modelSubmitButton')?.disabled",
                timeout=10_000,
            )
            submit.click()
            page.wait_for_function(
                """({prefix, previous}) =>
                    [...document.querySelectorAll('main img')].some(image => {
                        const src = image.currentSrc || image.src;
                        return src.startsWith(prefix) && !previous.includes(src)
                            && image.complete && image.naturalWidth >= 400
                            && image.naturalHeight >= 300;
                    })""",
                arg={"prefix": _DEEPAI_IMAGE_PREFIX, "previous": list(previous_urls)},
                timeout=180_000,
            )
        except Exception as exc:
            try:
                self._check_restriction(page)
            except DeepAIUnavailableError as restriction:
                raise restriction from exc
            self._disabled_reason = (
                f"DeepAI generation failed ({type(exc).__name__})"
            )
            raise DeepAIUnavailableError(self._disabled_reason) from exc

        image_urls = page.locator("main img").evaluate_all(
            """(images, args) => {
                const image = images.find(element => {
                    const src = element.currentSrc || element.src;
                    return src.startsWith(args.prefix) && !args.previous.includes(src)
                        && element.complete && element.naturalWidth >= 400
                        && element.naturalHeight >= 300;
                });
                return image ? [image.currentSrc || image.src] : [];
            }""",
            {"prefix": _DEEPAI_IMAGE_PREFIX, "previous": list(previous_urls)},
        )
        if not image_urls:
            self._disabled_reason = "DeepAI finished without returning an image"
            raise DeepAIUnavailableError(self._disabled_reason)

        response = page.request.get(image_urls[0], timeout=60_000)
        if not response.ok:
            self._disabled_reason = (
                f"DeepAI image download failed with HTTP {response.status}"
            )
            raise DeepAIUnavailableError(self._disabled_reason)
        try:
            image = Image.open(io.BytesIO(response.body())).convert("RGB")
        except Exception as exc:
            self._disabled_reason = "DeepAI returned an invalid image"
            raise DeepAIUnavailableError(self._disabled_reason) from exc

        self._last_generation = time.monotonic()
        return image
