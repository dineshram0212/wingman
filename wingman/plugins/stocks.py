import yfinance as yf
from wingman.utils.tool_decorator import tool
from llama_index.core.tools.tool_spec.base import BaseToolSpec
import yfinance as yf
import pandas as pd

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



class YahooFinanceToolSpec(BaseToolSpec):
    """Yahoo Finance tool spec."""

    spec_functions = [
        "balance_sheet",
        "income_statement",
        "cash_flow",
        "stock_basic_info",
        "stock_analyst_recommendations",
        "stock_news",
    ]

    def __init__(self) -> None:
        """Initialize the Yahoo Finance tool spec."""
        super().__init__()

    def balance_sheet(self, ticker: str) -> str:
        stock = yf.Ticker(ticker)
        bs = stock.balance_sheet
        if bs.empty:
            return f"No balance sheet available for {ticker}."
        return "📊 Balance Sheet:\n" + pd.DataFrame(bs).to_string()

    def income_statement(self, ticker: str) -> str:
        stock = yf.Ticker(ticker)
        is_df = stock.income_stmt
        if is_df.empty:
            return f"No income statement available for {ticker}."
        return "📈 Income Statement:\n" + pd.DataFrame(is_df).to_string()

    def cash_flow(self, ticker: str) -> str:
        stock = yf.Ticker(ticker)
        cf = stock.cashflow
        if cf.empty:
            return f"No cash flow data available for {ticker}."
        return "💵 Cash Flow:\n" + pd.DataFrame(cf).to_string()

    def stock_basic_info(self, ticker: str) -> str:
        stock = yf.Ticker(ticker)
        info = stock.info
        if not info:
            return f"No basic info available for {ticker}."
        keys_to_show = ["longName", "sector", "industry", "marketCap", "currentPrice", "previousClose"]
        output = "ℹ️ Basic Stock Info:\n"
        for k in keys_to_show:
            if k in info:
                output += f"- {k}: {info[k]}\n"
        return output.strip()

    def stock_analyst_recommendations(self, ticker: str) -> str:
        stock = yf.Ticker(ticker)
        recs = stock.recommendations
        if recs is None or recs.empty:
            return f"No analyst recommendations found for {ticker}."
        return "🧠 Analyst Recommendations:\n" + recs.tail(10).to_string()

    def stock_news(self, ticker: str) -> str:
      stock = yf.Ticker(ticker)
      news = stock.news
      if not news or not isinstance(news, list):
          return f"No news available for {ticker}."

      out = f"📰 Latest News for {ticker.upper()}:\n"
      for item in news[:5]:
          title = item.get("title")
          link = item.get("link")
          publisher = item.get("publisher", "Unknown")

          # ✅ Skip if title is literally just 'title'
          if not title or title.strip().lower() == "title":
              continue

          out += f"- {title} ({publisher})\n  {link}\n\n"

      return out.strip() if out.strip() else f"No valid news items found for {ticker}."
