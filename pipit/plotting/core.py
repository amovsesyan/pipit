import numpy as np
from bokeh.models import (
    ColorBar,
    HoverTool,
    LinearColorMapper,
    LogColorMapper,
    NumeralTickFormatter,
)
from bokeh.plotting import figure

from .util import (
    clamp,
    get_process_ticker,
    get_size_hover_formatter,
    get_size_tick_formatter,
    get_tooltips,
    show,
)


def comm_matrix(
    data, output="size", cmap="log", palette="Viridis256", return_figure=False
):
    """
    Plot the Trace's communication matrix.

    Args:
        data (numpy.ndarray): a 2D numpy array of shape (N, N) containing the
            communication matrix between N processes.
        output (str, optional): "size" or "count"
        cmap (str, optional): Specifies the color mapping. Options are "log",
            "linear", and "any"
        palette (str, optional): Name of Bokeh color palette to use. Defaults to
            "Viridis256".
        return_figure (bool, optional): Whether to return the Bokeh figure
            object. Defaults to False, which displays the result and returns nothing.

    Returns:
        None or Bokeh figure object
    """

    N = data.shape[0]

    # Define color mapper
    if cmap == "linear":
        color_mapper = LinearColorMapper(palette=palette, low=0, high=np.amax(data))
    elif cmap == "log":
        color_mapper = LogColorMapper(
            palette=palette, low=max(np.amin(data), 1), high=np.amax(data)
        )
    elif cmap == "any":
        color_mapper = LinearColorMapper(palette=palette, low=1, high=1)

    # Create bokeh plot
    p = figure(
        x_axis_label="Sender",
        y_axis_label="Receiver",
        x_range=(-0.5, N - 0.5),
        y_range=(N - 0.5, -0.5),
        x_axis_location="above",
        tools="hover,pan,reset,wheel_zoom,save",
        width=90 + clamp(N * 30, 200, 500),
        height=10 + clamp(N * 30, 200, 500),
        toolbar_location="below",
    )

    # Add glyphs and layouts
    p.image(
        image=[np.flipud(data)],
        x=-0.5,
        y=N - 0.5,
        dw=N,
        dh=N,
        color_mapper=color_mapper,
    )

    color_bar = ColorBar(
        color_mapper=color_mapper,
        formatter=get_size_tick_formatter(ignore_range=cmap == "log")
        if output == "size"
        else NumeralTickFormatter(),
        width=15,
    )
    p.add_layout(color_bar, "right")

    # Customize plot
    p.axis.ticker = get_process_ticker(N=N)
    # p.axis.major_tick_line_color = None
    p.grid.visible = False

    # Configure hover
    hover = p.select(HoverTool)
    hover.tooltips = get_tooltips(
        {
            "Sender": "Process $x{0.}",
            "Receiver": "Process $y{0.}",
            "Bytes": "@image{custom}",
        }
        if output == "size"
        else {
            "Sender": "Process $x{0.}",
            "Receiver": "Process $y{0.}",
            "Count": "@image",
        }
    )
    hover.formatters = {"@image": get_size_hover_formatter()}

    # Return plot
    return show(p, return_figure=return_figure)
