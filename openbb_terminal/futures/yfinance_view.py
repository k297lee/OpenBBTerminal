"""Yahoo Finance view"""
__docformat__ = "numpy"

from typing import Optional, List
import logging
import os

from datetime import datetime, timedelta
from matplotlib import pyplot as plt

from openbb_terminal.config_terminal import theme
from openbb_terminal.config_plot import PLOT_DPI
from openbb_terminal.decorators import log_start_end
from openbb_terminal.futures import yfinance_model
from openbb_terminal.helper_funcs import (
    export_data,
    plot_autoscale,
    print_rich_table,
    is_valid_axes_count,
)
from openbb_terminal.rich_config import console

logger = logging.getLogger(__name__)


@log_start_end(log=logger)
def display_search(
    category: str = "",
    exchange: str = "",
    description: str = "",
    export: str = "",
):
    """Display search futures [Source: Yahoo Finance]

    Parameters
    ----------
    category: str
        Select the category where the future exists
    exchange: str
        Select the exchange where the future exists
    description: str
        Select the description of the future
    export: str
        Type of format to export data
    """
    df = yfinance_model.get_search_futures(category, exchange, description)
    if df.empty:
        console.print("[red]No futures data found.\n[/red]")
        return

    print_rich_table(df)
    console.print()

    export_data(
        export,
        os.path.dirname(os.path.abspath(__file__)),
        "search",
        df,
    )


@log_start_end(log=logger)
def display_historical(
    tickers: List[str],
    expiry: str = "",
    start_date: str = (datetime.now() - timedelta(days=3 * 365)).strftime("%Y-%m-%d"),
    raw: bool = False,
    export: str = "",
    external_axes: Optional[List[plt.Axes]] = None,
):
    """Display historical futures [Source: Yahoo Finance]

    Parameters
    ----------
    tickers: List[str]
        List of future timeseries tickers to display
    expiry: str
        Future expiry date with format YYYY-MM
    start_date : str
        Initial date like string (e.g., 2021-10-01)
    raw: bool
        Display futures timeseries in raw format
    export: str
        Type of format to export data
    external_axes : Optional[List[plt.Axes]], optional
        External axes (1 axis is expected in the list), by default None
    """
    tickers_validated = list()
    for ticker in tickers:
        if ticker in yfinance_model.FUTURES_DATA["Ticker"].unique().tolist():
            tickers_validated.append(ticker)
        else:
            console.print(f"[red]{ticker} is not a valid ticker[/red]")

    tickers = tickers_validated

    if not tickers:
        console.print("No ticker was provided.\n")
        return

    historicals = yfinance_model.get_historical_futures(tickers, expiry)

    if historicals.empty:
        console.print(f"No data was found for the tickers: {', '.join(tickers)}\n")
        return

    if raw or len(historicals) == 1:

        if not raw and len(historicals) == 1:
            console.print(
                "\nA single datapoint is not enough to depict a chart, data is presented below."
            )

        print_rich_table(
            historicals[historicals.index > datetime.strptime(start_date, "%Y-%m-%d")],
            headers=list(historicals.columns),
            show_index=True,
            title="Futures timeseries",
        )
        console.print()

    else:

        # This plot has 1 axis
        if not external_axes:
            _, ax = plt.subplots(figsize=plot_autoscale(), dpi=PLOT_DPI)
        elif is_valid_axes_count(external_axes, 1):
            (ax,) = external_axes
        else:
            return

        if len(tickers) > 1:
            name = list()
            for tick in historicals["Adj Close"].columns.tolist():
                if len(historicals["Adj Close"][tick].dropna()) == 1:
                    console.print(
                        f"\nA single datapoint on {tick} is not enough to depict a chart, data shown below."
                    )
                    naming = yfinance_model.FUTURES_DATA[
                        yfinance_model.FUTURES_DATA["Ticker"] == tick
                    ]["Description"].values[0]
                    print_rich_table(
                        historicals[
                            historicals["Adj Close"][tick].index
                            > datetime.strptime(start_date, "%Y-%m-%d")
                        ]["Adj Close"][tick]
                        .dropna()
                        .to_frame(),
                        headers=[naming],
                        show_index=True,
                        title="Futures timeseries",
                    )
                    continue

                name.append(
                    yfinance_model.FUTURES_DATA[
                        yfinance_model.FUTURES_DATA["Ticker"] == tick
                    ]["Description"].values[0]
                )
                ax.plot(
                    historicals["Adj Close"][tick].dropna().index,
                    historicals["Adj Close"][tick].dropna().values,
                )
                ax.legend(name)

                first = datetime.strptime(start_date, "%Y-%m-%d")
                if historicals["Adj Close"].index[0] > first:
                    first = historicals["Adj Close"].index[0]
                ax.set_xlim(first, historicals["Adj Close"].index[-1])
                theme.style_primary_axis(ax)

                if external_axes is None:
                    theme.visualize_output()
        else:
            if len(historicals["Adj Close"]) == 1:
                console.print(
                    f"\nA single datapoint on {tickers[0]} is not enough to depict a chart, data shown below."
                )
                print_rich_table(
                    historicals[
                        historicals["Adj Close"].index
                        > datetime.strptime(start_date, "%Y-%m-%d")
                    ],
                    headers=list(historicals["Adj Close"].columns),
                    show_index=True,
                    title="Futures timeseries",
                )

            else:
                name = yfinance_model.FUTURES_DATA[
                    yfinance_model.FUTURES_DATA["Ticker"] == tickers[0]
                ]["Description"].values[0]
                ax.plot(
                    historicals["Adj Close"].dropna().index,
                    historicals["Adj Close"].dropna().values,
                )
                if expiry:
                    ax.set_title(f"{name} with expiry {expiry}")
                else:
                    ax.set_title(name)

                first = datetime.strptime(start_date, "%Y-%m-%d")
                if historicals["Adj Close"].index[0] > first:
                    first = historicals["Adj Close"].index[0]
                ax.set_xlim(first, historicals["Adj Close"].index[-1])
                theme.style_primary_axis(ax)

                if external_axes is None:
                    theme.visualize_output()

    export_data(
        export,
        os.path.dirname(os.path.abspath(__file__)),
        "historical",
        historicals[historicals.index > datetime.strptime(start_date, "%Y-%m-%d")],
    )


@log_start_end(log=logger)
def display_curve(
    ticker: str,
    raw: bool = False,
    export: str = "",
    external_axes: Optional[List[plt.Axes]] = None,
):
    """Display curve futures [Source: Yahoo Finance]

    Parameters
    ----------
    ticker: str
        Curve future ticker to display
    raw: bool
        Display futures timeseries in raw format
    export: str
        Type of format to export data
    external_axes : Optional[List[plt.Axes]], optional
        External axes (1 axis is expected in the list), by default None
    """
    if ticker not in yfinance_model.FUTURES_DATA["Ticker"].unique().tolist():
        console.print(f"[red]'{ticker}' is not a valid ticker[/red]")
        return

    df = yfinance_model.get_curve_futures(ticker)

    if df.empty:
        console.print("[red]No future data found to generate curve.[/red]\n")
        return

    if raw:
        print_rich_table(
            df,
            headers=list(df.columns),
            show_index=True,
            title="Futures curve",
        )
        console.print()

    else:
        # This plot has 1 axis
        if not external_axes:
            _, ax = plt.subplots(figsize=plot_autoscale(), dpi=PLOT_DPI)
        elif is_valid_axes_count(external_axes, 1):
            (ax,) = external_axes
        else:
            return

        name = yfinance_model.FUTURES_DATA[
            yfinance_model.FUTURES_DATA["Ticker"] == ticker
        ]["Description"].values[0]
        ax.plot(
            df.index,
            df.values,
            marker="o",
            linestyle="dashed",
            linewidth=2,
            markersize=12,
        )
        ax.set_title(name)
        theme.style_primary_axis(ax)

        if external_axes is None:
            theme.visualize_output()

        export_data(
            export,
            os.path.dirname(os.path.abspath(__file__)),
            "curve",
            df,
        )
