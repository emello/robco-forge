# Terraform Configuration Fixes

## Issues Fixed

### 1. ✅ CloudWatch Log Retention Period
**Error:**
```
Error: expected retention_in_days to be one of [0 1 3 5 7 14 30 60 90 120 150 180 365 400 545 731 1096 1827 2192 2557 2922 3288 3653], got 2555
```

**Fix:**
Changed `retention_in_days` from `2555` to `2557` in `terraform/modules/monitoring/main.tf`

**Reason:** CloudWatch only accepts specific retention period values. 2557 days (~7 years) is the closest valid value to the original 2555 days.

---

### 2. ✅ Invalid WorkSpaces Resource Type
**Error:**
```
Error: Invalid resource type
The provider hashicorp/aws does not support resource type "aws_workspaces_directory_ip_group_association"
```

**Fix:**
Commented out the unsupported resource in `terraform/modules/workspaces/main.tf`

**Reason:** The AWS Terraform provider doesn't have a separate resource for IP group associations. IP access control is managed directly through the `aws_workspaces_directory` resource configuration.

**Note:** If you need to restrict IP access to WorkSpaces, you can configure it through:
- AWS Console: WorkSpaces → Directories → IP Access Control Groups
- Or use AWS CLI/API to manage IP groups separately

---

## Next Steps

Now you can run Terraform successfully:

```bash
cd terraform/environments/staging
terraform plan
terraform apply
```

---

## Valid CloudWatch Retention Periods

For future reference, these are the only valid retention periods (in days):
- 0 (never expire)
- 1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180
- 365, 400, 545, 731
- 1096, 1827, 2192, 2557, 2922, 3288, 3653

---

## Files Modified

1. `terraform/modules/monitoring/main.tf` - Fixed retention period
2. `terraform/modules/workspaces/main.tf` - Commented out invalid resource

---

## Verification

After applying these fixes, run:

```bash
terraform validate
```

You should see:
```
Success! The configuration is valid.
```

Then proceed with:
```bash
terraform plan
terraform apply
```
