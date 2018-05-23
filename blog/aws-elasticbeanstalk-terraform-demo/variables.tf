# ============================================================================
# settings unrelated for elastic beanstalk ;)

variable "cname_prefix" {}

variable "app_dns_name" {
  default = "elbapp"
}

variable "app_subdomain_name" {
  default = "elbtest"
}

# ============================================================================
# required settings

variable "vpc_id" {}

variable "instance_role" {}

variable "subnets" {
  type = "list"
}

# sometimes required, don't know why
variable "ebs_service_role" {}

# ============================================================================
# settings for the ASG (hosts)

variable "asg_instance_type" {
  default = "t2.micro"
}

variable "asg_size_min" {
  default = "1"
}

variable "asg_size_max" {
  default = "4"
}

variable "asg_size_desired" {
  default = "2"
}

# yup, this is a thing. https://is.gd/QIH6IP
variable "asg_zones" {
  default = "Any 2"
}

variable "asg_security_groups" {
  type    = "list"
  default = []
}

# ============================================================================
# settings for scaling triggers

# Metric used for your Auto Scaling trigger.
# Valid values:
#   CPUUtilization, NetworkIn, NetworkOut, DiskWriteOps, DiskReadBytes,
#   DiskReadOps, DiskWriteBytes, Latency, RequestCount, HealthyHostCount,
#   UnhealthyHostCount
variable "asg_trigger_measure_name" {
  default = "CPUUtilization"
}

# Amount of time, in minutes, a metric can be beyond its defined limit
# (as specified in the UpperThreshold and LowerThreshold) before the trigger
# fires.
variable "asg_trigger_breach_duration" {
  default = "5"
}

# If the measurement falls below this number for the breach duration,
# a trigger is fired. (this default is for CPU usage)
variable "asg_trigger_lower_threshold" {
  default = "70"
}

# If the measurement is higher than this number for the breach duration,
# a trigger is fired. (this default is for CPU usage)
variable "asg_trigger_upper_threshold" {
  default = "85"
}

# How many Amazon EC2 instances to remove when performing a scaling activity.
variable "asg_trigger_lower_breach_scale_increment" {
  default = "-2"
}

# How many Amazon EC2 instances to add when performing a scaling activity.
variable "asg_trigger_upper_breach_scale_increment" {
  default = "4"
}

# Specifies how frequently Amazon CloudWatch measures the metrics for your
# trigger.
variable "asg_trigger_period" {
  default = "5"
}

# Statistic the trigger should use, such as Average.
# valid values: Minimum, Maximum, Sum, Average
variable "asg_trigger_statistic" {
  default = "Average"
}

# Unit for the trigger measurement, such as Bytes.
# valid values:
#     Seconds, Percent, Bytes, Bits, Count, Bytes/Second, Bits/Second,
#     Count/Second, None
variable "asg_trigger_unit" {
  default = "Percent"
}

# ============================================================================
# ELB settings

variable "elb_subnets" {
  type = "list"
}

variable "elb_cross_zone" {
  default = "true"
}

# "internal" for vpc only, "external" for public ELBs
variable "elb_scheme" {
  default = "internal"
}

variable "elb_drain_connections" {
  default = "true"
}

# ============================================================================
# rolling update settings

# The number of instances included in each batch of the rolling update.
variable "rupd_max_batch_size" {
  default = ""
}

# The minimum number of instances that must be in service within the
# autoscaling group while other instances are terminated.
variable "rupd_min_instances_in_service" {
  default = ""
}

# If true, enables rolling updates for an environment. Rolling updates are
# useful when you need to make small, frequent updates to your Elastic
# Beanstalk software application and you want to avoid application downtime.
# Setting this value to true automatically enables the MaxBatchSize,
# MinInstancesInService, and PauseTime options. Setting any of those options
# also automatically sets the RollingUpdateEnabled option value to true.
# Setting this option to false disables rolling updates.
variable "rupd_enabled" {
  default = "false"
}

# Time-based rolling updates apply a PauseTime between batches. Health-based
# rolling updates wait for new instances to pass health checks before moving
# on to the next batch. Immutable updates launch a full set of instances in
# a new AutoScaling group.
variable "rupd_type" {
  default = "Time"
}

# ============================================================================
# docker settings

# N/A

# ============================================================================
# other stuff

# see here:
# http://docs.aws.amazon.com/general/latest/gr/rande.html#elasticbeanstalk_region
# don't change. it's static.
variable "elb_hosted_zones" {
  type    = "map"
  default = {
    "us-east-2"      = "Z14LCN19Q5QHIC"
    "us-east-1"      = "Z117KPS5GTRQ2G"
    "us-west-1"      = "Z1LQECGX5PH1X"
    "us-west-2"      = "Z38NKT9BP95V3O"
    "ca-central-1"   = "ZJFCZL7SSZB5I"
    "ap-south-1"     = "Z18NTBI3Y7N9TZ"
    "ap-northeast-2" = "Z3JE5OI70TWKCP"
    "ap-southeast-1" = "Z16FZ9L249IFLT"
    "ap-southeast-2" = "Z2PCDNR3VC2G1N"
    "ap-northeast-1" = "Z1R25G3KIG2GBW"
    "eu-central-1"   = "Z1FRNW7UH4DEZJ"
    "eu-west-1"      = "Z2NYPWQ7DFZAZH"
    "eu-west-2"      = "Z1GKAAAUGATPF1"
    "sa-east-1"      = "Z10X7K2B4QSOFV"
  }
}


