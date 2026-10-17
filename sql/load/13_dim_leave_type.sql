-- target: dw.dim_leave_type
-- key: leave_type_code
-- stage: stg_dim_leave_type
SELECT leave_type_code, leave_type_name, pay_type, annual_quota_days,
       prorated_for_joiners = 'Y' AS prorated_for_joiners, carry_forward_allowed = 'Y' AS carry_forward_allowed,
       max_carry_forward_days, policy_note
FROM stg_dim_leave_type
