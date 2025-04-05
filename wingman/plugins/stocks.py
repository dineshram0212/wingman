import yfinance as yf
from wingman.utils.tool_decorator import tool

@tool
def get_stock_news(ticker: str, max_items: int = 5) -> str:
    """
    Fetches the latest stock news for a given ticker using yfinance.

    :param ticker: Stock ticker symbol (e.g., 'AAPL').
    :param max_items: Number of news articles to return.
    :return: Formatted string with news headlines and links.
    """
    import yfinance as yf

    try:
        stock = yf.Ticker(ticker)
        news = stock.news[:max_items]
        if not news:
            return f"No news found for {ticker.upper()}."

        output = [f"📰 News for {ticker.upper()}:"]
        for item in news:
            title = item.get("title", "Untitled")
            publisher = item.get("publisher", "Unknown")
            link = item.get("link", "No link available")
            output.append(f"- {title} ({publisher})\n{link}")
        return "\n\n".join(output)

    except Exception as e:
        return f"Error fetching news for {ticker}: {str(e)}"
