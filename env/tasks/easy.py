from env.models import TaskConfig

def get_easy_task():
    return TaskConfig(
        task_id="easy_oom_crash",
        name="Single Service OOM Crash",
        difficulty="easy",
        description="ALERT: payment-service is DOWN. Investigate and restore.",
        max_steps=15,
        services=["api-gateway","auth-service","payment-service","database","message-queue"],
        initial_status={"api-gateway":"UP","auth-service":"UP","payment-service":"DOWN","database":"UP","message-queue":"UP"},
        alert_message="INCIDENT ALERT - Severity: HIGH\nService: payment-service is DOWN\nImpact: All payment transactions failing\nTime: 2024-03-25 02:45:32 UTC\nInvestigate and resolve immediately.",
        root_cause="out_of_memory",
        root_cause_service="payment-service",
        affected_services=["payment-service"],
        correct_fix="restart_service",
        logs={
            "payment-service": "[02:44:15] WARN Memory usage at 78%\n[02:44:45] WARN Memory usage at 85%\n[02:45:02] WARN Memory usage at 91%\n[02:45:30] ERROR Memory usage at 97%\n[02:45:31] ERROR java.lang.OutOfMemoryError: Java heap space\n[02:45:31] FATAL Service crashed - OOM Killer invoked\n[02:45:32] FATAL payment-service PID 1842 killed by OOM killer",
            "api-gateway": "[02:45:33] ERROR POST /api/payment -> payment-service [502] Connection refused\n[02:45:40] ERROR Circuit breaker OPEN for payment-service",
            "auth-service": "[02:46:00] INFO Service healthy. Uptime: 5m",
            "database": "[02:46:00] INFO All systems nominal. Active connections: 2",
            "message-queue": "[02:45:32] WARN Consumer disconnected from payments queue\n[02:45:33] WARN Messages accumulating: 15 pending",
        },
        milestones={"viewed_relevant_log":0.10,"found_error_message":0.15,"identified_affected_service":0.15,"identified_root_cause":0.30,"correct_remediation":0.20,"services_restored":0.10},
    )
