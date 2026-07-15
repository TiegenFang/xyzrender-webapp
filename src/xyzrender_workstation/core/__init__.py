"""与 Flask、Qt 无关的共享业务服务。"""

from .models import (
    MultiwfnJobResult,
    MultiwfnJobSpec,
    RenderRequest,
    RenderResult,
    ToolSettings,
)
from .multiwfn import MultiwfnService
from .multiwfn_offline import (
    MultiwfnArtifactStore,
    MultiwfnPackageError,
    MultiwfnPackageGenerator,
    MultiwfnTemplateRegistry,
    QuantumInputPackageGenerator,
    inspect_wavefunction_source,
)
from .option_schema import OptionSpec, build_option_schema, parse_option_value
from .render_service import RenderService, UnsupportedRenderOption

__all__ = [
    "MultiwfnJobResult",
    "MultiwfnJobSpec",
    "MultiwfnService",
    "MultiwfnArtifactStore",
    "MultiwfnPackageError",
    "MultiwfnPackageGenerator",
    "MultiwfnTemplateRegistry",
    "QuantumInputPackageGenerator",
    "OptionSpec",
    "RenderRequest",
    "RenderResult",
    "RenderService",
    "ToolSettings",
    "UnsupportedRenderOption",
    "build_option_schema",
    "parse_option_value",
    "inspect_wavefunction_source",
]
