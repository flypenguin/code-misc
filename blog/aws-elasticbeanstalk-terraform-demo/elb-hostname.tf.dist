# not as easy as it seems.
# first, you need to figure out the hosted zone ID of the
# ELB region. This can be done by looking here:
#           http://docs.aws.amazon.com/general/latest/gr/rande.html#elasticbeanstalk_region
# (source: this ticket: https://github.com/hashicorp/terraform/issues/7071)
# then you need to add it :)


# let's make it easy and figure out the zone ID by the zone itself
data "aws_route53_zone" "myzone" {
  name         = "ENTER_YOUR_ZONE_HERE."
  private_zone = true
}

data "aws_region" "current" {
  current = true
}

resource "aws_route53_record" "www" {
  zone_id = "${data.aws_route53_zone.myzone.zone_id}"
  name    = "${var.app_dns_name}.${var.app_subdomain_name}.${data.aws_route53_zone.myzone.name}"
  type    = "A"

  alias {
    name                   = "${aws_elastic_beanstalk_environment.test_env.cname}"
    zone_id                = "${var.elb_hosted_zones["${data.aws_region.current.name}"]}"
    evaluate_target_health = true
  }
}
