"""CLI entry point for the mortgage underwriting agent system."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def run_demo() -> None:
    """Run the pipeline on the built-in sample application."""
    from src.orchestrator import MortgageUnderwritingOrchestrator, create_sample_application

    orchestrator = MortgageUnderwritingOrchestrator()
    application, uploaded_files = create_sample_application()

    application = orchestrator.process_application(application, uploaded_files)

    print(f"\n{'='*60}")
    print(f"PIPELINE COMPLETE — Final status: {application.status.value}")
    print(f"{'='*60}")

    if application.underwriter_dashboard:
        dashboard = application.underwriter_dashboard
        print(f"\nRisk level   : {dashboard.get('overall_risk_level')}")
        print(f"Recommendation: {dashboard.get('recommendation')}")

        positives = dashboard.get("key_positives", [])
        concerns = dashboard.get("key_concerns", [])
        conditions = dashboard.get("conditions_for_approval", [])

        if positives:
            print("\nKey positives:")
            for p in positives:
                print(f"  + {p}")
        if concerns:
            print("\nKey concerns:")
            for c in concerns:
                print(f"  ! {c}")
        if conditions:
            print("\nConditions for approval:")
            for cond in conditions:
                print(f"  → {cond}")

    if application.pipeline_errors:
        print("\nPipeline errors:")
        for e in application.pipeline_errors:
            print(f"  ✗ {e}")

    # Save full output to outputs/<app_id>.json
    outputs_dir = Path("outputs")
    outputs_dir.mkdir(exist_ok=True)
    output_path = outputs_dir / f"{application.application_id}.json"
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(
            json.loads(application.model_dump_json()),
            f,
            indent=2,
            ensure_ascii=False,
        )
    print(f"\nFull output saved to: {output_path}")


def run_server() -> None:
    """Start the FastAPI underwriter dashboard server."""
    import uvicorn
    sys.path.insert(0, str(Path(__file__).parent))
    print("Underwriting dashboard -> http://127.0.0.1:8000")
    print("Press Ctrl+C to stop.")
    uvicorn.run("src.api.app:app", host="127.0.0.1", port=8000, reload=False, log_level="info")


def run_seed() -> None:
    """Seed demo data for the work queue."""
    import importlib.util, sys as _sys
    spec = importlib.util.spec_from_file_location(
        "create_demo_data", Path(__file__).parent / "create_demo_data.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.main()


def main() -> None:
    args = sys.argv[1:]
    if not args or args[0] == "demo":
        run_demo()
    elif args[0] == "serve":
        run_server()
    elif args[0] == "seed":
        run_seed()
    else:
        print(f"Unknown command: {args[0]}")
        print("Usage: python main.py [demo|serve|seed]")
        sys.exit(1)


if __name__ == "__main__":
    main()
