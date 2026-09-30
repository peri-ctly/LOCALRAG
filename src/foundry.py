
"""
This module initializes Foundry Local and creates a shared manager
instance that can be used by other modules in the project.
"""

from foundry_local_sdk import (
    Configuration,
    FoundryLocalManager
)


# Foundry Local configuration
 
config = Configuration(
    app_name="LocalRAG",
    model_cache_dir=r"D:\FoundryCache",
    log_level="Info"
)



# Initialize Foundry Local
FoundryLocalManager.initialize( config )


# Get shared manager instance
manager = FoundryLocalManager.instance




try:
    print("Registering CUDAExecutionProvider...")

    manager.download_and_register_eps(
        ["CUDAExecutionProvider"]
    )

    print("CUDAExecutionProvider registered.")

except Exception as error:
    print(f"CUDA EP registration skipped: {error}")