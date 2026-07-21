import asyncio

from app import YouTubeClipApp


def test_app_starts():
    async def run_app():
        async with YouTubeClipApp().run_test() as pilot:
            await pilot.pause()
            assert pilot.app.query_one("#extract")
            assert pilot.app.theme == "tokyo-night"
            for expected_theme in ("catppuccin-mocha", "nord", "textual-light", "tokyo-night"):
                await pilot.press("ctrl+t")
                assert pilot.app.theme == expected_theme
                button = pilot.app.query_one("#extract")
                assert button.styles.color != button.styles.background

    asyncio.run(run_app())
