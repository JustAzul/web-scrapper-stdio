import importlib.util
import pathlib

_spec = importlib.util.spec_from_file_location(
    "src.output-format-handler", pathlib.Path(__file__).with_name("output-format-handler.py")
)
_output_format_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_output_format_module)  # type: ignore

OutputFormat = _output_format_module.OutputFormat
format_content = _output_format_module.format_content
truncate_content = _output_format_module.truncate_content
truncate_html = _output_format_module.truncate_html
to_markdown = _output_format_module.to_markdown
to_text = _output_format_module.to_text
to_html = _output_format_module.to_html
