$ErrorActionPreference = "Stop"

Push-Location backend
try {
    python -m pytest
}
finally {
    Pop-Location
}

