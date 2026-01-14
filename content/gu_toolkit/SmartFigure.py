
# === SECTION: OneShotOutput [id: OneShotOutput]===
import sympy as sp
from typing import Any, Type, TypeVar
import time
from .numpify import numpify
from .NamedFunction import NamedFunction
import plotly.graph_objects as go
from typing import Any
from sympy import Symbol
import numpy as np
import ipywidgets as widgets
from IPython.display import display


class OneShotOutput(widgets.Output):
    """
    A specialized Output widget that can only be displayed once.

    This widget enforces a one-time display policy to prevent accidental
    duplication in notebook interfaces. Once shown, any subsequent attempts
    to display it will raise a RuntimeError.

    Attributes
    ----------
    _displayed : bool
        Internal flag tracking whether the widget has been displayed.

    Notes
    -----
    - Inherits from ipywidgets.Output
    - Uses __slots__ for memory optimization
    - Designed for use in Jupyter notebook/lab environments

    Examples
    --------
    >>> output = OneShotOutput()
    >>> with output:
    ...     print("This will appear in the output widget")
    >>> output.show()  # First display - works
    >>> output.show()  # Second display - raises RuntimeError
    """

    __slots__ = ('_displayed',)

    def __init__(self):
        """Initialize a new OneShotOutput widget."""
        super().__init__()
        self._displayed = False

    def _repr_mimebundle_(self, include=None, exclude=None, **kwargs):
        """
        IPython rich display hook used by ipywidgets.

        This is what gets called when the widget is displayed (including via
        `display(self)` or by being the last expression in a cell).
        """
        if self._displayed:
            raise RuntimeError(
                "OneShotOutput has already been displayed. "
                "This widget supports only one-time display."
            )
        self._displayed = True
        bundle = super()._repr_mimebundle_(include=include, exclude=exclude, **kwargs)
        return bundle

    @property
    def has_been_displayed(self) -> bool:
        """
        Check if the widget has been displayed.

        Returns
        -------
        bool
            True if the widget has been displayed, False otherwise.
        """
        return self._displayed

    def reset_display_state(self) -> None:
        """
        Reset the display state to allow re-display.

        Warning
        -------
        This method should be used with caution as it bypasses the 
        one-time display protection.
        """
        self._displayed = False
# === END SECTION: OneShotOutput [id: OneShotOutput]===



# === SECTION: SmartFigure [id: SmartFigure]===
from .InputConvert import InputConvert


class SmartPlot():

    def __init__(self, var, func, smart_figure, parameters=None, x_domain=None, sampling_points=None, label="", visible=True):
        self._smart_figure = smart_figure
        self._smart_figure.add_scatter(x=[], y=[], mode='lines')
        self._plot_handle = self._smart_figure._figure.data[-1]

        self._suspend_render = True

        self.set_var_func(var, func, parameters)  # Private method 
        
        self.x_domain = x_domain

        self.sampling_points = sampling_points
        self.label = label
        self.visible = visible

        self._suspend_render = False

        self.render()

        # raise NotImplementedError("SmartPlot is not implemented yet.")

    def set_var_func(self, var, func, parameters=None):
        self._var = var
        self._parameters = parameters
        self.func = func

    @property
    def var(self):
        return self._var


    @property
    def func(self):
        return self._func

    @func.setter
    def func(self, value):
        self._func = value
        self._f_numpy = numpify(value, args=[self._var,] + (self._parameters or []) )
        self.render()

    @property
    def label(self):
        return self._plot_handle.name

    @label.setter
    def label(self, value):
        self._plot_handle.name = value

    @property
    def x_domain(self):
        return self._x_domain

    @x_domain.setter
    def x_domain(self, value):
        if value is not None: # Value normalization 
            x_min, x_max = value
            value = (InputConvert(x_min, dest_type=float), InputConvert(x_max, dest_type=float))
            if x_min > x_max:
                raise ValueError(f"x_min ({x_min}) must be less than x_max ({x_max})")
            
        self._x_domain = value
        self.render()

    @property
    def sampling_points(self):
        return self._sampling_points

    @sampling_points.setter
    def sampling_points(self, value):
        if value is not None:
            value = InputConvert(value, dest_type=int)
        self._sampling_points = value
        self.render()

    @property
    def visible(self):
        return self._plot_handle.visible

    @visible.setter
    def visible(self, value):
        self._plot_handle.visible = value
        self.render()

    def compute_data(self):
        viewport_x_range = self._smart_figure.current_x_range
        if self.x_domain is None:
            x_min = viewport_x_range[0]
            x_max = viewport_x_range[1]
        else:
            x_min = min(viewport_x_range[0], self.x_domain[0])
            x_max = max(viewport_x_range[1], self.x_domain[1])

        if self.sampling_points is None:
            num = self._smart_figure.sampling_points
        else:
            num = self.sampling_points

        x_values = np.linspace(x_min, x_max, num=num)

    
        args= [x_values]
        if self._parameters is not None:
            for param in self._parameters:
                args.append(self._smart_figure._params[param].value)
        
        y_values = self._f_numpy(*args)
        return x_values, y_values

    def render(self):
        if self._suspend_render:
            return
        if not self.visible == True:
            return
        x_values, y_values = self.compute_data()
        self._plot_handle.x = x_values
        self._plot_handle.y = y_values
    
    def update(self, var, func, label=None, x_domain=None, sampling_points=None):
        if label is not None:
            self.label = label
        if x_domain is not None:
            if x_domain=="figure_default":
                self.x_domain = None
            self.x_domain = x_domain
        if func is not None or var is not None:
            if var is None:
                var = self.var
            if func is None:
                func = self.func    
            self.set_var_func(var, func)
        if sampling_points is not None:
            if sampling_points=="figure_default":
                self.sampling_points = None
            self.sampling_points = sampling_points
        
        

from .SmartSlider import SmartFloatSlider

class SmartFigure():
    """
    A class for creating smart figures with enhanced functionalities.

    Uses Plotly for interactive visualizations.
    """
    __slots__ = ['_figure', '_output', 'plots',
                 '_sampling_points', '_x_range', '_y_range',
                 '_current_x_range', '_current_y_range', '_debug', '_last_relayout', '_controls_panel', '_params']

    # API
    # ------------
    _figure: go.FigureWidget  # the plotly figure widget
    _output: OneShotOutput  # the output widget to display the figure
    plots: dict  # dictionary to store plots by name

    _sampling_points: int  # default number of sampling points
    _x_range: tuple  # default x-axis range
    _y_range: tuple  # default y-axis range

    def __init__(self,
                 sampling_points: int = 500,
                 x_range: tuple = (-4, 4),
                 y_range: tuple = (-3, 3),
                 debug: bool = False
                 ):

        self._debug = debug
        self._output = OneShotOutput()

        # --- Figure layout setup ---
        with self._output:
            # 1. Create the FigureWidget
            self._figure = go.FigureWidget()

            # 2. Create the Layout Containers
            # Right Panel: Sidebar with a title
            self._controls_panel = widgets.VBox(
                [widgets.HTML(value="<b>Parameters</b>")],  # Title added here
                layout=widgets.Layout(width='400px', padding='0px 0px 0px 10px')
            )

            # Left Panel: Plot area (flex='1' makes it fill available space)
            _plot_panel = widgets.VBox(
                [self._figure],
                layout=widgets.Layout(flex='1') 
            )

            # Main Container: Combines Left and Right
            _main_layout = widgets.HBox(
                [_plot_panel, self._controls_panel],
                layout=widgets.Layout(width='100%', align_items='flex-start')
            )

            # 3. Display the layout
            display(_main_layout)

            if self._debug:
                print("Debug:")

            # 4. Configure the Plot
            # Removed fixed width, added autosize=True so it fills the left panel
            self._figure.update_layout(
                height=600,
                autosize=True, 
                template="plotly_white",
                showlegend=True,
                xaxis=dict(title='x',
                           zeroline=True,
                           zerolinewidth=2,
                           zerolinecolor='black',
                           showline=True,
                           ticks='outside',),
                yaxis=dict(title='y', 
                           zeroline=True,
                           zerolinewidth=2,
                           zerolinecolor='black',
                           showline=True,
                           ticks='outside',
                           ),
                title=dict(
                    x=0.5,
                    y=0.95,
                    xanchor='center'
                )
            )
            # --- End of figure layout setup ---

        if sampling_points=="figure_default":
            self.sampling_points = None
        else:
            self.sampling_points = sampling_points

        self.x_range = x_range
        self.y_range = y_range

        self.plots = {}

        self._params = {}

        

        self._last_relayout = time.monotonic()
        self._figure.layout.on_change(
            self._throttled_axis_range_callback, 'xaxis.range', 'yaxis.range')


    def _throttled_axis_range_callback(self, attr, old, new):
        if time.monotonic() - self._last_relayout < 0.5:
            return
        self._last_relayout = time.monotonic()

        if self._debug:
            with self._output:
                # print(f"Relayout event detected: from {old} to {new}")
                pass
        self.render()

    
    def add_param(self, parameter_id,value=0.0, min=-1, max=1, step=0.01):
        """
        Add a SmartFloatSlider parameter to the controls panel.

        Parameters
        ----------
        name : str
            The name of the parameter.
        slider : SmartFloatSlider
            The slider widget to add.
        """
        
        description = f"${sp.latex(parameter_id)}$" # Can be enriched later

        slider = SmartFloatSlider(description=description, value=value, min=min, max=max, step=step)
        self._controls_panel.children += (slider,)
        self._params[parameter_id] = slider

        def rerender_on_param_change(change):
            self.render()
        slider.observe(rerender_on_param_change, names='value')
        return 
        

    @property
    def title(self):
        return self._figure.layout.title.text

    @title.setter
    def title(self, value):
        self.update_layout(
            title=dict(
                text=value,  # Your title text here
            )
        )

    @property
    def x_range(self):
        return self._x_range

    @x_range.setter
    def x_range(self, value):
        x_min, x_max = value
        value = (InputConvert(x_min, dest_type=float), InputConvert(x_max, dest_type=float))
        if x_min > x_max:
            raise ValueError(f"x_min ({x_min}) must be less than x_max ({x_max})")
        self._figure.update_xaxes(range=value)
        self._x_range = value

    @property
    def y_range(self):
        return self._y_range

    @y_range.setter
    def y_range(self, value):
        y_min, y_max = value
        value = (InputConvert(y_min, dest_type=float), InputConvert(y_max, dest_type=float))
        if y_min > y_max:
            raise ValueError(f"y_min ({y_min}) must be less than y_max ({y_max})")  
        self._figure.update_yaxes(range=value)
        self._y_range = value

    @property
    def current_x_range(self):
        return self._figure.layout.xaxis.range

    @property
    def current_y_range(self):
        return self._figure.layout.yaxis.range

    @property
    def sampling_points(self):
        return self._sampling_points

    @sampling_points.setter
    def sampling_points(self, value):
        self._sampling_points = value

    def add_scatter(self, **scatter_kwargs):
        """
        Add a scatter trace to the figure.

        Parameters
        ----------
        scatter_kwargs : dict
            Keyword arguments for the scatter trace.
        """
        self._figure.add_scatter(**scatter_kwargs)

    def _ipython_display_(self, **kwargs):
        """
        IPython display hook to show the figure in Jupyter notebooks.
        """
        display(self._output)
        return self._output

    def update_layout(self, **layout_kwargs):
        """
        Update the layout of the figure.

        Parameters
        ----------
        layout_kwargs : dict
            Keyword arguments for updating the figure layout.
        """
        self._figure.update_layout(**layout_kwargs)

    def plot(self, var, func, parameters=None, id=None, x_domain=None, sampling_points=None):
        """
        Plot a function on the figure.

        Parameters
        ----------
        var : SymPy symbol
            independent variable.
        func : SymPy expression
            expression to plot.
        id : str, optional
            The unique identifier for the plot.
        x_domain : array-like, optional
            The domain of the x-axis. If not provided, the viewport range will be rendered.
        sampling_points : int, optional
            Number of sampling points for the plot. If not provided, or "figure_default", the figure's default will be used.
        """
        if id is None:
            for n in range(101):  # 0 to 100 inclusive
                if id not in self.plots:
                    id = f"f_{n}"
                    break
            if id is None: 
                raise ValueError("No available f_n identifiers (max 100 reached)")
            
        if parameters is not None:
            print(f"Parameters: {parameters}")

        if id in self.plots:
                plot=self.plots[id]
                plot.update(var, func, label=None, x_domain=x_domain, sampling_points=sampling_points)
        else:
            plot = SmartPlot(
                var=var,
                func=func,
                smart_figure=self,
                parameters=parameters,
                x_domain=None,
                label=str(id),
                sampling_points=sampling_points
            )
            self.plots[id] = plot

        return plot

    def render(self):
        """
        Render all plots on the figure.
        """
        with self._figure.batch_update():
            for plot in self.plots.values():
                plot.render()


# === END SECTION: SmartFigure [id: SmartFigure]===
