import importlib.util
import pathlib

spec = importlib.util.spec_from_file_location(
    __name__,
    pathlib.Path(__file__).with_name('output-format-handler.py')
)
_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(_module)

OutputFormat = _module.OutputFormat
format_content = _module.format_content
to_markdown = _module.to_markdown
to_text = _module.to_text
to_html = _module.to_html
