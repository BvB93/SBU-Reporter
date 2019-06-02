"""yaml templates for DataFrame plotting."""

from os.path import (join, dirname)
import yaml

_filename = join(dirname(__file__), 'palette.yaml')
with open(_filename, 'r') as f:
    lineplot_dict = yaml.load(f, Loader=yaml.Loader)
    style_overide = lineplot_dict.pop('style_overide')

__all__ = ['lineplot_dict', 'style_overide']
