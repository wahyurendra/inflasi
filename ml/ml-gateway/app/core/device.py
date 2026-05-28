"""GPU/device detection. torch is optional — the service runs CPU-only without it."""


def get_device_info() -> dict:
    try:
        import torch
    except Exception:
        return {"device": "cpu", "gpu": False, "torch": False}

    if torch.cuda.is_available():
        props = torch.cuda.get_device_properties(0)
        return {
            "device": "cuda",
            "gpu": True,
            "name": torch.cuda.get_device_name(0),
            "vram_total_gb": round(props.total_memory / 1e9, 1),
            "vram_allocated_gb": round(torch.cuda.memory_allocated() / 1e9, 2),
        }
    return {"device": "cpu", "gpu": False, "torch": True}
