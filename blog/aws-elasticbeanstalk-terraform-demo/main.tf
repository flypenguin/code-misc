resource "aws_elastic_beanstalk_application" "test_app" {
  name        = "test-app"
  description = "Test of CVS beanstalk deployment"
}

resource "aws_elastic_beanstalk_environment" "test_env" {
  name                = "test-env"
  application         = "${aws_elastic_beanstalk_application.test_app.name}"
  solution_stack_name = "64bit Amazon Linux 2016.09 v2.5.2 running Docker 1.12.6"
  cname_prefix        = "${var.cname_prefix}-test-app"

  # ..........................................................................
  # required settings

  setting {
    namespace = "aws:ec2:vpc"
    name      = "VPCId"
    value     = "${var.vpc_id}"
  }
  setting {
    namespace = "aws:ec2:vpc"
    name      = "Subnets"
    value     = "${join(",", var.subnets)}"
  }
  setting {
    namespace = "aws:autoscaling:launchconfiguration"
    name      = "IamInstanceProfile"
    value     = "${var.instance_role}"
  }
  setting {
    namespace = "aws:elasticbeanstalk:environment"
    name      = "ServiceRole"
    value     = "${var.ebs_service_role}"
  }

  # ..........................................................................
  # ASG (host) settings with defaults


  /*
  # maybe this causes problems
  setting {
      namespace = "aws:autoscaling:launchconfiguration"
      name      = "SecurityGroups"
      value     = "${join(",", var.asg_security_groups)}"
  }
  */

  setting {
    namespace = "aws:ec2:vpc"
    name      = "AssociatePublicIpAddress"
    value     = "false"
  }
  setting {
    namespace = "aws:autoscaling:launchconfiguration"
    name      = "InstanceType"
    value     = "${var.asg_instance_type}"
  }
  setting {
    namespace = "aws:autoscaling:asg"
    name      = "MinSize"
    value     = "${var.asg_size_min}"
  }
  setting {
    namespace = "aws:autoscaling:asg"
    name      = "MaxSize"
    value     = "${var.asg_size_max}"
  }
  setting {
    namespace = "aws:autoscaling:asg"
    name      = "Availability Zones"
    value     = "${var.asg_zones}"
  }
  setting {
    namespace = "aws:autoscaling:trigger"
    name      = "BreachDuration"
    value     = "${var.asg_trigger_breach_duration}"
  }
  setting {
    namespace = "aws:autoscaling:trigger"
    name      = "MeasureName"
    value     = "${var.asg_trigger_measure_name}"
  }
  setting {
    namespace = "aws:autoscaling:trigger"
    name      = "Period"
    value     = "${var.asg_trigger_period}"
  }
  setting {
    namespace = "aws:autoscaling:trigger"
    name      = "Statistic"
    value     = "${var.asg_trigger_statistic}"
  }
  setting {
    namespace = "aws:autoscaling:trigger"
    name      = "Unit"
    value     = "${var.asg_trigger_unit}"
  }
  setting {
    namespace = "aws:autoscaling:trigger"
    name      = "LowerBreachScaleIncrement"
    value     = "${var.asg_trigger_lower_threshold}"
  }
  setting {
    namespace = "aws:autoscaling:trigger"
    name      = "UpperBreachScaleIncrement"
    value     = "${var.asg_trigger_upper_breach_scale_increment}"
  }
  setting {
    namespace = "aws:autoscaling:trigger"
    name      = "LowerThreshold"
    value     = "${var.asg_trigger_lower_threshold}"
  }
  setting {
    namespace = "aws:autoscaling:trigger"
    name      = "UpperThreshold"
    value     = "${var.asg_trigger_upper_threshold}"
  }

  # ..........................................................................
  # ELB settings

  setting {
    namespace = "aws:ec2:vpc"
    name      = "ELBSubnets"
    value     = "${join(",", var.elb_subnets)}"
  }
  setting {
    namespace = "aws:ec2:vpc"
    name      = "ELBScheme"
    value     = "${var.elb_scheme}"
  }
  setting {
    namespace = "aws:elb:loadbalancer"
    name      = "CrossZone"
    value     = "${var.elb_cross_zone}"
  }
  setting {
    namespace = "aws:elb:policies"
    name      = "ConnectionDrainingEnabled"
    value     = "${var.elb_drain_connections}"
  }

  # ..........................................................................
  # rolling update settings

  setting {
    namespace = "aws:autoscaling:updatepolicy:rollingupdate"
    name      = "MaxBatchSize"
    value     = "${var.rupd_max_batch_size}"
  }
  setting {
    namespace = "aws:autoscaling:updatepolicy:rollingupdate"
    name      = "MinInstancesInService"
    value     = "${var.rupd_min_instances_in_service}"
  }
  setting {
    namespace = "aws:autoscaling:updatepolicy:rollingupdate"
    name      = "RollingUpdateEnabled"
    value     = "${var.rupd_enabled}"
  }
  setting {
    namespace = "aws:autoscaling:updatepolicy:rollingupdate"
    name      = "RollingUpdateType"
    value     = "${var.rupd_type}"
  }

  # ..........................................................................
  # environment variables in the application container :)


  /*
  setting {
    namespace = "aws:elasticbeanstalk:application:environment"
    name      = "MY_ENV_VAR"
    value     = "MY_ENV_VAR_VALUE"
  }
  */


  # ..........................................................................
  # other settings

  setting {
    namespace = "aws:elasticbeanstalk:application:environment"
    name      = "environment"
    value     = "uat"
  }
  setting {
    namespace = "aws:elasticbeanstalk:healthreporting:system"
    name      = "SystemType"
    value     = "enhanced"
  }
  setting {
    namespace = "aws:elasticbeanstalk:command"
    name      = "BatchSizeType"
    value     = "Fixed"
  }
  setting {
    namespace = "aws:elasticbeanstalk:command"
    name      = "BatchSize"
    value     = "1"
  }
  setting {
    namespace = "aws:elasticbeanstalk:command"
    name      = "DeploymentPolicy"
    value     = "Rolling"
  }
  tags {
    Name        = "${var.cname_prefix}-ebs-test"
    Team        = "${var.cname_prefix}-ebs-test"
    Environment = "DEV"
  }
}
