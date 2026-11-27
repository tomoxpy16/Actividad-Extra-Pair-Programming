"""Worker del MonitorAgent: corre en su propio contenedor y revisa el plan cada N segundos.

Se comunica con la API únicamente a través del estado compartido en PostgreSQL
(estilo pizarra / blackboard), sin acoplamiento directo.
"""
from __future__ import annotations

import logging
import signal
import time

from app.config import config
from app.main import build_orchestrator

log = logging.getLogger("kairos.worker")
_running = True


def _stop(*_: object) -> None:
    global _running
    _running = False


def main() -> None:
    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)
    orchestrator = build_orchestrator()
    log.info("MonitorAgent activo: revisión cada %ss", config.monitor_interval_seconds)
    while _running:
        try:
            result = orchestrator.monitor_tick()
            if result["delays"]:
                log.info("Retrasos detectados: %s -> replanificado", len(result["delays"]))
        except Exception:  # el worker no debe morir por un ciclo fallido
            log.exception("Fallo en el ciclo del monitor")
        for _ in range(config.monitor_interval_seconds):
            if not _running:
                break
            time.sleep(1)
    log.info("MonitorAgent detenido")


if __name__ == "__main__":
    main()
