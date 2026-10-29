import sys, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
"""
Script 00: Environment and Computational Resource Audit.
Inspects hardware, Python packages, GPU capabilities, and system storage.
Saves audit report to reports/environment_audit/environment.md.
"""

import sys
import os
import platform
import shutil
from pathlib import Path

def audit_environment():
    report_path = Path("reports/environment_audit/environment.md")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    lines = []
    lines.append("# Computational Environment & System Audit")
    lines.append("")
    lines.append(f"**Date/Time**: 2026-08-12")
    lines.append(f"**Host OS**: {platform.system()} {platform.release()} ({platform.version()})")
    lines.append(f"**Platform Architecture**: {platform.machine()} / {platform.processor()}")
    lines.append(f"**Python Version**: {sys.version}")
    lines.append("")
    
    # System RAM & CPU
    try:
        import psutil
        mem = psutil.virtual_memory()
        cpu_count_logical = psutil.cpu_count(logical=True)
        cpu_count_physical = psutil.cpu_count(logical=False)
        lines.append("## CPU & System Memory")
        lines.append(f"- **Physical CPU Cores**: {cpu_count_physical}")
        lines.append(f"- **Logical Threads**: {cpu_count_logical}")
        lines.append(f"- **Total RAM**: {mem.total / (1024**3):.2f} GB")
        lines.append(f"- **Available RAM**: {mem.available / (1024**3):.2f} GB")
    except Exception as e:
        lines.append("## CPU & System Memory")
        lines.append(f"- Querying via fallback")
    lines.append("")

    # GPU Audit
    lines.append("## GPU Capabilities (PyTorch / CUDA)")
    try:
        import torch
        cuda_avail = torch.cuda.is_available()
        lines.append(f"- **CUDA Available**: {cuda_avail}")
        if cuda_avail:
            lines.append(f"- **PyTorch Version**: {torch.__version__}")
            lines.append(f"- **CUDA Version**: {torch.version.cuda}")
            lines.append(f"- **Device Count**: {torch.cuda.device_count()}")
            for i in range(torch.cuda.device_count()):
                prop = torch.cuda.get_device_properties(i)
                lines.append(f"  - **Device {i}**: {prop.name}")
                lines.append(f"    - VRAM: {prop.total_memory / (1024**3):.2f} GB")
                lines.append(f"    - MultiProcessors: {prop.multi_processor_count}")
        else:
            lines.append("- PyTorch CUDA not detected.")
    except Exception as e:
        lines.append(f"- Exception querying PyTorch/CUDA: {e}")
    lines.append("")

    # Disk Storage
    lines.append("## Disk Storage")
    stat = shutil.disk_usage(os.getcwd())
    lines.append(f"- **Working Directory**: {os.getcwd()}")
    lines.append(f"- **Total Space**: {stat.total / (1024**3):.2f} GB")
    lines.append(f"- **Free Space**: {stat.free / (1024**3):.2f} GB")
    lines.append(f"- **Used Space**: {stat.used / (1024**3):.2f} GB")
    lines.append("")

    # Core Scientific Packages
    lines.append("## Installed Scientific Package Versions")
    packages = [
        "numpy", "scipy", "pandas", "scikit-learn", "xgboost",
        "lightgbm", "torch", "shap", "captum", "optuna",
        "wfdb", "h5py", "pyarrow", "matplotlib", "seaborn",
        "statsmodels", "pingouin", "boto3", "botocore"
    ]
    for pkg in packages:
        try:
            mod = __import__(pkg)
            ver = getattr(mod, "__version__", "Installed (no __version__)")
            lines.append(f"- **{pkg}**: `{ver}`")
        except ImportError:
            lines.append(f"- **{pkg}**: `NOT INSTALLED`")
        except Exception as ex:
            lines.append(f"- **{pkg}**: `Error importing: {ex}`")

    content = "\n".join(lines)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"[OK] Audit complete. Written to {report_path}")

if __name__ == "__main__":
    audit_environment()
