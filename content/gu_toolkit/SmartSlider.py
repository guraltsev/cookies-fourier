import ipywidgets as widgets
import traitlets
import sympy
from .InputConvert import InputConvert


class SmartFloatSlider(widgets.VBox):
    """A FloatSlider with reset, settings, live update toggle, and expression parsing."""

    value = traitlets.Float(0.0)

    def __init__(self, value=0.0, min=0.0, max=1.0, step=0.1, description='Value:', **kwargs):
        # Initialize internal state
        self._defaults = {'value': value, 'min': min, 'max': max, 'step': step}

        # 1. Main Components
        self.slider = widgets.FloatSlider(
            value=value, min=min, max=max, step=step,
            description=description,
            continuous_update=True,
            style={'description_width': 'initial'},
            # Adjusted width for compactness
            layout=widgets.Layout(width='60%')
        )

        # Changed to Text widget to allow expressions (e.g., "pi/2")
        self.text_input = widgets.Text(
            value=str(value),
            layout=widgets.Layout(width='80px')
        )

        self.btn_reset = widgets.Button(
            description='↺', tooltip='Reset', layout=widgets.Layout(width='35px')
        )
        self.btn_settings = widgets.Button(
            description='⚙', tooltip='Settings', layout=widgets.Layout(width='35px')
        )

        # 2. Settings Panel Components
        style_args = {'style': {'description_width': '50px'},
                      'layout': widgets.Layout(width='100px')}
        self.set_min = widgets.FloatText(
            value=min, description='Min:', **style_args)
        self.set_max = widgets.FloatText(
            value=max, description='Max:', **style_args)
        self.set_step = widgets.FloatText(
            value=step, description='Step:', **style_args)
        self.set_live = widgets.Checkbox(
            value=True, description='Live Update', indent=False, layout=widgets.Layout(width='100px'))

        # Settings Container (Hidden by default)
        self.settings_panel = widgets.VBox([
            widgets.HBox(
                [self.set_min, self.set_max, self.set_step]),
            widgets.HBox([self.set_live]),
        ],
            layout=widgets.Layout(
                display='none', border='1px solid #eee', padding='5px', margin='5px 0')
        )

        # 3. Assemble Layout
        top_row = widgets.HBox(
            [self.slider, self.text_input, self.btn_reset, self.btn_settings],
            layout=widgets.Layout(align_items='center')
        )
        super().__init__([top_row, self.settings_panel], **kwargs)

        # 4. Logic & Wiring
        # Sync Slider <-> Class Trait
        traitlets.link((self, 'value'), (self.slider, 'value'))

        # Slider -> Text (One way sync for display)
        self.slider.observe(lambda c: setattr(
            self.text_input, 'value', f"{c.new:.4g}"), names='value')

        # Text -> Slider (with Converter)
        self.text_input.observe(self._handle_text_input, names='value')

        # Buttons
        self.btn_reset.on_click(self._reset)
        self.btn_settings.on_click(self._toggle_settings)

        # Settings Wiring (Using simple links where possible)
        widgets.link((self.set_min, 'value'), (self.slider, 'min'))
        widgets.link((self.set_max, 'value'), (self.slider, 'max'))
        widgets.link((self.set_step, 'value'), (self.slider, 'step'))
        widgets.link((self.set_live, 'value'),
                     (self.slider, 'continuous_update'))

        # Initialize trait
        self.value = value

    def _handle_text_input(self, change):
        """Parses text input. If valid, updates slider. If invalid, reverts text."""
        # Avoid circular updates
        if change.new == str(self.slider.value) or change.new == f"{self.slider.value:.4g}":
            return

        try:
            # Use InputConvert to parse expression
            new_val = InputConvert(
                change.new, dest_type=float, truncate=True)

            # Clamp value
            new_val = max(self.slider.min, min(new_val, self.slider.max))
            self.value = new_val
        except (ValueError, TypeError, SyntaxError):
            # Revert to last valid value on failure
            self.text_input.value = f"{self.value:.4g}"

    def _reset(self, _):
        self.value = self._defaults['value']

    def _toggle_settings(self, _):
        self.settings_panel.layout.display = 'none' if self.settings_panel.layout.display == 'flex' else 'flex'
