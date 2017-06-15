# docker logging tests

Shamelessly stolen from [deviantony/docker-elk](https://github.com/deviantony/docker-elk).

Modified everything a bit, and not Kibana seems to be not working. Annoying, but the rest seems ok. So far. Well.


## Used links

* [fluentd filter plugin](http://docs.fluentd.org/v0.12/articles/filter_record_transformer#ltrecordgt-directive)
* [elastic search api](https://www.elastic.co/guide/en/elasticsearch/reference/current/search-search.html)
* [fluentd docker logging receipes](http://www.fluentd.org/guides/recipes/docker-logging)
* [fluentd logging in elastic & s3](http://www.fluentd.org/guides/recipes/elasticsearch-and-s3)
* [docker-logging-efk-compose](http://docs.fluentd.org/v0.12/articles/docker-logging-efk-compose)
* [process apachelogs with fluentd](http://docs.fluentd.org/v0.12/articles/filter-modify-apache)
* [add needed dev packages to image](https://github.com/cybercode/alpine-ruby)
* [show layers of docker image](http://blog.arungupta.me/show-layers-of-docker-image/)