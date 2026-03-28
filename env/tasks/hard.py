from env.models import TaskConfig

def get_hard_task():
    return TaskConfig(
        task_id="hard_race_condition",
        name="Intermittent Race Condition",
        difficulty="hard",
        description="ALERT: Intermittent 500 errors on checkout. 30% error rate. All services UP.",
        max_steps=25,
        services=["api-gateway","checkout-service","inventory-service","payment-service","redis","batch-reconciliation-job"],
        initial_status={"api-gateway":"UP","checkout-service":"UP","inventory-service":"UP","payment-service":"UP","redis":"UP","batch-reconciliation-job":"UP"},
        alert_message="INCIDENT ALERT - Severity: MEDIUM\nIntermittent errors detected:\n  - checkout endpoint: 30% error rate\n  - No services appear DOWN\n  - All health checks PASSING\nImpact: ~1 in 3 checkout attempts failing\nTime: 2024-03-25 04:08:00 UTC\nInvestigate the pattern and find root cause.",
        root_cause="lock_contention_race_condition",
        root_cause_service="batch-reconciliation-job",
        affected_services=["checkout-service","payment-service","batch-reconciliation-job"],
        correct_fix="restart_service",
        logs={
            "checkout-service": "[04:05:30] INFO Checkout chk_903: reserve_inventory -> OK\n[04:05:30] WARN payment lock acquisition waiting...\n[04:05:33] ERROR payment lock timeout after 3000ms\n[04:05:33] ERROR FAILED - TransactionLockTimeoutException\n[04:06:15] WARN payment lock acquisition waiting...\n[04:06:18] ERROR payment lock timeout after 3000ms",
            "payment-service": "[04:05:30] DEBUG lock for user_1001 held by batch_reconciliation_job\n[04:05:33] ERROR lock timeout for user_1001 (held by batch_reconciliation_job for 3200ms)\n[04:06:15] DEBUG lock for user_1001 held by batch_reconciliation_job\n[04:06:18] ERROR lock timeout for user_1001 (held by batch_reconciliation_job for 2950ms)",
            "redis": "[04:05:28] DEBUG LOCK acquired: payment:user_1001 by batch_reconciliation_job TTL=30000ms\n[04:05:30] DEBUG LOCK denied: payment:user_1001 requested by pay_903 (held by batch_reconciliation_job)\n[04:06:13] DEBUG LOCK acquired: payment:user_1001 by batch_reconciliation_job TTL=30000ms\n[04:06:15] DEBUG LOCK denied: payment:user_1001 requested by pay_906 (held by batch_reconciliation_job)",
            "batch-reconciliation-job": "[04:05:28] INFO Reconciliation cycle started for user_1001\n[04:05:28] INFO Acquired payment lock for user_1001 (TTL=30s)\n[04:05:58] INFO Reconciliation complete. Lock released.\n[04:06:13] INFO Reconciliation cycle started for user_1001\n[04:06:13] INFO Acquired payment lock for user_1001 (TTL=30s)\n[04:06:43] INFO Reconciliation complete. Lock released.",
            "api-gateway": "[04:05:30] ERROR POST /api/checkout -> checkout-service [500] 3042ms\n[04:06:15] ERROR POST /api/checkout -> checkout-service [500] 3105ms\n[04:08:00] WARN Error rate for checkout-service: 30%",
            "inventory-service": "[04:07:00] INFO Service healthy. No errors detected.",
        },
        milestones={"viewed_checkout_log":0.05,"viewed_payment_log":0.05,"viewed_redis_or_batch_log":0.05,"identified_lock_timeout":0.10,"identified_batch_job_conflict":0.15,"identified_root_cause":0.25,"identified_root_service":0.10,"correct_remediation":0.15,"services_restored":0.10},
    )
