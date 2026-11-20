# synthetic-electorate-toy: source and docs, part 3 of 16

Generated from commit `2d80910f7eef` (2026-11-20) of github.com/partyhat-ai/synthetic-electorate-toy by `scripts/llms_digest.py`, which `.github/workflows/llms-digest.yml` reruns on every push to `main`, so this text matches the code at that commit.
Files `infra/backup.tf` to `scripts/harness/build_franchise.py`. Lines are numbered as in the repository.

## `infra/backup.tf`

```hcl
    1| # Daily EFS backups, 35 days. Production state diverges from git the moment
    2| # the worker models anything, and 46 of the 60 bundles can't be regenerated.
    3| 
    4| resource "aws_backup_vault" "state" {
    5|   name = "${local.name}-state"
    6| }
    7| 
    8| resource "aws_backup_plan" "state" {
    9|   name = "${local.name}-state-daily"
   10|   rule {
   11|     rule_name         = "daily"
   12|     target_vault_name = aws_backup_vault.state.name
   13|     schedule          = "cron(0 7 * * ? *)"
   14|     lifecycle { delete_after = 35 }
   15|   }
   16| }
   17| 
   18| data "aws_iam_policy_document" "backup_assume" {
   19|   statement {
   20|     actions = ["sts:AssumeRole"]
   21|     principals {
   22|       type        = "Service"
   23|       identifiers = ["backup.amazonaws.com"]
   24|     }
   25|   }
   26| }
   27| 
   28| resource "aws_iam_role" "backup" {
   29|   name               = "${local.name}-backup"
   30|   assume_role_policy = data.aws_iam_policy_document.backup_assume.json
   31| }
   32| 
   33| resource "aws_iam_role_policy_attachment" "backup" {
   34|   role       = aws_iam_role.backup.name
   35|   policy_arn = "arn:aws:iam::aws:policy/service-role/AWSBackupServiceRolePolicyForBackup"
   36| }
   37| 
   38| resource "aws_iam_role_policy_attachment" "restore" {
   39|   role       = aws_iam_role.backup.name
   40|   policy_arn = "arn:aws:iam::aws:policy/service-role/AWSBackupServiceRolePolicyForRestores"
   41| }
   42| 
   43| resource "aws_backup_selection" "state" {
   44|   name         = "${local.name}-efs"
   45|   plan_id      = aws_backup_plan.state.id
   46|   iam_role_arn = aws_iam_role.backup.arn
   47|   resources    = [aws_efs_file_system.state.arn]
   48| }
```

## `infra/bootstrap.sh`

```bash
    1| #!/usr/bin/env bash
    2| # One-time: the Terraform state bucket. Re-runnable (every step is idempotent).
    3| # Run before the first `terraform init`.
    4| set -euo pipefail
    5| 
    6| B=simulacra-americana-tfstate
    7| test "$(aws sts get-caller-identity --query Account --output text)" = "${AWS_ACCOUNT_ID:?set AWS_ACCOUNT_ID to the target AWS account}"
    8| 
    9| if ! aws s3api head-bucket --bucket "$B" 2>/dev/null; then
   10|   aws s3api create-bucket --bucket "$B" --region us-east-1 --object-ownership BucketOwnerEnforced >/dev/null
   11| fi
   12| aws s3api put-public-access-block --bucket "$B" --public-access-block-configuration \
   13|   BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
   14| aws s3api put-bucket-encryption --bucket "$B" --server-side-encryption-configuration \
   15|   '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"},"BucketKeyEnabled":true}]}'
   16| aws s3api put-bucket-versioning --bucket "$B" --versioning-configuration Status=Enabled
   17| aws s3api put-bucket-tagging --bucket "$B" --tagging 'TagSet=[{Key=project,Value=simulacra-americana}]'
   18| echo "state bucket $B ready"
```

## `infra/cloudfront.tf`

```hcl
    1| # assets.simulacraamericana.com: CloudFront over the private assets bucket.
    2| # Only the robot assets and portraits; the site itself is served by Vercel.
    3| 
    4| resource "aws_cloudfront_origin_access_control" "assets" {
    5|   name                              = "${local.name}-assets"
    6|   origin_access_control_origin_type = "s3"
    7|   signing_behavior                  = "always"
    8|   signing_protocol                  = "sigv4"
    9| }
   10| 
   11| # Assets are versioned with ?v=, so the query string is part of the key.
   12| resource "aws_cloudfront_cache_policy" "assets" {
   13|   name        = "${local.name}-assets"
   14|   min_ttl     = 0
   15|   default_ttl = 86400
   16|   max_ttl     = 31536000
   17|   parameters_in_cache_key_and_forwarded_to_origin {
   18|     enable_accept_encoding_brotli = true
   19|     enable_accept_encoding_gzip   = true
   20|     cookies_config { cookie_behavior = "none" }
   21|     headers_config { header_behavior = "none" }
   22|     query_strings_config { query_string_behavior = "all" }
   23|   }
   24| }
   25| 
   26| resource "aws_cloudfront_response_headers_policy" "assets" {
   27|   name = "${local.name}-assets-cors"
   28|   cors_config {
   29|     access_control_allow_credentials = false
   30|     access_control_allow_headers { items = ["*"] }
   31|     access_control_allow_methods { items = ["GET", "HEAD"] }
   32|     access_control_allow_origins { items = var.cors_origins }
   33|     access_control_max_age_sec = 86400
   34|     origin_override            = true
   35|   }
   36| }
   37| 
   38| resource "aws_cloudfront_distribution" "assets" {
   39|   enabled         = true
   40|   is_ipv6_enabled = true
   41|   comment         = "Simulacra Americana robot assets and portraits"
   42|   aliases         = ["assets.${var.domain}"]
   43|   price_class     = "PriceClass_100"
   44|   http_version    = "http2and3"
   45| 
   46|   origin {
   47|     origin_id                = "assets-s3"
   48|     domain_name              = aws_s3_bucket.assets.bucket_regional_domain_name
   49|     origin_access_control_id = aws_cloudfront_origin_access_control.assets.id
   50|   }
   51| 
   52|   default_cache_behavior {
   53|     target_origin_id           = "assets-s3"
   54|     viewer_protocol_policy     = "redirect-to-https"
   55|     allowed_methods            = ["GET", "HEAD", "OPTIONS"]
   56|     cached_methods             = ["GET", "HEAD", "OPTIONS"]
   57|     compress                   = true
   58|     cache_policy_id            = aws_cloudfront_cache_policy.assets.id
   59|     response_headers_policy_id = aws_cloudfront_response_headers_policy.assets.id
   60|   }
   61| 
   62|   restrictions {
   63|     geo_restriction { restriction_type = "none" }
   64|   }
   65| 
   66|   viewer_certificate {
   67|     acm_certificate_arn      = aws_acm_certificate_validation.assets.certificate_arn
   68|     ssl_support_method       = "sni-only"
   69|     minimum_protocol_version = "TLSv1.2_2021"
   70|   }
   71| }
```

## `infra/ecs.tf`

```hcl
    1| # One cluster, one service, ONE task, on purpose: run state is an in-process
    2| # Map, the worker lock is a PID file (PIDs aren't unique across containers),
    3| # and two tasks would run two workers against the same EFS queue. So
    4| # desiredCount 1 and the old task stops before the new one starts
    5| # (minimumHealthyPercent 0 / maximumPercent 100): a few seconds of 503 per
    6| # deploy. The circuit breaker rolls back a revision that never gets healthy.
    7| #
    8| # The task definition is rendered from infra/taskdef.json.tftpl, here for the
    9| # first revision and by deploy-api.yml for every later one, so env and secrets
   10| # can't silently drop on a deploy. The service ignores task-definition drift.
   11| 
   12| resource "aws_ecr_repository" "api" {
   13|   name = "simulacra-api"
   14|   # SHA tags are immutable; the one moving tag is the registry layer cache
   15|   # deploy-api.yml writes on every build.
   16|   image_tag_mutability = "IMMUTABLE_WITH_EXCLUSION"
   17|   image_tag_mutability_exclusion_filter {
   18|     filter      = "buildcache"
   19|     filter_type = "WILDCARD"
   20|   }
   21|   image_scanning_configuration { scan_on_push = true }
   22| }
   23| 
   24| resource "aws_ecr_lifecycle_policy" "api" {
   25|   repository = aws_ecr_repository.api.name
   26|   policy = jsonencode({
   27|     rules = [{
   28|       rulePriority = 1
   29|       description  = "Keep the last 30 images (rollback depth)"
   30|       selection    = { tagStatus = "any", countType = "imageCountMoreThan", countNumber = 30 }
   31|       action       = { type = "expire" }
   32|     }]
   33|   })
   34| }
   35| 
   36| resource "aws_ecs_cluster" "main" {
   37|   name = local.name
   38|   setting {
   39|     name  = "containerInsights"
   40|     value = "disabled"
   41|   }
   42| }
   43| 
   44| locals {
   45|   taskdef_vars = {
   46|     image              = var.image
   47|     cpu                = var.task_cpu
   48|     memory             = var.task_memory
   49|     execution_role_arn = aws_iam_role.execution.arn
   50|     task_role_arn      = aws_iam_role.task.arn
   51|     efs_id             = aws_efs_file_system.state.id
   52|     access_point_id    = aws_efs_access_point.state.id
   53|     secret_arn         = aws_secretsmanager_secret.prod.arn
   54|     log_group          = aws_cloudwatch_log_group.api.name
   55|     region             = local.region
   56|   }
   57|   taskdef = jsondecode(templatefile("${path.module}/taskdef.json.tftpl", local.taskdef_vars))
   58| }
   59| 
   60| resource "aws_ecs_task_definition" "api" {
   61|   family                   = local.taskdef.family
   62|   network_mode             = local.taskdef.networkMode
   63|   requires_compatibilities = local.taskdef.requiresCompatibilities
   64|   cpu                      = local.taskdef.cpu
   65|   memory                   = local.taskdef.memory
   66|   execution_role_arn       = local.taskdef.executionRoleArn
   67|   task_role_arn            = local.taskdef.taskRoleArn
   68|   container_definitions    = jsonencode(local.taskdef.containerDefinitions)
   69|   runtime_platform {
   70|     cpu_architecture        = "ARM64"
   71|     operating_system_family = "LINUX"
   72|   }
   73|   volume {
   74|     name = "state"
   75|     efs_volume_configuration {
   76|       file_system_id     = aws_efs_file_system.state.id
   77|       transit_encryption = "ENABLED"
   78|       authorization_config {
   79|         access_point_id = aws_efs_access_point.state.id
   80|         iam             = "ENABLED"
   81|       }
   82|     }
   83|   }
   84|   # Only the first revision comes from here (var.image at stand-up); CI
   85|   # registers every later one from the same template.
   86|   lifecycle { ignore_changes = [container_definitions] }
   87| }
   88| 
   89| resource "aws_ecs_service" "api" {
   90|   name                               = "simulacra-api"
   91|   cluster                            = aws_ecs_cluster.main.id
   92|   task_definition                    = aws_ecs_task_definition.api.arn
   93|   desired_count                      = 1
   94|   launch_type                        = "FARGATE"
   95|   platform_version                   = "LATEST"
   96|   deployment_minimum_healthy_percent = 0
   97|   deployment_maximum_percent         = 100
   98|   health_check_grace_period_seconds  = 60
   99|   enable_execute_command             = false
  100| 
  101|   deployment_circuit_breaker {
  102|     enable   = true
  103|     rollback = true
  104|   }
  105| 
  106|   network_configuration {
  107|     subnets          = var.subnet_ids
  108|     security_groups  = [aws_security_group.task.id]
  109|     assign_public_ip = true
  110|   }
  111| 
  112|   load_balancer {
  113|     target_group_arn = aws_lb_target_group.api.arn
  114|     container_name   = "api"
  115|     container_port   = 8080
  116|   }
  117| 
  118|   lifecycle { ignore_changes = [task_definition] }
  119|   depends_on = [aws_lb_listener.https, aws_efs_mount_target.state]
  120| }
  121| 
  122| # A one-off task (scripts/sync-data.sh) that copies from the private data
  123| # bucket onto EFS: `seed` once, `cache` whenever the census data changes.
  124| resource "aws_ecs_task_definition" "seed" {
  125|   family                   = "simulacra-seed"
  126|   network_mode             = "awsvpc"
  127|   requires_compatibilities = ["FARGATE"]
  128|   cpu                      = 256
  129|   memory                   = 512
  130|   execution_role_arn       = aws_iam_role.execution.arn
  131|   task_role_arn            = aws_iam_role.task.arn
  132|   runtime_platform {
  133|     cpu_architecture        = "ARM64"
  134|     operating_system_family = "LINUX"
  135|   }
  136|   volume {
  137|     name = "state"
  138|     efs_volume_configuration {
  139|       file_system_id     = aws_efs_file_system.state.id
  140|       transit_encryption = "ENABLED"
  141|       authorization_config {
  142|         access_point_id = aws_efs_access_point.state.id
  143|         iam             = "ENABLED"
  144|       }
  145|     }
  146|   }
  147|   container_definitions = jsonencode([{
  148|     name       = "seed"
  149|     image      = "public.ecr.aws/aws-cli/aws-cli:latest"
  150|     essential  = true
  151|     entryPoint = ["sh", "-c"]
  152|     # MODE=seed copies only into an unseeded volume (marker file), so it can
  153|     # never overwrite what production has written. MODE=cache replaces the
  154|     # census-derived cache wholesale (read-only data).
  155|     command = [<<-EOT
  156|       set -eu
  157|       case "$MODE" in
  158|         seed)
  159|           if [ -e /state/.seeded ]; then echo "already seeded; refusing"; exit 0; fi
  160|           aws s3 sync "s3://${aws_s3_bucket.data.bucket}/seed/" /state/ --only-show-errors
  161|           aws s3 sync "s3://${aws_s3_bucket.data.bucket}/cache/" /state/cache/ --only-show-errors
  162|           date -u +%FT%TZ > /state/.seeded ;;
  163|         cache)
  164|           aws s3 sync "s3://${aws_s3_bucket.data.bucket}/cache/" /state/cache/ --delete --only-show-errors ;;
  165|         *) echo "MODE must be seed or cache"; exit 2 ;;
  166|       esac
  167|       find /state -maxdepth 1 | sort
  168|     EOT
  169|     ]
  170|     environment = [{ name = "MODE", value = "seed" }]
  171|     mountPoints = [{ sourceVolume = "state", containerPath = "/state" }]
  172|     logConfiguration = {
  173|       logDriver = "awslogs"
  174|       options = {
  175|         "awslogs-group"         = aws_cloudwatch_log_group.api.name
  176|         "awslogs-region"        = local.region
  177|         "awslogs-stream-prefix" = "seed"
  178|       }
  179|     }
  180|   }])
  181| }
```

## `infra/efs.tf`

```hcl
    1| # The service's state: serve/bundles, sessions, runs, whatifs, configs and
    2| # the census-derived cache, all under one access point owned by the image's
    3| # `app` user (uid 1000). The image symlinks the code-relative folders here.
    4| 
    5| resource "aws_efs_file_system" "state" {
    6|   creation_token   = "${local.name}-state"
    7|   encrypted        = true
    8|   performance_mode = "generalPurpose"
    9|   throughput_mode  = "elastic"
   10|   lifecycle_policy {
   11|     transition_to_ia = "AFTER_30_DAYS"
   12|   }
   13|   tags = { Name = "${local.name}-state" }
   14| }
   15| 
   16| resource "aws_efs_mount_target" "state" {
   17|   for_each        = toset(var.subnet_ids)
   18|   file_system_id  = aws_efs_file_system.state.id
   19|   subnet_id       = each.value
   20|   security_groups = [aws_security_group.efs.id]
   21| }
   22| 
   23| resource "aws_efs_access_point" "state" {
   24|   file_system_id = aws_efs_file_system.state.id
   25|   posix_user {
   26|     uid = 1000
   27|     gid = 1000
   28|   }
   29|   root_directory {
   30|     path = "/simulacra"
   31|     creation_info {
   32|       owner_uid   = 1000
   33|       owner_gid   = 1000
   34|       permissions = "0755"
   35|     }
   36|   }
   37|   tags = { Name = "${local.name}-state" }
   38| }
   39| 
   40| # Only through the access point, only over TLS, only by the task role.
   41| resource "aws_efs_file_system_policy" "state" {
   42|   file_system_id = aws_efs_file_system.state.id
   43|   policy = jsonencode({
   44|     Version = "2012-10-17"
   45|     Statement = [
   46|       {
   47|         Sid       = "TaskRoleViaAccessPoint"
   48|         Effect    = "Allow"
   49|         Principal = { AWS = aws_iam_role.task.arn }
   50|         Action    = ["elasticfilesystem:ClientMount", "elasticfilesystem:ClientWrite"]
   51|         Resource  = aws_efs_file_system.state.arn
   52|         Condition = {
   53|           StringEquals = { "elasticfilesystem:AccessPointArn" = aws_efs_access_point.state.arn }
   54|           Bool         = { "aws:SecureTransport" = "true" }
   55|         }
   56|       }
   57|     ]
   58|   })
   59| }
```

## `infra/iam.tf`

```hcl
    1| # Three roles, no static keys anywhere.
    2| #   execution: ECS pulls the image, writes logs, reads the one secret.
    3| #   task:      the running container: EFS client, read of the data bucket (seed/sync).
    4| #   deploy:    GitHub Actions via OIDC: push to this ECR repo, register task
    5| #              defs, roll this one service, read this log group.
    6| 
    7| data "aws_iam_policy_document" "ecs_tasks_assume" {
    8|   statement {
    9|     actions = ["sts:AssumeRole"]
   10|     principals {
   11|       type        = "Service"
   12|       identifiers = ["ecs-tasks.amazonaws.com"]
   13|     }
   14|     condition {
   15|       test     = "StringEquals"
   16|       variable = "aws:SourceAccount"
   17|       values   = [local.account_id]
   18|     }
   19|   }
   20| }
   21| 
   22| resource "aws_iam_role" "execution" {
   23|   name               = "${local.name}-execution"
   24|   assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume.json
   25| }
   26| 
   27| resource "aws_iam_role_policy_attachment" "execution_managed" {
   28|   role       = aws_iam_role.execution.name
   29|   policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
   30| }
   31| 
   32| resource "aws_iam_role_policy" "execution_secret" {
   33|   name = "read-prod-secret"
   34|   role = aws_iam_role.execution.id
   35|   policy = jsonencode({
   36|     Version = "2012-10-17"
   37|     Statement = [{
   38|       Effect   = "Allow"
   39|       Action   = ["secretsmanager:GetSecretValue"]
   40|       Resource = aws_secretsmanager_secret.prod.arn
   41|     }]
   42|   })
   43| }
   44| 
   45| resource "aws_iam_role" "task" {
   46|   name               = "${local.name}-task"
   47|   assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume.json
   48| }
   49| 
   50| resource "aws_iam_role_policy" "task" {
   51|   name = "efs-and-data-read"
   52|   role = aws_iam_role.task.id
   53|   policy = jsonencode({
   54|     Version = "2012-10-17"
   55|     Statement = [
   56|       {
   57|         Sid      = "EfsClient"
   58|         Effect   = "Allow"
   59|         Action   = ["elasticfilesystem:ClientMount", "elasticfilesystem:ClientWrite"]
   60|         Resource = aws_efs_file_system.state.arn
   61|         Condition = {
   62|           StringEquals = { "elasticfilesystem:AccessPointArn" = aws_efs_access_point.state.arn }
   63|         }
   64|       },
   65|       {
   66|         Sid      = "DataBucketRead"
   67|         Effect   = "Allow"
   68|         Action   = ["s3:GetObject", "s3:ListBucket"]
   69|         Resource = [aws_s3_bucket.data.arn, "${aws_s3_bucket.data.arn}/*"]
   70|       }
   71|     ]
   72|   })
   73| }
   74| 
   75| # The account's GitHub OIDC provider already exists (the auth server's deploy
   76| # uses it). Read it; never manage it from this stack.
   77| data "aws_iam_openid_connect_provider" "github" {
   78|   url = "https://token.actions.githubusercontent.com"
   79| }
   80| 
   81| resource "aws_iam_role" "deploy" {
   82|   name = "${local.name}-gha-deploy"
   83|   assume_role_policy = jsonencode({
   84|     Version = "2012-10-17"
   85|     Statement = [{
   86|       Effect    = "Allow"
   87|       Principal = { Federated = data.aws_iam_openid_connect_provider.github.arn }
   88|       Action    = "sts:AssumeRoleWithWebIdentity"
   89|       # Exact match, no wildcard: one repo, one branch (var.github_oidc_sub).
   90|       Condition = {
   91|         StringEquals = {
   92|           "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
   93|           "token.actions.githubusercontent.com:sub" = var.github_oidc_sub
   94|         }
   95|       }
   96|     }]
   97|   })
   98| }
   99| 
  100| resource "aws_iam_role_policy" "deploy" {
  101|   name = "deploy-api"
  102|   role = aws_iam_role.deploy.id
  103|   policy = jsonencode({
  104|     Version = "2012-10-17"
  105|     Statement = [
  106|       { Sid = "EcrAuth", Effect = "Allow", Action = ["ecr:GetAuthorizationToken"], Resource = "*" },
  107|       {
  108|         Sid    = "EcrRepo"
  109|         Effect = "Allow"
  110|         Action = ["ecr:BatchCheckLayerAvailability", "ecr:CompleteLayerUpload", "ecr:InitiateLayerUpload",
  111|           "ecr:PutImage", "ecr:UploadLayerPart", "ecr:BatchGetImage", "ecr:GetDownloadUrlForLayer",
  112|         "ecr:DescribeImages", "ecr:ListImages"]
  113|         Resource = aws_ecr_repository.api.arn
  114|       },
  115|       # RegisterTaskDefinition and Describe* don't support resource scoping.
  116|       {
  117|         Sid      = "EcsRegister"
  118|         Effect   = "Allow"
  119|         Action   = ["ecs:RegisterTaskDefinition", "ecs:DescribeTaskDefinition", "ecs:DescribeServices", "ecs:DescribeTasks", "ecs:ListTasks"]
  120|         Resource = "*"
  121|       },
  122|       # The service's ARN is built, not referenced, so this role can exist
  123|       # (and push the first image) before the service does.
  124|       {
  125|         Sid      = "EcsRoll"
  126|         Effect   = "Allow"
  127|         Action   = ["ecs:UpdateService"]
  128|         Resource = "arn:aws:ecs:${local.region}:${local.account_id}:service/${aws_ecs_cluster.main.name}/simulacra-api"
  129|       },
  130|       {
  131|         Sid       = "PassTaskRoles"
  132|         Effect    = "Allow"
  133|         Action    = "iam:PassRole"
  134|         Resource  = [aws_iam_role.execution.arn, aws_iam_role.task.arn]
  135|         Condition = { StringEquals = { "iam:PassedToService" = "ecs-tasks.amazonaws.com" } }
  136|       },
  137|       {
  138|         Sid      = "ReadDeployLogs"
  139|         Effect   = "Allow"
  140|         Action   = ["logs:FilterLogEvents", "logs:DescribeLogStreams"]
  141|         Resource = "${aws_cloudwatch_log_group.api.arn}:*"
  142|       }
  143|     ]
  144|   })
  145| }
```

## `infra/network.tf`

```hcl
    1| # The auth server's network pattern: default-VPC public subnets, tasks with a
    2| # public IP, no NAT gateway (~$32/mo saved). Only the ALB is reachable from
    3| # the internet; the task accepts its port from the ALB alone, EFS accepts NFS
    4| # from the tasks alone.
    5| 
    6| data "aws_subnet" "selected" {
    7|   for_each = toset(var.subnet_ids)
    8|   id       = each.value
    9| }
   10| 
   11| locals {
   12|   vpc_id = one(distinct([for s in data.aws_subnet.selected : s.vpc_id]))
   13| }
   14| 
   15| resource "aws_security_group" "alb" {
   16|   name        = "${local.name}-alb"
   17|   description = "Simulacra API load balancer: HTTP/HTTPS from anywhere"
   18|   vpc_id      = local.vpc_id
   19| }
   20| 
   21| resource "aws_vpc_security_group_ingress_rule" "alb_https" {
   22|   security_group_id = aws_security_group.alb.id
   23|   cidr_ipv4         = "0.0.0.0/0"
   24|   ip_protocol       = "tcp"
   25|   from_port         = 443
   26|   to_port           = 443
   27| }
   28| 
   29| resource "aws_vpc_security_group_ingress_rule" "alb_http" {
   30|   security_group_id = aws_security_group.alb.id
   31|   cidr_ipv4         = "0.0.0.0/0"
   32|   ip_protocol       = "tcp"
   33|   from_port         = 80
   34|   to_port           = 80
   35| }
   36| 
   37| resource "aws_vpc_security_group_egress_rule" "alb_to_task" {
   38|   security_group_id            = aws_security_group.alb.id
   39|   referenced_security_group_id = aws_security_group.task.id
   40|   ip_protocol                  = "tcp"
   41|   from_port                    = 8080
   42|   to_port                      = 8080
   43| }
   44| 
   45| resource "aws_security_group" "task" {
   46|   name        = "${local.name}-task"
   47|   description = "Simulacra API task: app port from the ALB only"
   48|   vpc_id      = local.vpc_id
   49| }
   50| 
   51| resource "aws_vpc_security_group_ingress_rule" "task_from_alb" {
   52|   security_group_id            = aws_security_group.task.id
   53|   referenced_security_group_id = aws_security_group.alb.id
   54|   ip_protocol                  = "tcp"
   55|   from_port                    = 8080
   56|   to_port                      = 8080
   57| }
   58| 
   59| # Out to Anthropic, ECR, Secrets Manager, S3, logs (no NAT: via the public IP).
   60| resource "aws_vpc_security_group_egress_rule" "task_all" {
   61|   security_group_id = aws_security_group.task.id
   62|   cidr_ipv4         = "0.0.0.0/0"
   63|   ip_protocol       = "-1"
   64| }
   65| 
   66| resource "aws_security_group" "efs" {
   67|   name        = "${local.name}-efs"
   68|   description = "Simulacra state: NFS from the API and seed tasks only"
   69|   vpc_id      = local.vpc_id
   70| }
   71| 
   72| resource "aws_vpc_security_group_ingress_rule" "efs_from_task" {
   73|   security_group_id            = aws_security_group.efs.id
   74|   referenced_security_group_id = aws_security_group.task.id
   75|   ip_protocol                  = "tcp"
   76|   from_port                    = 2049
   77|   to_port                      = 2049
   78| }
```

## `infra/observability.tf`

```hcl
    1| resource "aws_cloudwatch_log_group" "api" {
    2|   name              = "/ecs/simulacra"
    3|   retention_in_days = 30
    4| }
    5| 
    6| # A real subscriber this time (the auth server's topic had none). SNS emails a
    7| # confirmation link; alarms go nowhere until it's clicked.
    8| resource "aws_sns_topic" "alarms" {
    9|   name = "${local.name}-alarms"
   10| }
   11| 
   12| resource "aws_sns_topic_subscription" "email" {
   13|   topic_arn = aws_sns_topic.alarms.arn
   14|   protocol  = "email"
   15|   endpoint  = var.alert_email
   16| }
   17| 
   18| locals {
   19|   alb_dims = { LoadBalancer = aws_lb.api.arn_suffix, TargetGroup = aws_lb_target_group.api.arn_suffix }
   20| }
   21| 
   22| resource "aws_cloudwatch_metric_alarm" "no_healthy_target" {
   23|   alarm_name          = "${local.name}-no-healthy-target"
   24|   alarm_description   = "The API has had no healthy task for 3 minutes."
   25|   namespace           = "AWS/ApplicationELB"
   26|   metric_name         = "HealthyHostCount"
   27|   dimensions          = local.alb_dims
   28|   statistic           = "Minimum"
   29|   period              = 60
   30|   evaluation_periods  = 3
   31|   comparison_operator = "LessThanThreshold"
   32|   threshold           = 1
   33|   treat_missing_data  = "breaching"
   34|   alarm_actions       = [aws_sns_topic.alarms.arn]
   35|   ok_actions          = [aws_sns_topic.alarms.arn]
   36| }
   37| 
   38| resource "aws_cloudwatch_metric_alarm" "target_5xx" {
   39|   alarm_name          = "${local.name}-target-5xx"
   40|   alarm_description   = "The API returned 5xx responses (more than 5 in 5 minutes)."
   41|   namespace           = "AWS/ApplicationELB"
   42|   metric_name         = "HTTPCode_Target_5XX_Count"
   43|   dimensions          = { LoadBalancer = aws_lb.api.arn_suffix }
   44|   statistic           = "Sum"
   45|   period              = 300
   46|   evaluation_periods  = 1
   47|   comparison_operator = "GreaterThanThreshold"
   48|   threshold           = 5
   49|   treat_missing_data  = "notBreaching"
   50|   alarm_actions       = [aws_sns_topic.alarms.arn]
   51| }
   52| 
   53| resource "aws_cloudwatch_metric_alarm" "elb_5xx" {
   54|   alarm_name          = "${local.name}-elb-5xx"
   55|   alarm_description   = "The load balancer itself returned 5xx (no target, or target timeouts)."
   56|   namespace           = "AWS/ApplicationELB"
   57|   metric_name         = "HTTPCode_ELB_5XX_Count"
   58|   dimensions          = { LoadBalancer = aws_lb.api.arn_suffix }
   59|   statistic           = "Sum"
   60|   period              = 300
   61|   evaluation_periods  = 1
   62|   comparison_operator = "GreaterThanThreshold"
   63|   threshold           = 10
   64|   treat_missing_data  = "notBreaching"
   65|   alarm_actions       = [aws_sns_topic.alarms.arn]
   66| }
   67| 
   68| # The worker's log (sessions/intake.log) is echoed to stdout with a
   69| # "[worker]" prefix by docker/entrypoint.sh.
   70| resource "aws_cloudwatch_log_metric_filter" "worker_failure" {
   71|   name           = "${local.name}-worker-failure"
   72|   log_group_name = aws_cloudwatch_log_group.api.name
   73|   pattern        = "?\"[worker] STOP:\" ?\"[worker] Traceback\" ?refusing ?\"worker failed to start\""
   74|   metric_transformation {
   75|     name          = "WorkerFailures"
   76|     namespace     = "Simulacra"
   77|     value         = "1"
   78|     default_value = "0"
   79|   }
   80| }
   81| 
   82| resource "aws_cloudwatch_metric_alarm" "worker_failure" {
   83|   alarm_name          = "${local.name}-worker-failure"
   84|   alarm_description   = "The what-if worker stopped, refused, or raised. Read /ecs/simulacra for [worker] lines."
   85|   namespace           = "Simulacra"
   86|   metric_name         = "WorkerFailures"
   87|   statistic           = "Sum"
   88|   period              = 300
   89|   evaluation_periods  = 1
   90|   comparison_operator = "GreaterThanOrEqualToThreshold"
   91|   threshold           = 1
   92|   treat_missing_data  = "notBreaching"
   93|   alarm_actions       = [aws_sns_topic.alarms.arn]
   94| }
   95| 
   96| # Budgets filter on the project tag, which must be an active cost-allocation tag.
   97| resource "aws_ce_cost_allocation_tag" "project" {
   98|   tag_key = "project"
   99|   status  = "Active"
  100| }
  101| 
  102| resource "aws_budgets_budget" "stack" {
  103|   name         = "${local.name}-monthly"
  104|   budget_type  = "COST"
  105|   limit_amount = tostring(var.monthly_budget_usd)
  106|   limit_unit   = "USD"
  107|   time_unit    = "MONTHLY"
  108|   cost_filter {
  109|     name   = "TagKeyValue"
  110|     values = ["user:project$simulacra-americana"]
  111|   }
  112|   notification {
  113|     comparison_operator       = "GREATER_THAN"
  114|     threshold                 = 80
  115|     threshold_type            = "PERCENTAGE"
  116|     notification_type         = "FORECASTED"
  117|     subscriber_sns_topic_arns = [aws_sns_topic.alarms.arn]
  118|   }
  119|   notification {
  120|     comparison_operator       = "GREATER_THAN"
  121|     threshold                 = 100
  122|     threshold_type            = "PERCENTAGE"
  123|     notification_type         = "ACTUAL"
  124|     subscriber_sns_topic_arns = [aws_sns_topic.alarms.arn]
  125|   }
  126| }
  127| 
  128| # Budgets publishes to the topic only if the topic lets it.
  129| resource "aws_sns_topic_policy" "alarms" {
  130|   arn = aws_sns_topic.alarms.arn
  131|   policy = jsonencode({
  132|     Version = "2012-10-17"
  133|     Statement = [
  134|       {
  135|         Sid       = "AccountOwner"
  136|         Effect    = "Allow"
  137|         Principal = { AWS = "arn:aws:iam::${local.account_id}:root" }
  138|         Action    = ["SNS:Publish", "SNS:Subscribe", "SNS:GetTopicAttributes", "SNS:SetTopicAttributes", "SNS:ListSubscriptionsByTopic"]
  139|         Resource  = aws_sns_topic.alarms.arn
  140|       },
  141|       {
  142|         Sid       = "CloudWatchAlarms"
  143|         Effect    = "Allow"
  144|         Principal = { Service = "cloudwatch.amazonaws.com" }
  145|         Action    = "SNS:Publish"
  146|         Resource  = aws_sns_topic.alarms.arn
  147|       },
  148|       {
  149|         Sid       = "Budgets"
  150|         Effect    = "Allow"
  151|         Principal = { Service = "budgets.amazonaws.com" }
  152|         Action    = "SNS:Publish"
  153|         Resource  = aws_sns_topic.alarms.arn
  154|       }
  155|     ]
  156|   })
  157| }
```

## `infra/outputs.tf`

```hcl
    1| # infra/vercel-dns.sh reads these (terraform output -json); deploy-api.yml's
    2| # repo variables are set from them (docs/DEPLOY.md, "CI setup").
    3| 
    4| output "acm_validation_records" {
    5|   description = "CNAMEs to add in Vercel DNS before the certificates can issue."
    6|   value = {
    7|     for o in concat(tolist(aws_acm_certificate.api.domain_validation_options), tolist(aws_acm_certificate.assets.domain_validation_options)) :
    8|     o.domain_name => { name = o.resource_record_name, type = o.resource_record_type, value = o.resource_record_value }
    9|   }
   10| }
   11| 
   12| output "api_alb_dns_name" {
   13|   description = "Target of the api. CNAME."
   14|   value       = aws_lb.api.dns_name
   15| }
   16| 
   17| output "assets_cloudfront_domain" {
   18|   description = "Target of the assets. CNAME."
   19|   value       = aws_cloudfront_distribution.assets.domain_name
   20| }
   21| 
   22| output "assets_distribution_id" {
   23|   value = aws_cloudfront_distribution.assets.id
   24| }
   25| 
   26| output "deploy_role_arn" {
   27|   description = "Repo variable AWS_DEPLOY_ROLE_ARN."
   28|   value       = aws_iam_role.deploy.arn
   29| }
   30| 
   31| output "ecr_repository_url" {
   32|   value = aws_ecr_repository.api.repository_url
   33| }
   34| 
   35| # Everything deploy-api.yml needs to render infra/taskdef.json.tftpl
   36| # (repo variable TASKDEF_VARS, as JSON). Image is filled in per deploy.
   37| output "taskdef_vars" {
   38|   value = { for k, v in local.taskdef_vars : k => v if k != "image" }
   39| }
   40| 
   41| output "seed_task" {
   42|   description = "For scripts/sync-data.sh: aws ecs run-task parameters."
   43|   value = {
   44|     cluster         = aws_ecs_cluster.main.name
   45|     task_definition = aws_ecs_task_definition.seed.family
   46|     subnets         = var.subnet_ids
   47|     security_group  = aws_security_group.task.id
   48|   }
   49| }
```

## `infra/s3.tf`

```hcl
    1| # Two private buckets.
    2| #
    3| # simulacra-americana-data: the census-derived cache (NHGIS/IPUMS extracts are
    4| # "not for redistribution"), the EFS seed, and data backups. Created by hand to
    5| # take the pre-migration backups before anything else; adopted
    6| # here by the import block below.
    7| #
    8| # simulacra-americana-assets: the robot model, its paint set and the mirrored
    9| # portraits. Readable only by the CloudFront distribution (OAC).
   10| 
   11| import {
   12|   to = aws_s3_bucket.data
   13|   id = "simulacra-americana-data"
   14| }
   15| 
   16| resource "aws_s3_bucket" "data" {
   17|   bucket = "simulacra-americana-data"
   18|   tags   = { data = "census-derived-private" }
   19| }
   20| 
   21| resource "aws_s3_bucket_ownership_controls" "data" {
   22|   bucket = aws_s3_bucket.data.id
   23|   rule { object_ownership = "BucketOwnerEnforced" }
   24| }
   25| 
   26| resource "aws_s3_bucket_public_access_block" "data" {
   27|   bucket                  = aws_s3_bucket.data.id
   28|   block_public_acls       = true
   29|   block_public_policy     = true
   30|   ignore_public_acls      = true
   31|   restrict_public_buckets = true
   32| }
   33| 
   34| resource "aws_s3_bucket_server_side_encryption_configuration" "data" {
   35|   bucket = aws_s3_bucket.data.id
   36|   rule {
   37|     apply_server_side_encryption_by_default { sse_algorithm = "AES256" }
   38|     bucket_key_enabled = true
   39|   }
   40| }
   41| 
   42| resource "aws_s3_bucket_versioning" "data" {
   43|   bucket = aws_s3_bucket.data.id
   44|   versioning_configuration { status = "Enabled" }
   45| }
   46| 
   47| # Only the task role (seed/sync) and this account's admins; never public, never
   48| # over plain HTTP.
   49| resource "aws_s3_bucket_policy" "data" {
   50|   bucket = aws_s3_bucket.data.id
   51|   policy = jsonencode({
   52|     Version = "2012-10-17"
   53|     Statement = [{
   54|       Sid       = "DenyInsecureTransport"
   55|       Effect    = "Deny"
   56|       Principal = "*"
   57|       Action    = "s3:*"
   58|       Resource  = [aws_s3_bucket.data.arn, "${aws_s3_bucket.data.arn}/*"]
   59|       Condition = { Bool = { "aws:SecureTransport" = "false" } }
   60|     }]
   61|   })
   62|   depends_on = [aws_s3_bucket_public_access_block.data]
   63| }
   64| 
   65| resource "aws_s3_bucket" "assets" {
   66|   bucket = "simulacra-americana-assets"
   67| }
   68| 
   69| resource "aws_s3_bucket_ownership_controls" "assets" {
   70|   bucket = aws_s3_bucket.assets.id
   71|   rule { object_ownership = "BucketOwnerEnforced" }
   72| }
   73| 
   74| resource "aws_s3_bucket_public_access_block" "assets" {
   75|   bucket                  = aws_s3_bucket.assets.id
   76|   block_public_acls       = true
   77|   block_public_policy     = true
   78|   ignore_public_acls      = true
   79|   restrict_public_buckets = true
   80| }
   81| 
   82| resource "aws_s3_bucket_server_side_encryption_configuration" "assets" {
   83|   bucket = aws_s3_bucket.assets.id
   84|   rule {
   85|     apply_server_side_encryption_by_default { sse_algorithm = "AES256" }
   86|   }
   87| }
   88| 
   89| resource "aws_s3_bucket_versioning" "assets" {
   90|   bucket = aws_s3_bucket.assets.id
   91|   versioning_configuration { status = "Enabled" }
   92| }
   93| 
   94| resource "aws_s3_bucket_policy" "assets" {
   95|   bucket = aws_s3_bucket.assets.id
   96|   policy = jsonencode({
   97|     Version = "2012-10-17"
   98|     Statement = [
   99|       {
  100|         Sid       = "CloudFrontOAC"
  101|         Effect    = "Allow"
  102|         Principal = { Service = "cloudfront.amazonaws.com" }
  103|         Action    = "s3:GetObject"
  104|         Resource  = "${aws_s3_bucket.assets.arn}/*"
  105|         Condition = { StringEquals = { "AWS:SourceArn" = aws_cloudfront_distribution.assets.arn } }
  106|       },
  107|       {
  108|         Sid       = "DenyInsecureTransport"
  109|         Effect    = "Deny"
  110|         Principal = "*"
  111|         Action    = "s3:*"
  112|         Resource  = [aws_s3_bucket.assets.arn, "${aws_s3_bucket.assets.arn}/*"]
  113|         Condition = { Bool = { "aws:SecureTransport" = "false" } }
  114|       }
  115|     ]
  116|   })
  117|   depends_on = [aws_s3_bucket_public_access_block.assets]
  118| }
```

## `infra/secrets.tf`

```hcl
    1| # The shell only. The value is put by hand, never through Terraform, so it
    2| # never lands in state or git. It is JSON with two fields:
    3| #   ANTHROPIC_API_KEY      the model key
    4| #   SIMULACRA_ACCESS_KEYS  a JSON object (as a string) of name → access key; a
    5| #                          request needs one to queue new text (serve/guard.ts)
    6| # docs/DEPLOY.md "Access keys" has the command.
    7| # The IPUMS/NHGIS key is only for rebuilding the cache on a laptop; never here.
    8| 
    9| resource "aws_secretsmanager_secret" "prod" {
   10|   name                    = "simulacra/prod"
   11|   description             = "Simulacra API runtime secrets (ANTHROPIC_API_KEY, SIMULACRA_ACCESS_KEYS)"
   12|   recovery_window_in_days = 7
   13| }
```

## `infra/taskdef.json.tftpl`

```
    1| {
    2|   "family": "simulacra-api",
    3|   "networkMode": "awsvpc",
    4|   "requiresCompatibilities": ["FARGATE"],
    5|   "runtimePlatform": { "cpuArchitecture": "ARM64", "operatingSystemFamily": "LINUX" },
    6|   "cpu": "${cpu}",
    7|   "memory": "${memory}",
    8|   "executionRoleArn": "${execution_role_arn}",
    9|   "taskRoleArn": "${task_role_arn}",
   10|   "volumes": [
   11|     {
   12|       "name": "state",
   13|       "efsVolumeConfiguration": {
   14|         "fileSystemId": "${efs_id}",
   15|         "transitEncryption": "ENABLED",
   16|         "authorizationConfig": { "accessPointId": "${access_point_id}", "iam": "ENABLED" }
   17|       }
   18|     }
   19|   ],
   20|   "containerDefinitions": [
   21|     {
   22|       "name": "api",
   23|       "image": "${image}",
   24|       "essential": true,
   25|       "portMappings": [{ "containerPort": 8080, "protocol": "tcp" }],
   26|       "linuxParameters": { "initProcessEnabled": true },
   27|       "stopTimeout": 30,
   28|       "mountPoints": [{ "sourceVolume": "state", "containerPath": "/state" }],
   29|       "environment": [
   30|         { "name": "NODE_ENV", "value": "production" },
   31|         { "name": "PORT", "value": "8080" },
   32|         { "name": "SIMULACRA_LOG", "value": "1" },
   33|         { "name": "SIMULACRA_AUTORUN", "value": "configs/live-1920.json" },
   34|         { "name": "SIMULACRA_PYTHON", "value": "/opt/venv/bin/python" },
   35|         { "name": "SIMULACRA_BUNDLES", "value": "/app/serve/bundles" },
   36|         { "name": "SIMHARNESS_CACHE", "value": "/state/cache" },
   37|         { "name": "SIMULACRA_DAILY_USD", "value": "20" },
   38|         { "name": "SIMULACRA_MONTHLY_USD", "value": "200" },
   39|         { "name": "SIMULACRA_RETAIN_DAYS", "value": "7" },
   40|         { "name": "TRUST_PROXY_HOPS", "value": "2" }
   41|       ],
   42|       "secrets": [
   43|         { "name": "ANTHROPIC_API_KEY", "valueFrom": "${secret_arn}:ANTHROPIC_API_KEY::" },
   44|         { "name": "SIMULACRA_ACCESS_KEYS", "valueFrom": "${secret_arn}:SIMULACRA_ACCESS_KEYS::" }
   45|       ],
   46|       "logConfiguration": {
   47|         "logDriver": "awslogs",
   48|         "options": {
   49|           "awslogs-group": "${log_group}",
   50|           "awslogs-region": "${region}",
   51|           "awslogs-stream-prefix": "api"
   52|         }
   53|       }
   54|     }
   55|   ]
   56| }
```

## `infra/terraform.tfvars.example`

```
    1| # Copy to terraform.tfvars (gitignored) and fill in.
    2| 
    3| # The AWS account this stack deploys to. The provider refuses any other account.
    4| aws_account_id = "123456789012"
    5| 
    6| alert_email = "alerts@example.com"
    7| 
    8| # The deploy role's trusted sub: the repo's immutable subject prefix, as GitHub
    9| # reports it (GET repos/<owner>/<repo>/actions/oidc/customization/sub), plus main.
   10| # Only a workflow running on main can assume the role; a branch, tag, pull
   11| # request or environment gets a different sub.
   12| github_oidc_sub = "repo:<owner>@<owner-id>/<repo>@<repo-id>:ref:refs/heads/main"
```

## `infra/variables.tf`

```hcl
    1| variable "domain" {
    2|   description = "The site's apex domain (DNS hosted at Vercel)."
    3|   type        = string
    4|   default     = "simulacraamericana.com"
    5| }
    6| 
    7| variable "subnet_ids" {
    8|   description = "Default-VPC public subnets for the ALB, the task and EFS (the auth server's two AZs, us-east-1a/b)."
    9|   type        = list(string)
   10|   default     = ["subnet-8c3db5ea", "subnet-35f36514"]
   11| }
   12| 
   13| variable "image" {
   14|   description = "The API image for the FIRST task-definition revision only. CI registers every later one from infra/taskdef.json.tftpl; the service ignores task-definition drift."
   15|   type        = string
   16|   default     = "public.ecr.aws/docker/library/busybox:latest"
   17| }
   18| 
   19| variable "task_cpu" {
   20|   type    = number
   21|   default = 1024
   22| }
   23| 
   24| variable "task_memory" {
   25|   description = "MiB. The worker loads pandas/scipy plus a run's draws alongside Node."
   26|   type        = number
   27|   default     = 4096
   28| }
   29| 
   30| variable "aws_account_id" {
   31|   description = "The AWS account this stack deploys to; the provider refuses any other."
   32|   type        = string
   33|   validation {
   34|     condition     = can(regex("^[0-9]{12}$", var.aws_account_id))
   35|     error_message = "aws_account_id must be a 12-digit AWS account ID."
   36|   }
   37| }
   38| 
   39| variable "alert_email" {
   40|   description = "Subscriber for the alarm topic. SNS emails a confirmation link that must be clicked."
   41|   type        = string
   42| }
   43| 
   44| variable "monthly_budget_usd" {
   45|   description = "AWS Budgets alert threshold for this stack (AWS spend only; Anthropic spend is alerted in the Anthropic console)."
   46|   type        = number
   47|   default     = 150
   48| }
   49| 
   50| variable "github_oidc_sub" {
   51|   description = "The deploy role's trusted OIDC sub, matched exactly: repo:<owner>@<owner-id>/<repo>@<repo-id>:ref:refs/heads/main. Read the prefix from GET repos/<owner>/<repo>/actions/oidc/customization/sub; repo:owner/name:... silently never matches."
   52|   type        = string
   53|   validation {
   54|     condition     = !strcontains(var.github_oidc_sub, "*") && endswith(var.github_oidc_sub, ":ref:refs/heads/main")
   55|     error_message = "github_oidc_sub must name main exactly (…:ref:refs/heads/main), with no wildcard."
   56|   }
   57| }
   58| 
   59| variable "cors_origins" {
   60|   description = "Origins allowed to fetch robot assets (three.js fetches GLBs and textures cross-origin)."
   61|   type        = list(string)
   62|   # The site, plus local builds (pnpm serve :8790, vite dev :5173, vite preview :4173)
   63|   # so the 3D robot loads when the page is run on a laptop.
   64|   default = ["https://simulacraamericana.com", "http://localhost:8790", "http://localhost:5173", "http://localhost:4173"]
   65| }
```

## `infra/vercel-dns.sh`

```bash
    1| #!/usr/bin/env bash
    2| # Every DNS record the AWS side needs, added in Vercel DNS (the zone lives
    3| # there; scope camerons-projects-2a650f0d). Prints the commands by default;
    4| # --apply runs them. Each run needs Cameron's yes: these change production DNS.
    5| #
    6| #   infra/vercel-dns.sh certs [--apply]      before the full apply: CAA + ACM validation
    7| #   infra/vercel-dns.sh endpoints [--apply]  after it: api. -> ALB, assets. -> CloudFront
    8| #
    9| # The zone before any change:
   10| #   CAA   @  0 issue "pki.goog" | "sectigo.com" | "letsencrypt.org"   (Vercel defaults)
   11| #   ALIAS @  cname.vercel-dns-016.com.
   12| #   ALIAS *  cname.vercel-dns-016.com.
   13| # The explicit api/assets/_validation names below take precedence over the *
   14| # wildcard. Without the amazon.com CAA record ACM never issues.
   15| set -euo pipefail
   16| 
   17| DOMAIN=simulacraamericana.com
   18| MODE=${1:-}
   19| APPLY=${2:-}
   20| cd "$(dirname "$0")"
   21| out() { terraform output -json "$1"; }
   22| 
   23| run() {
   24|   if [ "$APPLY" = "--apply" ]; then "$@"; else printf '%q ' "$@"; echo; fi
   25| }
   26| 
   27| # A name relative to the zone ("_abc.api.simulacraamericana.com." -> "_abc.api").
   28| rel() { local n=${1%.}; echo "${n%.$DOMAIN}"; }
   29| 
   30| case "$MODE" in
   31|   certs)
   32|     run vercel dns add "$DOMAIN" '@' CAA '0 issue "amazon.com"'
   33|     out acm_validation_records | python3 -c '
   34| import json, sys
   35| for r in json.load(sys.stdin).values():
   36|     print(r["name"], r["value"])' | while read -r name value; do
   37|       run vercel dns add "$DOMAIN" "$(rel "$name")" CNAME "${value%.}"
   38|     done
   39|     ;;
   40|   endpoints)
   41|     run vercel dns add "$DOMAIN" api CNAME "$(out api_alb_dns_name | tr -d '"')"
   42|     run vercel dns add "$DOMAIN" assets CNAME "$(out assets_cloudfront_domain | tr -d '"')"
   43|     ;;
   44|   *)
   45|     echo "usage: $0 certs|endpoints [--apply]" >&2
   46|     exit 2
   47|     ;;
   48| esac
   49| if [ "$APPLY" = "--apply" ]; then vercel dns ls "$DOMAIN"; fi
```

## `infra/versions.tf`

```hcl
    1| # Simulacra Americana's AWS stack: the simulation API (ECS Fargate behind an
    2| # ALB, state on EFS), the assets CDN (CloudFront over a private S3 bucket) and
    3| # the private census-derived data bucket. Same account and region as the
    4| # Partyhat auth server, but nothing here references or modifies its resources;
    5| # the only shared object read is the account's GitHub OIDC provider.
    6| #
    7| # State lives in s3://simulacra-americana-tfstate (infra/bootstrap.sh creates it).
    8| # Apply order and the DNS steps between applies: docs/DEPLOY.md, "Stand-up".
    9| 
   10| terraform {
   11|   required_version = ">= 1.10"
   12|   required_providers {
   13|     aws = { source = "hashicorp/aws", version = "~> 6.0" }
   14|   }
   15|   backend "s3" {
   16|     bucket       = "simulacra-americana-tfstate"
   17|     key          = "prod/terraform.tfstate"
   18|     region       = "us-east-1"
   19|     encrypt      = true
   20|     use_lockfile = true
   21|   }
   22| }
   23| 
   24| provider "aws" {
   25|   region              = "us-east-1"
   26|   allowed_account_ids = [var.aws_account_id]
   27|   default_tags {
   28|     tags = { project = "simulacra-americana", managed-by = "terraform" }
   29|   }
   30| }
   31| 
   32| data "aws_caller_identity" "current" {}
   33| data "aws_region" "current" {}
   34| 
   35| locals {
   36|   account_id = data.aws_caller_identity.current.account_id
   37|   region     = data.aws_region.current.region
   38|   name       = "simulacra"
   39| }
```

## `package.json`

```json
    1| {
    2|   "name": "synthetic-voters-toy",
    3|   "private": true,
    4|   "version": "0.1.0",
    5|   "type": "module",
    6|   "packageManager": "pnpm@9.3.0",
    7|   "engines": { "node": ">=22" },
    8|   "scripts": {
    9|     "dev": "vite dev",
   10|     "build": "vite build",
   11|     "serve": "tsx serve/index.ts",
   12|     "prepare": "svelte-kit sync || true",
   13|     "check": "svelte-kit sync && svelte-check --tsconfig ./tsconfig.json --fail-on-warnings",
   14|     "lint": "biome lint --error-on-warnings .",
   15|     "size": "tsx scripts/size-check.ts",
   16|     "test": "vitest run",
   17|     "test:py": "python3 -m pytest -q",
   18|     "gate": "pnpm lint && pnpm check && pnpm size && pnpm test && pnpm test:py"
   19|   },
   20|   "dependencies": {
   21|     "express": "^5.3.0",
   22|     "lucide-svelte": "^0.562.0",
   23|     "three": "^0.181.2",
   24|     "zod": "^4.6.7"
   25|   },
   26|   "devDependencies": {
   27|     "@biomejs/biome": "^2.2.0",
   28|     "@sveltejs/adapter-static": "^3.0.11",
   29|     "@sveltejs/kit": "^2.70.4",
   30|     "@sveltejs/vite-plugin-svelte": "^5.0.0",
   31|     "@types/express": "^5.0.3",
   32|     "@types/node": "^22.15.0",
   33|     "@types/three": "^0.181.0",
   34|     "svelte": "^5.0.0",
   35|     "svelte-check": "^4.1.0",
   36|     "tsx": "^4.20.0",
   37|     "typescript": "^5.8.0",
   38|     "vite": "^6.4.6",
   39|     "vitest": "^4.1.12"
   40|   },
   41|   "pnpm": {
   42|     "onlyBuiltDependencies": ["esbuild", "@biomejs/biome"],
   43|     "auditConfig": { "ignoreCves": ["CVE-2026-128120"] }
   44|   }
   45| }
```

## `pyproject.toml`

```toml
    1| [build-system]
    2| requires = ["setuptools>=69"]
    3| build-backend = "setuptools.build_meta"
    4| 
    5| [project]
    6| name = "synthetic-voters-toy-harness"
    7| version = "0.1.0"
    8| description = "The simulation harness behind /api/simulacra: a calibrated backbone decides the counts, LLM agents supply paired changes and quotes."
    9| requires-python = ">=3.12"
   10| dependencies = [
   11|     "numpy>=2.0",
   12|     "pandas>=2.2",
   13|     "scipy>=1.13",
   14| ]
   15| 
   16| [project.optional-dependencies]
   17| test = ["pytest>=8.0"]
   18| # Only the paid stages (ask, research, whatif) import the SDK, lazily; CI never needs it.
   19| llm = ["anthropic>=1.0"]
   20| build = ["pyreadr>=0.5"]
   21| 
   22| [tool.setuptools]
   23| packages = ["simharness"]
   24| 
   25| [tool.pytest.ini_options]
   26| testpaths = ["tests"]
```

## `requirements.lock`

```
    1| # The harness's runtime dependencies for the API image (pyproject.toml plus the llm extra),
    2| # frozen from a clean Python 3.13 venv. anthropic must support speed='fast'.
    3| annotated-types==0.8.0
    4| anthropic==1.10.0
    5| anyio==4.15.1
    6| docstring_parser==0.18.0
    7| h11==0.16.0
    8| httpcore2==2.13.1
    9| httpx2==2.13.1
   10| idna==3.20
   11| jiter==0.17.0
   12| numpy==2.5.3
   13| pandas==3.0.6
   14| pydantic==2.13.5
   15| pydantic_core==2.46.5
   16| python-dateutil==2.9.0.post0
   17| scipy==1.18.1
   18| six==1.17.0
   19| sniffio==1.3.1
   20| truststore==0.10.4
   21| typing-inspection==0.4.4
   22| typing_extensions==4.16.0
```

## `scripts/harness/build_corpus.py`

```python
    1| #!/usr/bin/env python3
    2| """build_corpus.py — dated Chronicling America corpus for one election year.
    3| 
    4| Builds C/sources/corpus_<year>.jsonl in the 1920 corpus format (see
    5| C/sources/PROVENANCE-sources.md): page-level items from the loc.gov
    6| Chronicling America collection, each with a ~120-word excerpt cut
    7| programmatically from the fetched OCR, dated from 1 September of the election
    8| year through the day before election day (no item after the cutoff).
    9| 
   10| Usage:
   11|   python scripts/harness/build_corpus.py 1896 [1932 ...] --cache-dir DIR [--out-dir DIR]
   12|   python scripts/harness/build_corpus.py --provenance 1896 1932 --cache-dir DIR  # markdown
   13| 
   14| Politeness: single-threaded; >=3.2 s between www.loc.gov searches, >=1.1 s
   15| between tile.loc.gov OCR fetches; exponential backoff (honouring Retry-After)
   16| on 429/5xx/Cloudflare errors; every HTTP response is cached on disk so reruns
   17| make no new requests. Descriptive User-Agent.
   18| 
   19| Selection is fully automatic (no LLM): per topic, one national search plus the
   20| best-covered state in each census region (from the national query's
   21| location_state facet), plus a second national query. The top hits are fetched,
   22| the densest topic-keyword window of the OCR is excerpted, scored for OCR
   23| readability, ad/patent-medicine noise, prediction talk and candidate mentions,
   24| and items are then picked round-robin across regions with per-paper caps and
   25| near-duplicate (shingle Jaccard) rejection.
   26| """
   27| from __future__ import annotations
   28| 
   29| import argparse
   30| import datetime as dt
   31| import hashlib
   32| import http.client
   33| import json
   34| import math
   35| import os
   36| import re
   37| import sys
   38| import tempfile
   39| import time
   40| import urllib.error
   41| import urllib.parse
   42| import urllib.request
   43| 
   44| UA = ("SimulacraHarness-corpus-builder/1.0 (historical election research; "
   45|       "single-threaded, cached, backs off on 429)")
   46| SEARCH = "https://www.loc.gov/collections/chronicling-america/"
   47| DEFAULT_CACHE = os.environ.get("CORPUS_BUILD_CACHE") or os.path.join(
   48|     tempfile.gettempdir(), "simharness_corpus_build_cache")
   49| DEFAULT_OUT = os.path.expanduser(
   50|     "~/research_notes/historical_election_sim_data/harness_cache/sources")
   51| 
   52| # ---------------------------------------------------------------- geography
   53| REGION = {}
   54| for _r, _ss in {
   55|     "Northeast": ["maine", "new hampshire", "vermont", "massachusetts", "rhode island",
   56|                   "connecticut", "new york", "new jersey", "pennsylvania"],
   57|     "Midwest": ["ohio", "indiana", "illinois", "michigan", "wisconsin", "minnesota", "iowa",
   58|                 "missouri", "north dakota", "south dakota", "nebraska", "kansas", "dakota"],
   59|     "South": ["delaware", "maryland", "district of columbia", "virginia", "west virginia",
   60|               "north carolina", "south carolina", "georgia", "florida", "kentucky",
   61|               "tennessee", "alabama", "mississippi", "arkansas", "louisiana", "oklahoma",
   62|               "texas", "indian territory"],
   63|     "West": ["montana", "idaho", "wyoming", "colorado", "new mexico", "arizona", "utah",
   64|              "nevada", "washington", "oregon", "california", "alaska", "hawaii"],
   65| }.items():
   66|     for _s in _ss:
   67|         REGION[_s] = _r
   68| REGIONS = ["Northeast", "Midwest", "South", "West"]
   69| 
   70| # ------------------------------------------------------------- year configs
   71| # topics: (label, human description, [search queries], [extra window keywords])
   72| # names: candidate / running-mate / incumbent / party words (case-sensitive).
   73| Y: dict[int, dict] = {}
   74| 
   75| 
   76| def year(y, election, names, topics, cutoff=None):
   77|     e = dt.date.fromisoformat(election)
   78|     Y[y] = dict(election=e, cutoff=dt.date.fromisoformat(cutoff) if cutoff else e - dt.timedelta(days=1),
   79|                 names=names, topics=topics)
   80| 
   81| 
   82| GENERIC_PARTY = ["Republican", "Republicans", "Democrat", "Democrats", "Democratic", "Democracy"]
   83| 
   84| year(1840, "1840-10-30", ["Harrison", "Tyler", "Van Buren", "Johnson", "Birney", "Whig", "Whigs",
   85|                           "Loco Foco", "Locofoco", "Locofocos", "Tippecanoe", "Liberty party"] + GENERIC_PARTY, [
   86|     ("hard_times", "Hard times after the Panic of 1837", ["hard times", "times money scarce"], ["distress", "wages", "credit", "failures"]),
   87|     ("sub_treasury", "Independent Treasury (sub-treasury)", ["sub treasury", "independent treasury"], ["specie", "treasury"]),
   88|     ("banks_currency", "Banks, specie payments and paper money", ["specie payments banks", "bank notes currency"], ["suspension", "specie", "currency"]),
   89|     ("national_bank", "A national bank", ["national bank"], ["bank", "charter"]),
   90|     ("standing_army", "Militia plan / standing army", ["standing army", "militia"], ["poinsett", "army"]),
   91|     ("abolition", "Abolition and slavery", ["abolition", "abolitionists slavery"], ["slaves", "slavery"]),
   92|     ("tariff", "Tariff and home industry", ["tariff", "protection home industry"], ["duties", "manufactures"]),
   93|     ("public_lands", "Public lands and pre-emption", ["public lands", "pre-emption"], ["lands", "settlers"]),
   94| ], cutoff="1840-10-29")
   95| year(1844, "1844-11-01", ["Polk", "Dallas", "Clay", "Frelinghuysen", "Birney", "Tyler", "Whig", "Whigs",
   96|                           "Loco Foco", "Locofoco", "Locofocos", "Liberty party"] + GENERIC_PARTY, [
   97|     ("texas_annexation", "Annexation of Texas", ["annexation texas"], ["annex", "texas", "mexico"]),
   98|     ("tariff_1842", "The tariff of 1842", ["tariff of 1842", "tariff protection"], ["duties", "manufactures"]),
   99|     ("oregon", "The Oregon question", ["oregon territory", "oregon"], ["british", "boundary"]),
  100|     ("national_bank", "A national bank", ["national bank"], ["bank", "currency"]),
  101|     ("slavery_abolition", "Slavery and abolition", ["abolition slavery", "abolitionists"], ["slaves", "slavery"]),
  102|     ("nativism", "Native Americanism and naturalization", ["native american", "naturalization foreigners"], ["catholic", "riots", "foreigners"]),
  103|     ("distribution_lands", "Distribution of public land revenue", ["distribution public lands"], ["lands", "states"]),
  104|     ("hard_money", "Currency and banks", ["currency banks specie"], ["specie", "paper"]),
  105| ], cutoff="1844-10-31")
  106| year(1848, "1848-11-07", ["Taylor", "Fillmore", "Cass", "Butler", "Van Buren", "Adams", "Polk", "Whig", "Whigs",
  107|                           "Free Soil", "Free Soilers", "Barnburner", "Barnburners", "Loco Foco", "Locofoco",
  108|                           "Locofocos"] + GENERIC_PARTY, [
  109|     ("wilmot_proviso", "Slavery in the new territories (Wilmot Proviso)", ["wilmot proviso", "slavery territories"], ["slavery", "territory", "proviso"]),
  110|     ("mexican_war", "The Mexican War and its costs", ["mexican war", "war debt mexico"], ["war", "mexico", "soldiers"]),
  111|     ("tariff", "The tariff of 1846", ["tariff of 1846", "tariff"], ["duties", "manufactures"]),
  112|     ("california_gold", "California and the gold discovery", ["california gold"], ["gold", "mines"]),
  113|     ("internal_improvements", "Rivers, harbors and internal improvements", ["rivers and harbors", "internal improvements"], ["harbor", "river"]),
  114|     ("immigration_ireland", "Irish famine and immigration", ["ireland famine", "emigrants"], ["irish", "emigrants"]),
  115|     ("public_lands", "Public lands and homesteads", ["public lands settlers"], ["lands", "settlers"]),
  116|     ("europe_revolutions", "Revolutions in Europe", ["revolution france", "revolution europe"], ["republic", "france"]),
  117| ])
  118| year(1852, "1852-11-02", ["Pierce", "King", "Scott", "Graham", "Hale", "Julian", "Fillmore", "Whig", "Whigs",
  119|                           "Free Soil", "Free Soilers", "Free Democracy"] + GENERIC_PARTY, [
  120|     ("fugitive_slave_law", "The Fugitive Slave Law", ["fugitive slave law", "fugitive slave"], ["slave", "fugitive"]),
  121|     ("compromise_1850", "Finality of the Compromise of 1850", ["compromise measures", "compromise finality"], ["compromise", "agitation"]),
  122|     ("tariff", "The tariff", ["tariff", "protection iron"], ["duties", "iron"]),
  123|     ("foreigners", "Immigration and naturalization", ["foreigners naturalization", "adopted citizens"], ["foreign", "germans", "irish"]),
  124|     ("temperance", "Temperance and the Maine Law", ["maine law", "liquor law temperance"], ["liquor", "temperance"]),
  125|     ("internal_improvements", "Rivers, harbors and railroads", ["rivers and harbors", "railroad"], ["harbor", "railroad"]),
  126|     ("homestead", "Homestead / free land", ["homestead bill", "public lands"], ["lands", "homestead"]),
  127|     ("cuba", "Cuba and filibusters", ["cuba"], ["spain", "filibuster"]),
  128| ])
  129| year(1856, "1856-11-04", ["Buchanan", "Breckinridge", "Fremont", "Frémont", "Dayton", "Fillmore", "Donelson",
  130|                           "Pierce", "Know Nothing", "Know Nothings", "American party", "Black Republican",
  131|                           "Whig", "Whigs"] + GENERIC_PARTY, [
  132|     ("kansas", "Violence and slavery in Kansas", ["kansas border ruffians", "kansas"], ["lawrence", "free state", "ruffians"]),
  133|     ("slavery_extension", "Extension of slavery into the territories", ["slavery extension territories", "nebraska bill"], ["slavery", "territories"]),
  134|     ("sumner_assault", "The assault on Sumner", ["sumner brooks assault"], ["senate", "assault"]),
  135|     ("disunion", "Threats of disunion", ["disunion", "dissolution of the union"], ["union", "south"]),
  136|     ("foreigners_catholics", "Foreigners and Catholics (nativism)", ["foreigners naturalization", "catholics"], ["foreign", "catholic"]),
  137|     ("temperance", "Temperance / Maine Law", ["maine law", "liquor law"], ["liquor", "temperance"]),
  138|     ("pacific_railroad", "A Pacific railroad", ["pacific railroad"], ["railroad", "pacific"]),
  139|     ("cuba_ostend", "Cuba and the Ostend Manifesto", ["cuba ostend", "cuba"], ["spain", "cuba"]),
  140| ])
  141| year(1860, "1860-11-06", ["Lincoln", "Hamlin", "Douglas", "Johnson", "Breckinridge", "Lane", "Bell", "Everett",
  142|                           "Buchanan", "Constitutional Union", "Black Republican", "Wide Awake", "Wide Awakes",
  143|                           "Fusion"] + GENERIC_PARTY, [
  144|     ("slavery_territories", "Slavery in the territories", ["slavery territories", "slave code territories"], ["slavery", "territories"]),
  145|     ("secession", "Secession and disunion", ["secession", "disunion"], ["union", "dissolution"]),
  146|     ("homestead", "The homestead bill", ["homestead bill", "free homes"], ["lands", "settlers"]),
  147|     ("tariff", "Protective tariff", ["protective tariff", "tariff"], ["duties", "iron"]),
  148|     ("john_brown", "John Brown and slave insurrection fears", ["john brown", "insurrection"], ["harper", "insurrection"]),
  149|     ("pacific_railroad", "A Pacific railroad", ["pacific railroad"], ["railroad", "pacific"]),
  150|     ("slave_trade", "Reopening the slave trade", ["african slave trade"], ["slave", "trade"]),
  151|     ("hard_times", "Crops, money and business", ["crops prices money market"], ["crop", "prices"]),
  152| ])
  153| year(1864, "1864-11-08", ["Lincoln", "Johnson", "McClellan", "Pendleton", "Fremont", "Frémont", "Union party",
  154|                           "Copperhead", "Copperheads"] + GENERIC_PARTY, [
  155|     ("war_peace", "Peace negotiations vs. continuing the war", ["peace negotiations", "armistice"], ["peace", "war"]),
  156|     ("draft", "The draft and substitutes", ["draft conscription", "drafted substitutes"], ["draft", "quota"]),
  157|     ("emancipation", "Emancipation and abolition", ["emancipation", "abolition slavery"], ["slaves", "freedom"]),
  158|     ("soldiers_vote", "Soldiers voting in the field", ["soldiers vote"], ["soldiers", "field"]),
  159|     ("prices_currency", "Prices, gold and greenbacks", ["gold premium", "high prices"], ["greenbacks", "currency"]),
  160|     ("arbitrary_arrests", "Arbitrary arrests and civil liberties", ["arbitrary arrests", "habeas corpus"], ["arrest", "military"]),
  161|     ("war_news", "The military campaigns (Atlanta, Shenandoah)", ["atlanta sherman", "sheridan valley"], ["army", "rebels"]),
  162|     ("taxes_debt", "War taxes and the debt", ["taxes war debt", "internal revenue"], ["tax", "debt"]),
  163| ])
  164| year(1868, "1868-11-03", ["Grant", "Colfax", "Seymour", "Blair", "Johnson"] + GENERIC_PARTY, [
  165|     ("reconstruction", "Reconstruction of the South", ["reconstruction acts", "reconstruction"], ["military", "southern"]),
  166|     ("negro_suffrage", "Black suffrage", ["negro suffrage", "colored voters"], ["negro", "suffrage", "colored"]),
  167|     ("bonds_greenbacks", "Paying the bonds in greenbacks", ["bonds greenbacks", "five-twenty bonds"], ["bonds", "greenbacks", "currency"]),
  168|     ("taxes", "Taxes and the public debt", ["taxation public debt", "internal revenue tax"], ["tax", "debt"]),
  169|     ("ku_klux", "Ku Klux violence", ["ku klux", "outrages"], ["klan", "murdered"]),
  170|     ("impeachment", "The impeachment of the president", ["impeachment"], ["senate", "acquittal"]),
  171|     ("indian_war", "Indian wars on the plains", ["indian war", "indians"], ["indians", "frontier"]),
  172|     ("tariff", "Tariff and protection", ["tariff", "protection"], ["duties", "wool"]),
  173| ])
  174| year(1872, "1872-11-05", ["Grant", "Wilson", "Greeley", "Brown", "O'Conor", "Liberal Republican",
  175|                           "Liberal Republicans", "Liberals"] + GENERIC_PARTY, [
  176|     ("amnesty", "Amnesty for former Confederates", ["amnesty"], ["disabilities", "southern"]),
  177|     ("ku_klux", "Ku Klux prosecutions and violence", ["ku klux"], ["klan", "outrages"]),
  178|     ("civil_service_reform", "Civil service reform", ["civil service reform"], ["office", "reform"]),
  179|     ("credit_mobilier", "Corruption: Credit Mobilier", ["credit mobilier"], ["congress", "stock"]),
  180|     ("tammany", "The Tammany Ring", ["tammany ring", "tweed"], ["ring", "frauds"]),
  181|     ("tariff_free_trade", "Tariff vs. free trade", ["free trade", "tariff"], ["duties", "protection"]),
  182|     ("currency", "Specie payments and currency", ["specie payments", "greenbacks"], ["currency", "gold"]),
  183|     ("eight_hour", "Labor and the eight-hour day", ["eight hour", "workingmen"], ["labor", "hours"]),
  184| ])
  185| year(1876, "1876-11-07", ["Hayes", "Wheeler", "Tilden", "Hendricks", "Cooper", "Grant", "Greenback party",
  186|                           "Greenbackers"] + GENERIC_PARTY, [
  187|     ("southern_violence", "Southern elections, rifle clubs and violence", ["rifle clubs", "hamburg massacre"], ["negroes", "colored"]),
  188|     ("reconstruction", "Carpet-bag rule and Reconstruction", ["carpet bag", "carpet-baggers"], ["southern", "state government"]),
  189|     ("hard_times", "Hard times and unemployment", ["hard times", "out of employment"], ["work", "wages"]),
  190|     ("currency", "Resumption and greenbacks", ["resumption act", "greenbacks"], ["specie", "currency"]),
  191|     ("corruption", "Corruption and reform (Whisky Ring, Belknap)", ["whisky ring", "belknap"], ["fraud", "reform"]),
  192|     ("indian_war", "The Sioux war", ["sioux war", "custer"], ["indians", "sioux"]),
  193|     ("schools_sectarian", "Public schools and sectarian funds", ["public schools sectarian"], ["schools", "catholic"]),
  194|     ("tariff", "Tariff", ["tariff"], ["duties", "protection"]),
  195| ])
  196| year(1880, "1880-11-02", ["Garfield", "Arthur", "Hancock", "English", "Weaver", "Hayes", "Greenback party",
  197|                           "Greenbackers", "Morey"] + GENERIC_PARTY, [
  198|     ("tariff", "Tariff for revenue vs. protection", ["tariff for revenue", "protective tariff"], ["duties", "protection"]),
  199|     ("solid_south", "The Solid South and southern elections", ["solid south"], ["southern", "bourbon"]),
  200|     ("chinese", "Chinese immigration", ["chinese immigration", "chinese"], ["chinese", "coolie"]),
  201|     ("currency", "Greenbacks and resumption", ["greenbacks resumption", "national banks"], ["currency", "specie"]),
  202|     ("civil_service", "Civil service reform", ["civil service reform"], ["office", "reform"]),
  203|     ("exodus", "The Black exodus from the South", ["negro exodus", "exodusters"], ["colored", "kansas"]),
  204|     ("state_rights", "State rights and federal elections", ["state rights", "federal elections"], ["states", "constitution"]),
  205|     ("labor", "Workingmen and wages", ["workingmen wages"], ["labor", "wages"]),
  206| ])
  207| year(1884, "1884-11-04", ["Cleveland", "Hendricks", "Blaine", "Logan", "Butler", "St. John", "Arthur",
  208|                           "Mugwump", "Mugwumps", "Greenback party", "Prohibition party"] + GENERIC_PARTY, [
  209|     ("tariff", "Tariff and protection", ["tariff", "protection american industry"], ["duties", "wool"]),
  210|     ("civil_service", "Civil service reform", ["civil service reform"], ["office", "spoils"]),
  211|     ("labor", "Labor and contract labor", ["contract labor", "workingmen wages"], ["labor", "wages"]),
  212|     ("chinese", "Chinese immigration", ["chinese immigration"], ["chinese", "coolies"]),
  213|     ("prohibition", "Prohibition", ["prohibition"], ["liquor", "temperance"]),
  214|     ("monopolies", "Railroads and monopolies", ["monopolies", "railroad monopoly"], ["corporations", "rates"]),
  215|     ("solid_south", "The Solid South and the colored vote", ["solid south", "colored voters"], ["southern", "negro"]),
  216|     ("silver", "Silver coinage", ["silver coinage", "silver dollar"], ["silver", "currency"]),
  217| ])
  218| year(1888, "1888-11-06", ["Harrison", "Morton", "Cleveland", "Thurman", "Fisk", "Prohibition party",
  219|                           "Union Labor"] + GENERIC_PARTY, [
  220|     ("tariff_reform", "Tariff reform / the Mills bill", ["tariff reform", "mills bill"], ["duties", "protection"]),
  221|     ("surplus", "The Treasury surplus", ["treasury surplus"], ["surplus", "taxation"]),
  222|     ("wool_protection", "Wool, wages and protection", ["wool tariff", "free wool"], ["wool", "wages"]),
  223|     ("pensions", "Soldiers' pensions", ["pension veto", "soldiers pensions"], ["pension", "veterans"]),
  224|     ("trusts", "Trusts", ["trusts"], ["trust", "monopoly"]),
  225|     ("chinese", "Chinese exclusion", ["chinese exclusion"], ["chinese", "coolies"]),
  226|     ("prohibition", "Prohibition", ["prohibition"], ["liquor", "saloon"]),
  227|     ("civil_service", "Civil service reform", ["civil service reform"], ["office", "reform"]),
  228| ])
  229| year(1892, "1892-11-08", ["Cleveland", "Stevenson", "Harrison", "Reid", "Weaver", "Field", "Bidwell",
  230|                           "Populist", "Populists", "People's party", "Peoples party", "Prohibition party"]
  231|      + GENERIC_PARTY, [
  232|     ("tariff", "The McKinley tariff", ["mckinley tariff", "tariff reform"], ["duties", "protection"]),
  233|     ("force_bill", "The Force Bill / federal elections", ["force bill"], ["federal", "elections"]),
  234|     ("silver", "Free silver", ["free silver", "silver coinage"], ["silver", "currency"]),
  235|     ("homestead_strike", "The Homestead strike and labor", ["homestead strike", "pinkertons"], ["strikers", "labor"]),
  236|     ("farmers_alliance", "Farmers' Alliance and the sub-treasury", ["farmers alliance", "sub-treasury"], ["farmers", "alliance"]),
  237|     ("pensions", "Pensions", ["pensions"], ["pension", "soldiers"]),
  238|     ("prohibition", "Prohibition", ["prohibition"], ["liquor", "saloon"]),
  239|     ("railroads_monopolies", "Railroads and monopolies", ["railroad monopolies", "trusts"], ["rates", "corporations"]),
  240| ])
  241| year(1896, "1896-11-03", ["McKinley", "Hobart", "Bryan", "Sewall", "Watson", "Palmer", "Buckner", "Cleveland",
  242|                           "Populist", "Populists", "People's party", "Peoples party", "Popocrat", "Popocrats"]
  243|      + GENERIC_PARTY, [
  244|     ("free_silver", "Free silver at 16 to 1", ["free coinage silver", "free silver"], ["silver", "coinage", "16 to 1"]),
  245|     ("gold_standard", "The gold standard / sound money", ["gold standard", "sound money"], ["gold", "money"]),
  246|     ("tariff", "Protective tariff", ["protective tariff", "protection"], ["duties", "tariff"]),
  247|     ("farm_prices", "Farm prices and mortgages", ["price of wheat", "farmers mortgages"], ["wheat", "cotton", "prices"]),
  248|     ("trusts_railroads", "Trusts and railroads", ["trusts monopolies", "railroad rates"], ["corporations", "trust"]),
  249|     ("labor_injunctions", "Labor and government by injunction", ["government by injunction", "workingmen wages"], ["labor", "injunction"]),
  250|     ("income_tax", "The income tax and the Supreme Court", ["income tax"], ["income", "court"]),
  251|     ("bonds_reserve", "Bond issues and the gold reserve", ["bond issue gold reserve", "bonds"], ["bonds", "reserve"]),
  252| ])
  253| year(1900, "1900-11-06", ["McKinley", "Roosevelt", "Bryan", "Stevenson", "Debs", "Woolley", "Populist",
  254|                           "Populists"] + GENERIC_PARTY, [
  255|     ("imperialism", "Imperialism and the Philippines", ["imperialism", "philippines"], ["filipinos", "colonies"]),
  256|     ("trusts", "Trusts", ["trusts"], ["trust", "monopoly"]),
  257|     ("free_silver", "Free silver", ["free silver"], ["silver", "coinage"]),
  258|     ("prosperity", "Prosperity and wages (full dinner pail)", ["full dinner pail", "prosperity wages"], ["wages", "work"]),
  259|     ("coal_strike", "The anthracite coal strike", ["anthracite strike", "coal miners strike"], ["miners", "strike"]),
  260|     ("china", "China and the Boxer crisis", ["china boxers", "pekin"], ["china", "troops"]),
  261|     ("boers", "The Boer War", ["boers"], ["boer", "england"]),
  262|     ("disfranchisement", "Black disfranchisement in the South", ["disfranchise negro", "suffrage amendment"], ["negro", "suffrage"]),
  263| ])
  264| year(1904, "1904-11-08", ["Roosevelt", "Fairbanks", "Parker", "Davis", "Debs", "Swallow", "Watson",
  265|                           "Populist", "Populists"] + GENERIC_PARTY, [
  266|     ("trusts", "Trusts and corporations", ["trusts", "beef trust"], ["trust", "corporations"]),
  267|     ("tariff", "Tariff revision", ["tariff revision", "tariff"], ["duties", "protection"]),
  268|     ("philippines", "The Philippines", ["philippines"], ["filipinos", "islands"]),
  269|     ("panama_canal", "The Panama Canal", ["panama canal"], ["canal", "isthmus"]),
  270|     ("labor_strikes", "Strikes and labor (Colorado, packinghouse)", ["strike miners", "packing house strike"], ["strike", "union"]),
  271|     ("race_suffrage", "Race and the suffrage in the South", ["negro question", "disfranchisement"], ["negro", "suffrage"]),
  272|     ("pensions", "Pensions (Order No. 78)", ["pension order"], ["pension", "veterans"]),
  273|     ("cost_of_living", "Prices and wages", ["cost of living", "prices wages"], ["prices", "wages"]),
  274| ])
  275| year(1908, "1908-11-03", ["Taft", "Sherman", "Bryan", "Kern", "Debs", "Chafin", "Roosevelt", "Hisgen",
  276|                           "Independence party"] + GENERIC_PARTY, [
  277|     ("trusts", "Trusts and corporations", ["trusts", "standard oil"], ["trust", "corporations"]),
  278|     ("tariff_revision", "Tariff revision", ["tariff revision"], ["duties", "schedules"]),
  279|     ("bank_guaranty", "Bank deposit guaranty after the 1907 panic", ["guaranty of bank deposits", "guarantee deposits"], ["deposits", "banks"]),
  280|     ("labor_injunctions", "Labor and injunctions", ["injunction labor", "injunctions"], ["labor", "courts"]),
  281|     ("railroad_rates", "Railroad rates and regulation", ["railroad rates"], ["rates", "commission"]),
  282|     ("prohibition", "Local and county option", ["local option", "county option"], ["saloon", "liquor"]),
  283|     ("campaign_contributions", "Publicity of campaign contributions", ["campaign contributions publicity"], ["contributions", "funds"]),
  284|     ("conservation", "Conservation of forests and water", ["conservation natural resources", "forests irrigation"], ["forests", "water"]),
  285| ])
  286| year(1912, "1912-11-05", ["Wilson", "Marshall", "Taft", "Sherman", "Butler", "Roosevelt", "Johnson", "Debs",
  287|                           "Seidel", "Chafin", "Progressive party", "Progressives", "Bull Moose",
  288|                           "Bull Moosers"] + GENERIC_PARTY, [
  289|     ("trusts", "Trusts and monopoly", ["trusts", "anti-trust"], ["trust", "monopoly"]),
  290|     ("tariff_cost_of_living", "Tariff and the high cost of living", ["high cost of living", "tariff revision"], ["prices", "duties"]),
  291|     ("direct_democracy", "Initiative, referendum and recall", ["initiative referendum recall"], ["recall", "referendum"]),
  292|     ("woman_suffrage", "Votes for women", ["woman suffrage", "votes for women"], ["suffrage", "women"]),
  293|     ("labor", "Child labor, wages and hours", ["child labor", "minimum wage"], ["labor", "wages"]),
  294|     ("income_tax", "The income tax amendment", ["income tax amendment"], ["income", "amendment"]),
  295|     ("currency_banking", "Currency reform and the money trust", ["currency reform", "money trust"], ["banks", "currency"]),
  296|     ("prohibition", "Saloons and local option", ["local option saloon", "prohibition"], ["saloon", "liquor"]),
  297| ])
  298| year(1916, "1916-11-07", ["Wilson", "Marshall", "Hughes", "Fairbanks", "Benson", "Hanly", "Roosevelt",
  299|                           "Progressive party", "Progressives", "Bull Moose"] + GENERIC_PARTY, [
  300|     ("preparedness", "Military preparedness", ["preparedness army navy"], ["preparedness", "navy"]),
  301|     ("european_war", "The European war and neutrality", ["neutrality", "submarine"], ["war", "neutral"]),
  302|     ("mexico", "Mexico and the border", ["mexican border", "villa"], ["mexico", "border", "guardsmen"]),
  303|     ("eight_hour_law", "The eight-hour railroad law", ["eight hour law", "adamson"], ["railroad", "brotherhoods"]),
  304|     ("hyphenates", "German-Americans and the hyphen", ["hyphenated", "german american"], ["hyphen", "german"]),
  305|     ("woman_suffrage", "Woman suffrage", ["woman suffrage"], ["suffrage", "women"]),
  306|     ("tariff", "Tariff", ["tariff"], ["duties", "protection"]),
  307|     ("prohibition", "Prohibition amendments", ["prohibition amendment", "dry"], ["saloon", "liquor"]),
  308| ])
  309| year(1928, "1928-11-06", ["Hoover", "Curtis", "Smith", "Robinson", "Thomas", "Coolidge", "Raskob",
  310|                           "Tammany"] + GENERIC_PARTY, [
  311|     ("prohibition", "Prohibition and enforcement", ["prohibition enforcement", "wet dry"], ["liquor", "eighteenth"]),
  312|     ("religion", "Religion in the campaign", ["catholic religious issue", "religious intolerance"], ["catholic", "protestant"]),
  313|     ("farm_relief", "Farm relief (McNary-Haugen)", ["farm relief", "mcnary-haugen"], ["farmers", "surplus"]),
  314|     ("prosperity", "Prosperity and business", ["prosperity", "business conditions"], ["prosperity", "employment"]),
  315|     ("tariff", "Tariff", ["tariff"], ["duties", "protection"]),
  316|     ("water_power", "Water power and Muscle Shoals", ["muscle shoals", "water power"], ["power", "utilities"]),
  317|     ("immigration", "Immigration restriction", ["immigration restriction", "national origins"], ["immigration", "quota"]),
  318|     ("women_voters", "Women voters", ["women voters"], ["women", "register"]),
  319| ])
  320| year(1932, "1932-11-08", ["Roosevelt", "Garner", "Hoover", "Curtis", "Thomas", "Foster", "Coolidge",
  321|                           "Raskob"] + GENERIC_PARTY, [
  322|     ("unemployment_relief", "Unemployment and relief", ["unemployment relief", "jobless"], ["unemployed", "relief"]),
  323|     ("farm_crisis", "Farm prices and foreclosures", ["farm holiday", "farm mortgage foreclosure"], ["farmers", "prices"]),
  324|     ("prohibition_repeal", "Repeal of prohibition", ["prohibition repeal", "repeal eighteenth amendment"], ["repeal", "liquor"]),
  325|     ("banks", "Bank failures and hoarding", ["bank failure depositors", "hoarding"], ["bank", "deposits"]),
  326|     ("veterans_bonus", "The veterans' bonus and the Bonus Army", ["bonus army", "veterans bonus"], ["bonus", "veterans"]),
  327|     ("tariff", "Tariff", ["tariff"], ["duties", "smoot"]),
  328|     ("rfc_public_works", "Federal loans and public works (RFC)", ["reconstruction finance corporation", "public works"], ["loans", "works"]),
  329|     ("taxes_economy", "Taxes and government economy", ["sales tax", "taxes economy"], ["tax", "budget"]),
  330| ])
  331| year(1936, "1936-11-03", ["Roosevelt", "Garner", "Landon", "Knox", "Lemke", "Thomas", "Browder", "Hoover",
  332|                           "Union party", "New Deal", "New Dealers"] + GENERIC_PARTY, [
  333|     ("social_security", "Social security and old-age pensions", ["social security", "old age pension"], ["pension", "security"]),
  334|     ("townsend_plan", "The Townsend plan", ["townsend plan"], ["townsend", "pension"]),
  335|     ("relief_wpa", "Relief and the WPA", ["works progress administration", "relief"], ["relief", "wpa"]),
  336|     ("drought_farm", "Drought and farm programs", ["drought", "agricultural adjustment"], ["farmers", "drought"]),
  337|     ("labor_organizing", "Labor organizing (CIO)", ["labor union organize", "cio"], ["union", "labor"]),
  338|     ("spending_debt", "Spending and the national debt", ["national debt", "government spending"], ["debt", "spending"]),
  339|     ("trade_agreements", "Reciprocal trade agreements", ["reciprocal trade agreements"], ["trade", "tariff"]),
  340|     ("supreme_court", "The Supreme Court and the NRA/AAA", ["supreme court decision", "nra"], ["court", "constitution"]),
  341| ])
  342| year(1940, "1940-11-05", ["Roosevelt", "Wallace", "Willkie", "McNary", "Thomas", "Browder", "Garner",
  343|                           "New Deal", "New Dealers"] + GENERIC_PARTY, [
  344|     ("aid_to_britain", "Aid to Britain / destroyers deal", ["aid to britain", "destroyers"], ["britain", "aid"]),
  345|     ("draft", "The peacetime draft", ["selective service registration", "conscription"], ["draft", "registration"]),
  346|     ("third_term", "The third-term tradition", ["third term"], ["tradition", "term"]),
  347|     ("defense_jobs", "Defense spending and jobs", ["national defense contracts", "unemployment"], ["defense", "jobs"]),
  348|     ("keep_out_of_war", "Keeping out of the war", ["keep out of war", "isolation"], ["war", "peace"]),
  349|     ("farm_prices", "Farm prices", ["farm prices"], ["farmers", "prices"]),
  350|     ("labor", "Labor, wages and hours", ["wages hours", "labor union"], ["labor", "wages"]),
  351|     ("relief_wpa", "Relief and the WPA", ["wpa relief"], ["relief", "wpa"]),
  352| ])
  353| year(1944, "1944-11-07", ["Roosevelt", "Truman", "Dewey", "Bricker", "Thomas", "Wallace",
  354|                           "New Deal", "New Dealers"] + GENERIC_PARTY, [
  355|     ("soldier_vote", "Servicemen voting", ["soldier vote", "absentee ballots servicemen"], ["ballots", "servicemen"]),
  356|     ("postwar_jobs", "Postwar jobs and reconversion", ["postwar jobs", "reconversion"], ["jobs", "postwar"]),
  357|     ("world_organization", "A postwar world organization", ["dumbarton oaks", "world organization peace"], ["peace", "nations"]),
  358|     ("rationing_prices", "Rationing and price control", ["rationing", "price control opa"], ["ration", "prices"]),
  359|     ("labor_pac", "Labor and the CIO-PAC", ["political action committee", "labor union"], ["labor", "union"]),
  360|     ("taxes", "Taxes", ["taxes"], ["tax", "income"]),
  361|     ("veterans", "Veterans' benefits (GI Bill)", ["veterans benefits", "gi bill"], ["veterans", "benefits"]),
  362|     ("farm_prices", "Farm prices", ["farm prices"], ["farmers", "prices"]),
  363| ])
  364| year(1948, "1948-11-02", ["Truman", "Barkley", "Dewey", "Warren", "Thurmond", "Wright", "Wallace", "Taylor",
  365|                           "Dixiecrat", "Dixiecrats", "States' Rights", "States Rights", "Progressive party",
  366|                           "Progressives"] + GENERIC_PARTY, [
  367|     ("inflation", "High prices and inflation", ["high prices inflation", "cost of living"], ["prices", "inflation"]),
  368|     ("housing", "The housing shortage", ["housing shortage"], ["housing", "homes"]),
  369|     ("taft_hartley", "Taft-Hartley and labor", ["taft-hartley"], ["labor", "union"]),
  370|     ("civil_rights", "Civil rights and the poll tax", ["civil rights", "poll tax"], ["negro", "rights"]),
  371|     ("berlin_cold_war", "Berlin and the Soviet Union", ["berlin airlift", "russia"], ["soviet", "berlin"]),
  372|     ("communism_home", "Communists at home", ["un-american activities", "communists"], ["communist", "spy"]),
  373|     ("farm_price_supports", "Farm price supports", ["price supports", "farm prices"], ["farmers", "supports"]),
  374|     ("draft", "The peacetime draft", ["draft registration", "selective service"], ["draft", "registration"]),
  375| ])
  376| year(1952, "1952-11-04", ["Eisenhower", "Ike", "Nixon", "Stevenson", "Sparkman", "Truman", "Hallinan",
  377|                           "Taft", "Kefauver"] + GENERIC_PARTY, [
  378|     ("korea", "The Korean War", ["korea war", "korea truce"], ["korea", "troops"]),
  379|     ("communism", "Communists in government", ["communists in government", "communism"], ["communist", "loyalty"]),
  380|     ("corruption", "Corruption in government", ["corruption", "mink coat"], ["corruption", "scandal"]),
  381|     ("inflation_controls", "Prices, inflation and controls", ["price controls", "inflation"], ["prices", "controls"]),
  382|     ("taxes", "Taxes", ["taxes"], ["tax", "income"]),
  383|     ("tidelands_oil", "Tidelands oil", ["tidelands oil"], ["tidelands", "oil"]),
  384|     ("civil_rights", "Civil rights and FEPC", ["fepc", "civil rights"], ["rights", "negro"]),
  385|     ("farm_prices", "Farm price supports", ["farm price supports", "farm prices"], ["farmers", "prices"]),
  386| ])
  387| year(1956, "1956-11-06", ["Eisenhower", "Ike", "Nixon", "Stevenson", "Kefauver", "Truman"] + GENERIC_PARTY, [
  388|     ("suez_hungary", "Suez and Hungary", ["suez", "hungary"], ["egypt", "soviet"]),
  389|     ("h_bomb_tests", "H-bomb tests and the draft", ["h-bomb tests", "hydrogen bomb tests"], ["bomb", "tests"]),
  390|     ("school_desegregation", "School desegregation", ["desegregation", "integration schools"], ["segregation", "schools"]),
  391|     ("farm_soil_bank", "Farm prices and the soil bank", ["soil bank", "farm prices"], ["farmers", "prices"]),
  392|     ("highways", "The highway program", ["highway program", "interstate highway"], ["highway", "roads"]),
  393|     ("labor", "Labor and wages", ["labor union wages"], ["union", "wages"]),
  394|     ("taxes", "Taxes and the budget", ["taxes balanced budget"], ["tax", "budget"]),
  395|     ("cost_of_living", "Cost of living", ["cost of living"], ["prices", "living"]),
  396| ])
  397| year(1960, "1960-11-08", ["Kennedy", "Johnson", "Nixon", "Lodge", "Eisenhower", "Ike", "Jack",
  398|                           "Kennedy-Johnson", "Nixon-Lodge"] + GENERIC_PARTY, [
  399|     ("cuba_castro", "Castro and Cuba", ["castro cuba"], ["castro", "cuba"]),
  400|     ("khrushchev_cold_war", "Khrushchev and the cold war", ["khrushchev", "soviet"], ["soviet", "khrushchev"]),
  401|     ("defense_missiles", "Missiles and national defense", ["missile gap", "missiles defense"], ["missile", "defense"]),
  402|     ("civil_rights", "Civil rights and sit-ins", ["sit-in", "civil rights"], ["negro", "rights"]),
  403|     ("religion", "Religion and the presidency", ["catholic president", "religious issue"], ["catholic", "religion"]),
  404|     ("economy_jobs", "Recession and unemployment", ["unemployment recession"], ["jobs", "unemployment"]),
  405|     ("farm_surplus", "Farm surplus and prices", ["farm surplus", "farm prices"], ["farmers", "surplus"]),
  406|     ("medical_care_aged", "Medical care for the aged", ["medical care aged", "social security medical"], ["aged", "medical"]),
  407| ])
  408| 
  409| # --------------------------------------------------------------------- http
  410| _last = {}
  411| INTERVAL = {"www.loc.gov": 3.2, "tile.loc.gov": 1.5}
  412| LOG: list = []
  413| 
  414| 
  415| def _sleep_for(host):
  416|     gap = INTERVAL.get(host, 1.5)
  417|     t = _last.get(host, 0)
  418|     now = time.time()
  419|     if now - t < gap:
  420|         time.sleep(gap - (now - t))
  421|     _last[host] = time.time()
  422| 
  423| 
  424| def fetch_json(url, cache_dir):
  425|     key = hashlib.sha1(url.encode()).hexdigest()
  426|     p = os.path.join(cache_dir, "http", key[:2], key + ".json")
  427|     if os.path.exists(p):
  428|         with open(p) as f:
  429|             rec = json.load(f)
  430|         return rec["body"], rec["ts"]
  431|     host = urllib.parse.urlparse(url).netloc
  432|     delay = 15
  433|     for attempt in range(8):
  434|         _sleep_for(host)
  435|         try:
  436|             req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
  437|             with urllib.request.urlopen(req, timeout=60) as r:
  438|                 raw = r.read().decode("utf-8", "replace")
  439|             body = json.loads(raw)
  440|             ts = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
  441|             os.makedirs(os.path.dirname(p), exist_ok=True)
  442|             with open(p, "w") as f:
  443|                 json.dump({"url": url, "ts": ts, "body": body}, f)
  444|             return body, ts
  445|         except urllib.error.HTTPError as e:
  446|             if e.code in (429, 500, 502, 503, 504, 520, 521, 522, 524, 525):
  447|                 ra = e.headers.get("Retry-After") if e.headers else None
  448|                 wait = max(delay, int(ra) if ra and ra.isdigit() else 0)
  449|                 print(f"  [http {e.code}] backoff {wait}s {url[:100]}", file=sys.stderr)
  450|                 time.sleep(wait)
  451|                 delay = min(delay * 2, 300)
  452|                 continue
  453|             if e.code == 404:
  454|                 return None, None
  455|             print(f"  [http {e.code}] giving up {url[:100]}", file=sys.stderr)
  456|             return None, None
  457|         except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError, http.client.HTTPException) as e:
  458|             print(f"  [err {type(e).__name__}] backoff {delay}s {url[:100]}", file=sys.stderr)
  459|             time.sleep(delay)
  460|             delay = min(delay * 2, 300)
  461|     return None, None
  462| 
  463| 
  464| def search(q, y, state, cache_dir, c=20, facets=False):
  465|     cfg = Y[y]
  466|     params = [("q", q), ("dates", f"{y}-09-01/{cfg['cutoff'].isoformat()}"), ("fo", "json"), ("c", str(c)),
  467|               ("at", "results,pagination" + (",facets" if facets else ""))]
  468|     if state:
  469|         params.append(("fa", f"location_state:{state}"))
  470|     url = SEARCH + "?" + urllib.parse.urlencode(params)
  471|     body, ts = fetch_json(url, cache_dir)
  472|     total = None
  473|     res, fac = [], {}
  474|     if body:
  475|         total = (body.get("pagination") or {}).get("of")
  476|         res = body.get("results") or []
  477|         for f in body.get("facets") or []:
  478|             if f.get("field") == "location_state" or "location_state" in str(f.get("type", "")):
  479|                 for it in f.get("filters", []):
  480|                     fac[it.get("title", "").lower()] = it.get("count", 0)
  481|     LOG.append(dict(ts=ts, q=q, state=state or "—", total=total, returned=len(res)))
  482|     return res, fac
  483| 
  484| 
  485| def ocr_url_for(r):
  486|     w = r.get("word_coordinates_url") or ""
  487|     qs = urllib.parse.parse_qs(urllib.parse.urlparse(w).query)
  488|     seg = (qs.get("segment") or [None])[0]
  489|     if not seg:
  490|         return None
  491|     return ("https://tile.loc.gov/text-services/word-coordinates-service?segment="
  492|             + urllib.parse.quote(seg, safe="") + "&format=alto_xml&full_text=1")
  493| 
  494| 
  495| def fetch_ocr(url, cache_dir):
  496|     body, ts = fetch_json(url, cache_dir)
  497|     if not body or not isinstance(body, dict):
  498|         return None, ts
  499|     for v in body.values():
  500|         if isinstance(v, dict) and "full_text" in v:
  501|             return v["full_text"], ts
  502|     return None, ts
  503| 
  504| 
  505| # ------------------------------------------------------------------- text
  506| _DICT = None
  507| 
  508| 
  509| def words_dict():
  510|     global _DICT
  511|     if _DICT is None:
  512|         s = set()
  513|         for p in ("/usr/share/dict/words", "/usr/share/dict/web2"):
  514|             if os.path.exists(p):
  515|                 with open(p, errors="ignore") as f:
  516|                     s.update(w.strip().lower() for w in f)
  517|         s.update("a i the of and to in is was for on that by with as at from are be this which it "
  518|                  "he his they their has have had not but or an its were been will would who all".split())
  519|         _DICT = s
  520|     return _DICT
  521| 
  522| 
  523| def in_dict(w):
  524|     d = words_dict()
  525|     if w in d:
  526|         return True
  527|     for suf in ("'s", "s", "es", "ed", "d", "ing", "ly", "ies", "ers", "er", "ment", "ments"):
  528|         if w.endswith(suf) and len(w) - len(suf) >= 2:
  529|             b = w[: -len(suf)]
  530|             if b in d or (suf == "ies" and b + "y" in d) or (suf in ("ed", "ing") and b + "e" in d):
  531|                 return True
  532|     return False
  533| 
  534| 
  535| def normalize_ocr(t):
  536|     t = t.replace("^^", "").replace("^", " ").replace("\n", " ")
  537|     t = re.sub(r"(\w)- (\w)", r"\1\2", t)  # remaining line-break hyphens
  538|     return re.sub(r"\s+", " ", t).strip()
  539| 
  540| 
  541| STRAY = re.compile(r"^[\|■•»«\*\^_~`ijI!l1;:,\.'\"]{1,2}$")
  542| 
  543| 
  544| def clean_tokens(toks):
  545|     """Light cleaning: drop stray margin chars silently; collapse runs of garbage
  546|     tokens to [OCR illegible]. Returns (tokens, changed_with_brackets)."""
  547|     out, changed = [], False
  548|     for w in toks:
  549|         if STRAY.match(w) and w.lower() not in ("i", "a"):
  550|             continue
  551|         letters = sum(ch.isalpha() for ch in w)
  552|         bad = len(w) >= 3 and letters / len(w) < 0.5 and not re.match(r"^[\$\d,\.%-]+$", w)
  553|         if bad:
  554|             if not out or out[-1] != "[OCR illegible]":
  555|                 out.append("[OCR illegible]")
  556|                 changed = True
  557|             continue
  558|         out.append(w)
  559|     return out, changed
  560| 
  561| 
  562| def quality(toks):
  563|     al = [re.sub(r"[^a-z']", "", w.lower()).strip("'") for w in toks]
  564|     al = [w for w in al if len(w) >= 2]
  565|     if not al:
  566|         return 0.0
  567|     return sum(in_dict(w) for w in al) / len(al)
  568| 
  569| 
  570| AD_RX = re.compile(r"\b(pills?|sarsaparilla|druggists?|cures?d?|liniment|bitters|remedy|per bottle|"
  571|                    r"for sale|bargains?|ladies'? (?:hats|suits)|catarrh|rheumatism|kidney|dyspepsia|"
  572|                    r"sale price|special sale)\b", re.I)
  573| PRED_RX = re.compile(r"\b(electoral votes?|will carry|carry the state|majority of \d|plurality|"
  574|                      r"straw vote|poll shows|betting odds|even money)\b", re.I)
  575| 
  576| 
  577| def kw_list(topic):
  578|     """Search and extra keywords, cut to 7 letters so they match as word prefixes."""
  579|     _, _, queries, extra = topic
  580|     stop = {"the", "of", "and", "to", "in", "for", "by", "a", "on", "with", "out", "is"}
  581|     kws = {w[:7] for q in queries for w in re.split(r"[\s\-]+", q.lower()) if w and w not in stop and len(w) > 2}
  582|     kws.update(w.lower()[:7] for w in extra)
  583|     return sorted(kws)
  584| 
  585| 
  586| def best_window(toks, kws, W=125):
  587|     lows = [re.sub(r"[^a-z0-9]", "", w.lower()) for w in toks]
  588|     hit = [1 if any(l.startswith(k.replace(" ", "")) for k in kws) and l else 0 for l in lows]
  589|     if len(toks) <= W:
  590|         return 0, len(toks), sum(hit)
  591|     pref = [0]
  592|     for h in hit:
  593|         pref.append(pref[-1] + h)
  594|     best, bs = -1, 0
  595|     for s in range(0, len(toks) - W + 1):
  596|         v = pref[s + W] - pref[s]
  597|         if v > best:
  598|             best, bs = v, s
  599|     # centre the window on the hits a little: shift start back to a sentence start
  600|     s = bs
  601|     for j in range(bs, max(bs - 25, -1), -1):
  602|         if j > 0 and re.search(r"[\.\?!]['\"]?$", toks[j - 1]) and toks[j][:1].isupper():
  603|             s = j
  604|             break
  605|     e = min(len(toks), s + 120)
  606|     for j in range(e, min(len(toks), s + 160)):
  607|         if re.search(r"[\.\?!]['\"]?$", toks[j - 1]):
  608|             e = j
  609|             break
  610|     else:
  611|         for j in range(e, max(s + 90, e - 30), -1):
  612|             if re.search(r"[\.\?!]['\"]?$", toks[j - 1]):
  613|                 e = j
  614|                 break
  615|     return s, e, pref[e] - pref[s]
  616| 
  617| 
  618| def cand_regex(y):
  619|     names = Y[y]["names"]
  620|     pat = r"\b(" + "|".join(re.escape(n) for n in sorted(names, key=len, reverse=True)) + r")\b"
  621|     rx_names = re.compile(pat)
  622|     rx_gen = re.compile(r"\b(ticket|nominee|nominees|presidential candidate)\b", re.I)
  623|     return lambda t: bool(rx_names.search(t) or rx_gen.search(t))
  624| 
  625| 
  626| def lean_of(paper, y):
  627|     p = paper.lower()
  628|     if "springfield republican" in p:
  629|         return "ind"
  630|     if re.search(r"\b(labor|socialist|appeal to reason|worker|toiler|union record)\b", p):
  631|         return "ind"
  632|     if y >= 1856 and re.search(r"\brepublican\b", p) and "democrat" not in p:
  633|         return "R"
  634|     if re.search(r"\bdemocrat", p) and "republican" not in p:
  635|         return "D"
  636|     return "unknown"
  637| 
  638| 
  639| def shingles(text, n=5):
  640|     w = re.findall(r"[a-z]+", text.lower())
  641|     return {" ".join(w[i:i + n]) for i in range(max(0, len(w) - n + 1))}
  642| 
  643| 
  644| # ------------------------------------------------------------------- build
  645| def first(v):
  646|     if isinstance(v, list):
  647|         return v[0] if v else None
  648|     return v
  649| 
  650| 
  651| def select(cands, topics, target):
  652|     """Up to `target` items: per topic, round-robin across the least-covered regions (candidate
  653|     mentions only once half the topic's quota is filled), then the leftovers by score; at most
  654|     4 items per paper and no near-duplicates (shingle overlap > 0.3)."""
  655|     per_topic = math.ceil(target / len(topics))
  656|     chosen, paper_n = [], {}
  657|     reg_n = {r: 0 for r in REGIONS + ["unknown"]}
  658| 
  659|     def ok(c):
  660|         if paper_n.get(c["lccn"], 0) >= 4:
  661|             return False
  662|         for o in chosen:
  663|             if o["lccn"] == c["lccn"] and o["date"] == c["date"] and o["page"] == c["page"]:
  664|                 return False
  665|             a, b = c["_sh"], o["_sh"]
  666|             if a and b and len(a & b) / max(1, min(len(a), len(b))) > 0.3:
  667|                 return False
  668|         return True
  669| 
  670|     leftovers = []
  671|     for topic in topics:
  672|         pool = sorted([c for c in cands if c["topic"] == topic[0]], key=lambda c: -c["_score"])
  673|         got = 0
  674|         while got < per_topic and pool:
  675|             regs = sorted(REGIONS, key=lambda r: reg_n[r])
  676|             pick = None
  677|             for reg in regs:
  678|                 for c in pool:
  679|                     if c["region"] == reg and ok(c) and not (c["mentions_candidates"] and got < per_topic // 2):
  680|                         pick = c
  681|                         break
  682|                 if pick:
  683|                     break
  684|             if not pick:
  685|                 for c in pool:
  686|                     if ok(c):
  687|                         pick = c
  688|                         break
  689|             if not pick:
  690|                 break
  691|             pool.remove(pick)
  692|             chosen.append(pick)
  693|             paper_n[pick["lccn"]] = paper_n.get(pick["lccn"], 0) + 1
  694|             reg_n[pick["region"]] = reg_n.get(pick["region"], 0) + 1
  695|             got += 1
  696|         leftovers += pool
  697|     for c in sorted(leftovers, key=lambda c: -c["_score"]):
  698|         if len(chosen) >= target:
  699|             break
  700|         if ok(c):
  701|             chosen.append(c)
  702|             paper_n[c["lccn"]] = paper_n.get(c["lccn"], 0) + 1
  703|     return chosen
  704| 
  705| 
  706| def build_year(y, cache_dir, out_dir, target=88, verbose=True):
  707|     cfg = Y[y]
  708|     LOG.clear()
  709|     start, cutoff = dt.date(y, 9, 1), cfg["cutoff"]
  710|     is_cand = cand_regex(y)
  711|     topics = cfg["topics"]
  712|     seen_pages = set()
  713|     cands = []
  714|     rejected = {"date": 0, "no_ocr": 0, "low_quality": 0, "few_hits": 0, "territory": 0}
  715|     used_states = {r: {} for r in REGIONS}
  716| 
  717|     def consider(r, ti, q):
  718|         rid = r.get("id") or ""
  719|         if rid in seen_pages:
  720|             return
  721|         seen_pages.add(rid)
  722|         d = r.get("date")
  723|         try:
  724|             dd = dt.date.fromisoformat(d)
  725|         except (TypeError, ValueError):  # missing or malformed date
  726|             rejected["date"] += 1
  727|             return
  728|         if not (start <= dd <= cutoff):
  729|             rejected["date"] += 1
  730|             return
  731|         state = (first(r.get("location_state")) or "").lower()
  732|         if state in ("hawaii", "alaska") and y < 1960:
  733|             rejected["territory"] += 1
  734|             return
  735|         ou = ocr_url_for(r)
  736|         if not ou:
  737|             rejected["no_ocr"] += 1
  738|             return
  739|         txt, ts = fetch_ocr(ou, cache_dir)
  740|         if not txt:
  741|             rejected["no_ocr"] += 1
  742|             return
  743|         toks = normalize_ocr(txt).split(" ")
  744|         kws = kw_list(topics[ti])
  745|         s, e, hits = best_window(toks, kws)
  746|         raw = toks[s:e]
  747|         qual = quality(raw)
  748|         if qual < 0.70:
  749|             rejected["low_quality"] += 1
  750|             return
  751|         if hits < 3:
  752|             rejected["few_hits"] += 1
  753|             return
  754|         ctoks, changed = clean_tokens(raw)
  755|         excerpt = " ".join(ctoks).strip()
  756|         nwords = len(excerpt.split())
  757|         if nwords < 60:
  758|             rejected["few_hits"] += 1
  759|             return
  760|         mc = is_cand(excerpt)
  761|         ads = len(AD_RX.findall(excerpt))
  762|         preds = len(PRED_RX.findall(excerpt))
  763|         score = hits / max(1, nwords) * 40 + (qual - 0.7) * 20 - 4 * mc - 2.5 * ads - 2 * preds
  764|         m = re.search(r"[?&]sp=(\d+)", rid)
  765|         sp = m.group(1) if m else "1"
  766|         lccn = first(r.get("number_lccn")) or ""
  767|         paper = first(r.get("partof_title")) or (r.get("title") or "")
  768|         url = re.sub(r"&q=.*$", "", r.get("url") or rid).replace("http://", "https://")
  769|         cands.append(dict(
  770|             id=f"ca-{lccn}-{d}-{sp}", year=y, date=d, paper=paper,
  771|             city=(first(r.get("location_city")) or "").title(), state=state.title(),
  772|             region=REGION.get(state, "unknown"), lccn=lccn, page=int(sp),
  773|             url=url, ocr_url=ou, topic=topics[ti][0], topic_code=f"T{ti + 1}",
  774|             topic_label=topics[ti][1], query=q, excerpt=excerpt, excerpt_words=nwords,
  775|             excerpt_is_verbatim=not changed, mentions_candidates=mc, leans=lean_of(paper, y),
  776|             ocr_quality=round(qual, 3), retrieved_at=ts, _score=score, _sh=shingles(excerpt)))
  777| 
  778|     for ti, topic in enumerate(topics):
  779|         label, desc, queries, extra = topic
  780|         if verbose:
  781|             print(f"[{y}] T{ti + 1} {label}", file=sys.stderr)
  782|         # loc.gov searches take ~30 s each server-side, so: national searches with
  783|         # larger pages first, then a state-facet search only for regions that
  784|         # are still short of candidates for this topic.
  785|         res, fac = search(queries[0], y, None, cache_dir, c=40, facets=True)
  786|         for r in res[:10]:
  787|             consider(r, ti, queries[0])
  788|         for q in queries[1:]:
  789|             rs, _ = search(q, y, None, cache_dir, c=30)
  790|             for r in rs[:8]:
  791|                 consider(r, ti, q)
  792|         for reg in REGIONS:
  793|             have = sum(1 for c in cands if c["topic"] == label and c["region"] == reg)
  794|             if have >= 2:
  795|                 continue
  796|             opts = [(c, s) for s, c in fac.items() if REGION.get(s) == reg and c > 0
  797|                     and not (s in ("hawaii", "alaska") and y < 1960)]
  798|             if not opts:
  799|                 continue
  800|             opts.sort(key=lambda cs: (used_states[reg].get(cs[1], 0), -cs[0]))
  801|             st = opts[0][1]
  802|             used_states[reg][st] = used_states[reg].get(st, 0) + 1
  803|             rs, _ = search(queries[0], y, st, cache_dir, c=15)
  804|             for r in rs[:6]:
  805|                 consider(r, ti, queries[0])
  806| 
  807|     chosen = select(cands, topics, target)
  808|     chosen.sort(key=lambda c: (c["topic_code"], c["date"], c["id"]))
  809|     assert all(c["date"] <= cutoff.isoformat() for c in chosen)
  810|     os.makedirs(out_dir, exist_ok=True)
  811|     outp = os.path.join(out_dir, f"corpus_{y}.jsonl")
  812|     with open(outp, "w") as f:
  813|         for c in chosen:
  814|             f.write(json.dumps({k: v for k, v in c.items() if not k.startswith("_")}, ensure_ascii=False) + "\n")
  815|     meta = dict(year=y, election=cfg["election"].isoformat(), cutoff=cutoff.isoformat(),
  816|                 n_items=len(chosen), n_candidates=len(cands), n_queries=len(LOG),
  817|                 pages_seen=len(seen_pages), rejected=rejected,
  818|                 topics=[dict(code=f"T{i + 1}", label=t[0], desc=t[1], queries=t[2],
  819|                              n=sum(c["topic"] == t[0] for c in chosen),
  820|                              regions={r: sum(c["topic"] == t[0] and c["region"] == r for c in chosen)
  821|                                       for r in REGIONS}) for i, t in enumerate(topics)],
  822|                 mentions_candidates=sum(c["mentions_candidates"] for c in chosen),
  823|                 verbatim=sum(c["excerpt_is_verbatim"] for c in chosen),
  824|                 leans={k: sum(c["leans"] == k for c in chosen) for k in ("R", "D", "ind", "unknown")},
  825|                 states=sorted({c["state"] for c in chosen}),
  826|                 date_range=[min((c["date"] for c in chosen), default=None),
  827|                             max((c["date"] for c in chosen), default=None)],
  828|                 queries=list(LOG))
  829|     with open(os.path.join(cache_dir, f"meta_{y}.json"), "w") as f:
  830|         json.dump(meta, f, indent=1, default=str)
  831|     print(f"[{y}] wrote {len(chosen)} items ({len(cands)} candidates, {len(LOG)} queries) -> {outp}",
  832|           file=sys.stderr)
  833|     return meta
  834| 
  835| 
  836| def provenance_md(years, cache_dir):
  837|     out = []
  838|     for y in years:
  839|         p = os.path.join(cache_dir, f"meta_{y}.json")
  840|         if not os.path.exists(p):
  841|             continue
  842|         with open(p) as f:
  843|             m = json.load(f)
  844|         ts = [q["ts"] for q in m["queries"] if q.get("ts")]
  845|         out.append(f"\n### corpus_{y}.jsonl\n")
  846|         out.append(f"- Election {m['election']}; cutoff {m['cutoff']}; search filter "
  847|                    f"`dates={y}-09-01/{m['cutoff']}`. Item dates {m['date_range'][0]} to {m['date_range'][1]}.")
  848|         out.append(f"- **{m['n_items']} items** from {m['n_candidates']} scored candidates "
  849|                    f"({m['pages_seen']} distinct pages returned); {m['n_queries']} searches"
  850|                    + (f", retrieved {min(ts)} to {max(ts)} UTC" if ts else "") + ".")
  851|         out.append(f"- Rejected before scoring: {m['rejected']}.")
  852|         out.append(f"- `mentions_candidates=true`: {m['mentions_candidates']}; verbatim: {m['verbatim']}; "
  853|                    f"leans: {m['leans']}; states ({len(m['states'])}): {', '.join(m['states'])}.")
  854|         out.append("\n| Code | topic | Items | NE | MW | S | W | Queries |\n|---|---|---|---|---|---|---|---|")
  855|         for t in m["topics"]:
  856|             r = t["regions"]
  857|             out.append(f"| {t['code']} | `{t['label']}` — {t['desc']} | {t['n']} | {r['Northeast']} | "
  858|                        f"{r['Midwest']} | {r['South']} | {r['West']} | {'; '.join('`'+q+'`' for q in t['queries'])} |")
  859|     return "\n".join(out)
  860| 
  861| 
  862| def main():
  863|     ap = argparse.ArgumentParser()
  864|     ap.add_argument("years", nargs="+", type=int)
  865|     ap.add_argument("--cache-dir", default=DEFAULT_CACHE)
  866|     ap.add_argument("--out-dir", default=DEFAULT_OUT)
  867|     ap.add_argument("--target", type=int, default=88)
  868|     ap.add_argument("--provenance", action="store_true")
  869|     a = ap.parse_args()
  870|     os.makedirs(a.cache_dir, exist_ok=True)
  871|     if a.provenance:
  872|         print(provenance_md(a.years, a.cache_dir))
  873|         return
  874|     for y in a.years:
  875|         if y not in Y:
  876|             print(f"no config for {y}", file=sys.stderr)
  877|             continue
  878|         try:
  879|             build_year(y, a.cache_dir, a.out_dir, target=a.target)
  880|         except Exception as e:  # keep going across years
  881|             print(f"[{y}] FAILED: {type(e).__name__}: {e}", file=sys.stderr)
  882| 
  883| 
  884| if __name__ == "__main__":
  885|     main()
```

## `scripts/harness/build_franchise.py`

```python
    1| """Build franchise/state_franchise_all.csv: the legal franchise by state, presidential years 1868–1968.
    2| 
    3| Columns: year,state,poll_tax,literacy_test,alien_voting,women_vote,white_can,black_can,
    4|          felony_disenfranchised_share,voting_age,chosen_by,source,note
    5| 
    6| Sources:
    7|   poll_tax, literacy_test: Gray & Jenkins (2024) State-Level Data File, doi:10.7910/DVN/QIY9EM,
    8|     rows elec_type==1 (presidential), 1872–1968. 1868 uses the state's 1870 row [I]
    9|     (the file starts in 1870). DC (1964, 1968): no poll tax, no literacy test.
   10|   women_vote: Teele (2018) presidential-suffrage year (franchise/women_suffrage_pre19th.csv)
   11|     <= election year; every state from 1920 (19th Amendment).
   12|   alien_voting: declarant-alien voting, Keyssar (2000) The Right to Vote, Table A.12, and
   13|     Hayduk (2006) Democracy for All, ch. 2 — year ranges transcribed from those tables
   14|     without the book to hand, so tagged [I] (Gray & Jenkins has no alien-voting field).
   15|   voting_age: 21; GA 18 from 1944 (1943 amendment); KY 18 from 1956 (1955 amendment);
   16|     AK 19 and HI 20 from 1960 (statehood constitutions).
   17|   black_can / white_can: 1 from 1870 (15th Amendment). 1868: Black men barred by law
   18|     outside New England (except CT), WI, NE, and the reconstructed South; NY's $250
   19|     property test for Black men [I]; ex-Confederate test oaths in MO, TN, WV, AR [I].
   20|   felony_disenfranchised_share: blank (no state-level estimate before 1970; Gray &
   21|     Jenkins' exfelon law flag is kept in the note).
   22|   chosen_by: from labels/state_pres_all.csv.
   23| 
   24| Run: ~/.venvs/simharness/bin/python scripts/harness/build_franchise.py
   25| """
   26| from __future__ import annotations
   27| 
   28| import sys
   29| from pathlib import Path
   30| 
   31| import numpy as np
   32| import pandas as pd
   33| 
   34| HERE = Path(__file__).resolve().parent
   35| sys.path.insert(0, str(HERE.parents[1]))  # the repo root
   36| from simharness.config import CACHE  # noqa: E402
   37| 
   38| FR = CACHE / 'franchise'
   39| OUT = FR / 'state_franchise_all.csv'
   40| YEARS = list(range(1868, 1969, 4))
   41| 
   42| # Declarant-alien voting for president: state → (first, last) election year it applied.
   43| # Keyssar (2000) Table A.12; Hayduk (2006) [I].
   44| ALIEN = {
   45|     'WI': (1848, 1908), 'MI': (1850, 1894), 'IN': (1851, 1921), 'MN': (1857, 1896), 'OR': (1859, 1914),
   46|     'KS': (1861, 1918), 'NE': (1867, 1918), 'MO': (1865, 1921), 'TX': (1869, 1921), 'AR': (1868, 1926),
   47|     'AL': (1867, 1901), 'FL': (1868, 1894), 'GA': (1868, 1877), 'SC': (1868, 1895), 'LA': (1879, 1898),
   48|     'CO': (1876, 1902), 'ND': (1889, 1909), 'SD': (1889, 1918),
   49| }
   50| # 1868: Black men legally able to vote (share of adult Black men) [I].
   51| BLACK_1868 = {s: 0.0 for s in ['CA', 'CT', 'DE', 'IL', 'IN', 'KS', 'KY', 'MD', 'MI', 'MO', 'NJ', 'NV', 'OH', 'OR',
   52|                                'PA', 'WV', 'IA', 'MN']}
   53| BLACK_1868['NY'] = 0.1  # $250 freehold test for Black men only [I]
   54| # 1868: whites barred by ex-Confederate test oaths [I].
   55| WHITE_1868 = {'MO': 0.80, 'TN': 0.70, 'WV': 0.85, 'AR': 0.85}
   56| 
   57| 
   58| def voting_age(state: str, year: int) -> int:
   59|     if year >= 1972:
   60|         return 18
   61|     if state == 'GA' and year >= 1944:
   62|         return 18
   63|     if state == 'KY' and year >= 1956:
   64|         return 18
   65|     if state == 'AK' and year >= 1960:
   66|         return 19
   67|     if state == 'HI' and year >= 1960:
   68|         return 20
   69|     return 21
   70| 
   71| 
   72| def main():
   73|     gj = pd.read_csv(FR / 'raw/GrayJenkins_State-Level_Data_File.tab', sep='\t')
   74|     icp = pd.read_csv(FR / 'grayjenkins_state_franchise_1916_1920_1924.csv').drop_duplicates('state')
   75|     code = dict(zip(icp.icpsr_state.astype(int), icp.state))
   76|     gj['st'] = gj.state.astype(int).map(code)
   77|     pres = gj[gj.elec_type == 1].set_index(['year', 'st'])
   78|     first70 = gj[gj.year == 1870].sort_values('elec_type').drop_duplicates('st').set_index('st')
   79|     w = pd.read_csv(FR / 'women_suffrage_pre19th.csv').set_index('state')
   80|     wy = w.presidential_suffrage_year.combine_first(w.full_suffrage_year).to_dict()
   81|     ret = pd.read_csv(CACHE / 'labels/state_pres_all.csv')
   82|     rows = []
   83|     for _, r in ret[ret.year.isin(YEARS)].iterrows():
   84|         y, s = int(r.year), r.state
   85|         notes, src = [], []
   86|         if s == 'DC':
   87|             pt, lt, ex = 0, 0, np.nan
   88|             src.append('DC: no poll tax or literacy test')
   89|         elif y == 1868:
   90|             g = first70.loc[s] if s in first70.index else None
   91|             pt, lt, ex = (np.nan, np.nan, np.nan) if g is None else (g.poll_tax, g.lit_test, g.exfelon)
   92|             src.append('Gray&Jenkins doi:10.7910/DVN/QIY9EM 1870 row [I]')
   93|         else:
   94|             g = pres.loc[(y, s)]
   95|             pt, lt, ex = g.poll_tax, g.lit_test, g.exfelon
   96|             src.append('Gray&Jenkins doi:10.7910/DVN/QIY9EM elec_type 1')
   97|         py = wy.get(s)
   98|         wv = int(y >= 1920 or (py is not None and pd.notna(py) and float(py) <= y))
   99|         if y == 1920 and s in ('GA', 'MS'):
  100|             notes.append('women could not register in time for Nov 1920 (closed_1920)')
  101|         src.append('women: Teele doi:10.7910/DVN/EVYI2H')
  102|         a = ALIEN.get(s)
  103|         av = int(a is not None and a[0] <= y <= a[1])
  104|         if a is not None:
  105|             src.append('alien: Keyssar 2000 Table A.12 / Hayduk 2006 [I]')
  106|         bc = BLACK_1868.get(s, 1.0) if y == 1868 else 1.0
  107|         wc = WHITE_1868.get(s, 1.0) if y == 1868 else 1.0
  108|         if y == 1868 and (s in BLACK_1868 or s in WHITE_1868):
  109|             notes.append('pre-15th Amendment exclusions [I]')
  110|         if pd.notna(ex):
  111|             notes.append(f'exfelon law (GJ)={int(ex)}')
  112|         rows.append({'year': y, 'state': s, 'poll_tax': pt, 'literacy_test': lt, 'alien_voting': av, 'women_vote': wv,
  113|                      'white_can': wc, 'black_can': bc, 'felony_disenfranchised_share': np.nan,
  114|                      'voting_age': voting_age(s, y), 'chosen_by': r.chosen_by, 'source': '; '.join(src),
  115|                      'note': '; '.join(notes)})
  116|     out = pd.DataFrame(rows)
  117|     for c in ('poll_tax', 'literacy_test'):
  118|         out[c] = out[c].astype('Int64')
  119|     out.to_csv(OUT, index=False)
  120|     print(f'wrote {OUT} ({len(out)} rows)')
  121|     print(out.groupby('year')[['poll_tax', 'literacy_test', 'alien_voting', 'women_vote']].sum().T.to_string())
  122|     print('missing poll_tax:', out[out.poll_tax.isna()][['year', 'state']].values.tolist())
  123| 
  124| 
  125| if __name__ == '__main__':
  126|     main()
```
