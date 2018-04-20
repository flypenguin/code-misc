FROM fluent/fluentd

# no plugins, no fun
# uninstall dev packages later to keep image small

RUN \
     apk --update add build-base ruby-dev libc-dev \
  && gem install fluent-plugin-elasticsearch fluent-plugin-concat \
  && apk del build-base ruby-dev libc-dev \
  && apk add libffi libstdc++ ruby-libs yaml \
  && rm -rf /var/cache/apk/*



# this should add a layer with about ~10M size
# check with "docker history IMAGENAME"