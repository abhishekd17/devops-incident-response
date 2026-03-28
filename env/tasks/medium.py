from env.models import TaskConfig

def get_medium_task():
    return TaskConfig(
        task_id="medium_cascade",
        name="Cascading Dependency Failure",
        difficulty="medium",
        description="ALERT: Multiple services DOWN. Find root cause and fix in order.",
        max_steps=20,
        services=["api-gateway","auth-service","payment-service","order-service","database","message-queue"],
        initial_status={"api-gateway":"UP","auth-service":"UP","payment-service":"DOWN","order-service":"DOWN","database":"DOWN","message-queue":"UP"},
        alert_message="INCIDENT ALERT - Severity: CRITICAL\nMultiple services DOWN:\n  - payment-service: DOWN\n  - order-service: DOWN\nImpact: All payments and orders failing\nTime: 2024-03-25 03:12:00 UTC\nInvestigate root cause and restore services.",
        root_cause="disk_full",
        root_cause_service="database",
        affected_services=["database","payment-service","order-service"],
        correct_fix="restart_service",
        logs={
            "payment-service": "[03:11:50] WARN Database query timeout after 5000ms\n[03:11:55] ERROR Failed to process payment: database connection lost\n[03:11:56] ERROR Connection pool exhausted\n[03:12:00] FATAL payment-service shutting down",
            "order-service": "[03:11:52] WARN Database query slow: 4200ms\n[03:11:55] ERROR Database connection lost\n[03:11:58] FATAL order-service shutting down",
            "database": "[03:11:30] WARN Disk usage at 92%\n[03:11:35] WARN Disk usage at 95%\n[03:11:40] ERROR Disk usage at 99% cannot write WAL logs\n[03:11:41] ERROR PANIC: No space left on device\n[03:11:42] FATAL Database entering READ-ONLY mode\n[03:11:45] FATAL PostgreSQL shutting down due to disk full",
            "api-gateway": "[03:12:00] ERROR POST /api/payment -> payment-service [504] Gateway Timeout\n[03:12:15] ERROR Circuit breaker OPEN for payment-service",
            "auth-service": "[03:12:00] INFO Service healthy. No issues detected.",
            "message-queue": "[03:12:00] WARN Consumer payment-service disconnected\n[03:12:10] WARN Messages accumulating: payments=42, orders=28",
        },
        milestones={"viewed_relevant_log":0.05,"found_error_in_downstream":0.10,"found_error_in_root_service":0.10,"identified_root_cause":0.25,"identified_root_service":0.15,"fixed_root_service_first":0.15,"all_services_restored":0.20},
    )
